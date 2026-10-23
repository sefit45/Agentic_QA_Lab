"""Offline validation and orchestration contract tests. No API calls."""

import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pydantic import ValidationError
from agentic_qa.contracts import ArchitectPlan, prepare_model_context, source_ref, validate_traceability
from agentic_qa.agents.ai_test_architect import generate_plan
from agentic_qa.source_loader import load_object, normalize_sources


class ArchitectTests(unittest.TestCase):
    def setUp(self):
        self.context = normalize_sources(
            load_object(ROOT / "data/fixtures/jira_issue.json"),
            load_object(ROOT / "data/fixtures/confluence_page.json"),
        )
        self.ref = source_ref(self.context["requirements"][0])
        self.data = {
            "agent_name": "AI Test Architect", "issue_key": "TELCO-101", "summary": "Test proposal",
            "test_cases": [{"test_id": "TC-001", "title": "Authorized activation",
                "requirement_ids": ["REQ-001"], "test_type": "positive",
                "preconditions": ["Authorized agent; eligible offer"],
                "steps": ["Submit the activation order"],
                "expected_results": ["Order references are captured"],
                "assumptions": [], "source_refs": [self.ref]}],
            "clarification_questions": [],
        }

    def check_plan(self):
        return validate_traceability(ArchitectPlan.model_validate(self.data), self.context)

    def test_valid_plan_requires_human_review_and_reports_gaps(self):
        checks = self.check_plan()
        self.assertTrue(checks["human_review_required"])
        self.assertFalse(checks["semantic_coverage_verified"])
        self.assertEqual(len(checks["unaddressed_requirement_ids"]), 9)

    def test_empty_steps_rejected(self):
        self.data["test_cases"][0]["steps"] = []
        with self.assertRaises(ValidationError):
            self.check_plan()

    def test_extra_output_fields_rejected(self):
        self.data["executed"] = True
        with self.assertRaises(ValidationError):
            self.check_plan()

    def test_unknown_requirement_rejected(self):
        self.data["test_cases"][0]["requirement_ids"] = ["REQ-999"]
        with self.assertRaisesRegex(ValueError, "Unknown requirement"):
            self.check_plan()

    def test_fabricated_source_rejected(self):
        self.data["test_cases"][0]["source_refs"] = ["jira:FAKE:description"]
        with self.assertRaisesRegex(ValueError, "Unknown source"):
            self.check_plan()

    def test_requirement_source_must_match(self):
        self.data["test_cases"][0]["source_refs"] = [source_ref(self.context["context_sections"][0])]
        with self.assertRaisesRegex(ValueError, "missing a referenced"):
            self.check_plan()

    def test_duplicate_test_ids_rejected(self):
        self.data["test_cases"].append(copy.deepcopy(self.data["test_cases"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate test"):
            self.check_plan()

    def test_wrong_issue_rejected(self):
        self.data["issue_key"] = "TELCO-OTHER"
        with self.assertRaisesRegex(ValueError, "issue key"):
            self.check_plan()

    def test_clarification_is_not_test_coverage(self):
        req = self.context["requirements"][8]
        self.data["clarification_questions"] = [{
            "requirement_id": "REQ-009", "question": "What is the propagation deadline?",
            "blocks_test_design": True, "source_refs": [source_ref(req)]}]
        checks = self.check_plan()
        self.assertNotIn("REQ-009", checks["requirements_referenced_by_tests"])
        self.assertIn("REQ-009", checks["requirements_with_questions"])

    def test_unknown_clarification_requirement_rejected(self):
        self.data["clarification_questions"] = [{"requirement_id": "REQ-999",
            "question": "Missing details?", "blocks_test_design": True, "source_refs": [self.ref]}]
        with self.assertRaisesRegex(ValueError, "Unknown requirement"):
            self.check_plan()

    def test_fixture_mode_required(self):
        self.context["source_mode"] = "live"
        with self.assertRaisesRegex(ValueError, "synthetic"):
            prepare_model_context(self.context)

    def test_model_request_contract_and_report(self):
        captured = {}
        plan = ArchitectPlan.model_validate(self.data)

        def parse(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(status="completed", output_parsed=plan, usage=None, id="offline-test")

        client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
        report = generate_plan(self.context, client, "gpt-5.4-mini")
        self.assertEqual(captured["text_format"], ArchitectPlan)
        self.assertFalse(captured["store"])
        self.assertEqual(captured["max_output_tokens"], 8000)
        self.assertEqual(report["stage"], "test_design_proposal_only")

    def test_incomplete_model_response_rejected(self):
        response = SimpleNamespace(status="incomplete", output_parsed=None)
        client = SimpleNamespace(responses=SimpleNamespace(parse=lambda **kwargs: response))
        with self.assertRaisesRegex(ValueError, "incomplete or refused"):
            generate_plan(self.context, client, "gpt-5.4-mini")


if __name__ == "__main__":
    unittest.main()
