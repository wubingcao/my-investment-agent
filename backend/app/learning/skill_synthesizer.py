"""Monthly skill synthesizer.

Reads the accumulated learnings markdown and turns recurring patterns into
reusable "skills" — each skill is a markdown file describing a playbook that
future expert prompts can reference as best-practice.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from app.agents.claude_client import get_claude
from app.config import get_settings

log = logging.getLogger(__name__)


SYNTH_SYSTEM = """You are the Skill Synthesizer for a multi-agent investment system.
You receive a batch of "lessons learned" markdown docs. Identify patterns that recur
3+ times and distill each into a skill — a concise, reusable playbook an expert
persona can consult.

For each skill, write a self-contained markdown file with sections:
- # {Skill name}
- ## When to apply (pre-conditions, market regime, technical setup)
- ## What to do (actions, entry/exit/stop rules)
- ## What to avoid (anti-patterns)
- ## Evidence (1-3 historical cases that proved the rule)

Return a JSON object:
{
  "skills": [
    {"slug": "kebab-case-name", "filename": "kebab-case-name.md", "title": "...", "markdown": "full markdown content"},
    ...
  ],
  "meta_notes": "anything for the operators"
}
"""


async def run_monthly_skills() -> list[str]:
    cfg = get_settings()
    learnings_dir = cfg.kb_path / "learnings"
    if not learnings_dir.exists():
        log.info("Monthly skills skipped: no learnings dir yet")
        return []

    lessons = []
    for p in sorted(learnings_dir.glob("*.md"), reverse=True)[:12]:
        if p.name == "README.md":
            continue
        lessons.append({"name": p.stem, "content": p.read_text(encoding="utf-8")[:5000]})

    if not lessons:
        log.info("Monthly skills skipped: no lesson files yet")
        return []

    import orjson
    user = (
        f"Here are the {len(lessons)} most recent lesson files. Synthesize recurring skills.\n\n"
        f"```json\n{orjson.dumps(lessons, option=orjson.OPT_INDENT_2).decode()}\n```\n\n"
        "Return the JSON contract."
    )

    claude = get_claude()
    result = await claude.json_complete(
        system=SYNTH_SYSTEM,
        messages=[{"role": "user", "content": user}],
        max_tokens=8000,
        temperature=0.3,
    )

    written = []
    skills_dir = cfg.kb_path / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    for skill in result.get("skills", []) or []:
        fname = skill.get("filename") or f"{skill.get('slug','skill')}.md"
        md = skill.get("markdown", "")
        if not md:
            continue
        path = skills_dir / fname
        path.write_text(md, encoding="utf-8")
        written.append(str(path))
        log.info("Skill written: %s", path)

    # Refresh skills index
    entries = sorted(skills_dir.glob("*.md"))
    lines = ["# Skills index", ""]
    for e in entries:
        if e.name == "README.md":
            continue
        lines.append(f"- [{e.stem}]({e.name})")
    (skills_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Refresh top-level KB README
    await _refresh_top_kb(cfg.kb_path)
    return written


async def _refresh_top_kb(kb: Path):
    kb.mkdir(parents=True, exist_ok=True)
    content = f"""# Knowledge Base

Updated: {datetime.utcnow().isoformat()}

## Contents
- [Learnings](learnings/README.md) — weekly lessons from real outcomes
- [Skills](skills/README.md) — distilled playbooks from recurring patterns
- [Fundamentals](fundamentals/) — reference notes on companies/sectors
- [Technicals](technicals/) — chart patterns and indicator playbooks

The committee of agents may read these files during analysis to inform their reasoning.
"""
    (kb / "README.md").write_text(content, encoding="utf-8")
