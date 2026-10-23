"""Structured output and deterministic checks for AI Test Architect."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TestCase(StrictRecord):
    test_id: Text
    title: Text
    requirement_ids: list[Text] = Field(min_length=1)
    test_type: Literal["positive", "negative", "boundary", "security", "integration"]
    preconditions: list[Text]
    steps: list[Text] = Field(min_length=1)
    expected_results: list[Text] = Field(min_length=1)
    assumptions: list[Text]
    source_refs: list[Text] = Field(min_length=1)


class ClarificationQuestion(StrictRecord):
    requirement_id: Text
    question: Text
    blocks_test_design: bool
    source_refs: list[Text] = Field(min_length=1)


class ArchitectPlan(StrictRecord):
    agent_name: Literal["AI Test Architect"]
    issue_key: Text
    summary: Text
    test_cases: list[TestCase] = Field(min_length=1)
    clarification_questions: list[ClarificationQuestion]


def source_ref(item: dict) -> str:
    source = item["source"]
    return f"{source['source_type']}:{source['source_id']}:{source['locator']}"


def prepare_model_context(context: dict) -> dict:
    """Check the normalized fixture contract and expose canonical source refs."""
    if context.get("schema_version") != "0.1" or context.get("source_mode") != "synthetic_fixture":
        raise ValueError("Only schema 0.1 synthetic context is accepted in this exercise")
    requirements = context.get("requirements")
    sections = context.get("context_sections")
    if not isinstance(requirements, list) or not requirements or not isinstance(sections, list) or not sections:
        raise ValueError("Requirements and supporting context must be non-empty lists")
    issue_key = context["issue_key"]
    if not isinstance(issue_key, str) or not issue_key.strip():
        raise ValueError("A non-empty issue key is required")
    ids = [item["requirement_id"] for item in requirements]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate requirement IDs in input")
    prepared = []
    all_refs = []
    for role, items in (("requirement", requirements), ("supporting_context", sections)):
        for item in items:
            ref = source_ref(item)
            text = item["text"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Source text must not be empty")
            all_refs.append(ref)
            prepared.append({
                "role": role,
                "id": item.get("requirement_id", item.get("section_id")),
                "text": text,
                "source_ref": ref,
                "provenance": item["source"],
            })
    if len(all_refs) != len(set(all_refs)):
        raise ValueError("Duplicate source references in input")
    return {"issue_key": issue_key, "title": context["title"], "sources": prepared}


def validate_traceability(plan: ArchitectPlan, context: dict) -> dict:
    """Validate reference integrity, not the semantic correctness of test designs."""
    prepare_model_context(context)
    if plan.issue_key != context["issue_key"]:
        raise ValueError("Output issue key does not match input")
    req_refs = {item["requirement_id"]: source_ref(item) for item in context["requirements"]}
    allowed_refs = set(req_refs.values()) | {source_ref(item) for item in context["context_sections"]}
    test_ids = [test.test_id for test in plan.test_cases]
    if len(test_ids) != len(set(test_ids)):
        raise ValueError("Duplicate test IDs")
    referenced = set()
    questions = set()
    for test in plan.test_cases:
        if not set(test.requirement_ids) <= req_refs.keys():
            raise ValueError("Unknown requirement ID in test")
        if not set(test.source_refs) <= allowed_refs:
            raise ValueError("Unknown source reference in test")
        if not {req_refs[r] for r in test.requirement_ids} <= set(test.source_refs):
            raise ValueError("Test is missing a referenced requirement's source")
        referenced.update(test.requirement_ids)
    for question in plan.clarification_questions:
        if question.requirement_id not in req_refs:
            raise ValueError("Unknown requirement ID in clarification")
        if not set(question.source_refs) <= allowed_refs:
            raise ValueError("Unknown source reference in clarification")
        if req_refs[question.requirement_id] not in question.source_refs:
            raise ValueError("Clarification is missing its requirement source")
        questions.add(question.requirement_id)
    return {
        "schema_and_references_valid": True,
        "total_requirements": len(req_refs),
        "requirements_referenced_by_tests": sorted(referenced),
        "requirements_with_questions": sorted(questions),
        "unaddressed_requirement_ids": sorted(req_refs.keys() - referenced - questions),
        "semantic_coverage_verified": False,
        "human_review_required": True,
    }
