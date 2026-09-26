---
type: Change
title: Rename CLAUDE.md to AGENTS.md
description: Replaced the Claude-specific agent instruction file with the tool-neutral AGENTS.md and updated its content to version 0.8.0.
tags: [config, agents, documentation]
status: stable
generated:
  by: claude-code/claude-opus-5-5
  at: 2026-09-26T22:18:02Z
sources:
  - resource: AGENTS.md
  - resource: CLAUDE.md
---

# Summary
`CLAUDE.md` was removed and its content moved to `AGENTS.md`. The instructions were updated from version 0.6.0 to the `python_development` 0.8.0 template:

- "SOLID" expanded to "SOLID design principles".
- New `## General` section under Python Development requiring python tasks to run via `uv`.

# Rationale
`AGENTS.md` is the tool-neutral convention for coding-agent instructions, read by multiple agents rather than only Claude Code. Consolidating on it keeps a single source of instructions regardless of which agent operates on the repository. The `uv` rule prevents agents from invoking the system python instead of the project environment.
