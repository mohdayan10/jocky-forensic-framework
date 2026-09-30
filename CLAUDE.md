# JOCKY — Forensic Investigation Framework

Smart India Hackathon 2024 | PS 26148 | NTRO

## Project Overview

JOCKY is a domain-specific language and framework for forensic investigations.
Investigators write `.jky` programs that compile through a full pipeline
(Lexer → Parser → Semantic → JIR → Policy) and deploy as polymorphic agents
to authorized endpoints.

## Architecture

```
jocky/
├── compiler/        # The JOCKY language compiler
│   ├── lexer/       # Tokenizer for .jky files
│   ├── parser/      # Recursive descent parser → AST
│   ├── semantic/    # Type checking, scope resolution, forensic validation
│   ├── jir/         # JIR (JOCKY Intermediate Representation) emitter
│   └── policy/      # Authorization & capability validation
├── forge/           # Polymorphic build pipeline (per-host unique binaries)
├── kernel/          # Kernel-level forensic collection (hidden procs, hooks, BYOVD)
├── correlation/     # Multi-signal finding generation engine
├── blockchain/      # Hyperledger Fabric evidence integrity ledger
├── ai_assistant/    # Evidence-grounded explanation with citation validation
├── report/          # Report generation (JSON, PDF)
├── common/          # Shared data models (Evidence, Finding, Timeline, Graph)
├── cli.py           # CLI entry point (jocky compile/build/forge)
└── demo.py          # Full demo runner (all 17 steps)
```

## Running

```bash
# Compile a .jky program
python -m jocky compile examples/op_falcon.jky --verbose --emit-jir

# Build an agent binary
python -m jocky build examples/op_falcon.jky --output agent.bin

# Forge polymorphic builds for multiple hosts
python -m jocky forge deploy examples/op_falcon.jky --targets HOST-01,HOST-02,HOST-03

# Run the full demo
python -m jocky.demo
python -m jocky.demo --step 14     # Run specific step
python -m jocky.demo --no-pause    # Non-interactive
```

## Key Design Decisions

- Python for rapid development; production kernel components need native code
- No external dependencies for core compiler — stdlib only
- Evidence model is the shared contract between all components
- Blockchain ledger is simulated locally; production uses Hyperledger Fabric SDK
- AI assistant citation validation is a hard gate — invalid IDs reject the response
