# Plan 1: Foundation + Hero Loop — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation (repo, schemas, KB seeding, LLM clients) plus the hero gap→KB loop end-to-end — ticket arrives in Google Sheet, wiki-traversal agent reads KB and either drafts a reply to Gmail Drafts or flags a gap, gap routes to Slack for human resolution, auto-drafted KB entry is approved via Slack, n8n auto-commits to Git.

**Architecture:** Python FastAPI service hosts the agent + KB write logic; n8n orchestrates I/O (Google Sheet trigger, Gmail Drafts, Slack interactive messages, GitHub auto-commit) and calls the Python service via HTTP. KB is Markdown in Git with Pydantic-validated frontmatter. Wiki traversal at MVP scale = single LLM call with full KB in context (~50 files, well under context limit); the "traversal" pattern shows up as the agent's cited file paths in structured output.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2, httpx, pytest, pdfplumber, python-docx, n8n (Docker), Minimax 2.7 + Kimi 2.6 (OpenAI-compatible APIs).

---

## File Structure Overview

```
e27-revenue-rocket/
├── pyproject.toml
├── uv.lock
├── .env.example                                ← env var template
├── .gitignore
├── README.md
├── docker-compose.yml                          ← n8n container
│
├── intel_engine/                               ← Python service
│   ├── __init__.py
│   ├── api.py                                  ← FastAPI app
│   ├── settings.py                             ← env-driven config
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── event.py                            ← CommonEvent schema
│   │   ├── kb.py                               ← KBEntry, frontmatter
│   │   ├── traversal.py                        ← TraversalResult
│   │   └── gap.py                              ← Gap, GapResolution
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py                           ← OpenAI-compatible client
│   │   └── prompts.py                          ← prompt loader from kb/_workflows/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── traversal.py                        ← wiki-traversal agent
│   │   └── kb_drafter.py                       ← auto-draft KB entry agent
│   ├── kb/
│   │   ├── __init__.py
│   │   ├── reader.py                           ← load full KB into memory
│   │   ├── writer.py                           ← write entry, commit via git
│   │   └── index.py                            ← regenerate kb/index.md
│   └── gap/
│       ├── __init__.py
│       └── logger.py                           ← gap-log file writer
│
├── scripts/                                    ← one-shot KB seeding
│   ├── __init__.py
│   ├── seed_tickets.py                         ← CSV → two-tab Sheet structure
│   ├── seed_rate_cards.py                      ← CSV → kb/rate-cards/*.md
│   ├── seed_faq.py                             ← PDF → kb/faqs/*.md (LLM-assisted)
│   ├── seed_product_reference.py               ← docx → kb/products/*.md
│   ├── seed_sop.py                             ← docx → kb/_schema.md + policies/
│   ├── seed_personas.py                        ← hand-seeded personas
│   └── generate_index.py                       ← writes kb/index.md
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                             ← pytest fixtures
│   ├── fixtures/
│   │   ├── sample_event.json
│   │   ├── sample_kb/                          ← tiny KB for tests
│   │   └── llm_responses/                      ← mocked LLM JSON
│   ├── test_schemas.py
│   ├── test_llm_client.py
│   ├── test_kb_reader.py
│   ├── test_kb_writer.py
│   ├── test_traversal_agent.py
│   ├── test_kb_drafter.py
│   ├── test_api.py
│   └── test_e2e_smoke.py
│
├── workflows/
│   └── n8n/                                    ← exported JSON workflows
│       ├── 01_intake_and_traversal.json
│       ├── 02_gap_resolution.json
│       └── 03_kb_approval.json
│
├── kb/                                          ← Karpathy-style wiki
│   ├── index.md
│   ├── _schema.md                              ← brand voice
│   ├── _workflows/                              ← versioned prompts
│   │   ├── traversal-agent.md
│   │   └── kb-drafter-agent.md
│   ├── faqs/<slug>.md
│   ├── products/<sku>.md
│   ├── rate-cards/{engraving,servicing}.md
│   ├── policies/escalation.md
│   └── personas/{lifecycle,interest,behaviour}/*.md
│
├── gap-log/
│   └── (populated at runtime)
│
└── data/                                       ← (untouched, provided dummy data)
```

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `intel_engine/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Goal:** Working Python project with uv + pytest + ruff + Pydantic, repo-level scaffolding complete.

- [ ] **Step 1: Initialise uv project**

```bash
cd /Users/jon/code/hackathons/e27-revenue-rocket
uv init --python 3.12 --no-readme --no-pin-python
```

Expected: creates `pyproject.toml` and `.python-version`.

- [ ] **Step 2: Add core dependencies**

```bash
uv add fastapi uvicorn pydantic httpx pdfplumber python-docx pandas python-dotenv
uv add --dev pytest pytest-asyncio pytest-mock ruff httpx[cli]
```

- [ ] **Step 3: Replace `pyproject.toml` with complete config**

```toml
[project]
name = "intel-engine"
version = "0.1.0"
description = "Self-improving customer intelligence engine for Boldr"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "pydantic>=2.9",
    "httpx>=0.28",
    "pdfplumber>=0.11",
    "python-docx>=1.1",
    "pandas>=2.2",
    "python-dotenv>=1.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-mock>=3.14",
    "ruff>=0.7",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"
```

- [ ] **Step 4: Create `.env.example`**

```bash
# LLM endpoints (OpenAI-compatible)
LLM_MINIMAX_BASE_URL=https://api.minimax.chat/v1
LLM_MINIMAX_API_KEY=
LLM_MINIMAX_MODEL=MiniMax-Text-2.7

LLM_KIMI_BASE_URL=https://api.moonshot.ai/v1
LLM_KIMI_API_KEY=
LLM_KIMI_MODEL=kimi-k2-0905-preview

# Paths
KB_ROOT=./kb
GAP_LOG_ROOT=./gap-log

# Service
INTEL_ENGINE_HOST=0.0.0.0
INTEL_ENGINE_PORT=8000

# Git auto-commit
GIT_AUTHOR_NAME=Intel Engine
GIT_AUTHOR_EMAIL=intel-engine@boldr.local

# Slack (set later)
SLACK_BOT_TOKEN=
SLACK_APPROVAL_CHANNEL=
```

- [ ] **Step 5: Create `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.env
.DS_Store
*.egg-info/
dist/
build/
node_modules/
```

- [ ] **Step 6: Create empty package files**

Create `intel_engine/__init__.py`:
```python
"""Intel engine: self-improving customer intelligence."""

__version__ = "0.1.0"
```

Create `tests/__init__.py` (empty).

Create `tests/conftest.py`:
```python
"""Shared pytest fixtures."""
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _env_isolation(monkeypatch, tmp_path):
    """Each test starts with clean env and isolated paths."""
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path / "gap-log"))
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("LLM_KIMI_API_KEY", "test-key")
    (tmp_path / "kb").mkdir()
    (tmp_path / "gap-log").mkdir()


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
```

- [ ] **Step 7: Verify project boots**

```bash
uv run pytest --collect-only
```

Expected: `collected 0 items` (no tests yet, but pytest runs).

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock .env.example .gitignore intel_engine/ tests/ .python-version
git -c commit.gpgsign=false commit -m "chore: project scaffold with uv, pytest, ruff"
```

---

## Task 2: Common Event Schema

**Files:**
- Create: `intel_engine/schemas/__init__.py`
- Create: `intel_engine/schemas/event.py`
- Create: `tests/test_schemas.py`

**Goal:** Pydantic model representing a normalised customer ticket from any channel.

- [ ] **Step 1: Write failing test for CommonEvent**

Create `tests/test_schemas.py`:
```python
"""Test schemas validate correctly."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from intel_engine.schemas.event import Channel, CommonEvent, Customer


def test_common_event_minimal_fields():
    event = CommonEvent(
        event_id="evt_123",
        source=Channel.google_sheet,
        customer=Customer(id="anon_c042", name="Sarah K."),
        body="Are your watches MRI-safe?",
        ts=datetime(2026, 5, 16, 14, 23, 11, tzinfo=timezone.utc),
    )
    assert event.subject is None
    assert event.attachments == []
    assert event.channel_meta == {}


def test_common_event_rejects_empty_body():
    with pytest.raises(ValidationError):
        CommonEvent(
            event_id="evt_123",
            source=Channel.gmail,
            customer=Customer(id="anon_c042", name="Sarah K."),
            body="",
            ts=datetime.now(timezone.utc),
        )


def test_common_event_channels_enum():
    assert Channel.google_sheet.value == "google_sheet"
    assert Channel.gmail.value == "gmail"
    assert Channel.instagram_dm.value == "instagram_dm"
    assert Channel.whatsapp.value == "whatsapp"
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_schemas.py -v
```

Expected: `ModuleNotFoundError: No module named 'intel_engine.schemas'`

- [ ] **Step 3: Create the schema module**

Create `intel_engine/schemas/__init__.py` (empty).

Create `intel_engine/schemas/event.py`:
```python
"""Common Event Schema — all channel adapters normalise into this."""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Channel(str, Enum):
    google_sheet = "google_sheet"
    gmail = "gmail"
    instagram_dm = "instagram_dm"
    whatsapp = "whatsapp"


class Customer(BaseModel):
    id: str
    name: str


class CommonEvent(BaseModel):
    """Normalised inbound customer event from any channel."""

    event_id: str
    source: Channel
    channel_meta: dict[str, Any] = Field(default_factory=dict)
    customer: Customer
    subject: str | None = None
    body: str = Field(min_length=1)
    ts: datetime
    attachments: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_schemas.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add intel_engine/schemas/ tests/test_schemas.py
git -c commit.gpgsign=false commit -m "feat: common event schema with channel enum"
```

---

## Task 3: KB Entry + Traversal + Gap Schemas

**Files:**
- Create: `intel_engine/schemas/kb.py`
- Create: `intel_engine/schemas/traversal.py`
- Create: `intel_engine/schemas/gap.py`
- Modify: `tests/test_schemas.py`

**Goal:** All Pydantic models the agent and KB layer operate on.

- [ ] **Step 1: Write failing tests for KB and traversal schemas**

Append to `tests/test_schemas.py`:
```python
from datetime import date

from intel_engine.schemas.gap import Gap, GapStatus
from intel_engine.schemas.kb import KBEntry, KBFrontmatter, KBStatus, KBDomain
from intel_engine.schemas.traversal import Confidence, TraversalResult


def test_kb_frontmatter_required_fields():
    fm = KBFrontmatter(
        slug="bpa-free-straps",
        title="Are Boldr FKM rubber straps BPA-free?",
        domain=KBDomain.spec,
        themes=["materials_safety", "sustainability"],
        sources=["faq_v3"],
        last_verified=date(2026, 5, 16),
    )
    assert fm.status == KBStatus.active
    assert fm.supersedes == []


def test_kb_entry_serialises_to_markdown():
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="bpa-free-straps",
            title="Are Boldr FKM rubber straps BPA-free?",
            domain=KBDomain.spec,
            themes=["materials_safety"],
            sources=["faq_v3"],
            last_verified=date(2026, 5, 16),
        ),
        body="Yes. All Boldr FKM rubber and silicone straps are 100% BPA-free.",
    )
    md = entry.to_markdown()
    assert md.startswith("---\n")
    assert "slug: bpa-free-straps" in md
    assert "Yes. All Boldr FKM rubber" in md


def test_traversal_result_can_answer():
    result = TraversalResult(
        pages_read=["kb/faqs/bpa-straps.md"],
        can_answer_fully=True,
        missing_info=[],
        draft_reply="Hi Sarah, thanks for reaching out...",
        themes_detected=["materials_safety"],
        persona_hints=["health_conscious"],
        confidence=Confidence.high,
    )
    assert result.can_answer_fully is True


def test_traversal_result_cannot_answer_requires_missing_info():
    result = TraversalResult(
        pages_read=["kb/faqs/bpa-straps.md"],
        can_answer_fully=False,
        missing_info=["MRI compatibility unknown"],
        draft_reply=None,
        themes_detected=["materials_safety"],
        persona_hints=[],
        confidence=Confidence.low,
    )
    assert result.can_answer_fully is False
    assert result.draft_reply is None


def test_gap_default_status_is_open():
    gap = Gap(
        gap_id="gap_2026-05-16_abc",
        source_event_id="evt_123",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI compatibility unknown"],
        themes_detected=["materials_safety"],
    )
    assert gap.status == GapStatus.open
    assert gap.resolution is None
```

- [ ] **Step 2: Run tests, expect failure**

```bash
uv run pytest tests/test_schemas.py -v
```

Expected: `ModuleNotFoundError: No module named 'intel_engine.schemas.kb'`

- [ ] **Step 3: Create `intel_engine/schemas/kb.py`**

```python
"""Knowledge base entry schemas."""
from datetime import date
from enum import Enum

import yaml
from pydantic import BaseModel, Field


class KBDomain(str, Enum):
    """Per-fact-type canonical-source domain."""

    spec = "spec"            # product reference is canonical
    pricing = "pricing"      # rate cards are canonical
    policy = "policy"        # SOP is canonical
    faq = "faq"              # general consumer-facing
    persona = "persona"      # persona definitions


class KBStatus(str, Enum):
    active = "active"
    stale = "stale"
    draft = "draft"


class KBFrontmatter(BaseModel):
    slug: str
    title: str
    domain: KBDomain
    themes: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    last_verified: date
    supersedes: list[str] = Field(default_factory=list)
    status: KBStatus = KBStatus.active


class KBEntry(BaseModel):
    frontmatter: KBFrontmatter
    body: str

    def to_markdown(self) -> str:
        fm_dict = self.frontmatter.model_dump(mode="json")
        fm_yaml = yaml.safe_dump(fm_dict, sort_keys=False).strip()
        return f"---\n{fm_yaml}\n---\n\n{self.body.strip()}\n"

    @classmethod
    def from_markdown(cls, md: str) -> "KBEntry":
        if not md.startswith("---\n"):
            raise ValueError("KB entry must begin with YAML frontmatter")
        _, fm_str, body = md.split("---\n", 2)
        fm = yaml.safe_load(fm_str)
        return cls(frontmatter=KBFrontmatter(**fm), body=body.strip())
```

Add yaml to deps:

```bash
uv add pyyaml
```

- [ ] **Step 4: Create `intel_engine/schemas/traversal.py`**

