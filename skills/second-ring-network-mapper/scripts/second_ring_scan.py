#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Local Service Spotlight
"""Build a privacy-preserving Second Ring report from owner-authorized exports.

The script uses only the Python standard library, makes no network requests,
does not retain raw input, and does not select dedicated email/provider-ID
fields or input paths for any report.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import re
import struct
import sys
import unicodedata
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


PARSER_VERSION = "1.1.0"
MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_ENTRY_BYTES = 20 * 1024 * 1024
MAX_ENTRIES = 5_000
MAX_CONTACTS = 50_000
MAX_COMPRESSION_RATIO = 50

DIRECT_RECORD_BASE = 40
DIRECT_EXPORT_EVIDENCE = 18
PATH_RECORD_BASE = 25

EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])[\w.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}(?![\w.-])",
    re.IGNORECASE,
)
AT_TOKEN_PATTERN = re.compile(r"\S+@\S+")
KNOWN_PROVIDER_ID_PATTERN = re.compile(
    r"\burn:(?:li|linkedin|facebook|fb|meta|google):[^\s,;]+",
    re.IGNORECASE,
)

GOAL_KEYWORDS = {
    "customers": (
        "owner", "founder", "ceo", "president", "principal", "general manager",
        "marketing", "growth", "sales", "business development", "contractor", "service",
    ),
    "partners": (
        "owner", "founder", "ceo", "partner", "partnership", "alliance",
        "business development", "agency", "consultant", "community",
    ),
    "podcasts": (
        "podcast", "host", "media", "editor", "producer", "speaker", "author",
        "founder", "marketing", "community",
    ),
    "hiring": (
        "recruiter", "talent", "people", "human resources", "hr", "hiring",
        "operations", "manager", "founder", "ceo",
    ),
}

NEGATIVE_STATUSES = {
    "confirmation pending", "not consented", "not confirmed", "not documented",
    "not verified", "unconfirmed", "undocumented", "unverified",
}
VERIFIED_STATUSES = {"confirmed", "verified", "verified participant"}
CONSENTED_STATUSES = {"consented", "consented contribution", "contributed"}
DOCUMENTED_STATUSES = {
    "documented", "direct", "direct connection", "exported", "saved", "user export",
}
CONTEXTUAL_STATUSES = {
    "context", "contextual", "public", "shared", "shared context", "shared_context",
}


class ScanError(ValueError):
    """A safe, user-facing validation failure."""


@dataclass
class Contact:
    key: str
    name: str
    company: str = ""
    position: str = ""
    connected_on: str = ""
    source: str = ""
    has_email: bool = False
    has_profile: bool = False
    degree: int = 1


@dataclass
class Relationship:
    source_name: str
    target_name: str
    label: str
    status: str
    observed_at: str = ""
    target_company: str = ""
    target_position: str = ""
    target_url: str = ""


@dataclass
class ScoredDirect:
    contact: Contact
    score: int
    factors: list[str]


@dataclass
class ScoredPath:
    connector: Contact
    target: Contact
    relationship: Relationship
    score: int
    supported: bool
    factors: list[str]


@dataclass
class ScanResult:
    owner: str
    goal: str
    source_label: str
    contacts: list[Contact]
    direct: list[ScoredDirect]
    paths: list[ScoredPath]
    duplicates: int
    skipped: int
    warnings: list[str] = field(default_factory=list)
    target_query: str = ""
    target_state: str = "none"
    relationship_rows_supplied: int = 0
    relationship_rows_excluded: int = 0
    relationship_exclusion_reasons: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ZipEntryMetadata:
    compressed_size: int
    original_size: int
    local_header_offset: int
    physical_compressed_bytes: int


class NameRegistry:
    """Render one stable, identity-keyed alias map across a whole report."""

    def __init__(self, redact: bool):
        self.redact = redact
        self.aliases: dict[str, str] = {}
        self.counter = 0

    def owner(self, name: str) -> str:
        return "Network Owner" if self.redact else name

    def contact(self, contact: Contact) -> str:
        if not self.redact:
            return contact.name
        identity = f"contact:{contact.key}"
        if identity not in self.aliases:
            self.counter += 1
            self.aliases[identity] = f"Person {self.counter:03d}"
        return self.aliases[identity]


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.strip().lower().replace("_", " ").split())


def clean_untrusted(value: str, maximum: int = 180) -> str:
    """Remove terminal controls, collapse whitespace, and bound untrusted text."""
    safe = "".join(
        character for character in (value or "")
        if not unicodedata.category(character).startswith("C")
    )
    collapsed = " ".join(safe.split())
    return collapsed[:maximum]


def clean_display(value: str, maximum: int = 180) -> str:
    """Best-effort redact sensitive tokens from bounded display text."""
    cleaned = clean_untrusted(value, maximum)
    without_email_tokens = AT_TOKEN_PATTERN.sub("[email redacted]", cleaned)
    return KNOWN_PROVIDER_ID_PATTERN.sub("[provider id redacted]", without_email_tokens)


def markdown_cell(value: str) -> str:
    escaped = html.escape(clean_display(value), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", escaped)


def safe_http_url(value: str) -> str:
    candidate = clean_untrusted(value, 2_048)
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return ""
    return candidate


def safe_linkedin_profile_url(value: str) -> str:
    candidate = safe_http_url(value)
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    parts = [part for part in parsed.path.split("/") if part]
    if not (hostname == "linkedin.com" or hostname.endswith(".linkedin.com")):
        return ""
    if len(parts) < 2 or parts[0].lower() not in {"in", "pub"}:
        return ""
    return candidate


def safe_email_identity(value: str) -> str:
    candidate = clean_untrusted(value, 320)
    return candidate if EMAIL_PATTERN.fullmatch(candidate) else ""


def stable_key(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:18]
    return f"{prefix}-{digest}"


def decode_csv(raw: bytes) -> str:
    if len(raw) > MAX_ENTRY_BYTES:
        raise ScanError("The selected CSV exceeds the 20 MiB supported-entry limit.")
    return raw.decode("utf-8-sig", errors="replace")


def read_limited_csv(path: Path) -> str:
    """Read at most one supported CSV entry plus a single overflow byte."""
    with path.open("rb") as stream:
        raw = stream.read(MAX_ENTRY_BYTES + 1)
    if len(raw) > MAX_ENTRY_BYTES:
        raise ScanError("The selected CSV exceeds the 20 MiB supported-entry limit.")
    return decode_csv(raw)


def rows_from_text(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in csv.reader(io.StringIO(text)):
        cleaned = [cell.strip() for cell in row]
        if any(cleaned):
            rows.append(cleaned)
        if len(rows) > MAX_CONTACTS + 25:
            raise ScanError(f"The export exceeds the {MAX_CONTACTS:,}-record limit.")
    return rows


def header_index(rows: list[list[str]], required: set[str], limit: int = 20) -> int:
    for index, row in enumerate(rows[:limit]):
        normalized = {normalize(value) for value in row}
        if required.issubset(normalized):
            return index
    return -1


def header_map(row: list[str]) -> dict[str, int]:
    return {normalize(value): index for index, value in enumerate(row)}


def pick(row: list[str], mapping: dict[str, int], *aliases: str) -> str:
    for alias in aliases:
        index = mapping.get(normalize(alias))
        if index is not None and index < len(row):
            return clean_display(row[index])
    return ""


def pick_raw(row: list[str], mapping: dict[str, int], *aliases: str) -> str:
    """Read a bounded private identity field that will never enter a report."""
    for alias in aliases:
        index = mapping.get(normalize(alias))
        if index is not None and index < len(row):
            return clean_untrusted(row[index], 2_048)
    return ""


def merge_contacts(contacts: Iterable[tuple[Contact, str, str]]) -> tuple[list[Contact], int]:
    """Deduplicate on strong keys only; retain name-only homonyms separately."""
    merged: dict[str, Contact] = {}
    duplicates = 0
    for contact, email, profile_url in contacts:
        normalized_email = normalize(email)
        normalized_profile = normalize(safe_http_url(profile_url)).rstrip("/")
        identity = (
            f"email:{normalized_email}" if normalized_email
            else f"url:{normalized_profile}" if normalized_profile
            else contact.key
        )
        current = merged.get(identity)
        if current is None:
            merged[identity] = contact
            continue
        duplicates += 1
        current.company = current.company or contact.company
        current.position = current.position or contact.position
        current.connected_on = current.connected_on or contact.connected_on
        current.has_email = current.has_email or contact.has_email
        current.has_profile = current.has_profile or contact.has_profile
    return list(merged.values()), duplicates


def parse_linkedin_rows(rows: list[list[str]]) -> tuple[list[Contact], int, int]:
    index = header_index(rows, {"first name", "last name"})
    if index < 0:
        raise ScanError("This CSV does not contain LinkedIn First Name and Last Name columns.")
    mapping = header_map(rows[index])
    parsed: list[tuple[Contact, str, str]] = []
    skipped = 0
    for row_number, row in enumerate(rows[index + 1 :], start=1):
        first = pick(row, mapping, "First Name")
        last = pick(row, mapping, "Last Name")
        name = f"{first} {last}".strip()
        if not name:
            skipped += 1
            continue
        email = safe_email_identity(pick_raw(row, mapping, "Email Address"))
        profile = safe_linkedin_profile_url(pick_raw(row, mapping, "URL"))
        contact = Contact(
            key=stable_key("linkedin-row", f"{row_number}|{normalize(name)}"),
            name=name,
            company=pick(row, mapping, "Company"),
            position=pick(row, mapping, "Position"),
            connected_on=pick(row, mapping, "Connected On"),
            source="LinkedIn direct connection",
            has_email=bool(email),
            has_profile=bool(profile),
        )
        parsed.append((contact, email, profile))
    contacts, duplicates = merge_contacts(parsed)
    if len(contacts) > MAX_CONTACTS:
        raise ScanError(f"The export exceeds the {MAX_CONTACTS:,}-contact limit.")
    return contacts, duplicates, skipped


def parse_linkedin(text: str) -> tuple[list[Contact], int, int]:
    return parse_linkedin_rows(rows_from_text(text))


def parse_google_contacts_rows(rows: list[list[str]]) -> tuple[list[Contact], int, int]:
    index = header_index(rows, {"name"})
    if index < 0:
        index = header_index(rows, {"given name", "family name"})
    if index < 0:
        raise ScanError("This CSV is neither LinkedIn Connections.csv nor a recognized Google Contacts export.")
    mapping = header_map(rows[index])
    parsed: list[tuple[Contact, str, str]] = []
    skipped = 0
    for row_number, row in enumerate(rows[index + 1 :], start=1):
        name = pick(row, mapping, "Name")
        if not name:
            name = f"{pick(row, mapping, 'Given Name')} {pick(row, mapping, 'Family Name')}".strip()
        if not name:
            skipped += 1
            continue
        email = safe_email_identity(pick_raw(row, mapping, "E-mail 1 - Value", "Email 1 - Value", "Email"))
        # Google Contacts' generic Website field is often a shared company home
        # page. It is context, not a safe person-identity/deduplication key.
        profile = ""
        contact = Contact(
            key=stable_key("contacts-row", f"{row_number}|{normalize(name)}"),
            name=name,
            company=pick(row, mapping, "Organization 1 - Name", "Organization", "Company"),
            position=pick(row, mapping, "Organization 1 - Title", "Job Title", "Position"),
            source="Google Contacts address-book record",
            has_email=bool(email),
            has_profile=bool(profile),
        )
        parsed.append((contact, email, profile))
    contacts, duplicates = merge_contacts(parsed)
    if len(contacts) > MAX_CONTACTS:
        raise ScanError(f"The export exceeds the {MAX_CONTACTS:,}-contact limit.")
    return contacts, duplicates, skipped


def parse_google_contacts(text: str) -> tuple[list[Contact], int, int]:
    return parse_google_contacts_rows(rows_from_text(text))


def parse_contact_csv(text: str) -> tuple[str, list[Contact], int, int]:
    rows = rows_from_text(text)
    if header_index(rows, {"first name", "last name"}) >= 0:
        contacts, duplicates, skipped = parse_linkedin_rows(rows)
        return "LinkedIn", contacts, duplicates, skipped
    contacts, duplicates, skipped = parse_google_contacts_rows(rows)
    return "Google Contacts", contacts, duplicates, skipped


def inspect_zip_structure(raw: bytes) -> dict[int, ZipEntryMetadata]:
    """Validate classic single-disk ZIP metadata before decompression."""
    minimum_record_bytes = 22
    maximum_comment_bytes = 65_535
    if len(raw) < minimum_record_bytes:
        raise ScanError("The file is named ZIP but does not have a valid ZIP structure.")
    first_candidate = max(0, len(raw) - minimum_record_bytes - maximum_comment_bytes)
    for offset in range(len(raw) - minimum_record_bytes, first_candidate - 1, -1):
        if raw[offset : offset + 4] != b"PK\x05\x06":
            continue
        (
            _signature,
            disk_number,
            central_directory_disk,
            entries_on_disk,
            total_entries,
            central_directory_bytes,
            central_directory_offset,
            comment_length,
        ) = struct.unpack_from("<4s4H2LH", raw, offset)
        if offset + minimum_record_bytes + comment_length != len(raw):
            continue
        if (
            disk_number != 0
            or central_directory_disk != 0
            or entries_on_disk != total_entries
            or entries_on_disk == 0xFFFF
            or total_entries == 0xFFFF
            or central_directory_bytes == 0xFFFFFFFF
            or central_directory_offset == 0xFFFFFFFF
        ):
            raise ScanError("Multi-disk and ZIP64-dependent archives are not supported.")
        if total_entries > MAX_ENTRIES:
            raise ScanError(f"The ZIP contains more than {MAX_ENTRIES:,} entries.")
        if (
            central_directory_offset + central_directory_bytes > offset
            or central_directory_offset + central_directory_bytes > len(raw)
        ):
            raise ScanError("The ZIP has an invalid central directory.")

        declared_entries: list[tuple[int, int, int, int]] = []
        cursor = central_directory_offset
        for _index in range(total_entries):
            if cursor + 46 > len(raw) or raw[cursor : cursor + 4] != b"PK\x01\x02":
                raise ScanError("The ZIP has a truncated or invalid central-directory entry.")
            flags = struct.unpack_from("<H", raw, cursor + 8)[0]
            compressed_size = struct.unpack_from("<L", raw, cursor + 20)[0]
            original_size = struct.unpack_from("<L", raw, cursor + 24)[0]
            filename_length = struct.unpack_from("<H", raw, cursor + 28)[0]
            extra_length = struct.unpack_from("<H", raw, cursor + 30)[0]
            entry_comment_length = struct.unpack_from("<H", raw, cursor + 32)[0]
            starting_disk = struct.unpack_from("<H", raw, cursor + 34)[0]
            local_header_offset = struct.unpack_from("<L", raw, cursor + 42)[0]
            record_bytes = 46 + filename_length + extra_length + entry_comment_length
            if (
                compressed_size == 0xFFFFFFFF
                or original_size == 0xFFFFFFFF
                or local_header_offset == 0xFFFFFFFF
            ):
                raise ScanError("ZIP64-dependent entries are not supported.")
            if starting_disk != 0:
                raise ScanError("Multi-disk ZIP entries are not supported.")
            if cursor + record_bytes > len(raw):
                raise ScanError("The ZIP has truncated central-directory metadata.")
            if flags & 0x1:
                raise ScanError("Encrypted ZIP entries are not supported.")
            declared_entries.append(
                (local_header_offset, compressed_size, original_size, flags)
            )
            cursor += record_bytes
        if cursor != central_directory_offset + central_directory_bytes:
            raise ScanError("The ZIP has inconsistent central-directory metadata.")

        ordered = sorted(declared_entries)
        metadata: dict[int, ZipEntryMetadata] = {}
        for index, (local_offset, compressed_size, original_size, central_flags) in enumerate(ordered):
            next_offset = ordered[index + 1][0] if index + 1 < len(ordered) else central_directory_offset
            if local_offset in metadata or local_offset + 30 > central_directory_offset:
                raise ScanError("The ZIP has overlapping or truncated local entries.")
            if raw[local_offset : local_offset + 4] != b"PK\x03\x04":
                raise ScanError("The ZIP has an invalid local entry.")
            local_flags = struct.unpack_from("<H", raw, local_offset + 6)[0]
            local_name_length = struct.unpack_from("<H", raw, local_offset + 26)[0]
            local_extra_length = struct.unpack_from("<H", raw, local_offset + 28)[0]
            data_offset = local_offset + 30 + local_name_length + local_extra_length
            if (
                local_flags & 0x1
                or local_flags != central_flags
                or data_offset > next_offset
                or next_offset > central_directory_offset
            ):
                raise ScanError("The ZIP has inconsistent or overlapping local-entry metadata.")
            physical_compressed_bytes = next_offset - data_offset
            if compressed_size > physical_compressed_bytes:
                raise ScanError("The ZIP reports an impossible compressed size.")
            metadata[local_offset] = ZipEntryMetadata(
                compressed_size=compressed_size,
                original_size=original_size,
                local_header_offset=local_offset,
                physical_compressed_bytes=physical_compressed_bytes,
            )
        return metadata
    raise ScanError("The ZIP is missing its end-of-central-directory record.")


def validated_zip_entries(path: Path) -> tuple[bytes, list[zipfile.ZipInfo]]:
    """Return the immutable archive snapshot and entries that were validated."""
    with path.open("rb") as stream:
        raw = stream.read(MAX_ARCHIVE_BYTES + 1)
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ScanError("The ZIP exceeds the 25 MiB compressed archive limit.")
    metadata = inspect_zip_structure(raw)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
    except zipfile.BadZipFile as error:
        raise ScanError("The file is named ZIP but does not have a valid ZIP structure.") from error
    if len(entries) != len(metadata):
        raise ScanError("The ZIP entry count does not match its central directory.")
    expanded = 0
    for entry in entries:
        declared = metadata.get(entry.header_offset)
        if (
            declared is None
            or declared.original_size != entry.file_size
            or declared.compressed_size != entry.compress_size
        ):
            raise ScanError("The ZIP entry metadata is inconsistent.")
        if entry.flag_bits & 0x1:
            raise ScanError("Encrypted ZIP entries are not supported.")
        if entry.is_dir():
            continue
        if entry.file_size > MAX_ENTRY_BYTES:
            raise ScanError("A supported ZIP entry exceeds the 20 MiB per-entry limit.")
        if entry.file_size and (
            declared.physical_compressed_bytes == 0
            or entry.file_size / declared.physical_compressed_bytes > MAX_COMPRESSION_RATIO
        ):
            raise ScanError("A ZIP entry exceeds the safe 50:1 physical expansion ratio.")
        expanded += entry.file_size
        if expanded > MAX_EXPANDED_BYTES:
            raise ScanError("The ZIP expands beyond the 100 MiB total limit.")
    return raw, entries


def load_contacts(path: Path) -> tuple[str, list[Contact], int, int]:
    if not path.is_file():
        raise ScanError("The input path does not point to a readable file.")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_contact_csv(read_limited_csv(path))
    if suffix != ".zip":
        raise ScanError("Choose a LinkedIn ZIP, Connections.csv, or Google Contacts CSV.")

    raw, entries = validated_zip_entries(path)
    csv_entries = [entry for entry in entries if entry.filename.lower().endswith(".csv")]
    exact = [entry for entry in csv_entries if Path(entry.filename).name.lower() == "connections.csv"]
    if len(exact) > 1:
        raise ScanError("The ZIP contains multiple Connections.csv files; choose the intended CSV directly.")
    candidates = exact or csv_entries
    # Parse the same immutable bytes inspected above. Reopening the pathname here
    # would allow a local replacement between validation and decompression.
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for entry in candidates:
            try:
                source_label, contacts, duplicates, skipped = parse_contact_csv(
                    decode_csv(archive.read(entry))
                )
                return source_label, contacts, duplicates, skipped
            except ScanError:
                if exact:
                    raise
    raise ScanError("The ZIP does not contain a recognized Connections.csv or Google Contacts CSV.")


def add_count(counts: dict[str, int], reason: str) -> None:
    counts[reason] = counts.get(reason, 0) + 1


def parse_relationships(path: Path) -> tuple[list[Relationship], int, dict[str, int]]:
    if not path.is_file() or path.suffix.lower() != ".csv":
        raise ScanError("The relationship evidence must be a readable CSV file.")
    text = read_limited_csv(path)
    rows = rows_from_text(text)
    index = header_index(rows, {"source", "target", "relationship", "status"})
    if index < 0:
        raise ScanError("Relationship CSV needs Source, Target, Relationship, and Status columns.")
    mapping = header_map(rows[index])
    relationships: list[Relationship] = []
    exclusions: dict[str, int] = {}
    data_rows = rows[index + 1 :]
    if len(data_rows) > MAX_CONTACTS:
        raise ScanError(f"The relationship file exceeds the {MAX_CONTACTS:,}-row limit.")
    for row in data_rows:
        source_name = pick(row, mapping, "Source")
        target_name = pick(row, mapping, "Target")
        if not source_name or not target_name:
            add_count(exclusions, "missing_source_or_target")
            continue
        relationships.append(
            Relationship(
                source_name=source_name,
                target_name=target_name,
                label=pick(row, mapping, "Relationship") or "relationship",
                status=pick(row, mapping, "Status"),
                observed_at=pick(row, mapping, "Observed At", "Observed On", "Date"),
                target_company=pick(row, mapping, "Target Company"),
                target_position=pick(row, mapping, "Target Position"),
                target_url=safe_linkedin_profile_url(pick_raw(row, mapping, "Target URL")),
            )
        )
    return relationships, len(data_rows), exclusions


def parse_date(value: str) -> datetime | None:
    candidate = (value or "").strip()
    if not candidate:
        return None
    normalized_candidate = candidate.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized_candidate)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    slash_date = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", candidate)
    if slash_date:
        first, second, year = (int(part) for part in slash_date.groups())
        if first <= 12 and second <= 12:
            return None
        pattern = "%d/%m/%Y" if first > 12 else "%m/%d/%Y"
        try:
            return datetime.strptime(candidate, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    for pattern in ("%d %b %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(candidate, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def freshness_points(value: str) -> tuple[int, str]:
    observed = parse_date(value)
    if observed is None:
        return 0, "no usable date"
    now = datetime.now(timezone.utc)
    if observed > now:
        return 0, "future date; not usable"
    age_days = (now - observed).days
    if age_days <= 366:
        points = 15
    elif age_days <= 2 * 366:
        points = 12
    elif age_days <= 5 * 366:
        points = 8
    else:
        points = 3
    return points, f"dated {observed.date().isoformat()}"


def goal_points(contact: Contact, goal: str) -> tuple[int, str]:
    context = normalize(f"{contact.position} {contact.company}")
    if not context:
        return 0, "goal fit unknown"
    matches = [
        keyword
        for keyword in GOAL_KEYWORDS[goal]
        if re.search(rf"\b{re.escape(keyword)}\b", context)
    ]
    if len(matches) >= 2:
        return 15, f"matched {matches[0]} and {matches[1]}"
    if len(matches) == 1:
        return 12, f"matched {matches[0]}"
    return 4, "role context present; no goal keyword matched"


def identity_points(contact: Contact) -> tuple[int, str]:
    if contact.has_email or contact.has_profile:
        return 5, "strong identity field present"
    if contact.company or contact.position:
        return 3, "company or role helps disambiguate"
    return 0, "name-only record; confirm identity"


def evidence_points(status: str) -> tuple[int, str]:
    value = normalize(status)
    if value in NEGATIVE_STATUSES:
        return 4, "negative or pending evidence"
    if value in VERIFIED_STATUSES:
        return 25, "verified evidence"
    if value in CONSENTED_STATUSES:
        return 22, "consented contribution"
    if value in DOCUMENTED_STATUSES:
        return 18, "documented assertion"
    if value in CONTEXTUAL_STATUSES:
        return 10, "context only"
    return 4, "unknown evidence status"


def score_direct(contact: Contact, goal: str) -> ScoredDirect:
    fresh, fresh_reason = freshness_points(contact.connected_on)
    relevance, relevance_reason = goal_points(contact, goal)
    identity, identity_reason = identity_points(contact)
    score = min(
        100,
        DIRECT_RECORD_BASE + DIRECT_EXPORT_EVIDENCE + fresh + relevance + identity,
    )
    return ScoredDirect(
        contact=contact,
        score=score,
        factors=[
            f"direct-record base +{DIRECT_RECORD_BASE}",
            f"direct-export evidence +{DIRECT_EXPORT_EVIDENCE}",
            f"goal fit +{relevance} ({relevance_reason})",
            f"freshness +{fresh} ({fresh_reason})",
            f"identity +{identity} ({identity_reason})",
        ],
    )


def build_paths(
    contacts: list[Contact], relationships: list[Relationship], goal: str
) -> tuple[list[ScoredPath], dict[str, int]]:
    direct_by_name: dict[str, list[Contact]] = {}
    for contact in contacts:
        direct_by_name.setdefault(normalize(contact.name), []).append(contact)
    unique_direct = {
        name: matches[0] for name, matches in direct_by_name.items() if len(matches) == 1
    }
    direct_names = set(direct_by_name)
    paths: list[ScoredPath] = []
    exclusions: dict[str, int] = {}
    for row_number, relationship in enumerate(relationships, start=1):
        source_key = normalize(relationship.source_name)
        target_key = normalize(relationship.target_name)
        source_connector = unique_direct.get(source_key)
        target_connector = unique_direct.get(target_key)
        if bool(source_connector) == bool(target_connector):
            if source_connector and target_connector:
                add_count(exclusions, "both_endpoints_are_direct")
            elif source_key in direct_names or target_key in direct_names:
                add_count(exclusions, "direct_endpoint_is_ambiguous")
            else:
                add_count(exclusions, "no_direct_endpoint")
            continue
        connector = source_connector or target_connector
        assert connector is not None
        target_name = relationship.target_name if source_connector else relationship.source_name
        if normalize(target_name) in direct_names:
            add_count(exclusions, "other_endpoint_is_direct_or_ambiguous")
            continue
        target_company = relationship.target_company if source_connector else ""
        target_position = relationship.target_position if source_connector else ""
        target_url = relationship.target_url if source_connector else ""
        if target_url:
            target_identity = f"url:{normalize(target_url).rstrip('/')}"
        elif target_company or target_position:
            target_identity = f"context:{normalize(target_name)}|{normalize(target_company)}|{normalize(target_position)}"
        else:
            target_identity = f"row:{row_number}|{normalize(target_name)}"
        target = Contact(
            key=stable_key("relationship-target", target_identity),
            name=target_name,
            company=target_company,
            position=target_position,
            source="Owner-authorized relationship evidence",
            has_profile=bool(target_url),
            degree=2,
        )
        evidence, evidence_reason = evidence_points(relationship.status)
        fresh, fresh_reason = freshness_points(relationship.observed_at)
        relevance, relevance_reason = goal_points(target, goal)
        identity, identity_reason = identity_points(target)
        score = min(100, PATH_RECORD_BASE + evidence + fresh + relevance + identity)
        paths.append(
            ScoredPath(
                connector=connector,
                target=target,
                relationship=relationship,
                score=score,
                supported=evidence >= 18,
                factors=[
                    f"path base +{PATH_RECORD_BASE}",
                    f"evidence +{evidence} ({evidence_reason})",
                    f"goal fit +{relevance} ({relevance_reason})",
                    f"freshness +{fresh} ({fresh_reason})",
                    f"identity +{identity} ({identity_reason})",
                ],
            )
        )
    return (
        sorted(paths, key=lambda item: (not item.supported, -item.score, normalize(item.target.name))),
        exclusions,
    )


def apply_target(result: ScanResult, query: str) -> None:
    result.target_query = query
    normalized_query = normalize(query)
    if not normalized_query:
        return
    direct_matches = [item for item in result.direct if normalize(item.contact.name) == normalized_query]
    path_matches = [item for item in result.paths if normalize(item.target.name) == normalized_query]
    if not direct_matches and not path_matches:
        direct_matches = [item for item in result.direct if normalized_query in normalize(item.contact.name)]
        path_matches = [item for item in result.paths if normalized_query in normalize(item.target.name)]
    unique_people = {item.contact.key for item in direct_matches} | {item.target.key for item in path_matches}
    if len(unique_people) > 1:
        result.target_state = "ambiguous"
        result.direct = []
        result.paths = []
        result.warnings.append("The target matches multiple people. Refine the name; no connector was selected.")
    elif direct_matches:
        result.target_state = "direct"
        result.direct = direct_matches
        result.paths = []
    elif path_matches:
        result.target_state = "second_ring"
        result.direct = []
        result.paths = path_matches
    else:
        result.target_state = "unmatched"
        result.direct = []
        result.paths = []
        result.warnings.append("The target was not found in the supplied authorized data.")


def demo_data(owner: str, goal: str) -> ScanResult:
    contacts = [
        Contact("demo-alex", "Alex Owner", "Bright Roof Co.", "Founder", "2026-05-12", "Synthetic", True, True),
        Contact("demo-jordan", "Jordan Host", "Local Growth Show", "Podcast Host", "2025-11-20", "Synthetic", False, True),
        Contact("demo-riley", "Riley Recruiter", "Service Talent", "Recruiter", "2026-02-14", "Synthetic", True, False),
        Contact("demo-morgan", "Morgan Partner", "Trade Alliance", "Partnerships Director", "2024-08-03", "Synthetic", False, True),
    ]
    relationships = [
        Relationship(
            "Jordan Host", "Taylor Guest", "recorded podcast", "confirmed",
            observed_at="2026-06-01", target_company="Trade Media", target_position="Host",
        ),
        Relationship(
            "Morgan Partner", "Casey Buyer", "shared event", "shared_context",
            observed_at="2026-04-10", target_company="Home Services Group", target_position="President",
        ),
    ]
    direct = sorted((score_direct(contact, goal) for contact in contacts), key=lambda item: -item.score)
    paths, exclusions = build_paths(contacts, relationships, goal)
    return ScanResult(
        owner=owner,
        goal=goal,
        source_label="Synthetic demo",
        contacts=contacts,
        direct=direct,
        paths=paths,
        duplicates=0,
        skipped=0,
        warnings=["Every person and relationship in this report is fictional."],
        relationship_rows_supplied=len(relationships),
        relationship_rows_excluded=sum(exclusions.values()),
        relationship_exclusion_reasons=exclusions,
    )


def display_context(contact: Contact, redact: bool) -> str:
    if redact:
        return "Context redacted"
    return " · ".join(part for part in (contact.position, contact.company) if part) or "No role/company supplied"


def best_action(result: ScanResult, names: NameRegistry) -> tuple[str, str, str]:
    if result.direct:
        item = result.direct[0]
        person = names.contact(item.contact)
        return person, "; ".join(item.factors[:3]), f"Contact {person} directly with a specific, relevant reason."
    supported = [item for item in result.paths if item.supported]
    if supported:
        item = supported[0]
        connector = names.contact(item.connector)
        target = names.contact(item.target)
        return connector, "; ".join(item.factors[:3]), f"Ask {connector} whether they are comfortable introducing you to {target}; make it easy to decline."
    if result.paths:
        item = result.paths[0]
        connector = names.contact(item.connector)
        target = names.contact(item.target)
        return connector, "; ".join(item.factors[:2]), f"Verify {connector}'s current relationship with {target} before asking for any introduction."
    return "No person selected", "The supplied data does not support a path.", "Refine the goal, confirm ambiguous identities, or add separately authorized relationship evidence."


def markdown_report(
    result: ScanResult, redact: bool, names: NameRegistry | None = None
) -> str:
    names = names or NameRegistry(redact)
    ask, why, action = best_action(result, names)
    supported = [item for item in result.paths if item.supported]
    unsupported = [item for item in result.paths if not item.supported]
    lines = [
        "# Second Ring local report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')} · Parser {PARSER_VERSION}",
        f"Owner: {markdown_cell(names.owner(result.owner))} · Goal: {result.goal} · Source: {result.source_label}",
        "",
        "## Best next action",
        "",
        f"- **Ask/contact:** {markdown_cell(ask)}",
        f"- **Why:** {markdown_cell(why)}",
        f"- **Action:** {markdown_cell(action)}",
        "",
        "## What the input proves",
        "",
        f"{len(result.contacts):,} unique direct records · {result.duplicates:,} strong-key duplicates merged · {result.skipped:,} contact rows skipped · {result.relationship_rows_supplied:,} relationship rows supplied · {result.relationship_rows_excluded:,} relationship rows excluded · {len(supported):,} supported two-hop paths",
        "",
        f"Applied safety limits: {MAX_ARCHIVE_BYTES // (1024 * 1024)} MiB ZIP · {MAX_EXPANDED_BYTES // (1024 * 1024)} MiB expanded · {MAX_ENTRIES:,} ZIP entries · {MAX_ENTRY_BYTES // (1024 * 1024)} MiB per entry · {MAX_COMPRESSION_RATIO}:1 physical expansion · {MAX_CONTACTS:,} contact or relationship records.",
        "",
        "Direct-priority and path-priority scores use different ranking rubrics and are not comparable. Act on direct records before requesting an introduction.",
        "",
    ]
    if result.warnings:
        lines.extend(["## Review warnings", "", *[f"- {warning}" for warning in result.warnings], ""])
    if result.direct:
        lines.extend(["## Ranked direct actions", "", "| Rank | Person | Context | Direct priority | Components |", "|---:|---|---|---:|---|"])
        for index, item in enumerate(result.direct[:10], start=1):
            lines.append(
                f"| {index} | {markdown_cell(names.contact(item.contact))} | {markdown_cell(display_context(item.contact, redact))} | {item.score} | {markdown_cell('; '.join(item.factors))} |"
            )
        lines.append("")
    if supported:
        lines.extend(["## Supported two-hop paths", "", "| Rank | Target | Ask | Relationship | Path priority | Components |", "|---:|---|---|---|---:|---|"])
        for index, item in enumerate(supported[:10], start=1):
            lines.append(
                f"| {index} | {markdown_cell(names.contact(item.target))} | {markdown_cell(names.contact(item.connector))} | {markdown_cell(item.relationship.label)} ({markdown_cell(item.relationship.status)}) | {item.score} | {markdown_cell('; '.join(item.factors))} |"
            )
        lines.append("")
    if unsupported:
        lines.extend(["## Context to verify — not introduction paths", "", "| Target | Possible connector | Status | Why held back |", "|---|---|---|---|"])
        for item in unsupported[:10]:
            lines.append(
                f"| {markdown_cell(names.contact(item.target))} | {markdown_cell(names.contact(item.connector))} | {markdown_cell(item.relationship.status or 'unknown')} | {markdown_cell(item.relationship.label)}; {markdown_cell(item.factors[1])} |"
            )
        lines.append("")
    if not result.paths:
        lines.extend([
            "## Second-ring status",
            "",
            "This report contains no usable two-hop path. Direct data alone cannot prove a second ring; separately authorized relationship evidence must also map exactly one unambiguous direct connector to a non-direct target. Review any exclusions above—the scanner will not invent a path.",
            "",
        ])
    lines.extend([
        "## What it does not prove",
        "",
        "A platform connection does not prove closeness, willingness to reply, willingness to introduce, ranking value, revenue, or community access. Every outreach decision remains human.",
        "",
        "## Privacy receipt",
        "",
        "The parser made no network requests and emitted no telemetry. It does not select dedicated email/provider-ID fields, free-text Evidence notes, or include the source path, source filename, or raw rows. It best-effort redacts email-like and known provider-ID tokens found in selected display fields. If an AI product launched this script, that product's own workspace and data policy still apply.",
        "",
    ])
    return "\n".join(lines)


def html_report(result: ScanResult, redact: bool) -> str:
    names = NameRegistry(redact)
    markdown = markdown_report(result, redact, names)
    nodes = [item.contact for item in result.direct[:6]]
    supported_paths = [item for item in result.paths if item.supported][:4]
    width, height = 920, 560
    center_x, center_y = width / 2, height / 2
    node_markup: list[str] = []
    edge_markup: list[str] = []
    for index, contact in enumerate(nodes):
        angle = (2 * math.pi * index / max(1, len(nodes))) - math.pi / 2
        x = center_x + math.cos(angle) * 190
        y = center_y + math.sin(angle) * 170
        edge_markup.append(f'<line x1="{center_x:.1f}" y1="{center_y:.1f}" x2="{x:.1f}" y2="{y:.1f}" class="edge direct"/>')
        node_markup.append(f'<g><circle cx="{x:.1f}" cy="{y:.1f}" r="48" class="node direct"/><text x="{x:.1f}" y="{y:.1f}" class="label">{html.escape(names.contact(contact))}</text></g>')
    for index, path in enumerate(supported_paths):
        connector_index = next((i for i, contact in enumerate(nodes) if contact.key == path.connector.key), None)
        if connector_index is None:
            continue
        connector_angle = (2 * math.pi * connector_index / max(1, len(nodes))) - math.pi / 2
        connector_x = center_x + math.cos(connector_angle) * 190
        connector_y = center_y + math.sin(connector_angle) * 170
        target_angle = connector_angle + (0.18 if index % 2 == 0 else -0.18)
        target_x = center_x + math.cos(target_angle) * 315
        target_y = center_y + math.sin(target_angle) * 235
        edge_markup.append(f'<line x1="{connector_x:.1f}" y1="{connector_y:.1f}" x2="{target_x:.1f}" y2="{target_y:.1f}" class="edge second"/>')
        node_markup.append(f'<g><circle cx="{target_x:.1f}" cy="{target_y:.1f}" r="43" class="node second"/><text x="{target_x:.1f}" y="{target_y:.1f}" class="label">{html.escape(names.contact(path.target))}</text></g>')
    graph = "".join(edge_markup) + f'<circle cx="{center_x}" cy="{center_y}" r="58" class="node owner"/><text x="{center_x}" y="{center_y}" class="label owner-label">{html.escape(names.owner(result.owner))}</text>' + "".join(node_markup)
    escaped_markdown = html.escape(markdown)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Second Ring local report</title><style>
:root{{--ink:#18342d;--paper:#f5f1e8;--coral:#d76b4b;--mint:#9ed7bd;--lav:#b8a7db}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}
main{{max-width:1080px;margin:auto;padding:40px 24px 72px}}h1{{font-size:clamp(36px,7vw,72px);line-height:1;margin:.2em 0}}
.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-weight:800;color:var(--coral)}}
.trust{{padding:16px 18px;border:1px solid #b6c8c0;border-radius:14px;background:#fff}}
.graph{{margin:28px 0;background:#17372f;border-radius:24px;overflow:auto;box-shadow:0 16px 45px #16372f26}}
svg{{display:block;min-width:760px;width:100%;height:auto}}.edge{{stroke-width:3;opacity:.72}}.edge.direct{{stroke:var(--mint)}}.edge.second{{stroke:var(--lav);stroke-dasharray:8 7}}
.node{{stroke:#fff;stroke-width:3}}.node.owner{{fill:var(--coral)}}.node.direct{{fill:#2d7862}}.node.second{{fill:#725f9a}}
.label{{fill:#fff;text-anchor:middle;dominant-baseline:middle;font-size:13px;font-weight:750}}.owner-label{{font-size:14px}}
pre{{white-space:pre-wrap;background:#fff;padding:24px;border-radius:18px;border:1px solid #d8d2c7;font:14px/1.6 ui-monospace,monospace}}
</style></head><body><main><p class="eyebrow">Local · deterministic · no call-home</p><h1>Second Ring report</h1>
<p class="trust">The parser made no network requests. It does not select dedicated email/provider-ID fields, free-text Evidence notes, source paths, source filenames, or raw rows; selected display fields receive best-effort sensitive-token redaction. Your AI product or managed computer may have its own data policy.</p>
<div class="graph"><svg viewBox="0 0 {width} {height}" role="img" aria-label="Relationship graph"><title>Second Ring relationship graph</title>{graph}</svg></div>
<pre>{escaped_markdown}</pre></main></body></html>"""


