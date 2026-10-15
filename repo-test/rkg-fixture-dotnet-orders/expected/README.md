# Expected demo inventory

These files are non-normative, source-backed targets for future C#, ASP.NET Core
and EF Core adapters. They are not an analyzer output dump or an exhaustive census.
The current built-in registry does not include these adapters.

| File | Purpose |
|---|---|
| `applications.json` | App root, entrypoint, ignored directories and demo stages |
| `entities.json` | Required entity subset, semantic keys and source evidence |
| `edges.json` | Required relations plus separately marked optional cascade rules |
| `diagnostics.json` | Dynamic/ambiguous/unsupported cases and prohibited conclusions |
| `questions.json` | Ten manual prompts, required facts, evidence and forbidden claims |
| `source-manifest.json` | SHA-256 of source, inert negatives, manifests and package locks |
| `prohibited-values.txt` | Fake sentinel that must not occur in analyzer output |

Stage names `language`, `framework`, `data_access` express incremental demo goals;
`baseline_unsupported` has no positive C# graph expectations. A missing future-stage
fact before that stage is implemented is a capability gap, not a reason to change
the source-backed answer. Do not count optional edges as required failures.

Keys are fixture-local semantic references, never RKG hash IDs. Evidence uses
repository-relative file paths, 1-based lines and SHA-256 of the UTF-8 line without
its line terminator. The manifest pins whole-file bytes. Signatures and namespace
scope must distinguish overloads and duplicate simple names. No raw source body,
request payload, credential, absolute host path or runtime config value belongs
in exported graph evidence.

Dependency-injection registration may support an additional resolution rule later;
required method calls currently retain interface-member targets. Public framework
and repository helpers not listed here may be valid extra facts with evidence.

The Python validator checks pins and references; semantic review and native tests
remain separate. This fixture is not automatically added to the parent project's
50-case chatbot evaluation corpus and does not change its acceptance denominator.
