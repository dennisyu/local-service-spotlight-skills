"""The OpenRouter path, tested end to end without a key or a cent of spend.

A local stand-in for OpenRouter's chat-completions API answers every stage with the
public demo audit, the way a model would, and reports a cost per call the way OpenRouter
does. The tests drive the real HTTP adapter, the real pipeline and the real checks: what
the requests carry (privacy flags, cache breakpoints, JSON mode), retries, an out-of-credit
key, the spending cap, the four page batches, and a full audit run on the one-key tiers.
"""
from __future__ import annotations

import copy
import http.server
import json
import os
import pathlib
import shutil
import sys
import tempfile
import threading
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "audit-factory"
sys.path.insert(0, str(ROOT))

from factory20 import cli, cost, openrouter, pipeline, router  # noqa: E402
from factory20.testing import fake_from_fixture, split_fixture  # noqa: E402

DEMO = ROOT / "fixtures" / "demo"
AUDIT = json.loads((DEMO / "audit.json").read_text())
STAGE_OF = {"Stage 30": "identity", "Stage 40": "score", "Stage 50": "synthesis", "Stage 70": "actions",
            "Stage 80": "review"}
COST_PER_CALL = 0.001
CFG = cost.load_routing()
ROUTE_PRICE = {p["route"]: p for p in CFG["prices"].values() if p.get("provider") == "openrouter"}


class MockOpenRouter:
    """Answers POST /api/v1/chat/completions like OpenRouter: choices, usage with cost."""

    def __init__(self):
        self.requests: list[dict] = []
        self.script: list[tuple[int, dict, dict]] = []    # forced replies, consumed first
        self.cost = lambda body: COST_PER_CALL            # what OpenRouter "charges" for a call
        self.answer = fake_from_fixture(str(DEMO / "audit.json")).answer
        mock = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["content-length"])).decode())
                mock.requests.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()},
                                      "body": body})
                if mock.script:
                    status, headers, payload = mock.script.pop(0)
                else:
                    status, headers, payload = 200, {}, mock.reply(body)
                data = json.dumps(payload).encode()
                self.close_connection = True
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                self.send_header("connection", "close")
                self.end_headers()
                self.wfile.write(data)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}/api/v1"

    @staticmethod
    def text_of(content) -> str:
        return content if isinstance(content, str) else "".join(p.get("text", "") for p in content)

    def stage(self, body) -> str:
        system = self.text_of(body["messages"][0]["content"])
        user = self.text_of(body["messages"][1]["content"])
        for k, v in STAGE_OF.items():
            if k in system:
                return v
        return "pages" if "Write pages" in user else "fix"

    def reply(self, body) -> dict:
        user = self.text_of(body["messages"][1]["content"])
        obj = self.answer(self.stage(body), user)
        return {"id": "gen-test", "model": body["model"], "provider": "MockProvider",
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "```json\n" + json.dumps(obj) + "\n```"}}],
                "usage": {"prompt_tokens": len(user) // 4, "completion_tokens": 900,
                          "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
                          "completion_tokens_details": {"reasoning_tokens": 400}, "cost": self.cost(body)}}

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def run_dir(d: pathlib.Path, brief_extra: dict | None = None) -> pathlib.Path:
    shutil.copy(DEMO / "ledger.json", d / "ledger.json")
    shutil.copytree(DEMO / "assets", d / "assets")
    brief = {k: AUDIT["meta"][k] for k in cli.BRIEF_KEYS}
    brief.update(brief_extra or {})
    (d / "brief.json").write_text(json.dumps(brief))
    return d