```python
"""Wiki-traversal agent structured output."""
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Confidence(str, Enum):
    low = "low"
    med = "med"
    high = "high"


class TraversalResult(BaseModel):
    pages_read: list[str] = Field(
        description="KB file paths the agent considered relevant"
    )
    can_answer_fully: bool
    missing_info: list[str] = Field(
        default_factory=list,
        description="What the agent would need to know to answer fully; non-empty iff can_answer_fully=False",
    )
    draft_reply: str | None = Field(
        default=None,
        description="Brand-voice draft reply; None iff can_answer_fully=False",
    )
    themes_detected: list[str]
    persona_hints: list[str] = Field(default_factory=list)
    confidence: Confidence

    @model_validator(mode="after")
    def _consistency(self) -> "TraversalResult":
        if self.can_answer_fully and self.draft_reply is None:
            raise ValueError("draft_reply must be present when can_answer_fully is True")
        if not self.can_answer_fully and self.draft_reply is not None:
            raise ValueError("draft_reply must be None when can_answer_fully is False")
        return self
```

- [ ] **Step 5: Create `intel_engine/schemas/gap.py`**

```python
"""Knowledge-gap schemas."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GapStatus(str, Enum):
    open = "open"
    resolved = "resolved"
    superseded = "superseded"


class GapResolution(BaseModel):
    resolved_by: str          # human identifier (Slack user ID, email, etc.)
    resolution_text: str
    resolved_at: datetime
    source_note: str | None = None  # "vendor email", "internal team", etc.


class Gap(BaseModel):
    gap_id: str
    source_event_id: str
    customer_question: str
    missing_info: list[str]
    themes_detected: list[str] = Field(default_factory=list)
    persona_hints: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    status: GapStatus = GapStatus.open
    resolution: GapResolution | None = None
    drafted_kb_slug: str | None = None
```

- [ ] **Step 6: Run tests, expect pass**

```bash
uv run pytest tests/test_schemas.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add intel_engine/schemas/ tests/test_schemas.py pyproject.toml uv.lock
git -c commit.gpgsign=false commit -m "feat: KB, traversal, and gap schemas with validation"
```

---

## Task 4: LLM Client Wrapper

**Files:**
- Create: `intel_engine/settings.py`
- Create: `intel_engine/llm/__init__.py`
- Create: `intel_engine/llm/client.py`
- Create: `tests/test_llm_client.py`

**Goal:** Thin async client over OpenAI-compatible APIs (Minimax + Kimi) with JSON-mode support for structured outputs.

- [ ] **Step 1: Write failing test for client**

Create `tests/test_llm_client.py`:
```python
"""Test LLM client."""
import json

import httpx
import pytest

from intel_engine.llm.client import LLMClient, LLMProvider


@pytest.fixture
def mock_llm_response(respx_mock):
    """Mock a chat completion response."""
    return respx_mock


async def test_client_calls_correct_endpoint(monkeypatch, httpx_mock):
    monkeypatch.setenv("LLM_MINIMAX_BASE_URL", "https://test.minimax.local/v1")
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MINIMAX_MODEL", "test-model")

    httpx_mock.add_response(
        url="https://test.minimax.local/v1/chat/completions",
        json={
            "choices": [
                {"message": {"content": '{"answer": "yes"}'}}
            ]
        },
    )

    client = LLMClient(provider=LLMProvider.minimax)
    result = await client.complete_json(
        system="You are a helper.",
        user="Is the sky blue?",
    )
    assert result == {"answer": "yes"}


async def test_client_returns_plain_text(monkeypatch, httpx_mock):
    monkeypatch.setenv("LLM_KIMI_BASE_URL", "https://test.kimi.local/v1")
    monkeypatch.setenv("LLM_KIMI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_KIMI_MODEL", "test-model")

    httpx_mock.add_response(
        url="https://test.kimi.local/v1/chat/completions",
        json={
            "choices": [
                {"message": {"content": "Hello, world."}}
            ]
        },
    )

    client = LLMClient(provider=LLMProvider.kimi)
    result = await client.complete_text(system="You are a helper.", user="Say hi")
    assert result == "Hello, world."
```

- [ ] **Step 2: Add test dependency**

```bash
uv add --dev pytest-httpx
```

- [ ] **Step 3: Run test, expect failure**

```bash
uv run pytest tests/test_llm_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'intel_engine.llm'`

- [ ] **Step 4: Create `intel_engine/settings.py`**

```python
"""Environment-driven config."""
import os
from functools import cache
from pathlib import Path


@cache
def kb_root() -> Path:
    return Path(os.environ.get("KB_ROOT", "./kb")).resolve()


@cache
def gap_log_root() -> Path:
    return Path(os.environ.get("GAP_LOG_ROOT", "./gap-log")).resolve()


def llm_config(provider: str) -> dict[str, str]:
    """Return base_url, api_key, model for a provider ('minimax' or 'kimi')."""
    prefix = f"LLM_{provider.upper()}"
    return {
        "base_url": os.environ[f"{prefix}_BASE_URL"],
        "api_key": os.environ[f"{prefix}_API_KEY"],
        "model": os.environ[f"{prefix}_MODEL"],
    }
```

- [ ] **Step 5: Create `intel_engine/llm/__init__.py`** (empty)

- [ ] **Step 6: Create `intel_engine/llm/client.py`**

```python
"""OpenAI-compatible chat client for Minimax + Kimi."""
import json
from enum import Enum
from typing import Any

import httpx

from intel_engine.settings import llm_config


class LLMProvider(str, Enum):
    minimax = "minimax"
    kimi = "kimi"


class LLMClient:
    def __init__(self, provider: LLMProvider, timeout: float = 60.0):
        cfg = llm_config(provider.value)
        self.base_url = cfg["base_url"].rstrip("/")
        self.api_key = cfg["api_key"]
        self.model = cfg["model"]
        self.timeout = timeout

    async def _chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def complete_text(self, system: str, user: str) -> str:
        return await self._chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

    async def complete_json(
        self,
        system: str,
        user: str,
        max_retries: int = 1,
    ) -> dict[str, Any]:
        """Request a JSON response. Falls back to retry on parse failure."""
        prompt_with_json = (
            f"{system}\n\n"
            "You MUST respond with valid JSON only. No markdown fences, no prose."
        )
        last_err: Exception | None = None
        for _attempt in range(max_retries + 1):
            text = await self._chat(
                messages=[
                    {"role": "system", "content": prompt_with_json},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
            try:
                # Tolerate accidental code fences
                stripped = text.strip()
                if stripped.startswith("```"):
                    stripped = stripped.split("```")[1]
                    if stripped.startswith("json"):
                        stripped = stripped[4:]
                return json.loads(stripped)
            except json.JSONDecodeError as e:
                last_err = e
                continue
        raise ValueError(f"LLM returned non-JSON after retries: {last_err}")
```

- [ ] **Step 7: Run tests, expect pass**

```bash
uv run pytest tests/test_llm_client.py -v
```

Expected: 2 passed.

- [ ] **Step 8: Commit**

```bash
git add intel_engine/settings.py intel_engine/llm/ tests/test_llm_client.py pyproject.toml uv.lock
git -c commit.gpgsign=false commit -m "feat: LLM client wrapper for Minimax + Kimi"
```

---

## Task 5: Seed Tickets (CSV → Two-Tab Sheet structure)

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/seed_tickets.py`
- Create: `tests/test_seed_tickets.py`

**Goal:** Read `data/01_customer_tickets.csv`; split into `tickets_input.csv` (agent-visible columns) and `eval_labels.csv` (held-out gold) under `eval/data/`. These will populate the Google Sheet's two tabs.

- [ ] **Step 1: Write failing test**

Create `tests/test_seed_tickets.py`:
```python
"""Test ticket seeding script."""
import csv
from pathlib import Path

import pytest

from scripts.seed_tickets import split_tickets


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    src = tmp_path / "tickets.csv"
    src.write_text(
        "ticket_id,received_at,channel,customer_name,subject,body,"
        "question_type,buyer_persona,answered_by_kb,requires_escalation\n"
        "TKT-1001,2025-11-15,email,Alice,BPA?,Is this BPA-free?,"
        "materials_safety,health_conscious,yes,no\n"
        "TKT-1002,2025-11-16,chat,Bob,MRI?,Is this MRI-safe?,"
        "knowledge_gap,enthusiast,no,yes\n"
    )
    return src


def test_split_tickets_creates_two_files(sample_csv: Path, tmp_path: Path):
    out_dir = tmp_path / "out"
    split_tickets(sample_csv, out_dir)

    input_csv = out_dir / "tickets_input.csv"
    labels_csv = out_dir / "eval_labels.csv"
    assert input_csv.exists()
    assert labels_csv.exists()


def test_split_tickets_input_has_only_input_columns(sample_csv: Path, tmp_path: Path):
    out_dir = tmp_path / "out"
    split_tickets(sample_csv, out_dir)
    rows = list(csv.DictReader((out_dir / "tickets_input.csv").open()))
    assert len(rows) == 2
    assert set(rows[0].keys()) == {
        "ticket_id", "received_at", "channel", "customer_name", "subject", "body",
    }


def test_split_tickets_labels_has_id_plus_label_columns(sample_csv: Path, tmp_path: Path):
    out_dir = tmp_path / "out"
    split_tickets(sample_csv, out_dir)
    rows = list(csv.DictReader((out_dir / "eval_labels.csv").open()))
    assert rows[0]["ticket_id"] == "TKT-1001"
    assert rows[0]["question_type"] == "materials_safety"
    assert rows[0]["buyer_persona"] == "health_conscious"
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_seed_tickets.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts'`

- [ ] **Step 3: Create scripts package**

Create `scripts/__init__.py` (empty).

Create `scripts/seed_tickets.py`:
```python
"""Split provided customer_tickets.csv into agent-visible vs eval-only columns."""
import csv
from pathlib import Path

INPUT_COLUMNS = ["ticket_id", "received_at", "channel", "customer_name", "subject", "body"]
LABEL_COLUMNS = [
    "ticket_id",
    "question_type",
    "buyer_persona",
    "answered_by_kb",
    "requires_escalation",
]


def split_tickets(src: Path, out_dir: Path) -> None:
    """Read src CSV, write tickets_input.csv + eval_labels.csv to out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(src.open()))

    with (out_dir / "tickets_input.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=INPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in INPUT_COLUMNS})

    with (out_dir / "eval_labels.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LABEL_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in LABEL_COLUMNS})


if __name__ == "__main__":
    import sys

    src = Path(sys.argv[1] if len(sys.argv) > 1 else "data/01_customer_tickets.csv")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "eval/data")
    split_tickets(src, out_dir)
    print(f"Wrote {out_dir}/tickets_input.csv and {out_dir}/eval_labels.csv")
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_seed_tickets.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Run script against real data**

```bash
uv run python -m scripts.seed_tickets data/01_customer_tickets.csv eval/data
ls eval/data/
```

Expected: `tickets_input.csv  eval_labels.csv` listed.

- [ ] **Step 6: Spot-check the output**

```bash
head -3 eval/data/tickets_input.csv
head -3 eval/data/eval_labels.csv
```

Expected: input has no label columns; labels has `ticket_id` + 4 gold columns.

- [ ] **Step 7: Commit**

```bash
git add scripts/__init__.py scripts/seed_tickets.py tests/test_seed_tickets.py eval/data/
git -c commit.gpgsign=false commit -m "feat: split tickets CSV into agent-visible vs eval-only tabs"
```

---

## Task 6: Seed Rate Cards (CSV → kb/rate-cards/*.md)

**Files:**
- Create: `scripts/seed_rate_cards.py`
- Create: `tests/test_seed_rate_cards.py`

**Goal:** Convert the two rate-card CSVs into one KB Markdown entry each with `KBDomain.pricing` frontmatter.

- [ ] **Step 1: Write failing test**

Create `tests/test_seed_rate_cards.py`:
```python
"""Test rate card seeding."""
import csv
from pathlib import Path

from intel_engine.schemas.kb import KBEntry
from scripts.seed_rate_cards import seed_rate_card


def test_seed_engraving_rate_card(tmp_path: Path):
    src = tmp_path / "engraving.csv"
    src.write_text(
        "service,price_sgd,notes\n"
        "Initials engraving,25,Up to 4 Latin characters\n"
        "Full name engraving,45,Up to 15 Latin characters\n"
    )
    out = tmp_path / "kb" / "rate-cards" / "engraving.md"

    seed_rate_card(
        src=src,
        out_path=out,
        slug="engraving-rate-card",
        title="Engraving services — pricing and rules",
        themes=["engraving", "pricing"],
    )

    assert out.exists()
    md = out.read_text()
    entry = KBEntry.from_markdown(md)
    assert entry.frontmatter.slug == "engraving-rate-card"
    assert entry.frontmatter.domain.value == "pricing"
    assert "Initials engraving" in entry.body
    assert "SGD 25" in entry.body
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_seed_rate_cards.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.seed_rate_cards'`

- [ ] **Step 3: Create the script**

Create `scripts/seed_rate_cards.py`:
```python
"""Convert rate card CSVs into KB markdown entries (domain=pricing)."""
import csv
from datetime import date
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter


def _rows_to_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    out = ["| " + " | ".join(h.replace("_", " ").title() for h in headers) + " |"]
    out.append("|" + "---|" * len(headers))
    for r in rows:
        cells = []
        for h in headers:
            val = r.get(h, "")
            if h == "price_sgd" and val:
                cells.append(f"SGD {val}")
            else:
                cells.append(val)
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def seed_rate_card(
    src: Path,
    out_path: Path,
    slug: str,
    title: str,
    themes: list[str],
) -> None:
    rows = list(csv.DictReader(src.open()))
    table = _rows_to_table(rows)

    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug=slug,
            title=title,
            domain=KBDomain.pricing,
            themes=themes,
            sources=[f"data/{src.name}"],
            last_verified=date.today(),
        ),
        body=table,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(entry.to_markdown())


if __name__ == "__main__":
    seed_rate_card(
        src=Path("data/03a_rate_card_engraving.csv"),
        out_path=Path("kb/rate-cards/engraving.md"),
        slug="engraving-rate-card",
        title="Engraving services — pricing, character limits, fonts, turnaround",
        themes=["engraving", "pricing"],
    )
    seed_rate_card(
        src=Path("data/03b_rate_card_servicing.csv"),
        out_path=Path("kb/rate-cards/servicing.md"),
        slug="servicing-rate-card",
        title="Watch servicing — tiers, pricing, turnaround",
        themes=["servicing", "pricing", "aftercare"],
    )
    print("Wrote kb/rate-cards/engraving.md and kb/rate-cards/servicing.md")
```

