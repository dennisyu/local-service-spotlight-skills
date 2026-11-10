"""Stage -> model routing with provider adapters and one-rung-at-a-time escalation.

One runner owns the whole audit. There are no "lanes" waiting on other agents: every
stage is a function call that reads files and writes files in the run folder. That is
the fix for the Oct 25 cheap-lane pipeline, whose Gemini and Cursor lanes were work
orders filed in a repo that no running process ever read.

Providers
  anthropic   Messages API            ANTHROPIC_API_KEY
  openrouter  OpenAI-compatible chat  OPENROUTER_API_KEY   one key for Claude, DeepSeek, GPT, Grok, Gemini
  openai      Chat Completions        OPENAI_API_KEY
  gemini      generateContent         GEMINI_API_KEY
  manual      writes prompts/<stage>.md and waits for outputs/<stage>.json — for an app
              session (Muse, ChatGPT, Claude.ai) running the factory itself
  fake        deterministic stub for tests

Privacy on OpenRouter. Every call asks only for providers that do not collect user data
(provider.data_collection = "deny"). A confidential brief (one with do_not_print
items) also sets provider.zdr = true. That request flag follows the account's own privacy
setting: only an account set to "ZDR only" excludes OpenRouter's Safety Retention
endpoints, which may keep prompts and replies for safety review (self-serve accounts allow
them until you change it). If no endpoint qualifies, the call fails and the audit holds; it never
falls back to a provider that keeps or trains on data.

Reasoning. Sonnet, Opus and Fable think on every call, and several cheap models reason by default.
Thinking is billed as output and counts against the reply limit, so each stage names an
effort (deep for judgment, none or low for drafting) and its token limit is the answer
budget plus room for that effort.

Cost. The cost recorded for each OpenRouter call is the charge OpenRouter reports in the
reply (OpenRouter returns it on every response). The spending cap is checked before every
call against that call's worst case: every prompt byte counted as a token (a token is never
shorter than one byte), the whole reply limit spent, and the highest rate the call can be
charged. That rate includes a long-context tier when the prompt can reach it, and on
OpenRouter it is the ceiling the call itself sends as provider.max_price (the listed price
plus max_price_headroom), so no provider can charge more than the cap assumed. A call that
could cross the cap is never made.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import cost as K
from .cost import EFFORT_ROOM, effort_for  # noqa: F401  (re-exported for callers and tests)

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGES_DIR = ROOT / "stages"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
APP_URL = "https://github.com/dennisyu/local-service-spotlight-skills/tree/main/audit-factory"
APP_TITLE = "LSS Audit Factory"
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
FATAL_STATUS = {401, 402, 403}      # bad key, no credits, key not allowed: no other model fixes these
MODERATION = re.compile(r"moderat|flagged", re.I)   # a 403 for flagged input is about the text, not the key
MAX_RETRIES = 4
DEFAULT_MAX_OUT = 16000
DEFAULT_MODEL_MAX_OUT = 64000
FRAMING_TOKENS = 512                 # role markers and other per-call tokens a provider adds around the text
MAX_PRICE_HEADROOM = 1.25            # default; config may set "max_price_headroom"
# Prompts mark where their stable prefix ends (brief + ledger, then earlier stage files).
# Stages that call the same prefix more than once (page batches, fix rounds, review passes)
# ask Claude to cache up to each mark; every other provider just gets the joined text.
CACHE_MARK = "\n\n<!-- cache-break -->\n\n"
_sleep = time.sleep                 # tests replace this so retries do not wait


def _segments(user: str) -> list[str]:
    return [s for s in user.split(CACHE_MARK) if s]


def _flat(user: str) -> str:
    return "\n\n".join(_segments(user))


def _claude_user(user: str, cache: bool):
    """User content for a Claude call: one cache breakpoint at each prefix mark when caching pays."""
    segs = _segments(user)
    if not cache or len(segs) < 2:
        return _flat(user)
    parts = [{"type": "text", "text": s} for s in segs]
    for p in parts[:-1][:3]:            # Claude allows four breakpoints; the system card uses one
        p["cache_control"] = {"type": "ephemeral"}
    return parts


class Pending(Exception):
    """A manual stage is waiting for its output file."""


class ProviderError(Exception):
    """A provider refused or failed the call after retries. `fatal` means stop the audit."""

    def __init__(self, msg: str, status: int | None = None):
        super().__init__(msg)
        self.status = status
        self.fatal = status in FATAL_STATUS and not (status == 403 and MODERATION.search(msg))


class BudgetExceeded(Exception):
    """The run's spending cap would be crossed. The audit holds instead of spending more."""