class OpenRouterHTTPTests(unittest.TestCase):
    def setUp(self):
        self.mock = MockOpenRouter()
        self.env = {k: os.environ.get(k) for k in ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL")}
        os.environ["OPENROUTER_API_KEY"] = "test-key-not-a-secret"
        os.environ["OPENROUTER_BASE_URL"] = self.mock.base
        self.sleeps = []
        self._sleep, router._sleep = router._sleep, self.sleeps.append
        self.cfg = cost.load_routing()

    def tearDown(self):
        router._sleep = self._sleep
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.mock.close()

    # ---------------------------------------------------------------- one call
    def test_claude_route_carries_privacy_flag_attribution_and_cache_breakpoints(self):
        user = "BRIEF + LEDGER" + router.CACHE_MARK + "STAGE FILES" + router.CACHE_MARK + "the task"
        res = router.call("or:anthropic/claude-sonnet-5.5", "the card", user, self.cfg, max_tokens=12000, cache=True)
        req = self.mock.requests[-1]
        body = req["body"]
        self.assertEqual(req["path"], "/api/v1/chat/completions")
        self.assertEqual(req["headers"]["authorization"], "Bearer test-key-not-a-secret")
        self.assertEqual(req["headers"]["x-title"], router.APP_TITLE)
        self.assertEqual(body["model"], "anthropic/claude-sonnet-5.5")
        self.assertEqual(body["provider"], {"data_collection": "deny"})          # no zdr unless confidential
        self.assertNotIn("temperature", body)                                    # Claude 5.5 takes none
        self.assertEqual(body["max_tokens"], 12000)
        self.assertEqual(body["messages"][0]["content"][0]["cache_control"], {"type": "ephemeral"})
        parts = body["messages"][1]["content"]
        self.assertEqual([p["text"] for p in parts], ["BRIEF + LEDGER", "STAGE FILES", "the task"])
        self.assertEqual([("cache_control" in p) for p in parts], [True, True, False])
        self.assertEqual(res["reported_usd"], COST_PER_CALL)
        self.assertEqual(res["served_by"], "MockProvider")

    def test_confidential_call_asks_for_zero_retention_endpoints_only(self):
        router.call("or:anthropic/claude-opus-5.5", "card", "user", self.cfg, confidential=True)
        self.assertEqual(self.mock.requests[-1]["body"]["provider"], {"data_collection": "deny", "zdr": True})

    def test_open_model_gets_plain_text_json_mode_and_temperature(self):
        user = "BRIEF" + router.CACHE_MARK + "the task"
        router.call("or:deepseek/deepseek-v4.1-flash", "card", user, self.cfg, cache=True)
        body = self.mock.requests[-1]["body"]
        self.assertEqual(body["model"], "deepseek/deepseek-v4.1-flash")
        self.assertEqual(body["messages"][1]["content"], "BRIEF\n\nthe task")      # no marker leaks out
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual(body["temperature"], 0.3)

    def test_rate_limit_is_retried_with_the_servers_wait(self):
        self.mock.script = [(429, {"retry-after": "2"}, {"error": {"message": "rate limited", "code": 429}})]
        res = router.call("or:anthropic/claude-haiku-5.5", "card", "user", self.cfg)
        self.assertEqual(len(self.mock.requests), 2)
        self.assertEqual(self.sleeps, [2.0])
        self.assertEqual(res["reported_usd"], COST_PER_CALL)

    def test_upstream_error_inside_a_200_is_retried(self):
        self.mock.script = [(200, {}, {"error": {"message": "provider overloaded", "code": 503}})]
        router.call("or:anthropic/claude-haiku-5.5", "card", "user", self.cfg)
        self.assertEqual(len(self.mock.requests), 2)

    def test_missing_key_is_a_clear_fatal_error(self):
        os.environ.pop("OPENROUTER_API_KEY")
        with self.assertRaises(router.ProviderError) as e:
            router.call("or:anthropic/claude-haiku-5.5", "card", "user", self.cfg)
        self.assertTrue(e.exception.fatal)
        self.assertIn("OPENROUTER_API_KEY", str(e.exception))
        self.assertEqual(self.mock.requests, [])

    # ---------------------------------------------------------------- whole audits
    def test_full_audit_runs_through_the_one_key_lean_tier(self):
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False)
            self.assertEqual(res["verdict"], "READY", res)
            log = json.loads((d / "run.json").read_text())["attempts"]
            tier = self.cfg["tiers"]["openrouter-lean"]["models"]
            self.assertTrue(all(a["provider"] == "openrouter" for a in log))
            self.assertTrue(all(a["model"] == tier[a["stage"]] for a in log))
            self.assertTrue(all(a["cost_source"] == "reported" for a in log))
            self.assertAlmostEqual(res["usd"], COST_PER_CALL * len(self.mock.requests), places=6)
            self.assertEqual(sum(a["stage"] == "pages" for a in log), 4)          # four batches, not one reply
            self.assertEqual(sorted(p["n"] for p in json.loads((d / "pages.json").read_text())["pages"]),
                             list(range(3, 20)))
            bodies = [r["body"] for r in self.mock.requests]
            self.assertTrue(all(b["provider"]["data_collection"] == "deny" for b in bodies))
            self.assertFalse(any(router.CACHE_MARK.strip() in json.dumps(b) for b in bodies))
            claude_pages = [b for b in bodies if b["model"].startswith("anthropic/")
                            and isinstance(b["messages"][1]["content"], list)]
            self.assertTrue(claude_pages)                                         # review reuses the cached ledger

    def test_standard_through_openrouter_keeps_the_standard_models(self):
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter", render_pdf=False)
            self.assertEqual(res["verdict"], "READY", res)
            models = {r["body"]["model"] for r in self.mock.requests}
            self.assertEqual(models, {"anthropic/claude-sonnet-5.5", "anthropic/claude-opus-5.5"})

    def test_confidential_brief_never_reaches_a_flagged_model_on_openrouter(self):
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d), {"do_not_print": ["$14M valuation"]})
            res = pipeline.run(d, "openrouter-lean", render_pdf=False)
            self.assertEqual(res["verdict"], "READY", res)
            bodies = [r["body"] for r in self.mock.requests]
            self.assertFalse(any("deepseek" in b["model"] for b in bodies), {b["model"] for b in bodies})
            self.assertTrue(all(b["provider"] == {"data_collection": "deny", "zdr": True} for b in bodies))

    def test_out_of_credits_holds_the_audit_with_the_reason(self):
        self.mock.script = [(402, {}, {"error": {"message": "Insufficient credits", "code": 402}})]
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False)
            self.assertEqual(res["verdict"], "HOLD", res)
            self.assertIn("402", res["hold_reason"])
            self.assertIn("Insufficient credits", res["hold_reason"])
            self.assertEqual(len(self.mock.requests), 1)                          # no retry, no escalation

    def test_spending_cap_is_never_crossed(self):
        """Every call is charged its full worst case at list price, the most a real call can cost.
        The run must stop before the call that could cross the cap, never after it."""
        def worst(body):
            p = ROUTE_PRICE[body["model"]]
            chars = len(json.dumps(body["messages"], ensure_ascii=False))
            return (chars / router.CHARS_PER_TOKEN_FLOOR * max(p["in"], p["cache_write"]) + body["max_tokens"] * p["out"]) / 1e6
        self.mock.cost = worst
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False, max_usd=0.60)
            self.assertEqual(res["verdict"], "HOLD", res)
            self.assertIn("spending cap", res["hold_reason"])
            self.assertIn("could cost up to", res["hold_reason"])
            self.assertLessEqual(res["usd"], 0.60)
            self.assertGreater(len(self.mock.requests), 0)

    def test_a_cap_below_the_first_call_spends_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False, max_usd=0.01)
            self.assertEqual(res["verdict"], "HOLD", res)
            self.assertEqual(self.mock.requests, [])
            self.assertEqual(res["usd"], 0.0)

    def test_each_stage_sends_its_reasoning_effort_and_room_to_think(self):
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            pipeline.run(d, "openrouter-lean", render_pdf=False)
            by_stage = {}
            for r in self.mock.requests:
                by_stage.setdefault(self.mock.stage(r["body"]), r["body"])
            self.assertEqual(by_stage["identity"]["reasoning"], {"effort": "medium"})
            self.assertEqual(by_stage["identity"]["max_tokens"], 6000 + router.EFFORT_ROOM["medium"])
            self.assertEqual(by_stage["synthesis"]["reasoning"], {"effort": "high"})
            self.assertEqual(by_stage["pages"]["reasoning"], {"effort": "none"})      # DeepSeek can stop thinking
            self.assertEqual(by_stage["pages"]["max_tokens"], 12000)
            self.assertEqual(by_stage["review"]["reasoning"], {"effort": "high"})
            log = json.loads((d / "run.json").read_text())["attempts"]
            self.assertTrue(all(a["usage"].get("reasoning") == 400 for a in log))

    def test_claude_cannot_stop_thinking_so_drafting_gets_its_lowest_effort(self):
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            pipeline.run(d, "openrouter", render_pdf=False)
            pages = next(r["body"] for r in self.mock.requests if self.mock.stage(r["body"]) == "pages")
            self.assertEqual(pages["model"], "anthropic/claude-sonnet-5.5")
            self.assertEqual(pages["reasoning"], {"effort": "low"})
            self.assertEqual(pages["max_tokens"], 12000 + router.EFFORT_ROOM["low"])

    def test_a_reply_that_is_not_an_object_is_logged_and_retried(self):
        self.mock.script = [(200, {}, {"choices": [{"message": {"content": '["not an object"]'}, "finish_reason": "stop"}],
                                       "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.002}})]
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False)
            self.assertEqual(res["verdict"], "READY", res)
            first = json.loads((d / "run.json").read_text())["attempts"][0]
            self.assertEqual(first["usd"], 0.002)                                  # the charge is on the record
            self.assertIn("one JSON object", first["problems"][0])

    def test_a_cut_off_reply_gets_twice_the_room_on_the_same_model(self):
        self.mock.script = [(200, {}, {"choices": [{"message": {"content": '{"identity": {'}, "finish_reason": "length"}],
                                       "usage": {"prompt_tokens": 10, "completion_tokens": 12144, "cost": 0.12}})]
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False)
            self.assertEqual(res["verdict"], "READY", res)
            first, second = self.mock.requests[0]["body"], self.mock.requests[1]["body"]
            self.assertEqual(first["model"], second["model"])
            self.assertEqual(second["max_tokens"], 2 * 6000 + router.EFFORT_ROOM["medium"])
            log = json.loads((d / "run.json").read_text())["attempts"]
            self.assertIn("cut off", log[0]["problems"][0])

    def test_a_moderation_refusal_is_a_stage_problem_not_a_dead_key(self):
        self.mock.script = [(403, {}, {"error": {"message": "Input flagged by moderation", "code": 403}})]
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False)
            self.assertEqual(res["verdict"], "READY", res)
        self.mock.script = [(403, {}, {"error": {"message": "Key not allowed for this model", "code": 403}})]
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-lean", render_pdf=False)
            self.assertEqual(res["verdict"], "HOLD", res)
            self.assertIn("403", res["hold_reason"])

    def test_experimental_tier_runs_but_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            res = pipeline.run(d, "openrouter-budget", render_pdf=False)
            self.assertIn("experimental", res["warning"])
            self.assertEqual({r["body"]["model"] for r in self.mock.requests if self.mock.stage(r["body"]) == "review"},
                             {"openai/gpt-6.1-sol"})