- [ ] **Step 4: Run test, expect pass**

```bash
uv run pytest tests/test_seed_rate_cards.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Run against real data**

```bash
uv run python -m scripts.seed_rate_cards
cat kb/rate-cards/engraving.md
```

Expected: well-formed markdown with frontmatter and a table.

- [ ] **Step 6: Commit**

```bash
git add scripts/seed_rate_cards.py tests/test_seed_rate_cards.py kb/rate-cards/
git -c commit.gpgsign=false commit -m "feat: seed kb/rate-cards from rate card CSVs"
```

---

## Task 7: Seed FAQ (PDF → kb/faqs/*.md) — LLM-Assisted

**Files:**
- Create: `scripts/seed_faq.py`
- Create: `tests/test_seed_faq.py`
- Create: `tests/fixtures/faq_sample.json`

**Goal:** Use Kimi to parse FAQ PDF text into structured `[{theme, question, answer}]`, then write one markdown file per entry.

- [ ] **Step 1: Write failing test (parse-step only — LLM mocked)**

Create `tests/fixtures/faq_sample.json`:
```json
[
  {
    "theme": "materials_safety",
    "question": "Are Boldr FKM rubber straps BPA-free?",
    "answer": "Yes. All Boldr FKM rubber and silicone straps are 100% BPA-free."
  },
  {
    "theme": "engraving",
    "question": "Do you support Arabic engraving?",
    "answer": "Yes. Arabic script is supported with a custom font option."
  }
]
```

Create `tests/test_seed_faq.py`:
```python
"""Test FAQ seeding (LLM parsing mocked)."""
import json
from pathlib import Path

import pytest

from intel_engine.schemas.kb import KBEntry
from scripts.seed_faq import write_faqs_from_parsed


def test_write_faqs_creates_one_file_per_entry(tmp_path: Path):
    parsed = [
        {
            "theme": "materials_safety",
            "question": "Are Boldr FKM rubber straps BPA-free?",
            "answer": "Yes. All Boldr FKM rubber and silicone straps are 100% BPA-free.",
        },
        {
            "theme": "engraving",
            "question": "Do you support Arabic engraving?",
            "answer": "Yes. Arabic script is supported with a custom font option.",
        },
    ]
    out_dir = tmp_path / "kb" / "faqs"
    written = write_faqs_from_parsed(parsed, out_dir, source_file="04_faq_document.pdf")

    assert len(written) == 2
    for path in written:
        assert path.exists()
        entry = KBEntry.from_markdown(path.read_text())
        assert entry.frontmatter.domain.value == "faq"
        assert entry.frontmatter.sources == ["data/04_faq_document.pdf"]


def test_slug_generation_handles_punctuation(tmp_path: Path):
    parsed = [
        {
            "theme": "materials_safety",
            "question": "Is this watch safe for kids? (children's edition)",
            "answer": "Yes, all watches meet EU REACH toy safety standards.",
        }
    ]
    written = write_faqs_from_parsed(parsed, tmp_path, source_file="04_faq_document.pdf")
    assert written[0].stem == "is-this-watch-safe-for-kids-childrens-edition"
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_seed_faq.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.seed_faq'`

- [ ] **Step 3: Create the script**

Create `scripts/seed_faq.py`:
```python
"""Parse FAQ PDF into KB markdown via LLM."""
import asyncio
import json
import re
from datetime import date
from pathlib import Path

import pdfplumber

from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter

PARSE_PROMPT = """\
You are converting a Boldr customer-service FAQ PDF into a structured list.

Return a JSON object with key "entries" whose value is an array of objects:
{
  "entries": [
    {
      "theme": "...",         // one of: materials_safety, engraving, strap_compatibility, servicing, order_status, shipping, product_general, sustainability, aftercare
      "question": "...",      // the question verbatim
      "answer": "..."         // the answer verbatim, preserving the brand voice
    }
  ]
}

Rules:
- Preserve punctuation, currency formatting ("SGD 85"), and cited standards verbatim
- Do not summarise or rephrase
- One entry per Q/A pair; do not merge entries
- If a section header introduces multiple Q/A pairs, tag each with the section theme
"""


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


def extract_pdf_text(pdf_path: Path) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n\n".join((page.extract_text() or "") for page in pdf.pages)


async def parse_faq_with_llm(text: str) -> list[dict[str, str]]:
    client = LLMClient(provider=LLMProvider.kimi)
    result = await client.complete_json(
        system=PARSE_PROMPT,
        user=f"FAQ document:\n\n{text}",
    )
    return result["entries"]


def write_faqs_from_parsed(
    parsed: list[dict[str, str]],
    out_dir: Path,
    source_file: str,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in parsed:
        slug = slugify(item["question"])
        entry = KBEntry(
            frontmatter=KBFrontmatter(
                slug=slug,
                title=item["question"],
                domain=KBDomain.faq,
                themes=[item["theme"]],
                sources=[f"data/{source_file}"],
                last_verified=date.today(),
            ),
            body=item["answer"],
        )
        path = out_dir / f"{slug}.md"
        path.write_text(entry.to_markdown())
        written.append(path)
    return written


async def main() -> None:
    pdf_path = Path("data/04_faq_document.pdf")
    text = extract_pdf_text(pdf_path)
    parsed = await parse_faq_with_llm(text)
    written = write_faqs_from_parsed(parsed, Path("kb/faqs"), source_file=pdf_path.name)
    print(f"Wrote {len(written)} FAQ entries to kb/faqs/")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_seed_faq.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Run script against real FAQ PDF**

Requires `.env` with valid `LLM_KIMI_API_KEY`. Copy from `.env.example` and fill in.

```bash
cp .env.example .env
# edit .env to set LLM_KIMI_API_KEY
uv run python -m scripts.seed_faq
ls kb/faqs/ | head -10
```

Expected: ~28 markdown files (one per FAQ entry).

- [ ] **Step 6: Spot-check a generated entry**

```bash
cat kb/faqs/$(ls kb/faqs/ | head -1)
```

Expected: valid frontmatter + answer text matching the original FAQ.

- [ ] **Step 7: Commit**

```bash
git add scripts/seed_faq.py tests/test_seed_faq.py tests/fixtures/faq_sample.json kb/faqs/
git -c commit.gpgsign=false commit -m "feat: seed kb/faqs from FAQ PDF via LLM-assisted parser"
```

---

## Task 8: Seed Product Reference (docx → kb/products/*.md)

**Files:**
- Create: `scripts/seed_product_reference.py`
- Create: `tests/test_seed_product_reference.py`

**Goal:** Convert `data/05b_product_reference.docx` into one or more KB entries (one per model, plus a strap catalogue entry). Use LLM-assisted parsing for robustness.

- [ ] **Step 1: Write failing test**

Create `tests/test_seed_product_reference.py`:
```python
"""Test product reference seeding."""
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry
from scripts.seed_product_reference import write_products_from_parsed


def test_write_products_creates_files_with_spec_domain(tmp_path: Path):
    parsed = [
        {
            "sku": "BOLDR-VENT-TI",
            "name": "Venture Titanium",
            "specs": "Grade 5 titanium case, 38mm, 200m WR, Miyota 9015 movement.",
        },
        {
            "sku": "BOLDR-FKM-22",
            "name": "FKM Rubber Strap 22mm",
            "specs": "100% BPA-free, hypoallergenic, salt-resistant.",
        },
    ]
    written = write_products_from_parsed(parsed, tmp_path, source_file="05b_product_reference.docx")
    assert len(written) == 2

    entry = KBEntry.from_markdown(written[0].read_text())
    assert entry.frontmatter.domain == KBDomain.spec
    assert "Venture Titanium" in entry.body
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_seed_product_reference.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create the script**

Create `scripts/seed_product_reference.py`:
```python
"""Parse product reference docx into KB markdown via LLM."""
import asyncio
from datetime import date
from pathlib import Path

import docx

from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter
from scripts.seed_faq import slugify

PARSE_PROMPT = """\
You are converting a Boldr product reference document into a structured list of product entries.

Each entry is one product (watch model, strap, accessory) OR a related catalogue table (e.g., strap compatibility).

Return JSON: {"entries": [{"sku": "BOLDR-XXX", "name": "...", "specs": "..."}, ...]}

Rules:
- "sku" should be the most distinctive identifier in the source. If absent, use a kebab-case slug of the product name.
- "name" is the human-readable product name.
- "specs" is a verbatim chunk of all relevant detail: materials, dimensions, water resistance, movement, compatibility notes, warnings.
- Preserve units, standards (ISO 3157, Grade 5 Ti, EU REACH), and any ⚠ callouts.
- Treat the strap catalogue / Q-A quick-reference table as its own entry with sku "STRAP-CATALOGUE".
"""


def extract_docx_text(docx_path: Path) -> str:
    doc = docx.Document(str(docx_path))
    parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells)
            if row_text.strip(" |"):
                parts.append(row_text)
    return "\n".join(parts)


async def parse_with_llm(text: str) -> list[dict[str, str]]:
    client = LLMClient(provider=LLMProvider.kimi)
    result = await client.complete_json(
        system=PARSE_PROMPT,
        user=f"Document:\n\n{text}",
    )
    return result["entries"]


def write_products_from_parsed(
    parsed: list[dict[str, str]],
    out_dir: Path,
    source_file: str,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in parsed:
        sku = item["sku"]
        slug = slugify(sku) if sku else slugify(item["name"])
        entry = KBEntry(
            frontmatter=KBFrontmatter(
                slug=slug,
                title=item["name"],
                domain=KBDomain.spec,
                themes=["product_general"],
                sources=[f"data/{source_file}"],
                last_verified=date.today(),
            ),
            body=item["specs"],
        )
        path = out_dir / f"{slug}.md"
        path.write_text(entry.to_markdown())
        written.append(path)
    return written


async def main() -> None:
    src = Path("data/05b_product_reference.docx")
    text = extract_docx_text(src)
    parsed = await parse_with_llm(text)
    written = write_products_from_parsed(parsed, Path("kb/products"), source_file=src.name)
    print(f"Wrote {len(written)} product entries to kb/products/")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_seed_product_reference.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Run against real docx**

```bash
uv run python -m scripts.seed_product_reference
ls kb/products/
```

Expected: ~3-5 product entries.

- [ ] **Step 6: Commit**

```bash
git add scripts/seed_product_reference.py tests/test_seed_product_reference.py kb/products/
git -c commit.gpgsign=false commit -m "feat: seed kb/products from product reference docx"
```

---

## Task 9: Seed SOP (docx → kb/_schema.md + kb/policies/escalation.md)

**Files:**
- Create: `scripts/seed_sop.py`
- Create: `tests/test_seed_sop.py`

**Goal:** Extract SOP §5 (brand voice) into `kb/_schema.md` (NOT a normal KB entry — bare markdown). Extract SOP §7 (escalation triggers) into `kb/policies/escalation.md` with `KBDomain.policy`.

- [ ] **Step 1: Write failing test**

Create `tests/test_seed_sop.py`:
```python
"""Test SOP seeding."""
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry
from scripts.seed_sop import write_schema, write_escalation_policy


def test_write_schema_is_plain_markdown(tmp_path: Path):
    body = "## Openers\n\nPreferred: 'Yes.'\nForbidden: 'Great question!'"
    out = tmp_path / "_schema.md"
    write_schema(body, out)
    assert out.read_text().startswith("# Brand Voice Contract")
    assert "Preferred: 'Yes.'" in out.read_text()


def test_write_escalation_policy_is_kb_entry(tmp_path: Path):
    body = "Escalate when: customer angry, warranty > damage, refund > 10 days"
    out = tmp_path / "policies" / "escalation.md"
    write_escalation_policy(body, out, source_file="05a_SOP.docx")

    entry = KBEntry.from_markdown(out.read_text())
    assert entry.frontmatter.domain == KBDomain.policy
    assert entry.frontmatter.slug == "escalation-policy"
    assert "warranty" in entry.body
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_seed_sop.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create the script**

Create `scripts/seed_sop.py`:
```python
"""Extract SOP §5 (brand voice) and §7 (escalation) into KB."""
import asyncio
from datetime import date
from pathlib import Path

from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter
from scripts.seed_product_reference import extract_docx_text

EXTRACT_PROMPT = """\
You are extracting structured policy data from a customer-service SOP document.

Return JSON with two keys:
{
  "brand_voice": "...",      // The full content of Section 5 (Brand Voice / Response Style)
                              // including preferred openers, forbidden phrases, tone rules,
                              // currency conventions, and any examples — verbatim.
  "escalation": "..."         // The full content of Section 7 (Escalation Triggers) —
                              // a list of conditions that require escalating to senior staff,
                              // verbatim.
}

If a section is missing, set the value to an empty string.
"""


def write_schema(body: str, out_path: Path) -> None:
    content = (
        "# Brand Voice Contract\n\n"
        "This file defines Boldr's customer-service voice. "
        "The wiki-traversal agent reads this on every draft reply.\n\n"
        f"{body.strip()}\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content)


def write_escalation_policy(body: str, out_path: Path, source_file: str) -> None:
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="escalation-policy",
            title="Escalation triggers — when to route to senior staff",
            domain=KBDomain.policy,
            themes=["escalation", "policy"],
            sources=[f"data/{source_file}"],
            last_verified=date.today(),
        ),
        body=body.strip(),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(entry.to_markdown())


async def main() -> None:
    src = Path("data/05a_SOP.docx")
    text = extract_docx_text(src)
    client = LLMClient(provider=LLMProvider.kimi)
    result = await client.complete_json(
        system=EXTRACT_PROMPT,
        user=f"SOP:\n\n{text}",
    )

    write_schema(result["brand_voice"], Path("kb/_schema.md"))
    write_escalation_policy(result["escalation"], Path("kb/policies/escalation.md"), source_file=src.name)
    print("Wrote kb/_schema.md and kb/policies/escalation.md")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_seed_sop.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Run against real SOP**

```bash
uv run python -m scripts.seed_sop
cat kb/_schema.md | head -20
cat kb/policies/escalation.md | head -20
```

Expected: schema starts with `# Brand Voice Contract`, escalation has frontmatter.

