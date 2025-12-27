# Project Profile: depswiz

## What it does
Scans your polyglot codebase (Python, Rust, Dart, JS) and gives you a unified dashboard of what's broken, outdated, or vulnerable across ALL your dependencies. You run `depswiz check` and get one coherent view instead of juggling `npm audit`, `cargo audit`, `pip-audit`, and `dart pub deps` separately.

## The real problem
You're maintaining a modern app with a Python backend, React frontend, Rust microservice, and Flutter mobile app. A critical vulnerability drops on Tuesday. Now you're frantically running different audit tools, cross-referencing CVE databases, and trying to remember which package manager each project uses. You spend 2 hours just figuring out your attack surface, let alone fixing it.

## Who it's for
The full-stack developer or DevOps engineer managing polyglot projects who's tired of context-switching between 8 different dependency management tools. Someone who's been burned by missing a critical security update because it was buried in the noise of language-specific tooling.

## How it works
Detects manifest files (pyproject.toml, package.json, Cargo.toml, pubspec.yaml) across your codebase, queries each language's registry APIs (PyPI, npm, crates.io, pub.dev), cross-references against OSV vulnerability database, and presents everything in a unified CLI/TUI interface. Generates CycloneDX SBOMs for compliance and includes an AI integration that uses Claude to suggest upgrade strategies.

## What differentiates it from ChatGPT/others
ChatGPT can't read your actual dependency files, query live vulnerability databases, or generate compliance-ready SBOMs. This tool has real-time integrations with package registries and security databases. The AI component uses your actual project context - it's not generic advice but "here's how to safely upgrade React 17→18 in YOUR codebase given your current TypeScript version."

## The "Aha moment"
When you run `depswiz guide` and see the unified health score dashboard - watching it update in real-time as you fix issues across different languages. Seeing "73% → 89% → 94%" as you update a Rust crate, patch a Python vulnerability, and upgrade a Flutter dependency, all from one interface.

## 3 Marketing Angles (with example hook)

1. **Polyglot Pain Relief**
   Hook: "Managing dependencies across Python + Rust + React + Flutter? depswiz gives you ONE dashboard instead of juggling 8 different tools."
   Why it works: Immediately resonates with anyone doing full-stack development in 2024.

2. **Security Theater Killer**
   Hook: "Stop playing vulnerability whack-a-mole. depswiz scans Python, Rust, Dart AND JavaScript for CVEs in one command."
   Why it works: Security is everyone's nightmare and the multi-language aspect is a genuine differentiator.

3. **Compliance Made Simple**
   Hook: "Generate enterprise-ready SBOMs across your entire polyglot stack. One command, CycloneDX output, compliance team happy."
   Why it works: SBOM generation is becoming mandatory but tooling is fragmented - this solves a real enterprise need.