class DirectProviderTests(unittest.TestCase):
    def test_a_missing_key_holds_the_audit_with_its_name(self):
        env = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with tempfile.TemporaryDirectory() as d:
                d = run_dir(pathlib.Path(d))
                res = pipeline.run(d, "standard", render_pdf=False)
                self.assertEqual(res["verdict"], "HOLD", res)
                self.assertIn("ANTHROPIC_API_KEY", res["hold_reason"])
        finally:
            if env is not None:
                os.environ["ANTHROPIC_API_KEY"] = env

    def test_claude_direct_gets_an_effort_and_no_none(self):
        p = cost.load_routing()["prices"]["claude-opus-5-5"]
        self.assertEqual(router.effort_for(p, "high"), "high")
        self.assertEqual(router.effort_for(p, "none"), "low")


class PipelineGuardTests(unittest.TestCase):
    def test_confidential_fix_round_stays_off_flagged_models(self):
        """A fix round once ignored the confidential guard: lean-tier fixes would go to DeepSeek."""
        outs = split_fixture(AUDIT)
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d), {"do_not_print": ["$14M valuation"]})
            broken = copy.deepcopy(outs["pages"])
            p12 = next(p for p in broken["pages"] if p["n"] == 12)
            p12["blocks"] = [b for b in p12["blocks"] if b["type"] not in pipeline.M.VISUAL_BLOCKS]
            for name in ("identity", "score", "synthesis", "actions"):
                (d / f"{name}.json").write_text(json.dumps(outs[name]))
            (d / "pages.json").write_text(json.dumps(broken))
            good12 = next(p for p in outs["pages"]["pages"] if p["n"] == 12)
            base = fake_from_fixture(str(DEMO / "audit.json"))

            def fake(stage, model, system, user):
                return json.dumps({"pages": [good12]}) if stage == "fix" else base(stage, model, system, user)
            res = pipeline.run(d, "lean", fake=fake, render_pdf=False, review=False)
            self.assertEqual(res["fix_rounds"], 1, res)
            fix_models = {a["model"] for a in json.loads((d / "run.json").read_text())["attempts"] if a["stage"] == "fix"}
            self.assertTrue(fix_models)
            self.assertFalse(any("deepseek" in m for m in fix_models), fix_models)

    def test_pages_are_written_in_four_batches_that_see_earlier_layouts(self):
        prompts = []
        base = fake_from_fixture(str(DEMO / "audit.json"))

        def fake(stage, model, system, user):
            if stage == "pages":
                prompts.append(user)
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = run_dir(pathlib.Path(d))
            pipeline.run(d, "standard", fake=fake, render_pdf=False, review=False)
        self.assertEqual([p.count("Write pages") for p in prompts], [1, 1, 1, 1])
        self.assertIn('"pages_so_far": []', prompts[0])
        self.assertIn('"n": 6', prompts[1])                                       # batch 2 sees batch 1's layout

    def test_unknown_tier_fails_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                pipeline.run(run_dir(pathlib.Path(d)), "openrouter-cheapest", render_pdf=False)