- [ ] **Step 6: Commit**

```bash
git add scripts/seed_sop.py tests/test_seed_sop.py kb/_schema.md kb/policies/
git -c commit.gpgsign=false commit -m "feat: seed brand voice + escalation policy from SOP docx"
```

---

## Task 10: Seed Personas + Generate kb/index.md

**Files:**
- Create: `scripts/seed_personas.py`
- Create: `scripts/generate_index.py`
- Create: `intel_engine/kb/__init__.py`
- Create: `intel_engine/kb/reader.py`
- Create: `tests/test_kb_reader.py`
- Create: `tests/test_generate_index.py`

**Goal:** Seed the 5 brief-derived personas as placeholder markdown files (cold-start discovery is Plan 3); build the index generator that scans `kb/` and produces `kb/index.md`. Also implement the KB reader the agent will use.

- [ ] **Step 1: Write failing tests**

Create `tests/test_kb_reader.py`:
```python
"""Test KB reader."""
from pathlib import Path

from intel_engine.kb.reader import load_kb


def test_load_kb_reads_all_markdown_files(tmp_path: Path):
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "a.md").write_text(
        "---\nslug: a\ntitle: A\ndomain: faq\nlast_verified: 2026-05-16\n---\n\nbody A"
    )
    (tmp_path / "faqs" / "b.md").write_text(
        "---\nslug: b\ntitle: B\ndomain: faq\nlast_verified: 2026-05-16\n---\n\nbody B"
    )

    entries = load_kb(tmp_path)
    assert len(entries) == 2
    slugs = {e.frontmatter.slug for e in entries}
    assert slugs == {"a", "b"}


def test_load_kb_skips_underscore_files(tmp_path: Path):
    (tmp_path / "_schema.md").write_text("# brand voice")
    (tmp_path / "_log.md").write_text("# audit")
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "a.md").write_text(
        "---\nslug: a\ntitle: A\ndomain: faq\nlast_verified: 2026-05-16\n---\n\nbody A"
    )

    entries = load_kb(tmp_path)
    assert len(entries) == 1


def test_load_kb_skips_stale_entries(tmp_path: Path):
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "active.md").write_text(
        "---\nslug: active\ntitle: A\ndomain: faq\nlast_verified: 2026-05-16\nstatus: active\n---\n\nactive"
    )
    (tmp_path / "faqs" / "stale.md").write_text(
        "---\nslug: stale\ntitle: S\ndomain: faq\nlast_verified: 2026-01-01\nstatus: stale\n---\n\nstale"
    )

    entries = load_kb(tmp_path)
    slugs = {e.frontmatter.slug for e in entries}
    assert slugs == {"active"}
```

Create `tests/test_generate_index.py`:
```python
"""Test index generation."""
from pathlib import Path

from scripts.generate_index import generate_index


def test_generate_index_lists_all_entries(tmp_path: Path):
    (tmp_path / "faqs").mkdir()
    (tmp_path / "faqs" / "bpa.md").write_text(
        "---\nslug: bpa\ntitle: BPA-free?\ndomain: faq\nthemes: [materials]\nlast_verified: 2026-05-16\n---\n\nbody"
    )
    (tmp_path / "rate-cards").mkdir()
    (tmp_path / "rate-cards" / "engraving.md").write_text(
        "---\nslug: engraving-rates\ntitle: Engraving prices\ndomain: pricing\nthemes: [engraving]\nlast_verified: 2026-05-16\n---\n\nbody"
    )

    out = tmp_path / "index.md"
    generate_index(tmp_path, out)

    md = out.read_text()
    assert "# Knowledge Base Index" in md
    assert "bpa" in md
    assert "engraving-rates" in md
    assert "## faq" in md.lower() or "### faq" in md.lower()
```

- [ ] **Step 2: Run tests, expect failure**

```bash
uv run pytest tests/test_kb_reader.py tests/test_generate_index.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create the KB reader**

Create `intel_engine/kb/__init__.py` (empty).

Create `intel_engine/kb/reader.py`:
```python
"""Load KB entries from disk."""
from pathlib import Path

from intel_engine.schemas.kb import KBEntry, KBStatus


def load_kb(kb_root: Path) -> list[KBEntry]:
    """Walk kb_root, parse all *.md files (excluding _*.md), filter out stale."""
    entries: list[KBEntry] = []
    for path in kb_root.rglob("*.md"):
        if path.name.startswith("_"):
            continue
        try:
            entry = KBEntry.from_markdown(path.read_text())
        except (ValueError, KeyError) as e:
            # Malformed entries are skipped, not fatal
            print(f"Skipping malformed entry {path}: {e}")
            continue
        if entry.frontmatter.status == KBStatus.stale:
            continue
        entries.append(entry)
    return sorted(entries, key=lambda e: e.frontmatter.slug)
```

- [ ] **Step 4: Create persona-seeding script**

Create `scripts/seed_personas.py`:
```python
"""Seed 5 brief-derived personas as placeholder KB markdown.

These are seed entries; Plan 3 implements cold-start discovery and drift detection.
"""
from datetime import date
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter

PERSONAS = [
    {
        "axis": "interest",
        "slug": "health-conscious-buyer",
        "title": "Health-Conscious Buyer",
        "body": (
            "Buyers prioritising BPA-free, nickel-free, hypoallergenic materials. "
            "Often buying for children or for skin-sensitive use cases. "
            "Trigger keywords: BPA-free, nickel allergy, hypoallergenic, kids, REACH, safe."
        ),
    },
    {
        "axis": "interest",
        "slug": "gifter",
        "title": "Gifter",
        "body": (
            "Buyers purchasing for someone else. Care about engraving, gift wrap, "
            "turnaround time, presentation. Trigger keywords: gift, engraving, "
            "birthday, anniversary, Father's Day, Valentine's, wrap."
        ),
    },
    {
        "axis": "interest",
        "slug": "enthusiast-collector",
        "title": "Enthusiast / Collector",
        "body": (
            "Watch enthusiasts who care about Grade 5 titanium, Miyota movement details, "
            "limited editions, craftsmanship. Trigger keywords: titanium grade, Miyota, "
            "limited edition, movement, craftsmanship."
        ),
    },
    {
        "axis": "interest",
        "slug": "active-outdoor-buyer",
        "title": "Active / Outdoor Buyer",
        "body": (
            "Buyers for trail running, diving, climbing. Care about water resistance, "
            "shock rating, FKM rubber strap. Trigger keywords: water resistance, shock, "
            "trail, dive, FKM, rubber strap, altitude."
        ),
    },
    {
        "axis": "interest",
        "slug": "sustainability-advocate",
        "title": "Sustainability Advocate",
        "body": (
            "Buyers focused on vegan straps, carbon-neutral shipping, eco packaging, "
            "take-back programmes. Trigger keywords: vegan, carbon offset, recycling, "
            "eco, sustainability."
        ),
    },
]


def main() -> None:
    out_root = Path("kb/personas/interest")
    out_root.mkdir(parents=True, exist_ok=True)
    for p in PERSONAS:
        entry = KBEntry(
            frontmatter=KBFrontmatter(
                slug=p["slug"],
                title=p["title"],
                domain=KBDomain.persona,
                themes=[p["axis"]],
                sources=["challenge_brief"],
                last_verified=date.today(),
            ),
            body=p["body"],
        )
        path = out_root / f"{p['slug']}.md"
        path.write_text(entry.to_markdown())
    print(f"Wrote {len(PERSONAS)} personas to kb/personas/interest/")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create the index generator**

Create `scripts/generate_index.py`:
```python
"""Generate kb/index.md from all KB entries."""
from collections import defaultdict
from pathlib import Path

from intel_engine.kb.reader import load_kb


def generate_index(kb_root: Path, out_path: Path) -> None:
    entries = load_kb(kb_root)

    by_domain: dict[str, list] = defaultdict(list)
    for entry in entries:
        by_domain[entry.frontmatter.domain.value].append(entry)

    lines: list[str] = [
        "# Knowledge Base Index",
        "",
        "Generated automatically. Do not edit by hand — re-run `scripts/generate_index.py`.",
        "",
        f"Total active entries: {len(entries)}",
        "",
    ]
    for domain in sorted(by_domain.keys()):
        lines.append(f"## {domain}")
        lines.append("")
        for entry in sorted(by_domain[domain], key=lambda e: e.frontmatter.slug):
            fm = entry.frontmatter
            themes = ", ".join(fm.themes) if fm.themes else "—"
            lines.append(
                f"- **{fm.slug}** — {fm.title}  "
                f"_(themes: {themes})_"
            )
        lines.append("")

    out_path.write_text("\n".join(lines))


if __name__ == "__main__":
    generate_index(Path("kb"), Path("kb/index.md"))
    print("Wrote kb/index.md")
```

- [ ] **Step 6: Run tests, expect pass**

```bash
uv run pytest tests/test_kb_reader.py tests/test_generate_index.py -v
```

Expected: 4 passed.

- [ ] **Step 7: Run scripts**

```bash
uv run python -m scripts.seed_personas
uv run python -m scripts.generate_index
head -30 kb/index.md
```

Expected: index lists faq, pricing, spec, policy, persona sections with all entries.

- [ ] **Step 8: Commit**

```bash
git add intel_engine/kb/ scripts/seed_personas.py scripts/generate_index.py tests/test_kb_reader.py tests/test_generate_index.py kb/personas/ kb/index.md
git -c commit.gpgsign=false commit -m "feat: KB reader + index generator + seed personas"
```

---

## Task 11: Traversal Agent Prompt + Workflow File

**Files:**
- Create: `kb/_workflows/traversal-agent.md`
- Create: `intel_engine/llm/prompts.py`
- Create: `tests/test_prompts.py`

**Goal:** Externalise the traversal agent's prompt as a versioned Markdown file (Symphony pattern). Build a prompt loader.

- [ ] **Step 1: Write failing test for prompt loader**

Create `tests/test_prompts.py`:
```python
"""Test prompt loader."""
from pathlib import Path

import pytest

from intel_engine.llm.prompts import load_prompt


def test_load_prompt_reads_markdown_file(tmp_path: Path, monkeypatch):
    workflows_dir = tmp_path / "kb" / "_workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "test-agent.md").write_text(
        "# Test Agent\n\nYou are a test assistant.\n"
    )
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))

    text = load_prompt("test-agent")
    assert "You are a test assistant." in text


def test_load_prompt_raises_on_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        load_prompt("does-not-exist")
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_prompts.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create prompt loader**

Create `intel_engine/llm/prompts.py`:
```python
"""Load versioned agent prompts from kb/_workflows/."""
from intel_engine.settings import kb_root


def load_prompt(name: str) -> str:
    """Read kb/_workflows/<name>.md, returning the prompt text."""
    path = kb_root() / "_workflows" / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text()
```

- [ ] **Step 4: Create the traversal agent prompt**

Create `kb/_workflows/traversal-agent.md`:
```markdown
# Wiki-Traversal Agent — System Prompt

You are Boldr's customer-service AI. You answer inbound customer messages by reading Boldr's internal knowledge base (the "KB") and drafting a reply in Boldr's voice — OR by honestly flagging that you cannot answer.

## Your job

For each customer message you receive:

1. Read the KB entries provided to you (full content of every relevant page).
2. Decide whether the KB contains a complete answer to the customer's question.
3. If YES: draft a reply in Boldr's voice, citing the specific KB files you used.
4. If NO: explicitly list what's missing. Do NOT invent facts. Do NOT speculate.
5. Tag themes detected (e.g., materials_safety, engraving, servicing, sustainability).
6. Tag persona hints (e.g., health_conscious, gifter, enthusiast, active_outdoor, sustainability).

## Brand voice (from kb/_schema.md)

The brand voice contract is loaded separately and included in your context. Match it exactly.

Critical rules:
- Open with `Yes.` or `No.` for direct factual questions.
- Use `SGD XX` for prices, never `$XX` or `S$XX`.
- Cite standards by name when relevant: ISO 3157, EU REACH, RoHS, Grade 5 Ti.
- No emoji. No exclamation marks. No "Great question!" or "Dear Sir/Madam".
- Preferred warm opener: `Hi [Name], thanks for reaching out — happy to help with that.`

## Conflict resolution

If two KB entries disagree, prefer by domain authority:
- `pricing` domain wins for prices, fees, turnaround
- `policy` domain wins for escalation, refunds, procedures
- `spec` domain wins for product specs, materials, dimensions
- `faq` is the catch-all

If same-domain entries disagree, set `can_answer_fully=false` and put the conflict in `missing_info`.

## Output format

You MUST respond with valid JSON matching this schema:

```json
{
  "pages_read": ["kb/faqs/bpa-free-straps.md", "kb/rate-cards/engraving.md"],
  "can_answer_fully": true,
  "missing_info": [],
  "draft_reply": "Hi Sarah, thanks for reaching out — happy to help with that. Yes, all Boldr FKM rubber straps are 100% BPA-free, certified to EU REACH...",
  "themes_detected": ["materials_safety"],
  "persona_hints": ["health_conscious"],
  "confidence": "high"
}
```

Rules for the output:
- `pages_read`: KB file paths you ACTUALLY used. If you didn't use a file, don't list it.
- `can_answer_fully`: true ONLY if every claim in `draft_reply` is grounded in `pages_read`.
- `missing_info`: when false, list what additional information would be needed.
- `draft_reply`: must be `null` when `can_answer_fully` is false.
- `confidence`: "high" when KB content directly answers; "med" when answer is inferred from related entries; "low" when uncertain.

