# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Launch Command

```bash
cd AIAgentBookCC
claude --dangerously-skip-permissions
```

## Repository Overview

This is an **AI Agent development workflow system** that generates comprehensive artifacts through a structured 6-phase process:

1. **01_business-requirements**: Business requirements definition (BR-01 ~ BR-07)
2. **02_system-requirements**: System requirements definition (SR-01 ~ SR-18)
3. **03_system-design**: System design (SD-01 ~ SD-10)
4. **04_basic-design**: Basic design (BD-01 ~ BD-05)
5. **05_detailed-design**: Detailed design (DD-01 ~ DD-09)
6. **06_code-generation**: Code generation and implementation (IG-01 ~ IG-04)

Each phase generates Japanese-language documentation and design artifacts that feed into the next phase, culminating in executable Python code for multi-agent AI systems using AWS Bedrock.

## Critical Workflow Rules

### Always Check STATE.md First

**Before any work**, read `STATE.md` at the project root:

1. Check the `次アクション待ち状態` (Next Action Status) field:
   - `⏸️ ユーザー指示待ち` → **STOP. Do not start any work.** Report current status and wait for user instruction.
   - `⏸️ ユーザー指示待ち（第2周確認）` → **STOP.** Ask user if they want to proceed with the second iteration.
   - `▶️ 作業中` → Proceed to next steps.

2. Verify the current phase (`現在のフェーズ`)
3. Check artifact completion status: Only work on `🔲 未着手` or `🔄 作業中` items. Never recreate `✅ 完了` artifacts.

### Phase Progression Rules

- **Never automatically advance to the next phase** when a phase completes
- Always wait for explicit user instruction before starting a new phase
- Display completion message and pause:
  ```
  ✅ [フェーズ名] が完了しました。
  次フェーズ（[次フェーズ名]）を開始する場合は、その旨を指示してください。
  ```

### Do Not Modify Steering Files

- **Never modify files in `.claude/rules/`** without explicit user permission
- These are user-managed configuration files
- If changes are needed, propose them and wait for approval

### Multi-Iteration Workflow (Multiple Passes)

When artifacts within a phase have dependencies on each other:

- **First iteration**: Create all artifacts in sequence. Mark undefined dependencies as `要件上未定義`
- **Second iteration** (if needed): Fill in undefined items using now-available dependency artifacts
- Always check if a second iteration is needed based on artifact dependencies
- Wait for user confirmation before starting each new iteration

## Source of Truth Files

- **Overall rules**: `.claude/rules/WORKFLOW.md`
- **Artifact definitions**: `.claude/rules/artifact-catalog.yaml`
- **Generation prompts**: `.claude/skills/phase-XX-*/references/*.md`
- **Templates**: `.claude/skills/phase-XX-*/assets/*.md`
- **Generated artifacts**: `artifacts/XX_*/outputs/*.md`

## Using Phase Skills

When users request work on a specific phase, use the corresponding skill:

- `/phase-01-business-requirements` - Business requirements phase
- `/phase-02-system-requirements` - System requirements phase
- `/phase-03-system-design` - System design phase
- `/phase-04-basic-design` - Basic design phase
- `/phase-05-detailed-design` - Detailed design phase
- `/phase-06-code-generation` - Code generation phase

Each skill handles the complete workflow for that phase, including:
- Reading the artifact catalog
- Loading prompts and templates
- Generating artifacts in the correct order
- Updating STATE.md
- Quality checks

## Artifact Generation Process

For each artifact:

1. Read definition from `artifact-catalog.yaml`
2. Load the corresponding prompt from `.claude/skills/phase-XX-*/references/`
3. Load the template from `.claude/skills/phase-XX-*/assets/`
4. Check dependencies (`depends_on`) - ensure no `要件上未定義` or `TBD` items exist
5. Generate artifact following template structure exactly
6. Update STATE.md status from `🔲 未着手` → `🔄 作業中` → `✅ 完了`
7. Run quality checks defined in the prompt

**Never**:
- Skip template sections
- Guess or fill in undefined dependency values
- Batch-read all prompts/templates at phase start
- Add explanatory notes outside the template structure

> **`depends_on` is not an ordering directive.** It defines which prior artifacts to read as input. Creation order comes solely from `phases[].default_sequence` in `artifact-catalog.yaml`.

## Reference Materials

Training reference data used during code generation lives in `materials/06_code-generation/`:
- `fixed_fares.json`, `train_fares.json` — fare lookup data for the sample system
- `交通費申請書_template.xlsx`, `経費精算申請書_template.xlsx` — Excel output templates

Exercise prompts (workflow entry points for training use) are in `prompts/` (files numbered 01–13).

## Phase Output Structure

```
artifacts/
├── 01_business-requirements/
│   ├── outputs/      # Generated documents
│   └── reviews/      # フェーズ品質チェック_review.md
├── 02_system-requirements/
│   ├── outputs/
│   └── reviews/
├── 03_system-design/
│   ├── outputs/
│   └── reviews/
├── 04_basic-design/
│   ├── outputs/
│   └── reviews/
├── 05_detailed-design/
│   ├── outputs/
│   └── reviews/
└── 06_code-generation/
    ├── outputs/      # tasks.md, code_review_report.md
    └── src/          # Generated Python code
```

## Generated Code Technology Stack

The final phase (06_code-generation) produces Python code using:

- **Framework**: `strands-agents` (AWS Bedrock multi-agent framework)
- **LLM**: AWS Bedrock (Claude models)
- **Tools**: `strands-agents-tools`
- **Configuration**: Pydantic settings
- **Testing**: pytest

Dependencies are in `requirements.txt`.

## Language Conventions

- **Documentation**: Japanese
- **Code identifiers**: English (variable names, function names, class names)
- **Code comments**: Japanese
- **Output format**: All artifacts use Japanese except code identifiers

## Common Issues

1. **Starting work without checking STATE.md** → Always read STATE.md before any action
2. **Auto-advancing phases** → Always wait for user instruction between phases
3. **Modifying .claude/rules/ files** → Never modify without explicit permission
4. **Ignoring undefined dependencies** → Always stop and report when finding `要件上未定義` or `TBD`
5. **Batch loading prompts** → Only load prompt/template for the current artifact being generated
