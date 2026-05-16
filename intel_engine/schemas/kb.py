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