If the customer's message is too vague to classify (e.g., "my watch is broken"), set `can_answer_fully` to false with `missing_info: ["clarification needed: which model, when purchased, what's happening"]` so the orchestrator can route a clarification question back to the customer.
```

- [ ] **Step 5: Run tests, expect pass**

```bash
uv run pytest tests/test_prompts.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add kb/_workflows/traversal-agent.md intel_engine/llm/prompts.py tests/test_prompts.py
git -c commit.gpgsign=false commit -m "feat: traversal agent prompt + loader (kb/_workflows pattern)"
```

---

## Task 12: Wiki-Traversal Agent Core

**Files:**
- Create: `intel_engine/agents/__init__.py`
- Create: `intel_engine/agents/traversal.py`
- Create: `tests/test_traversal_agent.py`
- Create: `tests/fixtures/sample_kb/`

**Goal:** The traversal agent: takes a `CommonEvent`, loads the KB, calls Minimax, returns a validated `TraversalResult`.

- [ ] **Step 1: Build a tiny KB fixture**

```bash
mkdir -p tests/fixtures/sample_kb/_workflows tests/fixtures/sample_kb/faqs
```

Create `tests/fixtures/sample_kb/_schema.md`:
```markdown
# Brand Voice Contract
Open with Yes/No. Use SGD for prices. No emoji.
```

Create `tests/fixtures/sample_kb/_workflows/traversal-agent.md`:
(Copy of the prompt from Task 11 — the test will use the real prompt to validate end-to-end shape.)

```bash
cp kb/_workflows/traversal-agent.md tests/fixtures/sample_kb/_workflows/traversal-agent.md
```

Create `tests/fixtures/sample_kb/faqs/bpa.md`:
```markdown
---
slug: bpa
title: Are straps BPA-free?
domain: faq
themes: [materials_safety]
sources: [faq_v3]
last_verified: 2026-05-16
---

Yes. All Boldr FKM rubber straps are 100% BPA-free.
```

- [ ] **Step 2: Write failing test**

Create `tests/test_traversal_agent.py`:
```python
"""Test wiki-traversal agent."""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.traversal import traverse
from intel_engine.schemas.event import Channel, CommonEvent, Customer
from intel_engine.schemas.traversal import Confidence, TraversalResult


@pytest.fixture
def sample_event() -> CommonEvent:
    return CommonEvent(
        event_id="evt_test",
        source=Channel.google_sheet,
        customer=Customer(id="anon_x", name="Sarah"),
        body="Are your straps BPA-free?",
        ts=datetime(2026, 5, 16, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_kb_root(monkeypatch, fixtures_dir) -> Path:
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))
    return fixtures_dir / "sample_kb"


@pytest.mark.asyncio
async def test_traverse_returns_validated_result(sample_event, sample_kb_root):
    mock_response = {
        "pages_read": ["kb/faqs/bpa.md"],
        "can_answer_fully": True,
        "missing_info": [],
        "draft_reply": "Hi Sarah, thanks for reaching out — Yes, all Boldr FKM straps are 100% BPA-free.",
        "themes_detected": ["materials_safety"],
        "persona_hints": ["health_conscious"],
        "confidence": "high",
    }
    with patch(
        "intel_engine.agents.traversal.LLMClient.complete_json",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await traverse(sample_event)

    assert isinstance(result, TraversalResult)
    assert result.can_answer_fully is True
    assert result.draft_reply is not None
    assert "BPA-free" in result.draft_reply
    assert result.confidence == Confidence.high


@pytest.mark.asyncio
async def test_traverse_handles_gap(sample_event, sample_kb_root):
    mock_response = {
        "pages_read": ["kb/faqs/bpa.md"],
        "can_answer_fully": False,
        "missing_info": ["MRI safety not in KB"],
        "draft_reply": None,
        "themes_detected": ["materials_safety"],
        "persona_hints": [],
        "confidence": "low",
    }
    with patch(
        "intel_engine.agents.traversal.LLMClient.complete_json",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await traverse(sample_event)

    assert result.can_answer_fully is False
    assert result.draft_reply is None
    assert "MRI" in result.missing_info[0]
```

- [ ] **Step 3: Run test, expect failure**

```bash
uv run pytest tests/test_traversal_agent.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 4: Create the agent**

Create `intel_engine/agents/__init__.py` (empty).

Create `intel_engine/agents/traversal.py`:
```python
"""Wiki-traversal agent."""
import json

from intel_engine.kb.reader import load_kb
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.event import CommonEvent
from intel_engine.schemas.traversal import TraversalResult
from intel_engine.settings import kb_root


def _format_kb_for_prompt(kb_path) -> str:
    """Render the entire KB into a single text block the LLM can read."""
    entries = load_kb(kb_path)
    schema_path = kb_path / "_schema.md"
    schema_text = schema_path.read_text() if schema_path.exists() else ""

    parts: list[str] = []
    if schema_text:
        parts.append("=== BRAND VOICE CONTRACT (kb/_schema.md) ===")
        parts.append(schema_text)
        parts.append("")

    parts.append(f"=== KB ENTRIES ({len(entries)} active) ===\n")
    for entry in entries:
        fm = entry.frontmatter
        # Map slug back to relative path for citation accuracy
        path_hint = f"kb/{fm.domain.value}/{fm.slug}.md"  # agent uses this in pages_read
        parts.append(f"--- {path_hint} ---")
        parts.append(f"slug: {fm.slug}")
        parts.append(f"title: {fm.title}")
        parts.append(f"domain: {fm.domain.value}")
        parts.append(f"themes: {', '.join(fm.themes)}")
        parts.append("")
        parts.append(entry.body)
        parts.append("")
    return "\n".join(parts)


async def traverse(event: CommonEvent) -> TraversalResult:
    """Run the wiki-traversal agent on a single event."""
    kb_path = kb_root()
    system_prompt = load_prompt("traversal-agent")
    kb_block = _format_kb_for_prompt(kb_path)

    user_message = (
        f"=== CUSTOMER MESSAGE ===\n"
        f"Channel: {event.source.value}\n"
        f"From: {event.customer.name}\n"
        f"Subject: {event.subject or '(none)'}\n"
        f"Body:\n{event.body}\n\n"
        f"{kb_block}"
    )

    client = LLMClient(provider=LLMProvider.minimax)
    raw = await client.complete_json(system=system_prompt, user=user_message)
    return TraversalResult.model_validate(raw)
```

- [ ] **Step 5: Run tests, expect pass**

```bash
uv run pytest tests/test_traversal_agent.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add intel_engine/agents/ tests/test_traversal_agent.py tests/fixtures/sample_kb/
git -c commit.gpgsign=false commit -m "feat: wiki-traversal agent with KB-in-context pattern"
```

---

## Task 13: KB Drafter Agent (Auto-Draft New Entry)

**Files:**
- Create: `kb/_workflows/kb-drafter-agent.md`
- Create: `intel_engine/agents/kb_drafter.py`
- Create: `tests/test_kb_drafter.py`

**Goal:** Given a gap + a human-provided resolution, the drafter produces a `KBEntry` in brand voice ready for human approval.

- [ ] **Step 1: Write the drafter prompt**

Create `kb/_workflows/kb-drafter-agent.md`:
```markdown
# KB Drafter Agent — System Prompt

You convert a (customer question + human-provided resolution) pair into a Boldr KB Markdown entry.

## Inputs

- The original customer question
- The themes detected by the traversal agent
- The text the human posted to resolve the gap (may be informal, a paste, a forwarded email)
- The brand voice contract

## Output

Return JSON:

```json
{
  "frontmatter": {
    "slug": "kebab-case-slug",
    "title": "Direct question phrasing — verbatim if possible",
    "domain": "spec | pricing | policy | faq",
    "themes": ["theme_a", "theme_b"],
    "sources": ["gap_2026-05-16_abc"],
    "last_verified": "2026-05-16",
    "supersedes": []
  },
  "body": "Polished answer in Boldr voice, grounded in the human's resolution text."
}
```

Rules:
- `domain` picks per fact type: pricing facts → `pricing`; policy/process → `policy`; product spec → `spec`; otherwise `faq`.
- `slug` derived from the question, kebab-case, ≤80 chars.
- `themes` use the same theme tags the traversal agent used.
- `sources` reference the gap ID (passed in).
- `body` follows the brand voice: open with `Yes.`/`No.` when applicable, use `SGD XX`, cite standards by exact name.
- Do NOT invent facts beyond what the human provided. If the human's resolution is too thin, return `body` starting with `[NEEDS REVIEW]` and explain in the body what's missing.
```

- [ ] **Step 2: Write failing test**

Create `tests/test_kb_drafter.py`:
```python
"""Test KB drafter agent."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from intel_engine.agents.kb_drafter import draft_kb_entry
from intel_engine.schemas.gap import Gap, GapResolution, GapStatus
from intel_engine.schemas.kb import KBDomain, KBEntry


@pytest.fixture
def sample_gap() -> Gap:
    return Gap(
        gap_id="gap_2026-05-16_mri",
        source_event_id="evt_xyz",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI compatibility not in KB"],
        themes_detected=["materials_safety"],
        status=GapStatus.resolved,
        resolution=GapResolution(
            resolved_by="sarah@boldr.sg",
            resolution_text=(
                "Boldr Grade 5 titanium watches are MRI-safe. Titanium is non-magnetic. "
                "Customers should remove leather and FKM rubber straps with metal clasps before MRI."
            ),
            resolved_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
            source_note="confirmed with manufacturer",
        ),
    )


@pytest.fixture
def sample_kb_root(monkeypatch, fixtures_dir):
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))


@pytest.mark.asyncio
async def test_draft_kb_entry_returns_valid_entry(sample_gap, sample_kb_root):
    mock_response = {
        "frontmatter": {
            "slug": "are-boldr-watches-mri-safe",
            "title": "Are Boldr watches MRI-safe?",
            "domain": "spec",
            "themes": ["materials_safety"],
            "sources": ["gap_2026-05-16_mri"],
            "last_verified": "2026-05-16",
            "supersedes": [],
        },
        "body": (
            "Yes. Boldr Grade 5 titanium watches are MRI-safe. "
            "Titanium is non-magnetic. We recommend removing leather or FKM straps "
            "with metal clasps before an MRI procedure."
        ),
    }
    with patch(
        "intel_engine.agents.kb_drafter.LLMClient.complete_json",
        new=AsyncMock(return_value=mock_response),
    ):
        entry = await draft_kb_entry(sample_gap)

    assert isinstance(entry, KBEntry)
    assert entry.frontmatter.slug == "are-boldr-watches-mri-safe"
    assert entry.frontmatter.domain == KBDomain.spec
    assert "titanium" in entry.body.lower()


@pytest.mark.asyncio
async def test_draft_kb_entry_raises_if_no_resolution(sample_kb_root):
    from intel_engine.schemas.gap import Gap
    gap = Gap(
        gap_id="gap_test",
        source_event_id="evt_test",
        customer_question="Q?",
        missing_info=["unknown"],
    )
    with pytest.raises(ValueError, match="resolution"):
        await draft_kb_entry(gap)
```

- [ ] **Step 3: Run test, expect failure**

```bash
uv run pytest tests/test_kb_drafter.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 4: Create the drafter**

Create `intel_engine/agents/kb_drafter.py`:
```python
"""KB Drafter agent — converts a resolved gap into a KB entry."""
from intel_engine.llm.client import LLMClient, LLMProvider
from intel_engine.llm.prompts import load_prompt
from intel_engine.schemas.gap import Gap
from intel_engine.schemas.kb import KBEntry, KBFrontmatter


async def draft_kb_entry(gap: Gap) -> KBEntry:
    if gap.resolution is None:
        raise ValueError("Cannot draft KB entry: gap has no resolution")

    system_prompt = load_prompt("kb-drafter-agent")

    schema_text = ""
    from intel_engine.settings import kb_root
    schema_path = kb_root() / "_schema.md"
    if schema_path.exists():
        schema_text = schema_path.read_text()

    user_message = (
        f"=== BRAND VOICE CONTRACT ===\n{schema_text}\n\n"
        f"=== CUSTOMER QUESTION ===\n{gap.customer_question}\n\n"
        f"=== THEMES DETECTED ===\n{', '.join(gap.themes_detected)}\n\n"
        f"=== HUMAN RESOLUTION ===\n{gap.resolution.resolution_text}\n\n"
        f"=== SOURCE NOTE ===\n{gap.resolution.source_note or '(none)'}\n\n"
        f"=== GAP ID (for sources field) ===\n{gap.gap_id}\n"
    )

    client = LLMClient(provider=LLMProvider.minimax)
    raw = await client.complete_json(system=system_prompt, user=user_message)
    return KBEntry(
        frontmatter=KBFrontmatter.model_validate(raw["frontmatter"]),
        body=raw["body"],
    )
```

- [ ] **Step 5: Run tests, expect pass**

```bash
uv run pytest tests/test_kb_drafter.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add kb/_workflows/kb-drafter-agent.md intel_engine/agents/kb_drafter.py tests/test_kb_drafter.py
git -c commit.gpgsign=false commit -m "feat: KB drafter agent for auto-drafting entries from resolved gaps"
```

---

## Task 14: KB Writer + Git Auto-Commit

**Files:**
- Create: `intel_engine/kb/writer.py`
- Create: `tests/test_kb_writer.py`

**Goal:** Function that writes a `KBEntry` to disk under `kb/<domain>/<slug>.md`, regenerates `kb/index.md`, and commits the change with a descriptive message.

- [ ] **Step 1: Write failing test**

Create `tests/test_kb_writer.py`:
```python
"""Test KB writer + git auto-commit."""
import subprocess
from datetime import date
from pathlib import Path

import pytest

from intel_engine.kb.writer import write_and_commit_entry
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch) -> Path:
    """Create a fresh git repo at tmp_path with kb/ structure."""
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Test Bot")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@test.local")

    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test Bot"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.local"], cwd=tmp_path, check=True
    )
    # Initial commit so HEAD exists
    (tmp_path / "README.md").write_text("# Test repo")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path


def test_write_and_commit_writes_entry_to_correct_path(git_repo: Path):
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="test-entry",
            title="Test entry",
            domain=KBDomain.faq,
            themes=["test"],
            sources=["test-source"],
            last_verified=date(2026, 5, 16),
        ),
        body="Test body.",
    )
    sha = write_and_commit_entry(
        entry,
        approver="sarah@boldr.sg",
        repo_root=git_repo,
    )
    expected_path = git_repo / "kb" / "faq" / "test-entry.md"
    assert expected_path.exists()
    assert "test body" in expected_path.read_text().lower()
    assert len(sha) >= 7  # short SHA


