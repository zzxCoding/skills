# Flydb Skills

A self-contained Agent Plugins 1.0 package for planning and operating
[Flydb](https://github.com/zzxCoding/Flydb) database schema migrations.
It includes exactly four skills and their offline references:

| Skill | Purpose |
| --- | --- |
| `flydb` | Route a request to the appropriate workflow. |
| `flydb-cli-release` | Install and verify releases; use CLI, local Web workbench, JSON/Plan and MCP; diagnose migration and JDBC errors. |
| `flydb-migration-scripts` | Manage V/R/U scripts, version and directory conventions, and checksum discipline. |
| `flydb-multi-environment` | Organize database/environment configurations, credential injection, CI approvals, baseline adoption and offline drivers. |

The skill instructions and most references are in Simplified Chinese. You can
request explanations in English. Guidance targets Flydb CLI 0.3.x (Web requires
0.3.5+); always verify the installed CLI and its matching documentation first.
Reading these skills needs no Flydb source checkout. Running Flydb needs Java 8+
and a separately installed Flydb distribution; its optional MCP host needs
Node.js 20+. This package installs no hooks, MCP servers, drivers or binaries.

## Install with GitHub Copilot CLI

Clone the immutable plugin release, then install the plugin directory:

```bash
git clone --branch flydb-skills-v1.0.0 --depth 1 https://github.com/zzxCoding/skills.git
copilot plugin install ./skills/plugins/flydb-skills
copilot plugin list
```

The plugin is submitted for Awesome Copilot review; a submission is not a
marketplace listing. The existing Skills CLI and Claude Code marketplace
installation paths remain available in the repository README.

## Example prompts

```text
Use flydb to identify the right workflow for adopting migrations in an existing project.
Explain the plan in English. Do not connect to a database yet.

Use flydb-migration-scripts to add a V migration for a customer status column.
Follow this project's version convention and preserve every applied migration.

Use flydb-cli-release to prepare validate and dry-run commands for this flydb.conf.
Explain the JSON/Plan review evidence and stop before any database writes.

Use flydb-multi-environment to draft test, staging and production configurations.
Inject passwords externally and require a production approval step.
```

Database writes require environment-appropriate authorization. Production changes
require preview and explicit approval. Applied versioned scripts stay immutable;
repair is a deliberate recovery action, and undo/clean do not belong in unattended CI.
Credentials must stay out of commands, logs and source control.

## Maintenance and verification

The repository's top-level `skills/flydb*/` directories are the canonical source.
From the repository root, run `python3 scripts/package_flydb_plugin.py` after an
intentional source update, then `python3 scripts/package_flydb_plugin.py --check`.
The checked-in package uses regular files, so installation preserves sibling skill
links and bundled references without paths outside the plugin.

Validate the manifest against Agent Plugins 1.0, run Microsoft's `vally lint`,
and smoke-test the fixed release with Copilot CLI before submission. These checks
prove packaging and installation; they do not prove model behavior or successful
database migrations. The included `evals/evals.json` files describe behavioral
scenarios and are not evidence that Copilot executed those scenarios.

## License

Copyright 2026 zzxCoding. All files in this plugin directory are licensed under
the [Apache License, Version 2.0](LICENSE). References derived from Flydb retain
their attribution and `upstream-sync.json` provenance. The repository-level
`LICENSE-SCOPE.md` defines the matching grant for the canonical skill sources;
unrelated skills are outside that grant.
