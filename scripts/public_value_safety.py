"""Dependency-free privacy checks for values published in audit artifacts.

The same high-signal boundary is used by standards metadata, HTML audit rails,
receipt envelopes, and identity registries.  Field-specific URL/identity rules
remain with their owners; this module only catches values that must never be
published anywhere.
"""

from __future__ import annotations

import html
import ipaddress
import re
import unicodedata
from urllib.parse import unquote, urlparse


MAX_DECODE_ROUNDS = 16
_PLACEHOLDER_SLUG_TOKEN = re.compile(
    r"(?:unknown|placeholder|example|sample|tbd|pending|anonymous|redacted)"
    r"(?:v?[0-9]+)?$",
    re.IGNORECASE,
)

_SLASH_TRANSLATION = str.maketrans(
    {
        "\u2044": "/",  # fraction slash
        "\u2215": "/",  # division slash
        "\u2236": "/",  # ratio / colon lookalike
        "\u02d0": "/",  # modifier letter triangular colon
        "\u2027": "/",  # hyphenation point
        "\u30fb": "/",  # katakana middle dot
        "\ua789": "/",  # modifier letter colon
        "\u29f5": "\\",  # reverse solidus operator
        "\uff0f": "/",
        "\uff3c": "\\",
        "\u3002": ".",  # IDNA/browser dot-equivalent separators
        "\uff0e": ".",
        "\uff61": ".",
    }
)

_MACHINE_ROOTS = (
    "Applications|app|bin|boot|code|data|dev|etc|home|Library|media|mnt|"
    "Network|nix|opt|private|proc|project|repo|root|run|sbin|sdcard|snap|"
    "srv|storage|sys|System|tmp|usr|Users|var|Volumes|work|workspace|workspaces"
)
_BARE_MACHINE_ROOTS = (
    "Applications|bin|boot|dev|etc|home|Library|mnt|Network|nix|opt|proc|run|"
    "sbin|sdcard|snap|storage|sys|System|tmp|usr|Users|var|Volumes|workspace|"
    "workspaces"
)

_SENSITIVE_LABELS = {
    "apikey",
    "accountkey",
    "accesstoken",
    "authorization",
    "authtoken",
    "client",
    "clientdata",
    "clientid",
    "clientsecret",
    "credential",
    "cron",
    "customer",
    "customerdata",
    "customerid",
    "jobid",
    "machinepath",
    "password",
    "passwd",
    "privatejob",
    "privatejobid",
    "privatekey",
    "privateprompt",
    "prompt",
    "registrypath",
    "schedule",
    "secret",
    "sessiontoken",
    "taskid",
    "token",
}

_CREDENTIAL_RE = re.compile(
    r"(?:"
    r"\bsk_(?:live|test|proj)_[A-Za-z0-9_-]{8,}\b|"
    r"\bsk-(?:live|test|proj)-[A-Za-z0-9_-]{8,}\b|"
    r"\brk_live_[A-Za-z0-9_-]{8,}\b|"
    r"\bsk-[A-Za-z0-9_-]{12,}\b|"
    r"\bgh[pousr]_[A-Za-z0-9]{12,}\b|"
    r"\bgithub_pat_[A-Za-z0-9_]{16,}\b|"
    r"\bglpat-[A-Za-z0-9_-]{16,}\b|"
    r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b|"
    r"\bA[KS]IA[0-9A-Z]{16}\b|"
    r"\bAIza[0-9A-Za-z_-]{20,}\b|"
    r"\bnpm_[A-Za-z0-9]{20,}\b|"
    r"\bya29\.[A-Za-z0-9_-]{20,}\b|"
    r"\bpypi-[A-Za-z0-9_-]{8,}\b|"
    r"\bdop_v1_[A-Za-z0-9_-]{8,}\b|"
    r"\bhf_[A-Za-z0-9_-]{8,}\b|"
    r"\bwhsec_[A-Za-z0-9_-]{12,}\b|"
    r"\bglrt-[A-Za-z0-9_-]{16,}\b|"
    r"\bshp(?:at|ca)_[A-Za-z0-9_-]{12,}\b|"
    r"\bsq0atp-[A-Za-z0-9_-]{12,}\b|"
    r"\bSK[0-9A-Fa-f]{32}\b|"
    r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----|"
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b|"
    r"\bSG\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}\b|"
    r"\bBearer\s+[A-Za-z0-9._~-]{12,}|"
    r"\bBasic(?:\s+|[-_.:])[A-Za-z0-9+/=_-]{12,}|"
    r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\."
    r"[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])|"
    r"\bAuthorization\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"\bpassword\s+(?:letmein|hunter2|password[0-9]*|qwerty[0-9]*)\b|"
    r"\baccount[ _-]?key\s*[:=]\s*[A-Za-z0-9+/=_-]{8,}"
    r")",
    re.IGNORECASE,
)