def _env_key(name: str) -> str:
    key = os.environ.get(name)
    if not key:
        raise ProviderError(f"{name} is not set. Export it from your own secret store; "
                            "never write it into the run folder or the repo.", 401)
    return key


def _error_detail(raw: bytes) -> str:
    try:
        d = json.loads(raw.decode() or "{}")
        e = d.get("error", d)
        return str(e.get("message") or e)[:300] if isinstance(e, dict) else str(e)[:300]
    except (ValueError, UnicodeDecodeError):
        return raw[:300].decode(errors="replace")


def _wait(attempt: int, retry_after: str | None) -> float:
    try:
        return min(float(retry_after), 60.0) if retry_after else min(2.0 ** attempt, 30.0)
    except ValueError:
        return min(2.0 ** attempt, 30.0)


def _post(url: str, headers: dict, body: dict, timeout: int = 600, retries: int = MAX_RETRIES) -> dict:
    """POST JSON. Retry rate limits, server errors and dropped connections with backoff
    (honouring Retry-After); raise ProviderError with the provider's own message otherwise."""
    host = urllib.parse.urlsplit(url).netloc
    data = json.dumps(body).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers={**headers, "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = _error_detail(e.read())
            if e.code in RETRY_STATUS and attempt < retries:
                _sleep(_wait(attempt, e.headers.get("retry-after")))
                continue
            raise ProviderError(f"HTTP {e.code} from {host}: {detail}", e.code) from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < retries:
                _sleep(_wait(attempt, None))
                continue
            raise ProviderError(f"could not reach {host}: {e}") from None
        err = out.get("error") if isinstance(out, dict) else None
        if err and not out.get("choices"):          # OpenRouter can report an upstream failure in a 200
            code = err.get("code") if isinstance(err, dict) else None
            if isinstance(code, int) and code in RETRY_STATUS and attempt < retries:
                _sleep(_wait(attempt, None))
                continue
            raise ProviderError(f"{host} returned an error: {_error_detail(json.dumps(out).encode())}",
                                code if isinstance(code, int) else None)
        return out
    raise ProviderError(f"no answer from {host}")    # unreachable; keeps type checkers honest


# ------------------------------------------------------------------ reasoning effort
def token_budget(p: dict, answer: int, effort: str | None) -> int:
    """The reply limit for one call: answer budget + room to think, capped by the model."""
    cap = int(p.get("max_out", DEFAULT_MODEL_MAX_OUT))
    return min(answer + EFFORT_ROOM.get(effort or "none", 0), cap)


def prompt_token_bound(system: str, user: str) -> int:
    """More tokens than the prompt can possibly be. Byte-level tokenizers never emit a token
    shorter than one byte, so a prompt has at most one token per UTF-8 byte, plus framing."""
    return len(system.encode("utf-8")) + len(_flat(user).encode("utf-8")) + FRAMING_TOKENS


def headroom(cfg: dict) -> float:
    return float(cfg.get("max_price_headroom", MAX_PRICE_HEADROOM))


def ceiling_rates(cfg: dict, model: str, prompt_tokens: float) -> dict:
    """The highest per-million rates one call of this size can be charged: the long-context tier
    when the prompt can reach it, raised by the max_price headroom on OpenRouter (where the
    call sends that ceiling, so a pricier provider is never chosen)."""
    p = K.price(cfg, model, prompt_tokens)
    h = headroom(cfg) if p.get("provider") == "openrouter" else 1.0
    return {k: float(p.get(k, 0) or 0) * h for k in ("in", "out", "cache_read", "cache_write")}


def max_price(cfg: dict, model: str, prompt_tokens: float) -> dict:
    """provider.max_price for an OpenRouter call, in dollars per million tokens."""
    r = ceiling_rates(cfg, model, prompt_tokens)
    return {"prompt": round(r["in"], 6), "completion": round(r["out"], 6)}


def worst_case_usd(cfg: dict, model: str, system: str, user: str, max_tokens: int) -> float:
    """An upper bound for one call: every prompt byte a token, every prompt token at the higher of
    the input and cache-write ceiling, and the whole reply limit spent at the output ceiling."""
    n_in = prompt_token_bound(system, user)
    r = ceiling_rates(cfg, model, n_in)
    return round((n_in * max(r["in"], r["cache_write"]) + max_tokens * r["out"]) / 1e6, 6)


# ------------------------------------------------------------------ providers
def _openrouter(p: dict, model: str, system: str, user: str, max_tokens: int, confidential: bool,
                cache: bool = False, effort: str | None = None, ceiling: dict | None = None) -> dict:
    key = _env_key("OPENROUTER_API_KEY")
    base = os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE).rstrip("/")
    route = p.get("route", model)
    if route.startswith("anthropic/"):       # Claude caches only where a breakpoint says so
        sys_msg = {"role": "system", "content": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]}
        user_content = _claude_user(user, cache)
    else:                                    # other providers cache repeated prefixes on their own
        sys_msg = {"role": "system", "content": system}
        user_content = _flat(user)
    body = {"model": route, "max_tokens": max_tokens,
            "messages": [sys_msg, {"role": "user", "content": user_content}],
            "provider": {"data_collection": "deny", **({"zdr": True} if confidential else {}),
                         **({"max_price": ceiling} if ceiling else {})}}
    if effort:
        body["reasoning"] = {"effort": effort}
    if p.get("temperature") is not None:     # newer Claude and GPT models take no temperature
        body["temperature"] = p["temperature"]
    if p.get("json_mode"):
        body["response_format"] = {"type": "json_object"}
    r = _post(f"{base}/chat/completions",
              {"authorization": f"Bearer {key}", "HTTP-Referer": APP_URL, "X-Title": APP_TITLE}, body)
    choice = (r.get("choices") or [{}])[0] or {}
    msg = choice.get("message") or {}
    u = r.get("usage") or {}
    ptd = u.get("prompt_tokens_details") or {}
    ctd = u.get("completion_tokens_details") or {}
    reported = u.get("cost")
    return {"text": msg.get("content") or "",
            "usage": {"in": u.get("prompt_tokens", 0) or 0, "out": u.get("completion_tokens", 0) or 0,
                      "cache_read": ptd.get("cached_tokens", 0) or 0, "cache_write": ptd.get("cache_write_tokens", 0) or 0,
                      "reasoning": ctd.get("reasoning_tokens", 0) or 0},
            "model": model, "provider": "openrouter", "served_by": r.get("provider"), "served_model": r.get("model"),
            "truncated": choice.get("finish_reason") == "length",
            "reported_usd": float(reported) if reported is not None else None}


