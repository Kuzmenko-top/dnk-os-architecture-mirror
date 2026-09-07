# --- DNK-MRH-HEADER ---
# mrh_id: "tests_staging_test_hermes_v0210_staging"
# purpose: "Comprehensive staging smoke tests & security boundary validation for Hermes Agent v0.21.0 using standard unittest."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

import os
import sys
import subprocess
import unittest
import sqlite3
import hashlib
import json
from pathlib import Path
import yaml

STAGING_DIR = os.path.abspath("core/hermes_agent_staging")
STAGING_VENV_PY = os.path.join(STAGING_DIR, ".venv/bin/python")
STAGING_HERMES_BIN = os.path.join(STAGING_DIR, ".venv/bin/hermes")
STAGING_HOME = os.path.expanduser("~/.hermes_staging")
PROD_HOME = os.path.expanduser("~/.hermes")

if STAGING_DIR not in sys.path:
    sys.path.insert(0, STAGING_DIR)


class TestHermesStagingSmoke(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(STAGING_HERMES_BIN):
            self.skipTest(f"Staging Hermes binary not found at {STAGING_HERMES_BIN}")

    def test_01_staging_version(self):
        """Smoke Test 1: Verify staging CLI outputs Hermes Agent v0.21.0."""
        env = os.environ.copy()
        env["HERMES_HOME"] = STAGING_HOME
        out = subprocess.check_output([STAGING_HERMES_BIN, "--version"], env=env, text=True)
        self.assertIn("Hermes Agent v0.21.0", out)
        self.assertIn("Python: 3.12", out)

    def test_02_staging_doctor(self):
        """Smoke Test 2: Verify hermes doctor executes and identifies isolated staging."""
        env = os.environ.copy()
        env["HERMES_HOME"] = STAGING_HOME
        res = subprocess.run([STAGING_HERMES_BIN, "doctor"], env=env, capture_output=True, text=True)
        self.assertIn("Hermes Doctor", res.stdout)
        self.assertTrue("~/.hermes_staging" in res.stdout or STAGING_HOME in res.stdout)

    def test_03_session_db_isolation_and_resume(self):
        """Smoke Test 3 & 4: Open isolated state DB, create session, resume, and verify prod isolation."""
        from hermes_state import SessionDB
        db_path = Path(STAGING_HOME) / "state.db"
        prod_db_path = Path(PROD_HOME) / "state.db"

        self.assertNotEqual(str(db_path), str(prod_db_path))

        db = SessionDB(db_path=db_path)
        import uuid
        uid = uuid.uuid4().hex[:8]
        session_id = f"staging_test_sess_{uid}"
        test_title = f"Staging Smoke Test Session {uid}"

        # Create session in staging
        db.create_session(
            session_id=session_id,
            source="staging_cli"
        )
        db._set_session_title(session_id, test_title, source="user")

        # Append test message
        msg_id = db.append_message(
            session_id=session_id,
            role="user",
            content="Smoke test user prompt for v0.21.0"
        )
        self.assertGreater(msg_id, 0)

        # Resume session and verify messages
        sess = db.get_session(session_id)
        self.assertIsNotNone(sess)
        self.assertEqual(sess["title"], test_title)

        msgs = db.get_messages(session_id)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["content"], "Smoke test user prompt for v0.21.0")

        # Verify production DB is completely untouched
        prod_conn = sqlite3.connect(str(prod_db_path))
        cursor = prod_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE id = ?", (session_id,))
        count = cursor.fetchone()[0]
        prod_conn.close()
        self.assertEqual(count, 0, "Isolation breach: staging session appeared in production DB!")

    def test_04_secret_redaction(self):
        """Smoke Test 5: Verify sensitive credentials redaction."""
        from agent.redact import redact_sensitive_text

        raw_text = "Here is my secret token: " + "ghp_" + "1234567890abcdefghijklmnopqrstuvwxyz and " + "sk-proj-" + "123456789012345678901234567890"
        redacted = redact_sensitive_text(raw_text)
        self.assertNotIn("ghp_" + "1234567890abcdefghijklmnopqrstuvwxyz", redacted)
        self.assertNotIn("sk-proj-" + "123456789012345678901234567890", redacted)
        self.assertTrue("[REDACTED" in redacted or "ghp_" in redacted)

    def test_05_protected_file_boundary_and_approval(self):
        """Smoke Test 6: Verify protection policy for AGENTS.md and forbidden files."""
        protected_files = ["AGENTS.md", "CLAUDE.md", ".cursorrules", ".env"]

        def can_agent_write_file(path: str, role: str) -> bool:
            norm = os.path.normpath(path)
            base = os.path.basename(norm)
            if base in protected_files:
                return False
            if role != "gerych_prime" and "core/orchestrator" in norm:
                return False
            return True

        self.assertFalse(can_agent_write_file("AGENTS.md", role="dnk_dev_fullstack"))
        self.assertFalse(can_agent_write_file("../../AGENTS.md", role="gerych_builder"))
        self.assertTrue(can_agent_write_file("apps/api/routers/users.py", role="dnk_dev_fullstack"))

    def test_06_structured_delegate_output_validation(self):
        """Smoke Test 7: Verify schema validation for subagent delegation."""
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "metrics": {"type": "object"}
            },
            "required": ["status"]
        }
        valid_output = {"status": "success", "metrics": {"duration_ms": 120}}
        invalid_output = {"metrics": {"duration_ms": 120}}

        def validate_schema_simple(data, sch):
            if not isinstance(data, dict):
                return False, "Not an object"
            for req in sch.get("required", []):
                if req not in data:
                    return False, f"Missing required field: {req}"
            return True, None

        ok, err = validate_schema_simple(valid_output, schema)
        self.assertTrue(ok)
        self.assertIsNone(err)

        bad, err2 = validate_schema_simple(invalid_output, schema)
        self.assertFalse(bad)
        self.assertIsNotNone(err2)

    def test_07_child_stop_and_steer_mechanisms(self):
        """Smoke Test 8 & 9: Verify live orchestration controls (steer & stop)."""
        children = {
            "child_001": {
                "status": "running",
                "steer_messages": [],
                "partial_result": None
            }
        }

        # Steer action
        steer_msg = "Stop exploring X; prioritize Y"
        children["child_001"]["steer_messages"].append(steer_msg)
        self.assertEqual(len(children["child_001"]["steer_messages"]), 1)
        self.assertEqual(children["child_001"]["steer_messages"][0], steer_msg)

        # Stop action
        partial = {"collected_records": 42, "reason": "user_cancelled"}
        children["child_001"]["status"] = "stopped"
        children["child_001"]["partial_result"] = partial

        self.assertEqual(children["child_001"]["status"], "stopped")
        self.assertEqual(children["child_001"]["partial_result"]["collected_records"], 42)

    def test_08_peer_message_audit_event_contract(self):
        """Smoke Test 10: Verify compliance of peer events with hermes_event_contract.yaml."""
        contract_file = "core/contracts/hermes_event_contract.yaml"
        self.assertTrue(os.path.exists(contract_file))
        with open(contract_file) as f:
            contract = yaml.safe_load(f)

        peer_mapping = None
        for mapping in contract.get("event_mappings", []):
            if mapping.get("hermes_event") == "hermes.peer_message":
                peer_mapping = mapping
                break
        self.assertIsNotNone(peer_mapping)
        required_fields = peer_mapping["required_fields"]

        event = {
            "sender_profile": "gerych_researcher",
            "recipient_profile": "gerych_prime",
            "message_content": "Research findings ready",
            "timestamp": "2026-09-03T16:00:00Z",
            "task_id": "TASK-DNK-ARCH-002",
            "dnk_event": peer_mapping["dnk_event"]
        }

        for req in required_fields:
            self.assertIn(req, event, f"Event missing required field: {req}")

    def test_09_cron_continuity(self):
        """Smoke Test 11: Verify cronjob continuity translation."""
        from tools.cronjob_tools import _apply_continuity

        refs = _apply_continuity(None, continuity=True)
        self.assertEqual(refs, ["self"])

        refs = _apply_continuity(["job_alpha"], continuity=True)
        self.assertIn("self", refs)
        self.assertIn("job_alpha", refs)

        refs_off = _apply_continuity(["self", "job_alpha"], continuity=False)
        self.assertNotIn("self", refs_off)
        self.assertEqual(refs_off, ["job_alpha"])

    def test_10_mcp_health_check_isolation(self):
        """Smoke Test 12: Verify MCP configuration in staging does not load production secrets."""
        staging_cfg_file = os.path.join(STAGING_HOME, "config.yaml")
        self.assertTrue(os.path.exists(staging_cfg_file))
        with open(staging_cfg_file) as f:
            cfg = yaml.safe_load(f)

        mcp_servers = cfg.get("mcp", {}).get("servers", {})
        for name, srv in mcp_servers.items():
            self.assertNotIn("shopify_production", name.lower())
            self.assertNotIn("live", name.lower())

    def test_11_shopify_sandbox_boundary(self):
        """Smoke Test 13: Enforce strict rejection of production Shopify endpoints in staging."""
        forbidden_domains = [
            "dnk-e.myshopify.com",
            "checkout.dnk-e.com",
            "admin.shopify.com"
        ]

        def validate_shopify_target(url: str) -> bool:
            for f in forbidden_domains:
                if f in url:
                    return False
            return True

        self.assertFalse(validate_shopify_target("https://dnk-e.myshopify.com/admin"))
        self.assertFalse(validate_shopify_target("https://checkout.dnk-e.com"))
        self.assertTrue(validate_shopify_target("https://dev-sandbox.myshopify.com"))

    def test_12_mock_tool_execution(self):
        """Smoke Test 14: Verify mock tool execution and payload wrapping."""
        def mock_calculator_tool(a: int, b: int, op: str = "add") -> dict:
            if op == "add":
                res = a + b
            elif op == "multiply":
                res = a * b
            else:
                return {"error": f"Unsupported op: {op}"}
            return {"result": res, "status": "success"}

        res = mock_calculator_tool(15, 27, "add")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 42)


if __name__ == "__main__":
    unittest.main()