_URL_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9+.-])[A-Za-z][A-Za-z0-9+.-]*://[^\s<>\"']+",
    re.IGNORECASE,
)
_PRIVATE_HOSTNAME_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?:localhost|"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\."
    r"(?:localhost|local|internal|intranet|lan|home|corp))\.?"
    r"(?![A-Za-z0-9_.-])",
    re.IGNORECASE,
)


def _public_https_url_problem(value: str) -> str | None:
    """Validate URL tokens before exempting their paths from path scanning."""

    if any(character.isspace() or unicodedata.category(character).startswith("C")
           for character in value):
        return "contains whitespace or control characters in a URL"
    if "\\" in value:
        return "contains a backslash in a URL"
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return "contains a malformed URL"
    if parsed.scheme.casefold() != "https" or not parsed.netloc or not hostname:
        return "contains a non-public or unsupported URL scheme"
    if parsed.username is not None or parsed.password is not None:
        return "contains URL credentials"
    normalized = hostname.rstrip(".").casefold()
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        if normalized == "localhost" or normalized.endswith(
            (".localhost", ".local", ".internal", ".intranet", ".lan", ".home", ".corp")
        ):
            return "contains a URL that uses a private/local hostname"
        if re.fullmatch(r"[0-9.]+", normalized):
            return "contains a URL that uses a malformed or non-public numeric host"
        if "." not in normalized:
            return "contains a URL that uses a dotless non-public hostname"
        try:
            ascii_host = normalized.encode("idna").decode("ascii")
        except UnicodeError:
            return "contains a URL with an invalid hostname"
        if len(ascii_host) > 253 or any(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) is None
            for label in ascii_host.split(".")
        ):
            return "contains a URL with a malformed hostname"
    else:
        if not address.is_global:
            return "contains a URL that uses a private/local IP address"
    payload_forms: list[str] = []
    for component in (parsed.query, parsed.fragment):
        decoded, excessive = decoded_public_forms(component)
        if excessive:
            return "contains excessively nested URL/HTML encoding"
        payload_forms.extend(_canonical_for_safety(item) for item in decoded)
    payload = "\n".join(payload_forms)
    if payload and (
        re.search(
            rf"(?:file://|(?<![A-Za-z0-9._~/-])/(?:{_MACHINE_ROOTS})"
            rf"(?=$|[/\\\s<>()\[\]{{}}\"',;:&])|"
            r"(?:^|[^A-Za-z0-9])\.\.[/\\]|"
            r"\$(?:\{)?(?:HOME|USERPROFILE|TMPDIR|PWD|OLDPWD)(?:\})?[/\\])",
            payload,
            re.IGNORECASE,
        )
        or _CREDENTIAL_RE.search(payload)
        or re.search(
            r"(?:^|[?&;])(?:api[._-]?key|authorization|auth|password|passwd|"
            r"session(?:id)?|[A-Za-z0-9_.-]*(?:token|secret|credential|signature)|"
            r"private[._-]?key)\s*=",
            payload,
            re.IGNORECASE,
        )
    ):
        return "contains private or credential-bearing URL data"
    return None


def _bare_network_identifier_problem(value: str) -> str | None:
    if _PRIVATE_HOSTNAME_RE.search(value):
        return "contains a private/local hostname"
    candidates = list(
        re.finditer(
            r"(?<![A-Za-z0-9_.-])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9_.-])",
            value,
        )
    )
    candidates += list(
        re.finditer(
            r"(?<![A-Za-z0-9_.-])(?:0|10|127|169|172|192|0177)"
            r"(?:\.\d+){1,3}(?![A-Za-z0-9_.-])",
            value,
        )
    )
    candidates += list(
        re.finditer(
            r"(?<![A-Za-z0-9:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}"
            r"(?![A-Za-z0-9:])",
            value,
        )
    )
    for match in candidates:
        candidate = match.group(0)
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            if re.fullmatch(r"[0-9.]+", candidate):
                return "contains a malformed or non-public numeric host"
            continue
        if not address.is_global:
            return "contains a private, loopback, link-local, or reserved IP address"
    return None


