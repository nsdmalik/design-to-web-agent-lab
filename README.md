# Design-to-Web Agent Lab

**A traceable workflow from a design brief to a reviewable static website.**

A Python agent workflow with separate planning, implementation, validation, and bounded repair stages. It includes a deterministic offline example and a live Anthropic Messages API provider. Generated files are written only after they pass the documented checks, then handed to a person for review.

## Run the offline example

Python 3.11 or later. No dependencies or credentials required.

```sh
python3 workflow.py brief.json --provider replay --output runs/demo
python3 -m http.server 8080 --bind 127.0.0.1 --directory runs/demo/preview
python3 -m unittest -v
```

Open http://127.0.0.1:8080 after reviewing the files. Use a new output directory for each run. The offline provider replays the included fictional workshop design; it does not pretend to generate a new design for arbitrary briefs.

## Run with a model

Set `ANTHROPIC_API_KEY` in your local environment and pass an available model ID for your account:

```sh
python3 workflow.py your-brief.json --provider anthropic --model YOUR_MODEL_ID --output runs/first-live-run
```

A live run sends your brief, design plan, and generated implementation to Anthropic. It makes two calls, plus at most one repair call, and incurs the provider's normal usage charges. No live calls are made by the test suite or offline demo. Keys are read from the environment and are never written to run artifacts. See the [Messages API](https://platform.claude.com/docs/en/api/messages/create).

## Workflow

| Stage | Output | Boundary |
| --- | --- | --- |
| Plan | goal, layout, visual direction | JSON shape validation |
| Build | index.html and style.css | Exact file allowlist |
| Validate | explicit list of structural/resource errors | No execution of generated code |
| Repair | one corrected implementation | At most one attempt |
| Review | static preview files and run.json | Human review required; no deployment |

`run.json` records the provider, stages, validation results, and final status. The model is free to design within a constrained static-page contract. The engine owns allowed files, checks, repair budget, and output writes.

## What is checked

- One h1, document title, language attribute, stylesheet link, unique IDs, and valid section anchors.
- No scripts, inline event handlers, forms, embedded media, meta refresh, or arbitrary file paths.
- No external URLs in known resource/link attributes and no CSS imports, URLs, or escapes.
- A 200 KB per-file limit and a 20 KB brief limit.
- Existing output directories are never overwritten.

These are structural quality checks for a constrained example, not a browser sandbox, a full HTML/CSS sanitizer, an accessibility certification, or a visual-design evaluator. Inspect output before opening it. Visual quality and content accuracy still need review. Future work can add browser-based checks and a separately isolated preview environment.

## Extend it

A provider is a callable `(stage, payload) -> JSON text`. Add another provider without changing validation or output policy. Tests use synthetic payloads and a replay provider, so workflow behavior can be checked without model variability or cost.

This is an independent public implementation using fictional sample content. Built by [Nauman Masood](https://nsdmalik.dev). [MIT license](LICENSE).