class OpenRouterCheckTests(unittest.TestCase):
    def models(self, **over):
        cfg = cost.load_routing()
        out = []
        for p in cfg["prices"].values():
            if p.get("provider") == "openrouter":
                out.append({"id": p["route"], "pricing": {"prompt": str(p["in"] / 1e6), "completion": str(p["out"] / 1e6),
                                                          "input_cache_read": str(p["cache_read"] / 1e6)}})
        for route, pricing in over.items():
            out = [m for m in out if m["id"] != route] + ([{"id": route, "pricing": pricing}] if pricing else [])
        return out

    def test_config_matches_the_latest_saved_openrouter_list(self):
        """Not the config against itself: a dated copy of what OpenRouter actually listed."""
        snap = openrouter.latest_snapshot()
        self.assertIsNotNone(snap)
        rep = openrouter.check(cost.load_routing(), openrouter.load_models(snap))
        self.assertTrue(rep["ok"], rep)

    def test_a_tampered_config_price_fails_against_the_saved_list(self):
        cfg = copy.deepcopy(cost.load_routing())
        cfg["prices"]["or:anthropic/claude-opus-5.5"]["in"] *= 100
        rep = openrouter.check(cfg, openrouter.load_models(openrouter.latest_snapshot()))
        self.assertEqual(rep["drifted"], ["or:anthropic/claude-opus-5.5"])

    def test_a_changed_effort_list_is_drift(self):
        models = openrouter.load_models(openrouter.latest_snapshot())
        ds = next(m for m in models if m["id"] == "deepseek/deepseek-v4.1-flash")
        ds["reasoning"] = dict(ds["reasoning"], supported_efforts=["high", "low"])       # "none" withdrawn
        rep = openrouter.check(cost.load_routing(), models)
        self.assertIn("or:deepseek/deepseek-v4.1-flash", rep["drifted"])

    def test_a_removed_route_and_a_price_rise_both_fail(self):
        models = self.models(**{"x-ai/grok-4.7": None,
                                "anthropic/claude-opus-5.5": {"prompt": "0.000008", "completion": "0.00002"}})
        rep = openrouter.check(cost.load_routing(), models)
        self.assertFalse(rep["ok"])
        self.assertIn("or:x-ai/grok-4.7", rep["missing"])
        self.assertIn("or:x-ai/grok-4.7", rep["missing_in_use"])
        self.assertEqual(rep["drifted"], ["or:anthropic/claude-opus-5.5"])

    def test_write_updates_only_the_drifted_line(self):
        models = self.models(**{"anthropic/claude-opus-5.5": {"prompt": "0.000008", "completion": "0.00002",
                                                               "input_cache_read": "0.0000002"}})
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "routing.json"
            shutil.copy(cost.ROUTING, path)
            before = path.read_text().splitlines()
            rep = openrouter.check(cost.load_routing(path), models)
            self.assertEqual(openrouter.write_prices(rep, path, today="2026-12-01"), ["or:anthropic/claude-opus-5.5"])
            after = path.read_text().splitlines()
            changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
            self.assertEqual(len(before), len(after))
            self.assertEqual(len(changed), 1)
            line = json.loads(after[changed[0]].split(":", 2)[2].rstrip(",").strip())
            self.assertEqual(line["in"], 8.0)
            self.assertIn("read 2026-12-01", line["source"])
            self.assertTrue(openrouter.check(cost.load_routing(path), models)["ok"])