def call(model: str, system: str, user: str, cfg: dict, max_tokens: int = DEFAULT_MAX_OUT,
         run_dir: pathlib.Path | None = None, stage: str = "stage", fake=None, confidential: bool = False,
         cache: bool = False, effort: str | None = None) -> dict:
    """Return {"text", "usage": {"in","out","cache_read","cache_write"}, "model", "provider", "truncated"}
    plus, for OpenRouter, "reported_usd" (the charge OpenRouter reports) and "served_by".
    max_tokens is the whole reply limit, thinking included (see token_budget)."""
    p = cfg["prices"][model]
    prov = p["provider"]
    if fake is not None:
        flat = _flat(user)
        text = fake(stage, model, system, flat)
        return {"text": text, "usage": {"in": len(flat) // 4, "out": len(text) // 4, "cache_read": 0, "cache_write": 0},
                "model": model, "provider": "fake", "truncated": False}
    if prov == "openrouter":
        return _openrouter(p, model, system, user, max_tokens, confidential, cache, effort,
                           ceiling=max_price(cfg, model, prompt_token_bound(system, user)))
    user = _flat(user) if prov != "anthropic" else user
    truncated = False
    if prov == "anthropic":
        body = {"model": model, "max_tokens": max_tokens,
                "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                "messages": [{"role": "user", "content": _claude_user(user, cache)}]}
        if effort:
            body["output_config"] = {"effort": effort}
        r = _post("https://api.anthropic.com/v1/messages",
                  {"x-api-key": _env_key("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01"}, body)
        text = "".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")
        u = r.get("usage", {})
        usage = {"in": u.get("input_tokens", 0), "out": u.get("output_tokens", 0),
                 "cache_read": u.get("cache_read_input_tokens", 0), "cache_write": u.get("cache_creation_input_tokens", 0)}
        truncated = r.get("stop_reason") == "max_tokens"
    elif prov == "openai":
        body = {"model": p.get("route", model), "temperature": 0.3, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        r = _post("https://api.openai.com/v1/chat/completions", {"authorization": f"Bearer {_env_key('OPENAI_API_KEY')}"}, body)
        choice = (r.get("choices") or [{}])[0] or {}
        text = (choice.get("message") or {}).get("content") or ""
        u = r.get("usage", {})
        usage = {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0), "cache_read": 0, "cache_write": 0}
        truncated = choice.get("finish_reason") == "length"
    elif prov == "gemini":
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/{p.get('route', model)}:generateContent"
               f"?key={_env_key('GEMINI_API_KEY')}")
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens}}
        r = _post(url, {}, body)
        cand = (r.get("candidates") or [{}])[0] or {}
        text = "".join(pt.get("text", "") for pt in (cand.get("content") or {}).get("parts", []))
        u = r.get("usageMetadata", {})
        usage = {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0), "cache_read": 0, "cache_write": 0}
        truncated = cand.get("finishReason") == "MAX_TOKENS"
    elif prov == "manual":
        assert run_dir is not None, "manual provider needs a run folder"
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
        out = run_dir / "outputs" / f"{stage}.json"
        if out.exists():
            return {"text": out.read_text(encoding="utf-8"), "usage": {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0},
                    "model": model, "provider": "manual", "truncated": False}
        (run_dir / "prompts" / f"{stage}.md").write_text(f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}\n", encoding="utf-8")
        raise Pending(f"answer {run_dir / 'prompts' / (stage + '.md')} and save the JSON to {out}")
    else:
        raise ValueError(f"no provider for {model}")
    return {"text": text, "usage": usage, "model": model, "provider": prov, "truncated": truncated}


