# Legal AI Assistant

Contract analysis toolkit for clause extraction, risk scoring, executive summaries, contract comparison, and REST/CLI reporting.

## Supported Inputs

PDF, DOCX, plain text, HTML, and pasted text saved as a file.

## Supported Contracts

NDA, SaaS agreement, employment agreement, statement of work, MSA, lease, IP assignment, and vendor agreement.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m cli.main analyze tests/fixtures/sample_contracts/sample_nda.txt --type nda --jurisdiction "New York" --output markdown
```

The default path uses deterministic heuristic extraction so the project works without an LLM key. Add `ANTHROPIC_API_KEY` in `.env` when you connect a production LLM client.

## API

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@tests/fixtures/sample_contracts/sample_nda.txt" \
  -F "contract_type=nda" \
  -F "depth=deep" \
  -F "jurisdiction=New York"
```

Streaming endpoint:

```bash
curl -N -X POST http://localhost:8000/analyze/stream \
  -H "Accept: text/event-stream" \
  -F "file=@tests/fixtures/sample_contracts/sample_nda.txt"
```

## CLI

```bash
python -m cli.main analyze contract.pdf --depth deep --output json
python -m cli.main analyze nda.docx --type nda --jurisdiction "New York"
python -m cli.main compare v1.pdf v2.pdf --show-diff
python -m cli.main analyze contract.pdf --stream --output markdown
```

## Tests

```bash
pytest tests -v
```

## Architecture

Input parsing flows through token-aware chunking, heuristic clause detection, extraction, Pydantic validation, holistic risk analysis, summary generation, and output formatting. The `SQLiteLLMCache` stores MD5-hashed prompt/chunk pairs for repeat analysis.