def json_report(result: ScanResult, redact: bool) -> str:
    names = NameRegistry(redact)
    supported = [item for item in result.paths if item.supported]
    ask, why, action = best_action(result, names)
    payload = {
        "schemaVersion": "second-ring-local-report-v1",
        "parserVersion": PARSER_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "owner": names.owner(result.owner),
        "goal": result.goal,
        "source": result.source_label,
        "counts": {
            "direct": len(result.contacts),
            "duplicates": result.duplicates,
            "skipped": result.skipped,
            "relationshipRowsSupplied": result.relationship_rows_supplied,
            "relationshipRowsExcluded": result.relationship_rows_excluded,
            "supportedTwoHopPaths": len(supported),
        },
        "relationshipExclusionReasons": result.relationship_exclusion_reasons,
        "limits": {
            "maxArchiveBytes": MAX_ARCHIVE_BYTES,
            "maxExpandedBytes": MAX_EXPANDED_BYTES,
            "maxEntries": MAX_ENTRIES,
            "maxEntryBytes": MAX_ENTRY_BYTES,
            "maxPhysicalExpansionRatio": MAX_COMPRESSION_RATIO,
            "maxRecords": MAX_CONTACTS,
        },
        "scoring": {
            "directScope": "direct_priority",
            "pathScope": "two_hop_path_priority",
            "comparableAcrossScopes": False,
            "instruction": "Act on direct records before requesting an introduction.",
        },
        "bestAction": {"person": ask, "why": why, "action": action},
        "warnings": result.warnings,
        "direct": [
            {
                "person": names.contact(item.contact),
                "context": display_context(item.contact, redact),
                "score": item.score,
                "scoreScope": "direct_priority",
                "factors": item.factors,
            }
            for item in result.direct[:10]
        ],
        "paths": [
            {
                "target": names.contact(item.target),
                "connector": names.contact(item.connector),
                "score": item.score,
                "scoreScope": "two_hop_path_priority",
                "supported": item.supported,
                "relationship": item.relationship.label,
                "status": item.relationship.status,
                "factors": item.factors,
            }
            for item in result.paths[:20]
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", type=Path, help="LinkedIn ZIP/CSV or Google Contacts CSV")
    input_group.add_argument("--demo", action="store_true", help="Use fictional built-in data")
    parser.add_argument("--relationships", type=Path, help="Separately authorized relationship CSV")
    parser.add_argument(
        "--confirm-relationship-data-authorized",
        action="store_true",
        help="Confirm authority to analyze the relationship CSV",
    )
    parser.add_argument("--owner", required=True, help="Network owner display name")
    parser.add_argument("--goal", required=True, choices=tuple(GOAL_KEYWORDS))
    parser.add_argument("--target", default="", help="Optional person to locate")
    parser.add_argument("--format", choices=("markdown", "html", "json"), default="markdown")
    parser.add_argument("--redact-names", action="store_true", help="Use stable aliases and remove context")
    parser.add_argument("--output", type=Path, help="Write the report instead of stdout")
    return parser


def run(args: argparse.Namespace) -> str:
    if args.relationships and not args.confirm_relationship_data_authorized:
        raise ScanError("Relationship evidence requires --confirm-relationship-data-authorized.")
    if args.demo:
        result = demo_data(clean_display(args.owner), args.goal)
    else:
        source_label, contacts, duplicates, skipped = load_contacts(args.input)
        direct = sorted((score_direct(contact, args.goal) for contact in contacts), key=lambda item: (-item.score, normalize(item.contact.name)))
        if args.relationships:
            relationships, relationship_rows, relationship_exclusions = parse_relationships(
                args.relationships
            )
        else:
            relationships, relationship_rows, relationship_exclusions = [], 0, {}
        paths, path_exclusions = build_paths(contacts, relationships, args.goal)
        for reason, count in path_exclusions.items():
            relationship_exclusions[reason] = relationship_exclusions.get(reason, 0) + count
        warnings: list[str] = []
        name_counts: dict[str, int] = {}
        for contact in contacts:
            name_key = normalize(contact.name)
            name_counts[name_key] = name_counts.get(name_key, 0) + 1
        duplicate_names = sum(1 for count in name_counts.values() if count > 1)
        if duplicate_names:
            warnings.append(f"{duplicate_names} normalized name collisions remain separate and require human review.")
        relationship_rows_excluded = sum(relationship_exclusions.values())
        if relationship_rows_excluded:
            detail = ", ".join(
                f"{count} {reason.replace('_', ' ')}"
                for reason, count in sorted(relationship_exclusions.items())
            )
            warnings.append(
                f"{relationship_rows_excluded} of {relationship_rows} relationship rows did not become paths ({detail})."
            )
        if args.relationships and not relationships:
            warnings.append(
                "The relationship CSV contained no rows with both Source and Target; direct results remain available."
            )
        result = ScanResult(
            owner=clean_display(args.owner),
            goal=args.goal,
            source_label=source_label,
            contacts=contacts,
            direct=direct,
            paths=paths,
            duplicates=duplicates,
            skipped=skipped,
            warnings=warnings,
            relationship_rows_supplied=relationship_rows,
            relationship_rows_excluded=relationship_rows_excluded,
            relationship_exclusion_reasons=relationship_exclusions,
        )
    apply_target(result, clean_display(args.target))
    if args.format == "html":
        return html_report(result, args.redact_names)
    if args.format == "json":
        return json_report(result, args.redact_names)
    return markdown_report(result, args.redact_names)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = run(args)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report, encoding="utf-8")
            print(f"Wrote {args.format} report to {args.output}", file=sys.stderr)
        else:
            sys.stdout.write(report)
        return 0
    except (OSError, ScanError, zipfile.BadZipFile, csv.Error) as error:
        print(f"Second Ring scan stopped safely: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