def test_write_and_commit_includes_approver_in_commit_message(git_repo: Path):
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="test2",
            title="T2",
            domain=KBDomain.faq,
            themes=[],
            sources=[],
            last_verified=date(2026, 5, 16),
        ),
        body="body",
    )
    write_and_commit_entry(entry, approver="alice@boldr.sg", repo_root=git_repo)
    log = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=git_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "alice@boldr.sg" in log
    assert "kb: add" in log or "kb: update" in log


def test_write_and_commit_regenerates_index(git_repo: Path):
    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="indexed",
            title="Indexed entry",
            domain=KBDomain.faq,
            themes=["x"],
            sources=[],
            last_verified=date(2026, 5, 16),
        ),
        body="body",
    )
    write_and_commit_entry(entry, approver="x@x.com", repo_root=git_repo)
    index_path = git_repo / "kb" / "index.md"
    assert index_path.exists()
    assert "indexed" in index_path.read_text()
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_kb_writer.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create the writer**

Create `intel_engine/kb/writer.py`:
```python
"""Write KB entries and commit to git."""
import os
import subprocess
from pathlib import Path

from intel_engine.schemas.kb import KBEntry
from intel_engine.settings import kb_root


def _regenerate_index(kb_path: Path) -> None:
    from scripts.generate_index import generate_index
    generate_index(kb_path, kb_path / "index.md")


def write_and_commit_entry(
    entry: KBEntry,
    approver: str,
    repo_root: Path | None = None,
    commit_subject_prefix: str = "kb: add",
) -> str:
    """Write entry to kb/<domain>/<slug>.md, regen index, commit.

    Returns the short SHA of the new commit.
    """
    if repo_root is None:
        repo_root = kb_root().parent
    kb_dir = repo_root / "kb"

    domain_dir = kb_dir / entry.frontmatter.domain.value
    domain_dir.mkdir(parents=True, exist_ok=True)
    entry_path = domain_dir / f"{entry.frontmatter.slug}.md"

    is_update = entry_path.exists()
    entry_path.write_text(entry.to_markdown())

    _regenerate_index(kb_dir)

    subject_verb = "update" if is_update else "add"
    commit_msg = (
        f"kb: {subject_verb} {entry.frontmatter.slug}\n\n"
        f"Title: {entry.frontmatter.title}\n"
        f"Domain: {entry.frontmatter.domain.value}\n"
        f"Themes: {', '.join(entry.frontmatter.themes) or '(none)'}\n"
        f"Sources: {', '.join(entry.frontmatter.sources) or '(none)'}\n"
        f"\n"
        f"Approved by: {approver}\n"
    )

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = os.environ.get("GIT_AUTHOR_NAME", "Intel Engine")
    env["GIT_AUTHOR_EMAIL"] = os.environ.get("GIT_AUTHOR_EMAIL", "intel-engine@local")
    env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
    env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]

    subprocess.run(
        ["git", "add", str(entry_path.relative_to(repo_root)), "kb/index.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", commit_msg],
        cwd=repo_root,
        check=True,
        capture_output=True,
        env=env,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return sha
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_kb_writer.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add intel_engine/kb/writer.py tests/test_kb_writer.py
git -c commit.gpgsign=false commit -m "feat: KB writer with git auto-commit and index regeneration"
```

---

## Task 15: Gap Logger

**Files:**
- Create: `intel_engine/gap/__init__.py`
- Create: `intel_engine/gap/logger.py`
- Create: `tests/test_gap_logger.py`

**Goal:** Persist gap entries to `gap-log/YYYY-MM-DD-<slug>.md`, support reading them back for resolution.

- [ ] **Step 1: Write failing test**

Create `tests/test_gap_logger.py`:
```python
"""Test gap logger."""
from datetime import datetime, timezone
from pathlib import Path

from intel_engine.gap.logger import load_gap, write_gap
from intel_engine.schemas.gap import Gap, GapStatus


def test_write_gap_creates_file(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))

    gap = Gap(
        gap_id="gap_2026-05-16_mri",
        source_event_id="evt_xyz",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI compatibility unknown"],
        themes_detected=["materials_safety"],
        created_at=datetime(2026, 5, 16, 14, 23, tzinfo=timezone.utc),
    )
    path = write_gap(gap)
    assert path.exists()
    assert path.name == "gap_2026-05-16_mri.md"


def test_load_gap_round_trip(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))

    gap = Gap(
        gap_id="gap_test",
        source_event_id="evt_test",
        customer_question="Q?",
        missing_info=["m1", "m2"],
        themes_detected=["t1"],
    )
    write_gap(gap)
    loaded = load_gap("gap_test")
    assert loaded.customer_question == "Q?"
    assert loaded.missing_info == ["m1", "m2"]
    assert loaded.status == GapStatus.open
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_gap_logger.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create the logger**

Create `intel_engine/gap/__init__.py` (empty).

Create `intel_engine/gap/logger.py`:
```python
"""Persist gap entries to disk."""
import json
from pathlib import Path

from intel_engine.schemas.gap import Gap
from intel_engine.settings import gap_log_root


def write_gap(gap: Gap) -> Path:
    """Serialise gap to JSON-in-Markdown under GAP_LOG_ROOT."""
    root = gap_log_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{gap.gap_id}.md"
    payload = gap.model_dump_json(indent=2)
    content = (
        f"# Gap: {gap.customer_question}\n\n"
        f"```json\n{payload}\n```\n"
    )
    path.write_text(content)
    return path


def load_gap(gap_id: str) -> Gap:
    """Read a gap by id."""
    path = gap_log_root() / f"{gap_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"Gap not found: {gap_id}")
    text = path.read_text()
    # Extract the JSON block between ``` markers
    start = text.find("```json\n") + len("```json\n")
    end = text.find("\n```", start)
    payload = text[start:end]
    return Gap.model_validate_json(payload)


def update_gap(gap: Gap) -> Path:
    """Re-write an existing gap (e.g., after status change)."""
    return write_gap(gap)
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_gap_logger.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add intel_engine/gap/ tests/test_gap_logger.py
git -c commit.gpgsign=false commit -m "feat: gap logger for persistent open/resolved gap tracking"
```

---

## Task 16: FastAPI Service — Skeleton + Settings Endpoint

**Files:**
- Create: `intel_engine/api.py`
- Create: `tests/test_api.py`

**Goal:** Boot a FastAPI service with a healthcheck. This is the surface n8n calls.

- [ ] **Step 1: Write failing test**

Create `tests/test_api.py`:
```python
"""Test FastAPI service."""
import pytest
from httpx import ASGITransport, AsyncClient

from intel_engine.api import app


@pytest.mark.asyncio
async def test_healthcheck():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_api.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create the service**

Create `intel_engine/api.py`:
```python
"""FastAPI service exposing intel engine endpoints to n8n."""
from fastapi import FastAPI

app = FastAPI(title="Boldr Intel Engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run test, expect pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Smoke-run the server manually**

```bash
uv run uvicorn intel_engine.api:app --reload --port 8000 &
sleep 2
curl -s http://localhost:8000/health
kill %1
```

Expected: `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add intel_engine/api.py tests/test_api.py
git -c commit.gpgsign=false commit -m "feat: FastAPI service skeleton with /health"
```

---

## Task 17: API — /traverse endpoint

**Files:**
- Modify: `intel_engine/api.py`
- Modify: `tests/test_api.py`

**Goal:** Expose the traversal agent over HTTP. Input: `CommonEvent`. Output: `TraversalResult`.

- [ ] **Step 1: Append failing test**

Append to `tests/test_api.py`:
```python
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from intel_engine.schemas.traversal import Confidence, TraversalResult


