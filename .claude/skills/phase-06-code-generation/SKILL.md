---
name: phase-06-code-generation
description: コード生成フェーズ（06_code-generation）の成果物（IG-01〜IG-04）を生成する。実装タスク計画・コード生成実行（Pythonコード + pytestによるテスト実行）・評価テストコード生成・コードレビューを順番に実施する。「コード生成フェーズを開始して」「コードを生成して」など、コード生成フェーズの実行に関する指示があれば必ずこのスキルを使用する。
---

# フェーズ06: コード生成 実行スキル

このフェーズのスキルが担当する成果物: **IG-01〜IG-04**（実装タスク計画、コード生成実行、評価テストコード生成、コードレビュー）

---

## Section 1: 起動時必須確認

### 1-1. 状態ファイルの読み込み

以下のファイルを必ず読み込む。

1. `STATE.md`（プロジェクトルート）

### 1-2. 「次アクション待ち状態」の確認

- `⏸️ ユーザー指示待ち` または `⏸️ ユーザー指示待ち（第2周確認）` の場合 → **即停止**。現在の状態をユーザーに報告して作業を開始しない。
- `▶️ 作業中` の場合 → 次ステップへ進む。

### 1-3. フェーズ確認

`STATE.md` の「現在のフェーズ」が `06_code-generation` 以外の場合は、以下を報告して停止する。

```
⚠️ フェーズ不一致
このスキルは 06_code-generation 用です。
現在のフェーズは [現在のフェーズ] です。
正しいフェーズスキルを使用してください。
```

### 1-4. artifact-catalog.yaml の読み込み

`.claude/rules/artifact-catalog.yaml` を読み込み、`phase: 06_code-generation` の成果物定義を確認する。

### 1-5. 作業対象の特定

`STATE.md` の成果物別進捗から `🔲 未着手` または `🔄 作業中` の成果物のみを作業対象とする。`✅ 完了` の成果物は再作成しない。

---

## Section 2: 依存チェック

各成果物の `depends_on` に記載されたファイルを確認する。

依存ファイルに以下のパターンが含まれる場合は **即座に停止** して報告する。

- `要件上未定義`
- `〇〇フェーズで定義`
- `TBD`

報告形式:
```
⚠️ 作業開始不可：依存成果物に未定義項目があります

| ファイル | 項目 | 記載内容 |
|---|---|---|
| [ファイル名] | [項目名] | [記載内容] |

上記を定義・解決してから再度依頼してください。
未定義のまま進める場合は、その旨を明示的に指示してください。
```

**第1周ルール（例外）**: `depends_on` に記載されたファイルが同フェーズ内の成果物であり、かつその成果物がまだ未作成の場合は、ユーザー確認なしで作業を続行してよい。

---

## Section 3: 成果物作成手順

### IG-01: 実装タスク計画

1. `STATE.md` の該当行を `🔄 作業中` に更新する
2. `.claude/skills/phase-06-code-generation/references/実装タスク計画.md` を Read する
3. 詳細設計の全成果物（`artifacts/05_detailed-design/outputs/`）を参照して実装タスクを計画する
4. `artifact-catalog.yaml` の `output` パスに実装タスク計画を Write する
5. プロンプト内の受入基準で品質チェックを実施する
6. `STATE.md` の該当行を `✅ 完了` に更新する

### IG-02: コード生成実行

1. `STATE.md` の該当行を `🔄 作業中` に更新する
2. `.claude/skills/phase-06-code-generation/references/コード生成実行.md` を Read する
3. `.claude/skills/phase-06-code-generation/assets/` のスケルトンファイル群を、作成対象ファイルごとに順次 Read する（遅延ロード）:
   - `01_skeleton_data_models.md` → `models/data_models.py`
   - `02_skeleton_model_config.md` → `config/model_config.py`
   - `03_skeleton_error_handler.md` → `handlers/error_handler.py`
   - `04_skeleton_loop_control_hook.md` → `handlers/loop_control_hook.py`
   - `05_skeleton_human_approval_hook.md` → `handlers/human_approval_hook.py`
   - `06_skeleton_session_manager.md` → `session/session_manager.py`
   - `07_skeleton_prompt_orchestrator.md` → `prompt/{orchestrator_name}.py`
   - `08_skeleton_prompt_specialist.md` → `prompt/{specialist_name}.py`（スペシャリストの数だけ繰り返す）
   - `09_skeleton_policies.md` → `knowledge/policies.py`
   - `10_skeleton_tools.md` → `tools/{domain}_tools.py`（ドメインごとに繰り返す）
   - `11_skeleton_orchestrator_agent.md` → `agents/orchestrator_agent.py`
   - `12_skeleton_specialist_agent.md` → `agents/{specialist_name}_agent.py`（スペシャリストの数だけ繰り返す）
   - `13_skeleton_main.md` → `main.py`
   - `14_design_data_files.md` → `data/*.json`（マスターデータファイル）
   - `15_skeleton_settings.md` → `pyproject.toml`, `.env.template`
   - `16_guardrails_cloudformation_yaml.md` → `guardrails/*.yaml`
   - `17_skeleton_base_agent.md` → `agents/base_agent.py`