def usd(cfg: dict, model: str, usage: dict) -> float:
    """List-price cost of one call from its token counts (USD), at the long-context rates when
    the prompt reached that tier."""
    p = K.price(cfg, model, usage.get("in", 0))
    fresh = max(usage["in"] - usage.get("cache_read", 0) - usage.get("cache_write", 0), 0)
    return round((fresh * p["in"] + usage.get("cache_read", 0) * p["cache_read"]
                  + usage.get("cache_write", 0) * p["cache_write"] + usage["out"] * p["out"]) / 1e6, 5)


def extract_json(text: str):
    """First JSON object/array in a model reply (fenced or bare)."""
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"):text.rfind("}") + 1] if "{" in text else text
    return json.loads(raw)


def ladder(cfg: dict, tier: str | None = None) -> list[str]:
    """The escalation ladder: the tier's own when it has one (so a one-key tier stays on one key)."""
    return (cfg["tiers"].get(tier, {}) if tier else {}).get("escalation") or cfg["escalation"]


def next_rung(cfg: dict, model: str, tier: str | None = None) -> str | None:
    steps = ladder(cfg, tier)
    if model not in steps:
        return steps[min(2, len(steps) - 1)]
    i = steps.index(model)
    return steps[i + 1] if i + 1 < len(steps) else None


def confidential_ok(cfg: dict, model: str) -> bool:
    """False for models flagged as unsafe with confidential briefs (the Oct 25 bake-off)."""
    return bool(cfg["prices"].get(model, {}).get("confidential_ok", True))


def safe_model(cfg: dict, model: str, confidential: bool, tier: str | None = None) -> str:
    """A confidential brief never goes to a flagged model: climb the ladder to the first safe one."""
    m = model
    while confidential and m and not confidential_ok(cfg, m):
        m = next_rung(cfg, m, tier)
    if m is None:
        raise ValueError(f"no model on the ladder above {model} is cleared for confidential briefs")
    return m


def spent(run_dir: pathlib.Path) -> float:
    """What this run has cost so far, from its own call log."""
    log_path = run_dir / "run.json"
    if not log_path.exists():
        return 0.0
    return round(sum(a.get("usd", 0) or 0 for a in json.loads(log_path.read_text()).get("attempts", [])), 5)


def run_stage(stage_id: str, user: str, tier: str, run_dir: pathlib.Path, check=None, cfg: dict | None = None,
              fake=None, max_escalations: int = 1, confidential: bool = False, max_usd: float | None = None,
              write: bool = True, model: str | None = None) -> dict:
    """Run one stage: call, parse, check; retry once with the error, then escalate one rung.
    model overrides the tier's model for this stage (the fix loop's one-rung-up round uses it).

    check(obj) -> list of problems (empty = accepted). Every attempt is logged with tokens
    and cost to run.json before anything else happens, so the per-audit attribution is
    measured, not estimated: OpenRouter attempts log the charge OpenRouter reported, the rest
    log list price. With confidential=True (the brief lists do-not-print items) flagged
    models are skipped. max_usd is the run's spending cap: a call whose worst case would
    cross it is never made. A reply cut off at its token limit is retried once on the same
    model with twice the room before the stage moves up a rung.
    """
    cfg = cfg or K.load_routing()
    st = next(s for s in cfg["stages"] if s["id"] == stage_id)
    system = (STAGES_DIR / st["card"]).read_text(encoding="utf-8")
    answer = int(st.get("max_out", DEFAULT_MAX_OUT))
    model = safe_model(cfg, model or cfg["tiers"][tier]["models"][stage_id], confidential, tier)
    log_path = run_dir / "run.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {"tier": tier, "attempts": []}
    escalations, prompt, boosted = 0, user, False
    for attempt in range(1, 6):
        p = cfg["prices"][model]
        effort = effort_for(p, st.get("effort"))
        limit = token_budget(p, answer * (2 if boosted else 1), effort)
        so_far = round(sum(a.get("usd", 0) or 0 for a in log["attempts"]), 6)
        if max_usd is not None and fake is None and p["provider"] not in ("manual", "none"):
            worst = worst_case_usd(cfg, model, system, prompt, limit)
            if so_far + worst > max_usd:
                raise BudgetExceeded(f"spending cap ${max_usd:.2f}: ${so_far:.4f} spent, and the {stage_id} call on "
                                     f"{model} could cost up to ${worst:.4f}")
        elif max_usd is not None and so_far >= max_usd:
            raise BudgetExceeded(f"spending cap ${max_usd:.2f} reached (${so_far:.4f} spent) before {stage_id}")
        t0 = time.time()
        entry = {"stage": stage_id, "attempt": attempt, "model": model, "effort": effort, "max_tokens": limit}
        res = None
        try:
            res = call(model, system, prompt, cfg, max_tokens=limit, run_dir=run_dir, stage=stage_id,
                       fake=fake, confidential=confidential, cache=bool(st.get("cache_prefix")), effort=effort)
        except ProviderError as e:
            entry.update({"provider": p["provider"], "usage": {"in": 0, "out": 0}, "usd": 0.0,
                          "seconds": round(time.time() - t0, 1), "problems": [f"provider error: {e}"]})
            log["attempts"].append(entry)
            log_path.write_text(json.dumps(log, indent=1))
            if e.fatal:
                raise
            problems = [f"provider error: {e}"]
        if res is not None:
            list_usd = usd(cfg, model, res["usage"])
            reported = res.get("reported_usd")
            entry.update({"provider": res["provider"], "usage": res["usage"],
                          "usd": round(reported, 6) if reported is not None else list_usd,
                          "usd_list": list_usd, "cost_source": "reported" if reported is not None else "list price",
                          "seconds": round(time.time() - t0, 1)})
            if res.get("served_by"):
                entry["served_by"] = res["served_by"]
            log["attempts"].append(entry)          # the charge is on the record before anything can fail
            log_path.write_text(json.dumps(log, indent=1))
            obj = None
            if res.get("truncated"):
                problems = [f"reply was cut off at its {limit}-token limit"]
            else:
                try:
                    obj = extract_json(res["text"])
                    if not isinstance(obj, dict):
                        problems = ["reply must be one JSON object, in the output shape your card defines"]
                    else:
                        problems = check(obj) if check else []
                except (ValueError, json.JSONDecodeError) as e:
                    problems = [f"reply was not valid JSON: {e}"]
                except Exception as e:                 # a malformed shape must not crash the run
                    problems = [f"reply did not match the output shape ({type(e).__name__}: {e})"]
            entry["problems"] = problems[:20]
            log_path.write_text(json.dumps(log, indent=1))
            if not problems:
                if write:
                    (run_dir / f"{stage_id}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
                return {"ok": True, "model": model, "obj": obj, "attempts": attempt}
            if res.get("truncated") and not boosted:  # a budget problem, not a writing problem
                boosted = True
                continue
            feedback = "\n".join(f"- {x}" for x in problems[:20])
            prompt = f"{user}\n\n# YOUR PREVIOUS ANSWER FAILED THESE CHECKS — fix every one and answer again\n{feedback}"
        if attempt % 2 == 0:  # two tries per rung, then one rung up
            up = next_rung(cfg, model, tier)
            if up is not None:
                up = safe_model(cfg, up, confidential, tier)
            if up is None or escalations >= max_escalations:
                break
            model, escalations, boosted = up, escalations + 1, False
    return {"ok": False, "model": model, "obj": None, "attempts": attempt}