def decoded_public_forms(value: str) -> tuple[tuple[str, ...], bool]:
    """Return recursively decoded forms and whether the safety cap was hit."""

    values = [value]
    for _ in range(MAX_DECODE_ROUNDS):
        decoded = unquote(html.unescape(values[-1]))
        if decoded == values[-1]:
            return tuple(values), False
        values.append(decoded)
    return tuple(values), unquote(html.unescape(values[-1])) != values[-1]


def _canonical_for_safety(value: str) -> str:
    return unicodedata.normalize("NFKC", value).translate(_SLASH_TRANSLATION)


def has_placeholder_slug_token(value: str) -> bool:
    """Return true when a public slug contains a reserved placeholder token."""

    normalized = _canonical_for_safety(value)
    return any(
        _PLACEHOLDER_SLUG_TOKEN.fullmatch(token) is not None
        for token in re.split(r"[._:/-]+", normalized)
        if token
    )


def _sensitive_label(value: str) -> bool:
    # Test each assignment delimiter.  Compacting the immediately preceding
    # label makes JSON/log spellings such as client.id, client/id, client-id,
    # client\u200bid, and api:key equivalent without guessing every separator.
    for match in re.finditer(r"[:=]", value):
        prefix = value[max(0, match.start() - 80) : match.start()]
        compact = "".join(character for character in prefix.casefold() if character.isalnum())
        if any(compact.endswith(label) for label in _SENSITIVE_LABELS):
            if value[match.end() :].lstrip():
                return True
    return False


def _sensitive_prefixed_value(value: str) -> bool:
    labels = (
        r"api[^A-Za-z0-9]*key|access[^A-Za-z0-9]*token|auth[^A-Za-z0-9]*token|"
        r"client[^A-Za-z0-9]*(?:id|secret|data)|customer[^A-Za-z0-9]*(?:id|data)|"
        r"job[^A-Za-z0-9]*id|task[^A-Za-z0-9]*id|machine[^A-Za-z0-9]*path|"
        r"registry[^A-Za-z0-9]*path|private[^A-Za-z0-9]*(?:prompt|job|key)|"
        r"session[^A-Za-z0-9]*token|credential|password|passwd|token|secret"
    )
    return re.search(
        rf"(?:^|[^A-Za-z0-9])(?:{labels})[^A-Za-z0-9\s]+[A-Za-z0-9]",
        value,
        re.IGNORECASE,
    ) is not None


def _sensitive_likely_value(value: str) -> bool:
    """Catch whitespace-delimited labels only when the next token looks valued."""

    labels = (
        r"api[^A-Za-z0-9]*key|access[^A-Za-z0-9]*token|auth[^A-Za-z0-9]*token|"
        r"client[^A-Za-z0-9]*(?:id|secret|data)|customer[^A-Za-z0-9]*(?:id|data)|"
        r"job[^A-Za-z0-9]*id|task[^A-Za-z0-9]*id|machine[^A-Za-z0-9]*path|"
        r"registry[^A-Za-z0-9]*path|private[^A-Za-z0-9]*(?:prompt|job|key)|"
        r"session[^A-Za-z0-9]*token|credential|password|passwd|token|secret"
    )
    for match in re.finditer(
        rf"(?:^|[^A-Za-z0-9])(?:{labels})[^A-Za-z0-9]+"
        r"([A-Za-z0-9._~-]{4,})",
        value,
        re.IGNORECASE,
    ):
        candidate = match.group(1)
        if (
            any(character.isalpha() for character in candidate)
            and any(character.isdigit() for character in candidate)
        ) or len(candidate) >= 16:
            return True
    return False