class CommandTests(unittest.TestCase):
    def test_init_from_demo_makes_a_run_folder_and_refuses_a_used_one(self):
        with tempfile.TemporaryDirectory() as d:
            run = pathlib.Path(d) / "run"
            self.assertEqual(cli.main(["init", str(run), "--from-demo"]), 0)
            self.assertTrue((run / "brief.json").exists() and (run / "ledger.json").exists() and (run / "assets").is_dir())
            self.assertEqual(set(json.loads((run / "brief.json").read_text())), set(cli.BRIEF_KEYS))
            self.assertEqual(cli.main(["init", str(run), "--from-demo"]), 2)

    def test_measured_estimate_sits_under_the_planning_envelope(self):
        cfg = cost.load_routing()
        for tier in cfg["tiers"]:
            r = cost.measured_range(tier, cfg)
            self.assertLessEqual(r["typical"]["total_usd"], r["worst"]["total_usd"])
            self.assertLessEqual(r["worst"]["total_usd"], cost.audit_cost(tier, cfg)["total_usd"], tier)
        lean = cost.measured_cost("openrouter-lean", cfg)
        self.assertGreater(lean["frontier_usd"], 0)                               # Opus via OpenRouter counts as frontier
        self.assertEqual(cost.measured_cost("openrouter-budget", cfg)["frontier_usd"], 0)


if __name__ == "__main__":
    unittest.main()
