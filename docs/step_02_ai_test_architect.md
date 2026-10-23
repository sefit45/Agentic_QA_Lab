# Step 02 AI Test Architect

This is one LLM-backed planning component, not the finished autonomous system.
It makes one bounded Responses API call with structured output. No tools,
SQL, live Jira/Confluence, RAG or telecom execution are implemented yet.

Prerequisites: completed Step 01 and generated outputs/source_context.json;
an active virtual environment and OPENAI_API_KEY in this terminal.
User-verified versions: openai 3.37.0 and pydantic 2.14.1 on Python 3.14.4.
No additional package installation is required for the existing environment.

Extract only the four new files into your project root. Do not overwrite
existing files without comparing them. The archive does not modify Step 01.

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python src\agentic_qa\agents\ai_test_architect.py
```

Expected offline test total: 23. Tests use fake model responses, never API calls.
The second command sends your SYNTHETIC source context to OpenAI and is billed.
One request only, no automatic retries, timeout 90 seconds, max output 8000 tokens.
Do not repeat if it errors; inspect the sanitized error first.

The report is outputs/ai_test_architect_report.json. It contains a run ID,
model, prompt version, request duration, usage if returned, integrity checks
and the proposed tests/questions. It is NOT a test execution result.
Test and question counts vary; review the actual output, not a promised count.
After a failed run an older report may remain: always inspect created_at/run_id.

## File responsibilities

- contracts.py: Pydantic schemas and deterministic source-reference checks.
- agents/ai_test_architect.py: instructions, bounded model call, report and CLI.
- tests/test_ai_test_architect.py: offline schema/reference/request checks.
- this file: commands and limitations.

## Read the first live report together

Check activation, usage boundaries, duplicated usage, bill correctness, document
availability, SAP and notification. REQ-009 must surface an undefined deadline.
Do not accept invented Amdocs SQL, tariff rules or timeout values.
Review referenced Confluence sections when expected results depend on them.
Valid IDs and schema do not prove semantic correctness or actual test coverage.
Missing tests, weak assertions and unsupported claims need a separate review.

Prompt instructions are not a complete security boundary. No external execution
tools are exposed in this step. Report files contain source-derived text and
belong under the ignored outputs/ directory. Keep API keys out of all files.

The model response uses structured outputs through responses.parse and a
Pydantic text_format. Official guide:
https://developers.openai.com/api/docs/guides/structured-outputs