@pytest.mark.asyncio
async def test_traverse_endpoint(fixtures_dir, monkeypatch):
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))

    mock_result = TraversalResult(
        pages_read=["kb/faqs/bpa.md"],
        can_answer_fully=True,
        missing_info=[],
        draft_reply="Yes, all our straps are BPA-free.",
        themes_detected=["materials_safety"],
        persona_hints=["health_conscious"],
        confidence=Confidence.high,
    )

    event_payload = {
        "event_id": "evt_test",
        "source": "google_sheet",
        "customer": {"id": "c1", "name": "Sarah"},
        "body": "BPA-free?",
        "ts": datetime(2026, 5, 16, tzinfo=timezone.utc).isoformat(),
    }

    with patch(
        "intel_engine.api.traverse",
        new=AsyncMock(return_value=mock_result),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/traverse", json=event_payload)

    assert r.status_code == 200
    body = r.json()
    assert body["can_answer_fully"] is True
    assert body["confidence"] == "high"
```

- [ ] **Step 2: Run test, expect failure**

```bash
uv run pytest tests/test_api.py::test_traverse_endpoint -v
```

Expected: `404 Not Found` or `AttributeError`.

- [ ] **Step 3: Add endpoint**

Replace `intel_engine/api.py`:
```python
"""FastAPI service exposing intel engine endpoints to n8n."""
from fastapi import FastAPI, HTTPException

from intel_engine.agents.traversal import traverse
from intel_engine.schemas.event import CommonEvent
from intel_engine.schemas.traversal import TraversalResult

app = FastAPI(title="Boldr Intel Engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/traverse", response_model=TraversalResult)
async def traverse_endpoint(event: CommonEvent) -> TraversalResult:
    try:
        return await traverse(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Traversal failed: {e}") from e
```

- [ ] **Step 4: Run test, expect pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add intel_engine/api.py tests/test_api.py
git -c commit.gpgsign=false commit -m "feat: /traverse endpoint wiring agent into HTTP service"
```

---

## Task 18: API — /gap, /draft-kb-entry, /commit-to-kb

**Files:**
- Modify: `intel_engine/api.py`
- Modify: `tests/test_api.py`

**Goal:** Three more endpoints completing the loop API surface.

- [ ] **Step 1: Append failing tests**

Append to `tests/test_api.py`:
```python
from datetime import date
from unittest.mock import patch

from intel_engine.schemas.gap import Gap, GapResolution, GapStatus
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter


@pytest.mark.asyncio
async def test_create_gap_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))

    payload = {
        "source_event_id": "evt_xyz",
        "customer_question": "Are Boldr watches MRI-safe?",
        "missing_info": ["MRI compatibility unknown"],
        "themes_detected": ["materials_safety"],
        "persona_hints": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/gap", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "open"
    assert body["gap_id"].startswith("gap_")


@pytest.mark.asyncio
async def test_draft_kb_entry_endpoint(monkeypatch, tmp_path, fixtures_dir):
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path))
    monkeypatch.setenv("KB_ROOT", str(fixtures_dir / "sample_kb"))

    # Pre-write a resolved gap
    from intel_engine.gap.logger import write_gap
    gap = Gap(
        gap_id="gap_resolve",
        source_event_id="evt_a",
        customer_question="Are Boldr watches MRI-safe?",
        missing_info=["MRI"],
        themes_detected=["materials_safety"],
        status=GapStatus.resolved,
        resolution=GapResolution(
            resolved_by="sarah@b.com",
            resolution_text="Titanium is non-magnetic; watches are MRI-safe.",
            resolved_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        ),
    )
    write_gap(gap)

    mock_entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="mri-safe",
            title="MRI-safe?",
            domain=KBDomain.spec,
            themes=["materials_safety"],
            sources=["gap_resolve"],
            last_verified=date(2026, 5, 16),
        ),
        body="Yes. Titanium is non-magnetic.",
    )
    with patch(
        "intel_engine.api.draft_kb_entry",
        new=AsyncMock(return_value=mock_entry),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post("/draft-kb-entry", json={"gap_id": "gap_resolve"})

    assert r.status_code == 200
    body = r.json()
    assert body["frontmatter"]["slug"] == "mri-safe"
    assert body["frontmatter"]["domain"] == "spec"
```

- [ ] **Step 2: Run tests, expect failure**

```bash
uv run pytest tests/test_api.py -v -k "gap or draft_kb"
```

Expected: `404` errors.

- [ ] **Step 3: Add endpoints**

Replace `intel_engine/api.py`:
```python
"""FastAPI service exposing intel engine endpoints to n8n."""
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from intel_engine.agents.kb_drafter import draft_kb_entry
from intel_engine.agents.traversal import traverse
from intel_engine.gap.logger import load_gap, write_gap
from intel_engine.kb.writer import write_and_commit_entry
from intel_engine.schemas.event import CommonEvent
from intel_engine.schemas.gap import Gap, GapResolution, GapStatus
from intel_engine.schemas.kb import KBEntry, KBFrontmatter
from intel_engine.schemas.traversal import TraversalResult

app = FastAPI(title="Boldr Intel Engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/traverse", response_model=TraversalResult)
async def traverse_endpoint(event: CommonEvent) -> TraversalResult:
    try:
        return await traverse(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Traversal failed: {e}") from e


class GapCreateRequest(BaseModel):
    source_event_id: str
    customer_question: str
    missing_info: list[str]
    themes_detected: list[str] = []
    persona_hints: list[str] = []


@app.post("/gap", response_model=Gap)
async def create_gap(payload: GapCreateRequest) -> Gap:
    today = datetime.now(timezone.utc).date()
    gap_id = f"gap_{today.isoformat()}_{secrets.token_hex(3)}"
    gap = Gap(
        gap_id=gap_id,
        source_event_id=payload.source_event_id,
        customer_question=payload.customer_question,
        missing_info=payload.missing_info,
        themes_detected=payload.themes_detected,
        persona_hints=payload.persona_hints,
    )
    write_gap(gap)
    return gap


class GapResolveRequest(BaseModel):
    gap_id: str
    resolved_by: str
    resolution_text: str
    source_note: str | None = None


@app.post("/gap/resolve", response_model=Gap)
async def resolve_gap(payload: GapResolveRequest) -> Gap:
    gap = load_gap(payload.gap_id)
    gap.status = GapStatus.resolved
    gap.resolution = GapResolution(
        resolved_by=payload.resolved_by,
        resolution_text=payload.resolution_text,
        resolved_at=datetime.now(timezone.utc),
        source_note=payload.source_note,
    )
    write_gap(gap)
    return gap


class DraftRequest(BaseModel):
    gap_id: str


@app.post("/draft-kb-entry", response_model=KBEntry)
async def draft_endpoint(payload: DraftRequest) -> KBEntry:
    gap = load_gap(payload.gap_id)
    if gap.resolution is None:
        raise HTTPException(status_code=400, detail="Gap is not resolved yet")
    try:
        return await draft_kb_entry(gap)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft failed: {e}") from e


class CommitRequest(BaseModel):
    entry: KBEntry
    approver: str
    gap_id: str | None = None


class CommitResponse(BaseModel):
    sha: str
    path: str


@app.post("/commit-to-kb", response_model=CommitResponse)
async def commit_endpoint(payload: CommitRequest) -> CommitResponse:
    from intel_engine.settings import kb_root
    repo_root = kb_root().parent
    try:
        sha = write_and_commit_entry(
            payload.entry,
            approver=payload.approver,
            repo_root=repo_root,
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Git commit failed: {e.stderr.decode() if e.stderr else e}",
        ) from e

    rel_path = (
        Path("kb") / payload.entry.frontmatter.domain.value /
        f"{payload.entry.frontmatter.slug}.md"
    )
    # Update gap status if linked
    if payload.gap_id:
        gap = load_gap(payload.gap_id)
        gap.drafted_kb_slug = payload.entry.frontmatter.slug
        write_gap(gap)

    return CommitResponse(sha=sha, path=str(rel_path))
```

- [ ] **Step 4: Run tests, expect pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add intel_engine/api.py tests/test_api.py
git -c commit.gpgsign=false commit -m "feat: /gap, /draft-kb-entry, /commit-to-kb endpoints"
```

---

## Task 19: Docker Compose for n8n

**Files:**
- Create: `docker-compose.yml`
- Create: `workflows/n8n/.gitkeep`

**Goal:** Spin up n8n locally with persistent storage; ensure it can reach the host's FastAPI service.

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=Asia/Singapore
      - N8N_DIAGNOSTICS_ENABLED=false
      - N8N_SECURE_COOKIE=false
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./.n8n_data:/home/node/.n8n
      - ./workflows/n8n:/workflows
```

- [ ] **Step 2: Create workflows directory placeholder**

```bash
mkdir -p workflows/n8n
touch workflows/n8n/.gitkeep
```

Add to `.gitignore`:
```
.n8n_data/
```

- [ ] **Step 3: Boot n8n and verify**

```bash
docker compose up -d
sleep 10
curl -sI http://localhost:5678/ | head -1
```

Expected: `HTTP/1.1 200 OK` or `HTTP/1.1 301 Moved Permanently`.

- [ ] **Step 4: Smoke-test that n8n can reach FastAPI**

In a separate terminal:
```bash
uv run uvicorn intel_engine.api:app --host 0.0.0.0 --port 8000 &
```

Then in the n8n container (via docker exec or test from inside n8n's HTTP node later), the URL `http://host.docker.internal:8000/health` should return `{"status":"ok"}`.

```bash
docker compose exec n8n wget -qO- http://host.docker.internal:8000/health
```

Expected: `{"status":"ok"}`.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml workflows/n8n/.gitkeep .gitignore
git -c commit.gpgsign=false commit -m "feat: docker-compose for self-hosted n8n with FastAPI bridge"
```

---

## Task 20: n8n Workflow — Intake + Traversal

**Files:**
- Create: `workflows/n8n/01_intake_and_traversal.json`
- Create: `docs/N8N_SETUP.md`

**Goal:** n8n workflow that fires on Google Sheet row append, normalises to `CommonEvent`, calls `/traverse`, branches on `can_answer_fully`. The Gmail Drafts node + Slack interactive cards are added in Task 21.

This task is **less TDD-heavy** because n8n workflows are JSON configurations, not testable Python. Verification is manual via the n8n UI.

- [ ] **Step 1: Build workflow in n8n UI**

Open `http://localhost:5678` in a browser. Create a new workflow named "01 — Intake and Traversal".

Add nodes in order:

1. **Google Sheets Trigger**
   - Operation: On row append
   - Document: (link to your Google Sheet — created in Task 5b below)
   - Sheet: `tickets_input`
   - Mode: Poll every 1 minute (for demo) or webhook

2. **Function** (rename: "Normalise to CommonEvent")
   - JavaScript:
     ```javascript
     const row = $input.first().json;
     return [{
       json: {
         event_id: `evt_${row.ticket_id}_${Date.now()}`,
         source: "google_sheet",
         channel_meta: { row_index: row.__row_number || 0 },
         customer: { id: `anon_${row.ticket_id}`, name: row.customer_name },
         subject: row.subject || null,
         body: row.body,
         ts: row.received_at || new Date().toISOString(),
         attachments: []
       }
     }];
     ```

3. **HTTP Request** (rename: "POST /traverse")
   - Method: POST
   - URL: `http://host.docker.internal:8000/traverse`
   - Body: JSON, expression `={{ JSON.stringify($json) }}`
   - Headers: `Content-Type: application/json`
   - Response: Parse JSON

4. **IF** (rename: "answerable?")
   - Condition: `={{ $json.can_answer_fully }}` equals `true`
   - True branch: feeds Task 21 (Gmail Drafts) — leave empty for now
   - False branch: feeds Task 21 (Gap creation) — leave empty for now

5. Save the workflow. Activate it.

- [ ] **Step 2: Create the demo Google Sheet**

Manually:
1. Go to https://sheets.google.com → new sheet
2. Name it: `Boldr Demo Tickets`
3. Tab 1: rename to `tickets_input`
4. Tab 2: rename to `eval_labels`
5. In Tab 1, paste the contents of `eval/data/tickets_input.csv`
6. In Tab 2, paste `eval/data/eval_labels.csv`
7. Share the sheet with the service account email that n8n's Google Sheets credential uses

Document this in `docs/N8N_SETUP.md`.

- [ ] **Step 3: Export workflow JSON**

In n8n UI → Workflow → ⋯ menu → Download → save as `workflows/n8n/01_intake_and_traversal.json`.

- [ ] **Step 4: Write `docs/N8N_SETUP.md`**

```markdown
# n8n Setup Guide

## Prerequisites

- Docker + Docker Compose
- Google account (for Sheet)
- Slack workspace (for approvals)
- Gmail account (for Drafts)

## Initial Setup

1. `docker compose up -d`
2. Open http://localhost:5678 and complete the n8n onboarding (set a local password)
3. Settings → Credentials → add:
   - **Google Sheets OAuth2** (n8n provides the OAuth flow)
   - **Gmail OAuth2** (same)
   - **Slack Bot** (paste your bot user OAuth token)
   - **GitHub** (personal access token with `repo` scope)

## Workflow Import

For each file in `workflows/n8n/*.json`:
1. Workflows → Import → upload the JSON
2. Open the workflow and verify all credentials are reattached
3. Activate

## Demo Google Sheet

- Sheet name: `Boldr Demo Tickets`
- Tab `tickets_input`: import `eval/data/tickets_input.csv`
- Tab `eval_labels`: import `eval/data/eval_labels.csv` (held-out, agent never sees)
- Share with the email of the Google credential used by n8n

## FastAPI Service

n8n containers reach the host's FastAPI service at `http://host.docker.internal:8000`. Always start it via:

```bash
uv run uvicorn intel_engine.api:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

- If Google Sheets trigger fails: re-auth the credential
- If HTTP node returns 500: check FastAPI logs
- If n8n container can't reach host: ensure `extra_hosts` is set in docker-compose.yml
```

- [ ] **Step 5: Smoke-test by appending a row to the Sheet**

Add a new row to `tickets_input` with body "Are Boldr watches BPA-free?"

Open n8n → Workflow 01 → Executions tab. You should see a successful execution with the traverse output.

- [ ] **Step 6: Commit**

```bash
git add workflows/n8n/01_intake_and_traversal.json docs/N8N_SETUP.md
git -c commit.gpgsign=false commit -m "feat: n8n intake workflow with Google Sheet trigger and /traverse call"
```

---

## Task 21: n8n Workflow — Answerable Branch (Gmail Drafts)

**Files:**
- Modify: `workflows/n8n/01_intake_and_traversal.json` (in n8n UI)

**Goal:** When `can_answer_fully=true`, create a draft in Gmail Drafts for the CS team to send.

- [ ] **Step 1: Add Gmail node to True branch of the IF**

In n8n UI → Workflow 01 → on the True output of the "answerable?" IF node, add:

**Gmail node** (rename: "Create Gmail Draft")
- Operation: Create draft
- To: `={{ $('Normalise to CommonEvent').item.json.customer.name }} <{{ $('Google Sheets Trigger').item.json.customer_email }}>` (adapt to whatever email column exists; for dummy data, generate a placeholder `customer@example.com`)
- Subject: `Re: {{ $('Normalise to CommonEvent').item.json.subject || 'Your enquiry' }}`
- Message: `={{ $('POST /traverse').item.json.draft_reply }}`
- Label: `agent-drafts` (create this label in Gmail first)

- [ ] **Step 2: Save and re-export**

Download → overwrite `workflows/n8n/01_intake_and_traversal.json`.

- [ ] **Step 3: Smoke-test**

Add a new row to the Sheet with an answerable question. Verify a draft appears in Gmail Drafts.

- [ ] **Step 4: Commit**

```bash
git add workflows/n8n/01_intake_and_traversal.json
git -c commit.gpgsign=false commit -m "feat: answerable branch creates Gmail draft for CS approval"
```

---

## Task 22: n8n Workflow — Gap Branch (Slack Interactive)

**Files:**
- Create: `workflows/n8n/02_gap_resolution.json` (in n8n UI)

**Goal:** When traversal returns `can_answer_fully=false`, create a gap entry via API and post a Slack interactive message with a "Resolve" button that opens a modal. On submission, gap is marked resolved and KB entry is drafted.

- [ ] **Step 1: In Workflow 01, add the False branch**

To the False output of the "answerable?" IF node, add:

**HTTP Request** (rename: "POST /gap")
- Method: POST
- URL: `http://host.docker.internal:8000/gap`
- Body (JSON, expression):
  ```javascript
  ={{ JSON.stringify({
    source_event_id: $('Normalise to CommonEvent').item.json.event_id,
    customer_question: $('Normalise to CommonEvent').item.json.body,
    missing_info: $('POST /traverse').item.json.missing_info,
    themes_detected: $('POST /traverse').item.json.themes_detected,
    persona_hints: $('POST /traverse').item.json.persona_hints
  }) }}
  ```

**Slack node** (rename: "Post Slack Gap Card")
- Operation: Post message
- Channel: `={{ $env.SLACK_APPROVAL_CHANNEL }}`
- Text: `New knowledge gap — please resolve`
- Blocks (JSON):
  ```json
  [
    { "type": "header", "text": { "type": "plain_text", "text": "🚨 New Knowledge Gap" } },
    { "type": "section", "text": { "type": "mrkdwn", "text": "*Customer question:*\n> {{$('POST /gap').item.json.customer_question}}" } },
    { "type": "section", "text": { "type": "mrkdwn", "text": "*Missing info:*\n• {{$('POST /gap').item.json.missing_info.join('\\n• ')}}" } },
    { "type": "actions", "elements": [
      { "type": "button", "text": { "type": "plain_text", "text": "Resolve this gap" }, "style": "primary", "action_id": "resolve_gap", "value": "{{$('POST /gap').item.json.gap_id}}" }
    ]}
  ]
  ```

- [ ] **Step 2: Create Workflow 02 — Gap Resolution Handler**

New workflow "02 — Gap Resolution Handler".

Add nodes:

1. **Webhook** (rename: "Slack interactivity webhook")
   - HTTP Method: POST
   - Path: `slack-interactivity`
   - Response: "Respond immediately" with `{"ok": true}`

2. **Function** (rename: "Parse Slack payload")
   - JavaScript:
     ```javascript
     const payload = JSON.parse($input.first().json.body.payload);
     // Slack sends form-encoded; if it's already parsed, adapt
     return [{ json: payload }];
     ```

3. **IF** (rename: "type?")
   - Branch on `={{ $json.type }}`:
     - `block_actions` → open modal for resolution
     - `view_submission` → process modal submission

4. **(block_actions branch) Slack — Open Modal**
   - Operation: Open view
   - Trigger ID: `={{ $json.trigger_id }}`
   - View (JSON):
     ```json
     {
       "type": "modal",
       "callback_id": "resolve_gap_modal",
       "private_metadata": "{{$json.actions[0].value}}",
       "title": { "type": "plain_text", "text": "Resolve Gap" },
       "submit": { "type": "plain_text", "text": "Submit & Draft KB Entry" },
       "blocks": [
         { "type": "input", "block_id": "resolution", "label": { "type": "plain_text", "text": "How would you answer this?" }, "element": { "type": "plain_text_input", "action_id": "text", "multiline": true } },
         { "type": "input", "block_id": "source", "optional": true, "label": { "type": "plain_text", "text": "Source (e.g., 'vendor email', 'internal team')" }, "element": { "type": "plain_text_input", "action_id": "text" } }
       ]
     }
     ```

5. **(view_submission branch) HTTP — POST /gap/resolve**
   - URL: `http://host.docker.internal:8000/gap/resolve`
   - Body:
     ```javascript
     ={{ JSON.stringify({
       gap_id: $json.view.private_metadata,
       resolved_by: $json.user.username,
       resolution_text: $json.view.state.values.resolution.text.value,
       source_note: $json.view.state.values.source?.text?.value || null
     }) }}
     ```

6. **HTTP — POST /draft-kb-entry**
   - URL: `http://host.docker.internal:8000/draft-kb-entry`
   - Body: `={{ JSON.stringify({ gap_id: $('Parse Slack payload').item.json.view.private_metadata }) }}`

7. **Slack — Post draft for approval**
   - Channel: same as before
   - Blocks:
     ```json
     [
       { "type": "header", "text": { "type": "plain_text", "text": "📝 KB entry drafted — please approve" } },
       { "type": "section", "text": { "type": "mrkdwn", "text": "*Title:* {{$('POST /draft-kb-entry').item.json.frontmatter.title}}" } },
       { "type": "section", "text": { "type": "mrkdwn", "text": "*Domain:* `{{$('POST /draft-kb-entry').item.json.frontmatter.domain}}`" } },
       { "type": "section", "text": { "type": "mrkdwn", "text": "```\n{{$('POST /draft-kb-entry').item.json.body}}\n```" } },
       { "type": "actions", "elements": [
         { "type": "button", "text": { "type": "plain_text", "text": "Approve & Commit" }, "style": "primary", "action_id": "approve_kb", "value": "{{$('POST /draft-kb-entry').item.json.frontmatter.slug}}" },
         { "type": "button", "text": { "type": "plain_text", "text": "Reject" }, "style": "danger", "action_id": "reject_kb", "value": "{{$('POST /draft-kb-entry').item.json.frontmatter.slug}}" }
       ]}
     ]
     ```

The state for the second approval (passing the drafted KBEntry into the approve handler) requires storing it temporarily — the simplest approach is to encode it in Slack message metadata or stash via Slack's `private_metadata`. For this MVP we serialize the entire entry JSON into the button's `value` field (Slack allows up to 2000 chars).

- [ ] **Step 3: Configure Slack app**

Outside n8n: in api.slack.com, configure your bot's "Interactivity & Shortcuts" → Request URL: `http://<your-tunneled-url>/webhook/slack-interactivity` (use ngrok for local dev).

- [ ] **Step 4: Smoke-test**

Add an unanswerable ticket to the Sheet. Verify:
1. Gap card appears in Slack
2. Clicking "Resolve" opens a modal
3. Submitting modal → draft KB entry card appears
4. Clicking "Approve" → next task

- [ ] **Step 5: Export workflow**

Download Workflow 02 as `workflows/n8n/02_gap_resolution.json`.

- [ ] **Step 6: Commit**

```bash
git add workflows/n8n/01_intake_and_traversal.json workflows/n8n/02_gap_resolution.json
git -c commit.gpgsign=false commit -m "feat: gap branch + Slack interactive resolution + draft KB entry"
```

---

## Task 23: n8n Workflow — KB Approval → Git Commit

**Files:**
- Create: `workflows/n8n/03_kb_approval.json` (in n8n UI)

**Goal:** When the user clicks "Approve & Commit", call `/commit-to-kb` and reply in Slack with the commit SHA.

- [ ] **Step 1: Extend Workflow 02 to handle `approve_kb` action**

In the IF branching on `type`, add another branch for `block_actions` where `actions[0].action_id == "approve_kb"`:

**HTTP — POST /commit-to-kb**
- URL: `http://host.docker.internal:8000/commit-to-kb`
- Body: payload from the button value (the full KBEntry JSON). The simplest robust approach is to re-fetch the gap, re-call /draft-kb-entry to reproduce the entry, and commit — this avoids the Slack 2000-char limit.

A cleaner pattern: in the previous step, after `/draft-kb-entry`, also save the entry to a small intermediate store (e.g., `kb-drafts/<gap_id>.json`). Then on approve, read that file and POST it.

Add an endpoint `/save-draft` and `/load-draft` to the FastAPI service for this. (See Step 2 below.)

- [ ] **Step 2: Add draft-staging endpoints to the API**

Append to `intel_engine/api.py`:
```python
DRAFT_STAGE_DIR = Path("./kb-drafts-staging")


class StageDraftRequest(BaseModel):
    gap_id: str
    entry: KBEntry


@app.post("/draft/stage")
async def stage_draft(payload: StageDraftRequest) -> dict[str, str]:
    DRAFT_STAGE_DIR.mkdir(exist_ok=True)
    (DRAFT_STAGE_DIR / f"{payload.gap_id}.json").write_text(payload.entry.model_dump_json(indent=2))
    return {"status": "staged"}


@app.get("/draft/staged/{gap_id}", response_model=KBEntry)
async def get_staged_draft(gap_id: str) -> KBEntry:
    path = DRAFT_STAGE_DIR / f"{gap_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No staged draft")
    return KBEntry.model_validate_json(path.read_text())
```

Append a test in `tests/test_api.py`:
```python
@pytest.mark.asyncio
async def test_stage_and_load_draft(monkeypatch, tmp_path):
    # Cheat: monkeypatch the global path
    import intel_engine.api as api_mod
    monkeypatch.setattr(api_mod, "DRAFT_STAGE_DIR", tmp_path)

    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="t", title="T", domain=KBDomain.faq, themes=[], sources=[],
            last_verified=date(2026, 5, 16),
        ),
        body="b",
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/draft/stage", json={"gap_id": "g1", "entry": entry.model_dump(mode="json")})
        assert r.status_code == 200
        r2 = await ac.get("/draft/staged/g1")
        assert r2.status_code == 200
        assert r2.json()["frontmatter"]["slug"] == "t"
```

- [ ] **Step 3: Run tests, expect pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: all tests pass.

Add `kb-drafts-staging/` to `.gitignore`:
```
kb-drafts-staging/
```

- [ ] **Step 4: Update Workflow 02 to stage drafts**

After `/draft-kb-entry`, add:
**HTTP — POST /draft/stage** — body: `{"gap_id": "{{...}}", "entry": {{...drafted entry...}}}`.

The Slack approve button's `value` becomes just the `gap_id`.

- [ ] **Step 5: Wire approve handler in Workflow 02**

For the `approve_kb` action branch:
1. **HTTP — GET /draft/staged/{gap_id}**
2. **HTTP — POST /commit-to-kb** with `{ entry: <step 1 result>, approver: <slack user>, gap_id: <gap_id> }`
3. **Slack — Reply** to the original message: `✅ Committed as kb/<domain>/<slug>.md (SHA: <sha>)`

- [ ] **Step 6: Export workflows**

Download Workflow 02 → overwrite `workflows/n8n/02_gap_resolution.json`.

Optionally export the approval-specific flow as `workflows/n8n/03_kb_approval.json` if you separated it. (Recommended: keep it as part of 02 for simplicity.)

- [ ] **Step 7: Smoke-test full loop**

1. Append unanswerable ticket to Sheet
2. Slack: gap card appears
3. Click Resolve → modal opens → submit a real answer
4. Slack: KB draft card appears
5. Click Approve & Commit
6. Verify: `git log --oneline` shows a new commit with the approver's name; `kb/<domain>/<slug>.md` exists; `kb/index.md` updated

- [ ] **Step 8: Commit**

```bash
git add intel_engine/api.py tests/test_api.py workflows/n8n/02_gap_resolution.json .gitignore
git -c commit.gpgsign=false commit -m "feat: KB approval → git commit loop closes hero workflow"
```

---

## Task 24: End-to-End Smoke Test

**Files:**
- Create: `tests/test_e2e_smoke.py`

**Goal:** Single Python test that exercises the full hero loop without n8n — directly calls API endpoints in sequence — to prove the loop closes end-to-end.

- [ ] **Step 1: Write the e2e test**

Create `tests/test_e2e_smoke.py`:
```python
"""End-to-end smoke test for the hero gap → KB loop.

This test bypasses n8n and Slack/Gmail; it directly drives the API endpoints
to prove the loop closes. Each external LLM call is mocked.
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from intel_engine.api import app
from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter
from intel_engine.schemas.traversal import Confidence, TraversalResult


@pytest.fixture
def repo_with_kb(tmp_path: Path, monkeypatch, fixtures_dir):
    """Set up a git repo with a tiny KB."""
    # Copy fixture KB into the repo
    import shutil
    kb_src = fixtures_dir / "sample_kb"
    kb_dst = tmp_path / "kb"
    shutil.copytree(kb_src, kb_dst)

    monkeypatch.setenv("KB_ROOT", str(kb_dst))
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path / "gap-log"))
    (tmp_path / "gap-log").mkdir()

    # Init git
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", "init"],
        cwd=tmp_path, check=True, capture_output=True,
    )

    # Monkeypatch DRAFT_STAGE_DIR to be inside tmp_path
    import intel_engine.api as api_mod
    monkeypatch.setattr(api_mod, "DRAFT_STAGE_DIR", tmp_path / "draft-stage")

    return tmp_path


@pytest.mark.asyncio
async def test_full_loop_gap_to_commit(repo_with_kb):
    """Drive the loop: traverse → gap → resolve → draft → stage → commit."""
    # Mock the traversal agent to return can_answer_fully=False
    gap_response = TraversalResult(
        pages_read=["kb/faqs/bpa.md"],
        can_answer_fully=False,
        missing_info=["MRI compatibility not in KB"],
        draft_reply=None,
        themes_detected=["materials_safety"],
        persona_hints=[],
        confidence=Confidence.low,
    )
    drafted_entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug="mri-safety",
            title="Are Boldr watches MRI-safe?",
            domain=KBDomain.spec,
            themes=["materials_safety"],
            sources=["gap_test"],
            last_verified=datetime(2026, 5, 16, tzinfo=timezone.utc).date(),
        ),
        body="Yes. Boldr Grade 5 titanium watches are MRI-safe. Titanium is non-magnetic.",
    )

    event = {
        "event_id": "evt_smoke",
        "source": "google_sheet",
        "customer": {"id": "c1", "name": "Sarah"},
        "body": "Are Boldr watches MRI-safe?",
        "ts": datetime(2026, 5, 16, tzinfo=timezone.utc).isoformat(),
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch("intel_engine.api.traverse", new=AsyncMock(return_value=gap_response)):
            r = await ac.post("/traverse", json=event)
        assert r.status_code == 200
        assert r.json()["can_answer_fully"] is False

        # Create gap
        r = await ac.post("/gap", json={
            "source_event_id": "evt_smoke",
            "customer_question": "Are Boldr watches MRI-safe?",
            "missing_info": ["MRI compatibility not in KB"],
            "themes_detected": ["materials_safety"],
        })
        assert r.status_code == 200
        gap_id = r.json()["gap_id"]

        # Resolve gap
        r = await ac.post("/gap/resolve", json={
            "gap_id": gap_id,
            "resolved_by": "sarah@boldr.sg",
            "resolution_text": "Titanium is non-magnetic; watches are MRI-safe.",
        })
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

        # Draft KB entry (mocked)
        with patch(
            "intel_engine.api.draft_kb_entry",
            new=AsyncMock(return_value=drafted_entry),
        ):
            r = await ac.post("/draft-kb-entry", json={"gap_id": gap_id})
        assert r.status_code == 200

        # Stage the draft
        r = await ac.post(
            "/draft/stage",
            json={"gap_id": gap_id, "entry": drafted_entry.model_dump(mode="json")},
        )
        assert r.status_code == 200

        # Retrieve staged
        r = await ac.get(f"/draft/staged/{gap_id}")
        assert r.status_code == 200
        staged = r.json()
        assert staged["frontmatter"]["slug"] == "mri-safety"

        # Commit
        r = await ac.post(
            "/commit-to-kb",
            json={"entry": staged, "approver": "sarah@boldr.sg", "gap_id": gap_id},
        )
        assert r.status_code == 200
        body = r.json()
        assert "sha" in body
        assert body["path"] == "kb/spec/mri-safety.md"

    # Verify the file exists and the commit landed
    committed = repo_with_kb / "kb" / "spec" / "mri-safety.md"
    assert committed.exists()
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo_with_kb, capture_output=True, text=True, check=True,
    ).stdout
    assert "mri-safety" in log
```

- [ ] **Step 2: Run the smoke test**

```bash
uv run pytest tests/test_e2e_smoke.py -v
```

Expected: 1 passed.

- [ ] **Step 3: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass (count should be ~20+).

- [ ] **Step 4: Commit**

```bash
git add tests/test_e2e_smoke.py
git -c commit.gpgsign=false commit -m "test: end-to-end smoke test for hero gap→KB loop"
```

---

## Task 25: Wire It All Together — Live Demo Rehearsal

**Files:** none (verification only)

**Goal:** Stand up everything and run a real ticket through the full pipeline including n8n + Slack + Gmail.

- [ ] **Step 1: Configure environment**

```bash
cp .env.example .env
# Fill in:
#   LLM_MINIMAX_API_KEY
#   LLM_KIMI_API_KEY
#   SLACK_BOT_TOKEN
#   SLACK_APPROVAL_CHANNEL=#boldr-intel-demo
```

- [ ] **Step 2: Boot FastAPI**

```bash
uv run uvicorn intel_engine.api:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] **Step 3: Boot n8n**

```bash
docker compose up -d
```

Wait 10 seconds, then verify:
```bash
curl -s http://localhost:5678 | head -3
curl -s http://localhost:8000/health
docker compose exec n8n wget -qO- http://host.docker.internal:8000/health
```

All three should respond.

- [ ] **Step 4: Make Slack reachable**

If running locally, expose n8n via ngrok or similar:
```bash
ngrok http 5678
```

Update your Slack app's Interactivity Request URL to `<ngrok-url>/webhook/slack-interactivity`.

- [ ] **Step 5: Run the answerable path**

Append a row to `tickets_input`:
- ticket_id: TKT-DEMO-1
- customer_name: Sarah
- body: `Are Boldr FKM rubber straps BPA-free?`
- received_at: (today's ISO date)

Within ~1 minute: a draft should appear in Gmail Drafts.

- [ ] **Step 6: Run the gap path**

Append:
- ticket_id: TKT-DEMO-2
- body: `Are Boldr watches MRI-safe?`

Within ~1 minute: a gap card should appear in Slack. Click Resolve → fill in the resolution → submit → KB draft card appears → click Approve & Commit → verify `git log --oneline` shows a new commit and `kb/spec/are-boldr-watches-mri-safe.md` exists.

- [ ] **Step 7: Send the same gap question again**

Append another row asking the same MRI question. The traversal should now return `can_answer_fully=true` and a draft should appear in Gmail Drafts citing the newly-committed file.

**This is the moment the hero loop is proven.** Capture screenshots / recordings for the video.

- [ ] **Step 8: Tag the release**

```bash
git tag -a plan-1-complete -m "Plan 1: Foundation + Hero Loop complete

The hero gap→KB loop runs end-to-end:
  Google Sheet row → traversal agent → answerable? → Gmail Draft OR gap
  → Slack resolve → drafted KB entry → Slack approve → git commit
  → next ticket on same question is answered automatically.

Ready to begin Plan 2 (eval harness)."
```

---

## Plan 1 Complete

At this point you have:
- A working Python FastAPI service with full test coverage on agents, KB I/O, and HTTP endpoints
- A seeded KB in Markdown with the brand voice contract, FAQ entries, rate cards, products, escalation policy, and 5 seed personas
- An n8n orchestration wired to Google Sheet intake, Gmail Drafts for replies, and Slack interactive cards for gap resolution + KB approval
- A self-improving hero loop that closes end-to-end with auditable git commits
- Demo-ready: capture the full loop in screen recordings for the video

**Next:** Plans 2, 3, 4 per the design spec §14.1.
