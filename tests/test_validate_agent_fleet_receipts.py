from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from scripts.agent_fleet_contract import (
    IDENTITY_REGISTRY_BYTES,
    PUBLIC_MODEL_IDS,
    parse_identity_registry_bytes,
    registry_history_problem,
)
from scripts import fleet_check
from scripts.validate_agent_fleet_receipts import (
    ALLOWED_FIELDS,
    COMMON_FIELDS,
    FAILURE_FIELDS,
    FAILURE_CONTRACTS,
    FLEET_LIVE_URL,
    GOLDEN_RECEIPT,
    GOLDEN_RAIL,
    GOLDEN_SOURCE,
    MARKER_END,
    MARKER_START,
    RECEIPTS_DIR,
    SOURCES_DIR,
    SOURCE_MANIFEST_FIELDS,
    SUCCESS_FIELDS,
    _canonical_receipt_id,
    _ledger_namespace_errors,
    _parse_iso_instant,
    _private_string,
    _read_bounded_regular_bytes,
    _schema_contract_errors,
    _source_binding_errors,
    _source_schema_contract_errors,
    _valid_human_identity,
    append_only_errors,
    validate_directory,
    validate_receipt,
    validate_source_manifest,
)


REPOSITORY = Path(__file__).resolve().parents[1]


def verified_receipt() -> dict:
    return json.loads(GOLDEN_RECEIPT.read_text(encoding="utf-8"))


def receipt(status: str = "verified") -> dict:
    value = verified_receipt()
    value["verificationHash"] = hashlib.sha256(
        b"unit-test-production-verification"
    ).hexdigest()
    value["receiptId"] = "fleet-page-" + value["verificationHash"][:20]
    value["contentHash"] = hashlib.sha256(
        b"unit-test-production-content"
    ).hexdigest()
    value["linkContentHash"] = value["contentHash"]
    if status == "verification-failed":
        for field in SUCCESS_FIELDS:
            value.pop(field)
        value["status"] = status
        value.update(
            {
                "failureStage": "anonymous-readback",
                "failureCode": "HASH_MISMATCH",
                "failureDetail": "The published bytes did not match the expected hashes.",
            }
        )
    return value


def receipt_path(value: dict) -> Path:
    return Path(f"{value['receiptId']}.json")