def public_value_problem(value: str) -> str | None:
    """Return a high-signal reason a string is unsafe for public evidence."""

    if not isinstance(value, str):
        return "is not a string"
    decoded, excessive = decoded_public_forms(value)
    if excessive:
        return "contains excessively nested URL/HTML encoding"
    forms = tuple(_canonical_for_safety(item) for item in decoded)
    inspected = "\n".join(forms)
    if re.search(r"%[0-9A-Fa-f]{2}", forms[-1]):
        return "contains excessively nested URL encoding"
    if re.search(
        r"(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~-])"
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@"
        r"(?:[A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,63}"
        r"(?![A-Za-z0-9-])",
        inspected,
    ):
        return "contains an email address"

    # Only a validated public HTTPS URL is exempt from local filesystem-root
    # matching. Other schemes and private hosts remain blocking public data.
    for match in _URL_TOKEN_RE.finditer(inspected):
        if problem := _public_https_url_problem(match.group(0)):
            return problem
    path_text = _URL_TOKEN_RE.sub("", inspected)
    if re.search(
        r"(?<![:/])//[A-Za-z0-9][A-Za-z0-9.-]*(?::\d+)?(?:/[^\s<>\"']*)?",
        path_text,
    ):
        return "contains a protocol-relative or network-path URL"
    if problem := _bare_network_identifier_problem(path_text):
        return problem
    if re.search(r"(?:^|[^A-Za-z0-9])\.\.[/\\]", path_text):
        return "contains a traversing private machine path"
    if re.search(
        rf"(?:^|[\s:=,;([{{-])\.[/\\](?:{_MACHINE_ROOTS})(?=$|[/\\])",
        path_text,
        re.IGNORECASE,
    ):
        return "contains a relative private machine path"
    if re.search(
        rf"(?:^|[\s:=,;([{{])(?:{_BARE_MACHINE_ROOTS})(?=[/\\])[/\\]|"
        r"(?:^|[\s:=,;([{])private[/\\](?:var|tmp|etc|Users)[/\\]",
        path_text,
        re.IGNORECASE,
    ) or re.search(
        r"(?:^|[-_.])Users[-_.][A-Za-z0-9]",
        path_text,
        re.IGNORECASE,
    ):
        return "contains a relative private machine path"
    if re.search(
        rf"(?:file://|(?<![A-Za-z0-9._~-])~[/\\]|"
        rf"(?<![A-Za-z0-9._~-])[A-Za-z]:[/\\]|"
        rf"(?<![\\])\\\\[^\\/\s<>\"']+|"
        rf"(?<![A-Za-z0-9._~/-])/(?:{_MACHINE_ROOTS})"
        rf"(?=$|[/\\\s<>()\[\]{{}}\"',;:])|"
        rf"/Users(?=$|[/\\\s<>()\[\]{{}}\"',;:])|"
        rf"(?:^|[/\\])\.ssh(?:$|[/\\]))",
        path_text,
        re.IGNORECASE,
    ):
        return "contains a private machine path"
    if re.search(
        r"%(?:USERPROFILE|APPDATA|LOCALAPPDATA|TEMP|TMP|HOMEDRIVE|HOMEPATH)%[/\\]|"
        r"\$(?:\{)?(?:HOME|USERPROFILE|TMPDIR|TEMP|TMP|PWD|OLDPWD|"
        r"XDG_[A-Z0-9_]+)(?:\})?[/\\]",
        path_text,
        re.IGNORECASE,
    ):
        return "contains an environment-relative machine path"

    # Report concrete credential shapes before the broader sensitive-label
    # boundary.  The latter deliberately catches ambiguous private metadata,
    # but it must not hide a positive token-pattern match behind a weaker
    # classification (for example ``password letmein``).
    if _CREDENTIAL_RE.search(inspected):
        return "contains credential/token pattern"

    if (
        _sensitive_label(path_text)
        or _sensitive_prefixed_value(path_text)
        or _sensitive_likely_value(path_text)
    ):
        compact = "".join(character for character in path_text.casefold() if character.isalnum())
        if any(
            word in compact
            for word in (
                "apikey", "authorization", "authtoken", "clientsecret",
                "credential", "password", "passwd", "privatekey", "secret",
                "sessiontoken", "token",
            )
        ):
            return "contains sensitive private-data label (credential)"
        return "contains sensitive private-data label"
    if re.search(
        r"(?:[?&;]|\b)(?:api[._-]?key|authorization|auth|password|passwd|sig|"
        r"session(?:id)?|[A-Za-z0-9_.-]*(?:token|secret|credential|signature)|"
        r"private[._-]?key)\s*=",
        inspected,
        re.IGNORECASE,
    ):
        return "contains a credential-bearing parameter"
    if any(
        re.search(r"[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]", item)
        for item in forms
    ):
        return "contains bidirectional text controls"
    if any(
        unicodedata.category(character).startswith("C")
        or "\u180b" <= character <= "\u180d"
        or "\ufe00" <= character <= "\ufe0f"
        or "\U000e0100" <= character <= "\U000e01ef"
        for item in forms
        for character in item
    ):
        return "contains a Unicode control or variation character"
    return None