4. コードを `artifact-catalog.yaml` の `output` パスに従い Write する
5. **pytest によるテスト実行**:
   - Bash ツールで `pytest` を実行する
   - テストが失敗した場合は、失敗内容を分析して該当コードを修正し、再度 `pytest` を実行する
   - 全テスト通過まで修正と再実行を繰り返す
   - 連続失敗が解消しない場合はユーザーに報告して停止する
6. `STATE.md` の該当行を `✅ 完了` に更新する

**コード生成の遵守事項**:
- `.claude/skills/phase-06-code-generation/references/00_rule_project_conventions.md` の命名規則・コードパターンに準拠する
- `.claude/skills/phase-06-code-generation/references/00_rule_directory_structure.md` のディレクトリ構造に準拠する
- コードは省略なく全量を生成する
- `要件上未定義` 項目を推測補完しない

### IG-03: 評価テストコード生成

1. `STATE.md` の該当行を `🔄 作業中` に更新する
2. `.claude/skills/phase-06-code-generation/references/評価テスト生成.md` を Read する
3. `.claude/skills/phase-06-code-generation/assets/18_eval_test.md` を Read する
4. 詳細設計の評価テスト詳細設計を参照して評価テストコードを生成する
5. `evals/` ディレクトリに評価テストコードを Write する
6. `STATE.md` の該当行を `✅ 完了` に更新する

### IG-04: コードレビュー

1. `STATE.md` の該当行を `🔄 作業中` に更新する
2. `.claude/skills/phase-06-code-generation/references/コードレビュー.md` を Read する
3. `.claude/skills/phase-06-code-generation/references/00_rule_code_review_checklist.md` を Read する
4. 生成コードと詳細設計を照合して以下の観点でレビューを実施する:
   - 生成コードが詳細設計と整合していること
   - 命名・構成・責務分割が設計と一致していること
   - 実装対象外の未定義項目を推測補完していないこと
   - `00_rule_code_review_checklist.md` の全チェック項目を確認
5. コードレビュー結果を `artifact-catalog.yaml` の IG-04 の `output` パスに Write する
6. `STATE.md` の該当行を `✅ 完了` に更新する

---

## Section 4: 複数周回ルール

フェーズ内の全成果物（IG-01〜IG-04）の第1周作成が完了したら、以下の2条件を確認する。

**条件1**: フェーズ内の成果物が、同フェーズ内の別の成果物を `depends_on` に持つか
**条件2**: その依存先成果物が、1周目の作成時点でまだ未作成だった（`要件上未定義` として記載した箇所が存在する）か

- **両条件を満たす場合** → `STATE.md` の「次アクション待ち状態」を `⏸️ ユーザー指示待ち（第2周確認）` に更新し、確認メッセージを表示して停止する。
- **両条件を満たさない場合** → Section 5（フェーズ品質チェック）へ直接進む。

---

## Section 5: フェーズ品質チェック

フェーズ内の全成果物が完了した後に、以下の品質基準を確認する。

**06_code-generation の品質基準**:
- 生成コードが詳細設計と整合していること
- 命名・構成・責務分割が設計と一致していること
- 実装対象外の未定義項目を推測補完していないこと
- 次の実装・テスト作業へ引き継げる情報が完備していること

品質チェック結果を `artifact-catalog.yaml` の `phase: 06_code-generation` かつ `artifact_type: review` のエントリの `review_output` パスに Write する。

**合格時**: `STATE.md` を以下のように更新する:
- 「品質チェック」列: `✅ 合格`
- 「現在のフェーズ」: `06_code-generation（完了）`
- 「次アクション待ち状態」: `⏸️ ユーザー指示待ち`

以下のメッセージを出力して**停止**する:
```
✅ 06_code-generation が完了しました。
全6フェーズのワークフローが完了しました。
```

---

## Section 6: 禁止事項

- `.claude/rules/` 配下ファイルの変更禁止（ユーザー明示指示がある場合のみ可）
- `要件上未定義` 項目の推測・補完・暫定値設定禁止
- スケルトンファイルの一括読み込み禁止（作成対象ファイルごとに遅延ロード）
- コードの省略禁止（全量生成すること）
- pytest 失敗時に自動で作業を継続しない（ユーザー報告→停止）
- 不明点はユーザーに確認する。推測や補完を行わない