class AgentFleetReceiptValidatorTests(unittest.TestCase):
    def test_identity_registry_is_exact_private_safe_and_version_immutable(self):
        original = json.loads(IDENTITY_REGISTRY_BYTES.decode("utf-8"))
        cases = (
            ("actorRegistries", "agent:unknown-review"),
            ("actorRegistries", "agent:none"),
            ("actorRegistries", "agent:botv2"),
            ("actorRegistries", "job:robot-audit"),
            ("actorRegistries", "agent:placeholder-worker"),
            ("actorRegistries", "job:system-checker"),
            ("modelRegistries", "unknown-pro"),
            ("modelRegistries", "pending"),
            ("modelRegistries", "pendingv2"),
            ("modelRegistries", "robot-runtime"),
            ("modelRegistries", "placeholder-enterprise"),
            ("modelRegistries", "example-release"),
            ("humanReviewerRegistries", "dennis@example.com"),
            ("humanReviewerRegistries", "/Users/dennis/private"),
            ("humanReviewerRegistries", "sk_live_ABCDEFGHIJKLMNOP"),
            ("humanReviewerRegistries", "Private Prompt: topsecret"),
            ("humanReviewerRegistries", "Ｄｅｎｎｉｓ Ｙｕ"),
            ("humanReviewerRegistries", "Dennis\u00a0Yu"),
            ("humanReviewerRegistries", "Dennis  Yu"),
            ("humanReviewerRegistries", "No One"),
            ("humanReviewerRegistries", "Nobody Home"),
            ("humanReviewerRegistries", "Not Assigned"),
            ("humanReviewerRegistries", "Review Pending"),
            ("humanReviewerRegistries", "Not Yet Reviewed"),
            ("humanReviewerRegistries", "Unknownv2 Reviewer"),
            ("humanReviewerRegistries", "Robot Smith"),
            ("humanReviewerRegistries", "Reviewer TBD"),
            ("humanReviewerRegistries", "Human Reviewer Alice"),
            ("humanReviewerRegistries", "The Named Reviewer"),
            ("modelRegistries", "/private/var/secrets/model"),
            ("modelRegistries", "client.secret=topsecret"),
            ("modelRegistries", "Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="),
            ("modelRegistries", "ＧＰＴ-5"),
            ("modelRegistries", "GPT‐5"),
            ("modelRegistries", "GPT-5\u007f"),
            ("modelRegistries", "GPT-5\u0085"),
            ("modelRegistries", "GPT-5\ufe0f"),
        )
        for collection, bad_value in cases:
            with self.subTest(collection=collection, bad_value=bad_value):
                changed = copy.deepcopy(original)
                version = next(iter(changed[collection]))
                changed[collection][version] = sorted(
                    changed[collection][version] + [bad_value]
                )
                with self.assertRaises(ValueError):
                    parse_identity_registry_bytes(
                        (json.dumps(changed, ensure_ascii=False) + "\n").encode()
                    )

        unspaced = copy.deepcopy(original)
        version = unspaced["humanReviewerRegistries"]
        key = next(iter(version))
        version[key] = sorted(version[key] + ["李小龙"])
        self.assertIsInstance(
            parse_identity_registry_bytes(
                (json.dumps(unspaced, ensure_ascii=False) + "\n").encode()
            ),
            dict,
        )

        changed = copy.deepcopy(original)
        version = next(iter(changed["actorRegistries"]))
        changed["actorRegistries"][version].append("agent:new-reviewed-actor")
        changed["actorRegistries"][version].sort()
        current_bytes = (json.dumps(changed, ensure_ascii=False) + "\n").encode()
        self.assertIn("changed immutable version", registry_history_problem(
            IDENTITY_REGISTRY_BYTES, current_bytes
        ))

    def test_registry_controlled_receipt_fields_require_exact_raw_members(self):
        value = receipt()
        substitutions = (
            ("model", "ＧＰＴ-5"),
            ("checkedBy", "ａｇｅｎｔ：ｃｏｄｅｘ－ｌｓｓ－ｖｅｒｉｆｉｅｒ"),
            ("browserCheckedBy", "ａｇｅｎｔ：ｃｏｄｅｘ－ｂｒｏｗｓｅｒ－ｖｅｒｉｆｉｅｒ"),
            ("humanReviewer", "Ｄｅｎｎｉｓ Ｙｕ"),
        )
        for field, replacement in substitutions:
            with self.subTest(field=field):
                changed = copy.deepcopy(value)
                changed[field] = replacement
                self.assertTrue(
                    validate_receipt(changed, receipt_path(changed)),
                    field,
                )

    def test_tracked_schema_and_shared_golden_fixture_pass(self):
        self.assertEqual(validate_directory(RECEIPTS_DIR), [])
        self.assertEqual(
            sorted(path.name for path in SOURCES_DIR.glob("*.json")),
            ["source.schema.json"],
        )
        self.assertTrue(GOLDEN_SOURCE.is_file())
        value = verified_receipt()
        self.assertEqual(set(value), COMMON_FIELDS | SUCCESS_FIELDS)
        self.assertEqual(set(value) | FAILURE_FIELDS, ALLOWED_FIELDS)

    def test_golden_fleet_rail_and_receipt_prove_one_cross_repo_contract(self):
        receipt_value = verified_receipt()
        body = GOLDEN_RAIL.read_bytes()
        text = body.decode("utf-8")
        start = MARKER_START.encode("utf-8")
        end = MARKER_END.encode("utf-8")
        self.assertEqual(body.count(start), 1)
        self.assertEqual(body.count(end), 1)
        marker_slice = body[body.index(start) : body.index(end) + len(end)]
        self.assertEqual(body[: body.index(start)].strip(), b"")
        self.assertEqual(body[body.index(end) + len(end) :].strip(), b"")
        self.assertEqual(
            hashlib.sha256(body).hexdigest(), receipt_value["postContentHash"]
        )
        self.assertEqual(
            hashlib.sha256(body).hexdigest(),
            receipt_value["anonymousResponseSha256"],
        )
        self.assertEqual(len(body), receipt_value["anonymousContentLength"])
        self.assertEqual(
            hashlib.sha256(marker_slice).hexdigest(),
            receipt_value["extractedPostContentSha256"],
        )
        self.assertEqual(fleet_check.provenance_contract_problems(text), [])

        parser = fleet_check._ProvenanceParser()
        parser.feed(text)
        parser.close()
        self.assertEqual(len(parser.rails), 1)
        attributes = parser.rails[0].attributes
        for receipt_field, rail_field in (
            ("receiptId", "data-publication-receipt-id"),
            ("sourceRevision", "data-source-revision"),
            ("model", "data-maintainer-model"),
            ("humanReviewer", "data-human-reviewer"),
            ("runId", "data-capture-run-id"),
        ):
            self.assertEqual(receipt_value[receipt_field], attributes[rail_field])
        expected_source_url = (
            fleet_check.FLEET_SOURCE_MANIFEST_PREFIX
            + receipt_value["sourceRevision"]
            + ".json"
        )
        self.assertEqual(attributes["data-source-url"], expected_source_url)
        self.assertEqual(attributes["data-document-provenance"],
                         "pending-external-verification")
        self.assertEqual(attributes["data-publication-verification-result"], "pending")
        self.assertEqual(receipt_value["status"], "verified")

        schemas = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', text
        )
        self.assertEqual(len(schemas), 1)
        article = json.loads(schemas[0])
        self.assertEqual(article["@type"], "Article")
        self.assertEqual(article["dateModified"], receipt_value["articleDateModified"])
        self.assertEqual(
            receipt_value["articleDateModified"], receipt_value["wordpressModifiedAt"]
        )
        self.assertLessEqual(
            _parse_iso_instant(attributes["data-last-checked"]),
            _parse_iso_instant(receipt_value["articleDateModified"]),
        )
        self.assertLessEqual(
            _parse_iso_instant(receipt_value["articleDateModified"]),
            _parse_iso_instant(receipt_value["checkedAt"]),
        )

    def test_verified_and_failed_receipts_have_distinct_valid_shapes(self):
        for status in ("verified", "verification-failed"):
            with self.subTest(status=status):
                value = receipt(status)
                self.assertEqual(validate_receipt(value, receipt_path(value)), [])

    def test_human_reviewer_length_matches_the_tracked_schema(self):
        value = receipt()
        value["humanReviewer"] = "Alice " + "Z" * 300
        errors = validate_receipt(value, receipt_path(value))
        self.assertTrue(any("human reviewer" in error for error in errors), errors)

    def test_sanitized_source_manifest_binds_verified_receipt(self):
        value = receipt()
        path = GOLDEN_SOURCE
        raw = path.read_bytes()
        manifest = json.loads(raw)
        self.assertEqual(set(manifest), SOURCE_MANIFEST_FIELDS)
        self.assertEqual(validate_source_manifest(manifest, path), [])
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(), value["sourceManifestSha256"]
        )
        bindings = {
            value["sourceRevision"]: (
                manifest,
                path,
                hashlib.sha256(raw).hexdigest(),
            )
        }
        self.assertEqual(_source_binding_errors(value, receipt_path(value), bindings), [])

        for field, bad_value in (
            ("sourceManifestSha256", "d" * 64),
            ("configuredCount", value["configuredCount"] + 1),
            ("sourceRevision", "e" * 40),
        ):
            with self.subTest(field=field):
                changed = receipt()
                changed[field] = bad_value
                errors = _source_binding_errors(
                    changed, receipt_path(changed), bindings
                )
                self.assertTrue(any(field in error for error in errors), errors)

        candidate_only_change = receipt()
        candidate_only_change["contentHash"] = "e" * 64
        candidate_only_change["linkContentHash"] = "e" * 64
        self.assertEqual(
            _source_binding_errors(
                candidate_only_change,
                receipt_path(candidate_only_change),
                bindings,
            ),
            [],
        )

        failed = receipt("verification-failed")
        missing_errors = _source_binding_errors(failed, receipt_path(failed), {})
        self.assertTrue(
            any("no sanitized source manifest" in error for error in missing_errors),
            missing_errors,
        )
        self.assertEqual(
            _source_binding_errors(failed, receipt_path(failed), bindings), []
        )

    def test_source_manifest_rejects_unknown_fields_and_backward_counts(self):
        value = receipt()
        path = GOLDEN_SOURCE
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["privateJobId"] = "private-123"
        manifest["publicDefinitionCount"] = manifest["configuredCount"] + 1
        errors = validate_source_manifest(manifest, path)
        self.assertTrue(any("unknown source-manifest" in error for error in errors), errors)
        self.assertTrue(any("exceeds configuredCount" in error for error in errors), errors)

        placeholder = json.loads(GOLDEN_SOURCE.read_text(encoding="utf-8"))
        placeholder["sourceRevision"] = "0" * 40
        placeholder_path = Path(("0" * 40) + ".json")
        errors = validate_source_manifest(placeholder, placeholder_path)
        self.assertTrue(any("placeholder commit" in error for error in errors), errors)

    def test_source_manifest_schema_version_rejects_numeric_lookalikes(self):
        manifest = json.loads(GOLDEN_SOURCE.read_text(encoding="utf-8"))
        for bad_version in (1.0, True):
            with self.subTest(schemaVersion=bad_version):
                changed = copy.deepcopy(manifest)
                changed["schemaVersion"] = bad_version
                errors = validate_source_manifest(changed, GOLDEN_SOURCE)
                self.assertTrue(
                    any("schemaVersion must be integer 1" in error for error in errors),
                    errors,
                )

    def test_source_manifest_reports_non_string_member_names_without_crashing(self):
        for bad_key in (1, ("tuple", "key")):
            with self.subTest(key=bad_key):
                errors = validate_source_manifest(
                    {bad_key: "value", "x": 3},
                    Path("a" * 40 + ".json"),
                )
                self.assertTrue(
                    any("unknown source-manifest field" in error for error in errors),
                    errors,
                )

    def test_source_manifest_is_stable_source_only_evidence(self):
        manifest = json.loads(GOLDEN_SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["sourceRepository"],
            "https://github.com/Local-Service-Spotlight/agent-fleet",
        )
        self.assertEqual(manifest["generatorContract"], "fleet-public-render-v3")
        for volatile_field in (
            "contentHash",
            "checkedAt",
            "checkedBy",
            "runId",
            "humanReviewer",
        ):
            self.assertNotIn(volatile_field, manifest)

    def test_two_candidates_from_one_source_revision_reuse_identical_manifest(self):
        first_receipt = receipt()
        first_manifest = json.loads(GOLDEN_SOURCE.read_text(encoding="utf-8"))
        first_raw = GOLDEN_SOURCE.read_bytes()

        second_receipt = copy.deepcopy(first_receipt)
        second_receipt["verificationHash"] = hashlib.sha256(
            b"second-candidate-verification"
        ).hexdigest()
        second_receipt["receiptId"] = (
            "fleet-page-" + second_receipt["verificationHash"][:20]
        )
        second_receipt["contentHash"] = hashlib.sha256(
            b"second-candidate-content"
        ).hexdigest()
        second_receipt["linkContentHash"] = second_receipt["contentHash"]

        self.assertEqual(first_receipt["sourceRevision"], second_receipt["sourceRevision"])
        self.assertEqual(validate_source_manifest(first_manifest, GOLDEN_SOURCE), [])
        self.assertEqual(
            first_receipt["sourceManifestSha256"],
            second_receipt["sourceManifestSha256"],
        )
        bindings = {
            first_receipt["sourceRevision"]: (
                first_manifest,
                GOLDEN_SOURCE,
                hashlib.sha256(first_raw).hexdigest(),
            )
        }
        self.assertEqual(
            _source_binding_errors(
                first_receipt, receipt_path(first_receipt), bindings
            ),
            [],
        )
        self.assertEqual(
            _source_binding_errors(
                second_receipt, receipt_path(second_receipt), bindings
            ),
            [],
        )
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source_dir = root / "receipts" / "agent-fleet" / "sources"
            source_dir.mkdir(parents=True)
            receipt_dir = source_dir.parent
            (receipt_dir / "README.md").write_text("fixture ledger\n", encoding="utf-8")
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "test@example.com"),
                ("git", "config", "user.name", "Test Reviewer"),
                ("git", "add", "."),
                ("git", "commit", "-qm", "ledger baseline"),
            ):
                subprocess.run(command, cwd=root, check=True)

            (source_dir / GOLDEN_SOURCE.name).write_bytes(first_raw)
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            subprocess.run(
                ("git", "commit", "-qm", "first source companion"),
                cwd=root,
                check=True,
            )
            (receipt_dir / f"{first_receipt['receiptId']}.json").write_text(
                json.dumps(first_receipt, indent=2) + "\n", encoding="utf-8"
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            self.assertEqual(append_only_errors("HEAD", root), [])
            subprocess.run(
                ("git", "commit", "-qm", "first publication receipt"),
                cwd=root,
                check=True,
            )

            (receipt_dir / f"{second_receipt['receiptId']}.json").write_text(
                json.dumps(second_receipt, indent=2) + "\n", encoding="utf-8"
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            self.assertEqual(append_only_errors("HEAD", root), [])

    def test_source_revision_change_gets_a_new_stable_manifest_url(self):
        first = json.loads(GOLDEN_SOURCE.read_text(encoding="utf-8"))
        second = copy.deepcopy(first)
        second["sourceRevision"] = "e1d2c3b4a5968778695a4b3c2d1e0f1234567890"
        second_path = GOLDEN_SOURCE.with_name(second["sourceRevision"] + ".json")
        self.assertEqual(validate_source_manifest(second, second_path), [])
        first_url = fleet_check.FLEET_SOURCE_MANIFEST_PREFIX + first["sourceRevision"] + ".json"
        second_url = fleet_check.FLEET_SOURCE_MANIFEST_PREFIX + second["sourceRevision"] + ".json"
        self.assertNotEqual(first_url, second_url)

    def test_failed_receipt_requires_typed_sanitized_failure_fields(self):
        for field, bad_value in (
            ("failureStage", None),
            ("failureCode", "hash mismatch"),
            ("failureDetail", None),
        ):
            with self.subTest(field=field):
                value = receipt("verification-failed")
                value[field] = bad_value
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any(field in error for error in errors), errors)

        missing = receipt("verification-failed")
        missing.pop("failureCode")
        errors = validate_receipt(missing, receipt_path(missing))
        self.assertTrue(any("failed receipt missing" in error for error in errors), errors)

    def test_failed_receipt_uses_only_approved_non_free_text_templates(self):
        for stage, code, detail in FAILURE_CONTRACTS:
            with self.subTest(code=code):
                value = receipt("verification-failed")
                value.update(
                    {
                        "failureStage": stage,
                        "failureCode": code,
                        "failureDetail": detail,
                    }
                )
                self.assertEqual(validate_receipt(value, receipt_path(value)), [])

        for detail in (
            "Private job somba-daily-new-member-scoring failed for client Sigrun.",
            "Registry local-agent-mode-sessions/a/b/scheduled-tasks.json failed.",
            "Token sk_live_1234567890 was rejected.",
            "Client member Dennis Yu was affected.",
        ):
            with self.subTest(detail=detail):
                value = receipt("verification-failed")
                value["failureDetail"] = detail
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any("approved sanitized" in error for error in errors), errors)

    def test_status_shapes_cannot_leak_fields_into_each_other(self):
        success = receipt()
        success["failureCode"] = "HASH_MISMATCH"
        self.assertTrue(
            any("failure-only" in error for error in validate_receipt(success, receipt_path(success)))
        )

        failed = receipt("verification-failed")
        failed["httpStatus"] = 500
        self.assertTrue(
            any("success-only" in error for error in validate_receipt(failed, receipt_path(failed)))
        )

    def test_success_hashes_and_counts_bind_the_exact_candidate(self):
        value = receipt()
        self.assertNotEqual(
            value["postContentHash"], value["extractedPostContentSha256"]
        )
        self.assertEqual(validate_receipt(value, receipt_path(value)), [])

        short_cache_buster = receipt()
        short_cache_buster["cacheBuster"] = "1"
        errors = validate_receipt(
            short_cache_buster, receipt_path(short_cache_buster)
        )
        self.assertTrue(any("cacheBuster" in error for error in errors), errors)
        cases = (
            ("extractedPostContentSha256", "not-a-hash", "lowercase SHA-256"),
            ("linkContentHash", "d" * 64, "must equal contentHash"),
            ("itemListCount", 30, "must equal publicDefinitionCount"),
            ("publicDefinitionCount", 54, "exceeds configuredCount"),
            ("configuredCount", True, "non-negative integer"),
        )
        for field, bad_value, expected in cases:
            with self.subTest(field=field):
                value = receipt()
                value[field] = bad_value
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any(expected in error for error in errors), errors)

        placeholders = receipt()
        for field in (
            "contentHash", "verificationHash", "postContentHash",
            "extractedPostContentSha256", "anonymousResponseSha256",
            "linkContentHash",
        ):
            placeholders[field] = "0" * 64
        placeholders["receiptId"] = "fleet-page-" + "0" * 20
        production_path = Path(f"{placeholders['receiptId']}.json")
        errors = validate_receipt(placeholders, production_path)
        self.assertTrue(any("placeholder digest" in error for error in errors), errors)

    def test_id_is_exactly_verification_hash_prefix(self):
        value = receipt()
        self.assertEqual(
            _canonical_receipt_id(value),
            "fleet-page-" + value["verificationHash"][:20],
        )
        original_id = value["receiptId"]
        value["verificationHash"] = "e" * 64
        errors = validate_receipt(value, Path(f"{original_id}.json"))
        self.assertTrue(any("verificationHash[:20]" in error for error in errors), errors)

    def test_unrelated_examples_parent_does_not_enable_fixture_digests(self):
        value = verified_receipt()
        lookalike = Path("/tmp/examples") / f"{value['receiptId']}.json"
        errors = validate_receipt(value, lookalike)
        self.assertTrue(any("placeholder digest" in error for error in errors), errors)

    def test_exact_marker_field_names_and_inclusive_bytes_do_not_drift(self):
        value = receipt()
        self.assertEqual(value["extractionStart"], MARKER_START)
        self.assertEqual(value["extractionEnd"], MARKER_END)
        for mutation in (
            {"markerStart": MARKER_START},
            {"extractionStart": "<!-- BM-FLEET-PAGE START -->"},
            {"markerEnd": MARKER_END},
            {"extractionEnd": "<!-- BM-FLEET-PAGE END -->"},
        ):
            with self.subTest(mutation=mutation):
                changed = receipt()
                changed.update(mutation)
                errors = validate_receipt(changed, receipt_path(changed))
                self.assertTrue(errors)

    def test_actual_reviewer_role_and_model_must_not_be_placeholders(self):
        cases = (
            ("humanReviewer", "unknown"),
            ("humanReviewer", "TBD"),
            ("humanReviewer", "pending review"),
            ("humanReviewer", "reviewer"),
            ("humanReviewer", "reviewed"),
            ("humanReviewer", "review complete"),
            ("humanReviewer", "someone"),
            ("humanReviewer", "anonymous"),
            ("humanReviewer", "redacted"),
            ("humanReviewer", "not disclosed"),
            ("humanReviewer", "unassigned"),
            ("humanReviewer", "review required"),
            ("humanReviewer", "system"),
            ("humanReviewer", "invalid public reviewer"),
            ("humanReviewer", "Codex"),
            ("humanReviewer", "Codex reviewer"),
            ("humanReviewer", "Claude human reviewer"),
            ("humanReviewer", "AI reviewer"),
            ("humanReviewer", "Robot Reviewer"),
            ("humanReviewer", "Llama 3 Reviewer"),
            ("humanReviewer", "LLM reviewer"),
            ("humanReviewer", "Agent Reviewer"),
            ("humanReviewer", "Qwen2 Reviewer"),
            ("humanReviewer", "DeepSeek reviewer"),
            ("humanReviewer", "%73omeone"),
            ("humanReviewer", "%61nonymous"),
            ("humanReviewer", "%72edacted"),
            ("humanReviewer", "%73ystem"),
            ("humanReviewer", "%70ending%20review"),
            ("humanReviewer", "%55NKNOWN"),
            ("humanReviewer", "%43odex reviewer"),
            ("humanReviewerRole", "reviewer"),
            ("model", "pending"),
            ("model", "%55NKNOWN"),
            ("checkedBy", "system"),
        )
        for field, bad_value in cases:
            with self.subTest(field=field, bad_value=bad_value):
                value = receipt()
                value[field] = bad_value
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any(field in error for error in errors), errors)

        unknown_model = receipt()
        unknown_model["model"] = "UNKNOWN"
        self.assertEqual(validate_receipt(unknown_model, receipt_path(unknown_model)), [])

    def test_numeric_fields_reject_bool_and_float_lookalikes(self):
        for field, bad_value in (
            ("schemaVersion", 1.0),
            ("schemaVersion", True),
            ("httpStatus", 200.0),
            ("articleSchemaCount", 1.0),
        ):
            with self.subTest(field=field, value=bad_value):
                value = receipt()
                value[field] = bad_value
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any(field in error for error in errors), errors)

    def test_unknown_and_case_normalized_private_fields_are_rejected(self):
        for key in (
            "clientData",
            "client_data",
            "apiKey",
            "API_KEY",
            "password",
            "privateJobId",
            "private_job_id",
            "ledgerCommit",
        ):
            with self.subTest(key=key):
                value = receipt()
                value[key] = "secret-value"
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any("unknown public field" in error for error in errors), errors)
                self.assertTrue(any("forbidden" in error for error in errors), errors)

        nested = receipt()
        nested["metadata"] = {"Api_Key": "secret-value"}
        errors = validate_receipt(nested, receipt_path(nested))
        self.assertTrue(any("forbidden" in error for error in errors), errors)

    def test_urls_fail_closed_without_raising(self):
        for invalid in (
            "https://[bad",
            "https://example.test:99999/page",
            "https://example.test/bad path",
            "https://example.test/page%0A",
            "http://example.test/page",
            "https://localhost/",
            "https://127.0.0.1/",
            "https://10.0.0.1/",
            "https://169.254.169.254/latest/meta-data/",
            "https://[::1]/",
            "https://internal/",
            "https://fleet.local/",
            FLEET_LIVE_URL + "?api_key=supersecretvalue",
            FLEET_LIVE_URL + "?token=supersecretvalue",
            FLEET_LIVE_URL + "?password=supersecretvalue",
        ):
            with self.subTest(url=invalid):
                value = receipt()
                value["liveUrl"] = invalid
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any("liveUrl" in error for error in errors), errors)

    def test_percent_encoded_private_values_are_rejected(self):
        nested_path = "/tmp/client-secret.json"
        for _ in range(20):
            nested_path = quote(nested_path, safe="")
        for private_value in (
            "%2Fprivate%2Fvar%2Ffolders%2Fab%2Fcandidate.json",
            "%252Ftmp%252Ffleet%252Fprivate-client.json",
            "%7E%2FLibrary%2FApplication%20Support%2FClaude%2Fsecret.json",
            "%3Fapi_key%3Dsupersecretvalue",
            nested_path,
        ):
            with self.subTest(value=private_value):
                value = receipt()
                value["cacheBuster"] = private_value
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(
                    any("receipt contains" in error for error in errors), errors
                )

    def test_non_url_receipt_fields_cannot_carry_private_artifact_urls(self):
        private_urls = (
            "https://secrets.internal.corp/client-alpha/private.json",
            "https://localhost/private.json",
            "https://10.0.0.1/private.json",
        )
        fields = (
            "cacheBuster",
            "runId",
            "linkReceiptId",
            "browserRunReceiptId",
            "wordpressRevision",
            "checkedBy",
            "model",
        )
        for field in fields:
            for private_url in private_urls:
                with self.subTest(field=field, url=private_url):
                    value = receipt()
                    value[field] = private_url
                    errors = validate_receipt(value, receipt_path(value))
                    self.assertTrue(
                        any("unapproved artifact URL" in error for error in errors),
                        errors,
                    )

    def test_public_identifiers_cannot_carry_common_live_secret_shapes(self):
        secrets = (
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghi1234567890",
            "AIzaabcdefghijklmnopqrstuvwxyz123456789",
            "SG.abcdefghijklmno.abcdefghijklmnopqrstuvwxyz123456",
            "github_pat_11AAabcdefghijklmnopqrstuvwxyz123456",
            "glpat-abcdefghijklmnopqrstuvwx",
            "sk_proj_abcdefghijklmnopqrstuvwx",
            "rk_live_abcdefghijklmnopqrstuvwx",
            "ASIAABCDEFGHIJKLMNOP",
            "-----BEGIN PRIVATE KEY-----",
            "npm_abcdefghijklmnopqrstuvwxyz123456",
            "ya29.abcdefghijklmnopqrstuvwxyz123456",
            "pypi-abcdefghijklmnopqrstuvwxyz",
            "dop_v1_abcdefghijklmnopqrstuvwxyz",
            "hf_abcdefghijklmnopqrstuvwxyz",
            "SK0123456789abcdef0123456789abcdef",
            "Basic dXNlcjpwYXNzd29yZA==",
            "Basic-dXNlcjpwYXNzd29yZA==",
            "glrt-abcdefghijklmnopqrstuvwxyz123456",
            "abcdefghijklmnopqrst.abcdef.uvwxyzabcdefghijklmn",
            "Account-Key: YWJjZGVmZ2hpamtsbW5vcA==",
        )
        fields = (
            "runId",
            "linkReceiptId",
            "browserRunReceiptId",
            "cacheBuster",
            "wordpressRevision",
        )
        for field in fields:
            for secret in secrets:
                with self.subTest(field=field, secret=secret[:5]):
                    value = receipt()
                    value[field] = secret
                    errors = validate_receipt(value, receipt_path(value))
                    self.assertTrue(
                        any("credential/token" in error for error in errors), errors
                    )
        for secret in secrets:
            with self.subTest(encoded_secret=secret[:5]):
                self.assertEqual(
                    _private_string(quote(secret, safe="")),
                    "credential/token pattern",
                )

    def test_public_fields_reject_protocol_relative_or_network_paths(self):
        cases = (
            ("runId", "capture-//fileserver/client-alpha"),
            ("linkReceiptId", "links-//10.0.0.1/share"),
            ("cacheBuster", "cache-//fileserver/private"),
            ("wordpressRevision", "rev-//fileserver/private"),
            ("humanReviewer", "Mina //fileserver/private Patel"),
            ("model", "GPT-5 //fileserver/private"),
        )
        for field, unsafe in cases:
            with self.subTest(field=field):
                value = receipt()
                value[field] = unsafe
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(
                    any("network-path URL" in error for error in errors), errors
                )

    def test_canonical_urls_are_valid_only_in_dedicated_url_fields(self):
        for url_form in (FLEET_LIVE_URL, quote(FLEET_LIVE_URL, safe="")):
            for field in (
                "humanReviewer",
                "browserCheckedBy",
                "checkedBy",
                "model",
                "runId",
                "linkReceiptId",
                "browserRunReceiptId",
                "cacheBuster",
                "wordpressRevision",
            ):
                with self.subTest(field=field, value=url_form):
                    value = receipt()
                    value[field] = url_form
                    errors = validate_receipt(value, receipt_path(value))
                    self.assertTrue(any(field in error for error in errors), errors)

        for field in ("cacheBuster", "wordpressRevision"):
            for encoded_placeholder in ("%73ample", "%70laceholder", "%55NKNOWN"):
                with self.subTest(field=field, value=encoded_placeholder):
                    value = receipt()
                    value[field] = encoded_placeholder
                    errors = validate_receipt(value, receipt_path(value))
                    self.assertTrue(any(field in error for error in errors), errors)

        for obfuscated_identity in (
            "some\u200bone",
            "anon\u200bymous",
            "un\u200bassigned",
            "pend\u200bing review",
            "Cod\u200bex reviewer",
            "Deep\u200bSeek reviewer",
        ):
            with self.subTest(humanReviewer=obfuscated_identity):
                value = receipt()
                value["humanReviewer"] = obfuscated_identity
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(
                    any("humanReviewer" in error for error in errors), errors
                )

        for field, obfuscated_identity in (
            ("humanReviewer", "Mina\u200b Patel"),
            ("model", "GPT-\u200b5"),
            ("checkedBy", "agent:cod\u200bex-verifier"),
            ("browserCheckedBy", "agent:browser\u200b-qa"),
        ):
            with self.subTest(field=field, obfuscated=obfuscated_identity):
                value = receipt()
                value[field] = obfuscated_identity
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any(field in error for error in errors), errors)

        for field in ("checkedBy", "browserCheckedBy"):
            for invalid_id in ("agent:a", "agent:ai", "job:x"):
                with self.subTest(field=field, invalid_id=invalid_id):
                    value = receipt()
                    value[field] = invalid_id
                    errors = validate_receipt(value, receipt_path(value))
                    self.assertTrue(any(field in error for error in errors), errors)
        obfuscated_model = receipt()
        obfuscated_model["model"] = "pend\ufe0fing"
        self.assertTrue(
            any(
                "model" in error
                for error in validate_receipt(
                    obfuscated_model, receipt_path(obfuscated_model)
                )
            )
        )
        obfuscated_unknown_model = receipt()
        obfuscated_unknown_model["model"] = "UNKN\u200bOWN"
        self.assertTrue(
            any(
                "model" in error
                for error in validate_receipt(
                    obfuscated_unknown_model,
                    receipt_path(obfuscated_unknown_model),
                )
            )
        )
        for generic_model in (
            "model",
            "AI",
            "assistant",
            "bot",
            "LLM",
            "language model",
            "runtime model",
            "some model",
            "GPT",
            "Claude",
            "Codex",
            "ChatGPT",
            "Gemini",
            "Qwen",
            "DeepSeek",
            "OpenAI",
            "Anthropic",
            "AI model",
            "LLM model",
            "production model",
            "current model",
            "latest model",
            "runtime",
            "default",
            "unspecified model",
            "model v1",
            "GPT model",
            "Claude model",
            "OpenAI model",
            "vendor model",
            "chatbot",
            "banana",
            "Alice Smith",
            "runtime banana",
            "vendor banana",
            "other",
            "proprietary",
            "frontier",
            "chat",
            "text generator",
            "Reviewer Alice",
            "GPT banana",
            "Claude banana",
        ):
            with self.subTest(generic_model=generic_model):
                value = receipt()
                value["model"] = generic_model
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any("model" in error for error in errors), errors)

        for concrete_model in sorted(PUBLIC_MODEL_IDS):
            with self.subTest(concrete_model=concrete_model):
                value = receipt()
                value["model"] = concrete_model
                self.assertEqual(validate_receipt(value, receipt_path(value)), [])

        for generic_reviewer in (
            "staff",
            "team",
            "employee",
            "manager",
            "owner",
            "auditor",
            "operator",
            "admin",
            "the team",
            "review staff",
            "quality team",
            "QA team",
            "Human Review Team",
            "Security Team",
            "Operations Team",
            "Compliance Team",
            "Editorial Board",
            "Review Committee",
            "QA Department",
            "Verification Department",
            "Documentation Department",
            "Content Function",
            "Review Desk",
            "Quality Assurance",
            "Human reviewer on duty",
            "The reviewer on duty",
            "Staff Reviewer",
            "Review Lead",
            "QA Lead",
        ):
            with self.subTest(generic_reviewer=generic_reviewer):
                value = receipt()
                value["humanReviewer"] = generic_reviewer
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any("humanReviewer" in error for error in errors), errors)

        for field in ("checkedBy", "browserCheckedBy"):
            for generic_verifier in (
                "the verifier",
                "verification team",
                "QA team",
                "auditor",
                "operator",
                "admin",
                "review bot",
                "automation team",
            ):
                with self.subTest(field=field, generic_verifier=generic_verifier):
                    value = receipt()
                    value[field] = generic_verifier
                    errors = validate_receipt(value, receipt_path(value))
                    self.assertTrue(any(field in error for error in errors), errors)

        concrete_verifier = receipt()
        concrete_verifier["checkedBy"] = "agent:codex-lss-verifier"
        concrete_verifier["browserCheckedBy"] = "job:fleet-browser-verification"
        self.assertEqual(
            validate_receipt(concrete_verifier, receipt_path(concrete_verifier)), []
        )

        for human_name in (
            "Claude Hopkins",
            "Claude Shannon",
            "Gemini Jones",
            "Qwen Li",
            "José García",
            "李 小龙",
            "Иван Иванов",
            "محمد علي",
            "山田 太郎",
            "김 민수",
            "李小龙",
            "山田太郎",
            "김민수",
            "Δημήτρης Παπαδόπουλος",
            "Łukasz Żółć",
            "M. Patel",
            "J. R. Smith",
        ):
            with self.subTest(human_name=human_name):
                self.assertTrue(_valid_human_identity(human_name))

        unregistered_human = receipt()
        unregistered_human["humanReviewer"] = "Mina Patel"
        errors = validate_receipt(
            unregistered_human, receipt_path(unregistered_human)
        )
        self.assertTrue(
            any("not in fleet-public-human" in error for error in errors), errors
        )

        for role_plus_name in (
            "Reviewer Alice",
            "QA Alice",
            "Human Jane",
            "Reviewed by Alice",
            "Mina Reviewer",
            "Compliance Bob",
            "Audit Alice",
            "External Alice",
            "Independent Alice",
            "Dr Smith",
            "Ms Patel",
        ):
            with self.subTest(role_plus_name=role_plus_name):
                invalid_human = receipt()
                invalid_human["humanReviewer"] = role_plus_name
                errors = validate_receipt(invalid_human, receipt_path(invalid_human))
                self.assertTrue(any("humanReviewer" in error for error in errors), errors)

        for field in ("checkedBy", "browserCheckedBy"):
            for generic_actor in (
                "agent:bot", "agent:agent", "agent:job", "agent:human",
                "agent:reviewer", "agent:model", "agent:gpt", "agent:current",
                "agent:latest", "agent:production", "job:bot", "job:job",
                "job:agent", "job:cron", "job:audit",
            ):
                with self.subTest(field=field, generic_actor=generic_actor):
                    invalid_actor = receipt()
                    invalid_actor[field] = generic_actor
                    errors = validate_receipt(invalid_actor, receipt_path(invalid_actor))
                    self.assertTrue(any(field in error for error in errors), errors)

        for bidi_identity in ("Mina\u202e Patel", "Alice\u2066 Bob"):
            with self.subTest(bidi_identity=bidi_identity):
                value = receipt()
                value["humanReviewer"] = bidi_identity
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any("bidirectional" in error for error in errors), errors)

    def test_public_receipt_cannot_contain_machine_paths_or_emails(self):
        for value_text in (
            "Read /Users/alice/private/output.json",
            "Read /private/var/folders/ab/candidate.json",
            "Read /tmp/fleet/private-client.json",
            "Read ~/Library/Application Support/Claude/secret.json",
            "Read /opt/company/client-alpha/schedules.json",
            "path:/tmp/client-alpha/schedules.json",
            "[/private/var/folders/secret/cache.json]",
            "at:/Users/dennis/project/file.json",
            "x,/home/user/secrets.txt",
            r"\\server\client-alpha\schedules.json",
            "/usr/local/client-alpha/secrets.json",
            "/bin/client-tool/config",
            "/sbin/private/tool",
            "/dev/shm/client/cache",
            "/proc/self/environ",
            "/sys/kernel/private",
            "/workspace/client-alpha/private.json",
            "/boot/grub/config",
            "/media/alice/drive",
            "/nix/store/private",
            "/Network/Servers/private",
            "/snap/private",
            "/storage/emulated/0/private",
            "/sdcard/private",
            "/.ssh/id_ed25519",
            "./etc/passwd",
            "./bin/tool",
            "./dev/null",
            "./proc/self",
            "./run/secrets",
            "./mnt/data",
            "./nix/store/x",
            "./Volumes/Data",
            "./System/Library",
            "/data/data/app/private",
            "/data/user/0/private",
            "%USERPROFILE%\\private",
            "%APPDATA%\\private",
            "$HOME/private",
            "$USERPROFILE/private",
            "$TMPDIR/private",
            "run-../../secret",
            "cache-../private",
            "./private/client",
            "Users/alice/private.json",
            "Library/Application Support/secret.json",
            "/tmp",
            "/Users",
            "/private",
            "/workspace",
            "~/",
            "C:\\",
            r"\\server",
            "Contact alice@example.test for raw output",
        ):
            with self.subTest(value=value_text):
                value = receipt("verification-failed")
                value["failureDetail"] = value_text
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(errors)

        for credential_text in (
            "client_secret=value", "refresh_token=value", "id_token=value",
            "oauth_token=value", "session_token=value", "authorization=value",
            "private_key=value", "signature=value", "sessionid=value",
        ):
            with self.subTest(credential_text=credential_text):
                self.assertIn("credential", _private_string(credential_text))

        safe = receipt("verification-failed")
        safe["failureDetail"] = "The publication candidate failed the public contract."
        self.assertFalse(
            any("machine path" in error for error in validate_receipt(safe, receipt_path(safe)))
        )

    def test_success_receipt_chronology_cannot_run_backwards(self):
        value = receipt()
        value["articleDateModified"] = "2026-09-02T00:00:01Z"
        value["wordpressModifiedAt"] = "2026-09-02T00:00:01Z"
        errors = validate_receipt(value, receipt_path(value))
        self.assertTrue(any("later than checkedAt" in error for error in errors), errors)

    def test_completed_evidence_clocks_cannot_be_in_the_future(self):
        value = receipt()
        for field in (
            "articleDateModified",
            "wordpressModifiedAt",
            "browserCheckedAt",
            "checkedAt",
        ):
            value[field] = "2099-01-01T00:00:00Z"
        errors = validate_receipt(value, receipt_path(value))
        self.assertTrue(any("checkedAt cannot be in the future" in error for error in errors), errors)

    def test_iso_offsets_must_be_real_timezone_offsets(self):
        for invalid_offset in ("+00:60", "+14:01", "+14:99", "+15:00"):
            with self.subTest(offset=invalid_offset):
                value = receipt()
                value["checkedAt"] = "2026-08-31T20:10:00" + invalid_offset
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any("checkedAt must be a real" in error for error in errors), errors)


    def test_browser_attestation_is_external_typed_and_monotonic(self):
        cases = (
            ("browserVisibilityVerified", False, "browserVisibilityVerified=true"),
            ("browserCheckedAt", "not-a-date", "real ISO instant"),
            ("browserCheckedAt", "2026-08-31T20:04:00-05:00", "cannot precede"),
            ("browserCheckedAt", "2026-08-31T20:11:00-05:00", "later than checkedAt"),
            ("browserCheckedBy", "unknown", "actual verifier"),
            ("browserRunReceiptId", "pending", "stable public identifier"),
        )
        for field, bad_value, expected in cases:
            with self.subTest(field=field):
                value = receipt()
                value[field] = bad_value
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_directory_reports_malformed_entries_without_crashing(self):
        with tempfile.TemporaryDirectory() as temp_name:
            directory = Path(temp_name)
            (directory / "broken.json").write_text("[]\n", encoding="utf-8")
            errors = validate_directory(directory)
        self.assertEqual(errors, ["broken.json: receipt must be a JSON object"])

        with tempfile.TemporaryDirectory() as temp_name:
            directory = Path(temp_name)
            (directory / "invalid-utf8.json").write_bytes(b"\xff\xfe")
            errors = validate_directory(directory)
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid-utf8.json: cannot parse JSON", errors[0])

        with tempfile.TemporaryDirectory() as temp_name:
            directory = Path(temp_name)
            nested = '{"x":' + ("[" * 1000) + "0" + ("]" * 1000) + "}"
            (directory / "too-deep.json").write_text(nested, encoding="utf-8")
            errors = validate_directory(directory)
        self.assertEqual(len(errors), 1)
        self.assertIn("too-deep.json: cannot parse JSON", errors[0])

        with tempfile.TemporaryDirectory() as temp_name:
            directory = Path(temp_name)
            (directory / "too-large.json").write_bytes(b" " * (1024 * 1024 + 1))
            errors = validate_directory(directory)
        self.assertEqual(len(errors), 1)
        self.assertIn("byte ledger limit", errors[0])

    def test_directory_rejects_duplicate_json_members(self):
        with tempfile.TemporaryDirectory() as temp_name:
            directory = Path(temp_name)
            (directory / "duplicate.json").write_text(
                '{"schemaVersion":999,"schemaVersion":1}\n',
                encoding="utf-8",
            )
            errors = validate_directory(directory)
        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate JSON member 'schemaVersion'", errors[0])

    def test_ledger_json_and_schemas_must_be_real_bounded_files(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            outside = root / "outside"
            outside.mkdir()
            ledger = root / "ledger"
            ledger.mkdir()
            value = receipt("verification-failed")
            outside_receipt = outside / "receipt.json"
            outside_receipt.write_text(json.dumps(value), encoding="utf-8")
            (ledger / f"{value['receiptId']}.json").symlink_to(outside_receipt)
            errors = validate_directory(ledger)
            self.assertEqual(len(errors), 1)
            self.assertIn("must not be a symlink", errors[0])

            outside_schema = outside / "schema.json"
            outside_schema.write_text("{}\n", encoding="utf-8")
            receipt_schema_dir = root / "receipt-schema"
            receipt_schema_dir.mkdir()
            (receipt_schema_dir / "receipt.schema.json").symlink_to(outside_schema)
            self.assertTrue(
                any(
                    "symlink" in error
                    for error in _schema_contract_errors(receipt_schema_dir)
                )
            )
            source_schema_dir = root / "source-schema"
            source_schema_dir.mkdir()
            (source_schema_dir / "source.schema.json").symlink_to(outside_schema)
            self.assertTrue(
                any(
                    "symlink" in error
                    for error in _source_schema_contract_errors(source_schema_dir)
                )
            )

            source_dir = root / "source-ledger"
            source_dir.mkdir()
            source_link = source_dir / (("a" * 40) + ".json")
            source_link.symlink_to(outside_receipt)
            with self.assertRaisesRegex(OSError, "symlink"):
                _read_bounded_regular_bytes(source_link, source_dir)

    def test_strict_ledger_namespace_rejects_unvalidated_paths(self):
        with tempfile.TemporaryDirectory() as temp_name:
            ledger = Path(temp_name) / "agent-fleet"
            shutil.copytree(RECEIPTS_DIR, ledger)
            self.assertEqual(_ledger_namespace_errors(ledger), [])

            archive = ledger / "sources" / "archive"
            archive.mkdir()
            (archive / "leak.json").write_text("{}\n", encoding="utf-8")
            (ledger / "sources" / "leak.txt").write_text(
                "unvalidated\n", encoding="utf-8"
            )
            (ledger / "notes.txt").write_text("unvalidated\n", encoding="utf-8")
            errors = _ledger_namespace_errors(ledger)
            self.assertTrue(any("sources/archive" in error for error in errors), errors)
            self.assertTrue(any("sources/leak.txt" in error for error in errors), errors)
            self.assertTrue(any("notes.txt" in error for error in errors), errors)

    def test_schema_contract_checks_fail_closed_on_wrong_json_shapes(self):
        receipt_shapes = (
            {"required": None},
            {
                "required": [],
                "properties": {},
                "additionalProperties": False,
                "allOf": [1],
            },
        )
        for schema in receipt_shapes:
            with self.subTest(receipt_schema=schema), tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                (directory / "receipt.schema.json").write_text(
                    json.dumps(schema), encoding="utf-8"
                )
                self.assertTrue(_schema_contract_errors(directory))

        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            (directory / "source.schema.json").write_text(
                json.dumps({"required": None}), encoding="utf-8"
            )
            self.assertTrue(_source_schema_contract_errors(directory))

    def test_full_machine_schema_contract_cannot_drift_from_validator(self):
        receipt_schema_path = RECEIPTS_DIR / "receipt.schema.json"
        receipt_schema = json.loads(receipt_schema_path.read_text(encoding="utf-8"))
        for field, replacement in (
            ("verificationHash", {"type": "number"}),
            ("browserVisibilityVerified", {"type": "string"}),
        ):
            with self.subTest(receipt_field=field), tempfile.TemporaryDirectory() as name:
                directory = Path(name)
                changed = copy.deepcopy(receipt_schema)
                changed["properties"][field] = replacement
                (directory / "receipt.schema.json").write_text(
                    json.dumps(changed), encoding="utf-8"
                )
                errors = _schema_contract_errors(directory)
                self.assertTrue(any("full canonical" in error for error in errors), errors)

        source_schema_path = SOURCES_DIR / "source.schema.json"
        source_schema = json.loads(source_schema_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            source_schema["properties"]["sourceRevision"] = {"type": "number"}
            (directory / "source.schema.json").write_text(
                json.dumps(source_schema), encoding="utf-8"
            )
            errors = _source_schema_contract_errors(directory)
            self.assertTrue(any("full canonical" in error for error in errors), errors)

    def test_validator_does_not_mutate_the_shared_fixture(self):
        original = verified_receipt()
        working = copy.deepcopy(original)
        validate_receipt(working, receipt_path(working))
        self.assertEqual(working, original)


class AgentFleetReceiptWorkflowTests(unittest.TestCase):
    def test_ci_validates_schema_and_enforces_append_only_receipts(self):
        workflow = (REPOSITORY / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("python3 scripts/validate_agent_fleet_receipts.py", workflow)
        self.assertIn('${{ github.event.pull_request.base.sha }}', workflow)
        self.assertIn('${{ github.event.before }}', workflow)
        self.assertEqual(workflow.count("--base-ref"), 2)

    def test_append_only_check_catches_rename_out_of_the_receipt_ledger(self):
        for destination in ("fleet-page-a.txt", "examples/fleet-page-a.json"):
            with self.subTest(destination=destination), tempfile.TemporaryDirectory() as temp_name:
                root = Path(temp_name)
                receipt_directory = root / "receipts" / "agent-fleet"
                receipt_directory.mkdir(parents=True)
                original = receipt_directory / "fleet-page-a.json"
                original.write_text('{"immutable":true}\n', encoding="utf-8")
                for command in (
                    ("git", "init", "-q"),
                    ("git", "config", "user.email", "test@example.com"),
                    ("git", "config", "user.name", "Test Reviewer"),
                    ("git", "add", "."),
                    ("git", "commit", "-qm", "add receipt"),
                ):
                    subprocess.run(command, cwd=root, check=True)
                destination_path = receipt_directory / destination
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                original.rename(destination_path)

                errors = append_only_errors("HEAD", root)

                self.assertEqual(len(errors), 1)
                self.assertIn("receipts/agent-fleet/fleet-page-a.json", errors[0])

    def test_append_only_check_catches_tamper_then_restore_commit(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            ledger = root / "receipts" / "agent-fleet"
            ledger.mkdir(parents=True)
            immutable = ledger / ("fleet-page-" + ("a" * 20) + ".json")
            original = b'{"immutable":true}\n'
            immutable.write_bytes(original)
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "test@example.com"),
                ("git", "config", "user.name", "Test Reviewer"),
                ("git", "add", "."),
                ("git", "commit", "-qm", "add receipt"),
            ):
                subprocess.run(command, cwd=root, check=True)
            base = subprocess.run(
                ("git", "rev-parse", "HEAD"), cwd=root, check=True,
                text=True, capture_output=True,
            ).stdout.strip()
            immutable.write_text('{"immutable":false}\n', encoding="utf-8")
            subprocess.run(("git", "commit", "-qam", "tamper"), cwd=root, check=True)
            immutable.write_bytes(original)
            subprocess.run(("git", "commit", "-qam", "restore"), cwd=root, check=True)

            errors = append_only_errors(base, root)

            self.assertTrue(any("intermediate commit" in error for error in errors), errors)

    def test_base_ref_cannot_be_interpreted_as_a_git_option(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "test@example.com"),
                ("git", "config", "user.name", "Test Reviewer"),
                ("git", "commit", "--allow-empty", "-qm", "baseline"),
            ):
                subprocess.run(command, cwd=root, check=True)
            output = root / "unexpected-output"
            errors = append_only_errors(f"--output={output}", root)
            self.assertEqual(len(errors), 1)
            self.assertIn("non-option", errors[0])
            self.assertFalse(output.exists())

    def test_publication_receipt_source_must_preexist_in_base_ref(self):
        for status in ("verified", "verification-failed"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp_name:
                root = Path(temp_name)
                receipt_directory = root / "receipts" / "agent-fleet"
                source_directory = receipt_directory / "sources"
                source_directory.mkdir(parents=True)
                (receipt_directory / "README.md").write_text(
                    "fixture ledger\n", encoding="utf-8"
                )
                for command in (
                    ("git", "init", "-q"),
                    ("git", "config", "user.email", "test@example.com"),
                    ("git", "config", "user.name", "Test Reviewer"),
                    ("git", "add", "."),
                    ("git", "commit", "-qm", "ledger baseline"),
                ):
                    subprocess.run(command, cwd=root, check=True)

                value = receipt(status)
                (source_directory / GOLDEN_SOURCE.name).write_bytes(
                    GOLDEN_SOURCE.read_bytes()
                )
                (receipt_directory / f"{value['receiptId']}.json").write_text(
                    json.dumps(value, indent=2) + "\n", encoding="utf-8"
                )
                subprocess.run(("git", "add", "."), cwd=root, check=True)
                errors = append_only_errors("HEAD", root)
                self.assertTrue(
                    any("must already exist in base ref" in error for error in errors),
                    errors,
                )

        for private_label in (
            "Cron: 0 0 * * *",
            "Schedule: every 5 minutes",
            "Private prompt: email the client",
            "Job ID: client-alpha-daily",
            "Task ID: client-alpha",
            "Client: Acme Roofing",
            "Customer: Example Dental",
            "Registry path: internal/registry.json",
            "API key: abcdefghijklmnop",
            "private_prompt: hidden",
            "client-id: abc",
            "customer_id: abc",
            "job-id: abc",
            "task_id: abc",
            "registry-path: private/registry.json",
            "api_key: abcdefghijklmnop",
            "access_token: abcdefghijklmnop",
            "auth-token: abcdefghijklmnop",
            "session_token: abcdefghijklmnop",
            "client_secret: abcdefghijklmnop",
            "private-job: abc",
            "machine_path: /tmp/private.json",
            "client‐id: abc",
            "api—key: abcdefghijklmnop",
            "client−id: abc",
            "clientid: abc",
            "registrypath: private/registry.json",
            "api\u200bkey: abcdefghijklmnop",
        ):
            with self.subTest(private_label=private_label):
                value = receipt()
                value["checkedBy"] = private_label
                errors = validate_receipt(value, receipt_path(value))
                self.assertTrue(
                    any(
                        "sensitive private-data label" in error
                        or "private machine path" in error
                        or "control characters" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_base_ref_source_companion_must_be_regular_valid_json(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            receipt_directory = root / "receipts" / "agent-fleet"
            source_directory = receipt_directory / "sources"
            source_directory.mkdir(parents=True)
            (receipt_directory / "README.md").write_text(
                "fixture ledger\n", encoding="utf-8"
            )
            source_link = source_directory / GOLDEN_SOURCE.name
            source_link.symlink_to("../README.md")
            for command in (
                ("git", "init", "-q"),
                ("git", "config", "user.email", "test@example.com"),
                ("git", "config", "user.name", "Test Reviewer"),
                ("git", "add", "."),
                ("git", "commit", "-qm", "invalid source baseline"),
            ):
                subprocess.run(command, cwd=root, check=True)
            value = receipt()
            (receipt_directory / f"{value['receiptId']}.json").write_text(
                json.dumps(value, indent=2) + "\n", encoding="utf-8"
            )
            subprocess.run(("git", "add", "."), cwd=root, check=True)
            errors = append_only_errors("HEAD", root)
            self.assertTrue(any("regular git blob" in error for error in errors), errors)

    def test_added_receipt_is_duplicate_aware_regular_json_before_source_lookup(self):
        for kind in ("malformed", "duplicate", "symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp_name:
                root = Path(temp_name)
                receipt_directory = root / "receipts" / "agent-fleet"
                receipt_directory.mkdir(parents=True)
                baseline = receipt_directory / "README.md"
                baseline.write_text("fixture ledger\n", encoding="utf-8")
                for command in (
                    ("git", "init", "-q"),
                    ("git", "config", "user.email", "test@example.com"),
                    ("git", "config", "user.name", "Test Reviewer"),
                    ("git", "add", "."),
                    ("git", "commit", "-qm", "ledger baseline"),
                ):
                    subprocess.run(command, cwd=root, check=True)
                added = receipt_directory / ("fleet-page-" + ("a" * 20) + ".json")
                if kind == "malformed":
                    added.write_text("{\n", encoding="utf-8")
                elif kind == "duplicate":
                    added.write_text(
                        '{"sourceRevision":"' + ("a" * 40) + '",'
                        '"sourceRevision":"' + ("b" * 40) + '"}\n',
                        encoding="utf-8",
                    )
                else:
                    added.symlink_to("README.md")
                subprocess.run(("git", "add", "."), cwd=root, check=True)
                errors = append_only_errors("HEAD", root)
                self.assertTrue(any("cannot parse safely" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
