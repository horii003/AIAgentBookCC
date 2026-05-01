---
name: strands-06-code-generation
description: Strands Agents SDKのAIエージェント開発ワークフローのコード生成フェーズ（06_code-generation）を実行するスキル。「実装タスク計画を作って」「コード生成を始めて」「Pythonコードを生成して」「実装を始めて」「コードを書いて」など、コード生成フェーズの成果物作成・実装に関する指示があれば必ずこのスキルを使用する。AIエージェント開発、Strands、コード生成、Python実装のキーワードが出た場合にも積極的にこのスキルを適用する。
---

# 06_code-generation フェーズ スキル

Strands Agents SDKのAIエージェント開発ワークフローにおけるコード生成フェーズを実行するスキル。
詳細設計に基づいて実装タスク計画を作成し、Pythonコードを生成する。

パスはすべて `skills/` からの相対パスで記載する。

---

## セッション開始時の必須手順

このスキルが呼び出されたら、作業開始前に必ず以下を実行すること。

1. `skills/workflow-state.md` を読み込む
2. `skills/session-context.md` を読み込む
3. **「次アクション待ち状態」欄を最初に確認する**
   - `⏸️ ユーザー指示待ち` の場合 → **作業を一切開始しない**。現在の状態を報告して指示を待つ
   - `▶️ 作業中` の場合 → 次のステップへ進む
4. 「現在のフェーズ」と各成果物の状態を確認する
5. `✅ 完了` の成果物は再作成しない
6. `🔲 未着手` または `🔄 作業中` の成果物のみを作業対象とする

---

## 成果物と参照ファイル一覧

| # | 成果物名 | ID | prompt | template | 出力先 |
|---|---|---|---|---|---|
| 1 | 実装タスク計画 | IG-01 | `prompts/06_code-generation/実装タスク計画.md` | なし | `../artifacts/06_code-generation/outputs/tasks.md` |
| 2 | コード生成実行 | IG-02 | `prompts/06_code-generation/コード生成実行.md` | 下記スケルトン参照 | `../artifacts/06_code-generation/src/` |

### コード生成で使用するスケルトンテンプレート

コード生成（IG-02）では以下のスケルトンファイルを参照してコードを生成する。

| スケルトン | ファイル | 対応コンポーネント |
|---|---|---|
| 01 | `templates/06_code-generation/01_skeleton_data_models.md` | `models/data_models.py` |
| 02 | `templates/06_code-generation/02_skeleton_model_config.md` | `config/model_config.py` |
| 03 | `templates/06_code-generation/03_skeleton_error_handler.md` | `handlers/error_handler.py` |
| 04 | `templates/06_code-generation/04_skeleton_loop_control_hook.md` | `handlers/loop_control_hook.py` |
| 05 | `templates/06_code-generation/05_skeleton_human_approval_hook.md` | `handlers/human_approval_hook.py` |
| 06 | `templates/06_code-generation/06_skeleton_session_manager.md` | `session/session_manager.py` |
| 07 | `templates/06_code-generation/07_skeleton_prompt_orchestrator.md` | `prompt/prompt_orchestrator.py` |
| 08 | `templates/06_code-generation/08_skeleton_prompt_specialist.md` | `prompt/prompt_{specialist}.py` |
| 09 | `templates/06_code-generation/09_skeleton_policies.md` | `agent_knowledge/{domain}_policies.py` |
| 10 | `templates/06_code-generation/10_skeleton_tools.md` | `tools/{domain}_tools.py` |
| 11 | `templates/06_code-generation/11_skeleton_orchestrator_agent.md` | `agents/orchestrator_agent.py` |
| 12 | `templates/06_code-generation/12_skeleton_specialist_agent.md` | `agents/{specialist}_agent.py` |
| 13 | `templates/06_code-generation/13_skeleton_main.md` | `main.py` |
| 14 | `templates/06_code-generation/14_design_data_files.md` | `data/*.json` |

### 依存関係

| 成果物 | 依存する成果物ID |
|---|---|
| IG-01 | BD-02, BD-05, SD-01〜SD-07, DD-01〜DD-03 |
| IG-02 | IG-01 |

---

## 基本方針

### 0. 不明点は必ずユーザーに確認すること
- 指示が不明確・曖昧な場合は、推測や補完を行わず、必ずユーザーに確認してから作業を開始する

### 1. 失敗時はユーザーに報告して停止すること
- 処理が失敗した場合は、即座に作業を停止する
- 自動リトライや続行は行わず、必ずユーザーの指示を待つ

### 2. 出力ルール
- すべてのコメント・docstring は日本語で記述する
- 識別子（変数名・関数名・クラス名）は英語（R7準拠）
- 実装対象外の未定義項目を推測・補完してはならない
- 詳細設計と命名・構成・責務分割を一致させること

### 3. フェーズ完了の宣言
- コード生成が完了したら以下を提示して待機する

```
✅ 06_code-generation が完了しました。
次の実装・テスト作業へ引き継ぐ情報が完備しています。
```

---

## 成果物作成手順

### Step 1: 前フェーズ成果物の確認

`../artifacts/05_detailed-design/outputs/` 配下の全成果物が揃っていることを確認する。
不足がある場合はユーザーに報告して停止する。

### Step 2: workflow-state.md を「作業中」に更新

成果物の作成開始直前に、該当行を `🔲 未着手` → `🔄 作業中` に変更する。

### Step 3: prompt の読み込み

対象成果物の **prompt ファイル** を読み込む。
- コード生成（IG-02）の場合は、生成対象コンポーネントに対応するスケルトンテンプレートを1ファイルずつ読み込む
- フェーズ開始時に全スケルトンを一括読み込みしてはならない

### Step 4: 実装タスク計画（IG-01）

`prompts/06_code-generation/実装タスク計画.md` の指示に従い、
詳細設計・基本設計・システム設計の成果物をもとに `../artifacts/06_code-generation/outputs/tasks.md` を作成する。

tasks.md の内容：
- 実装対象コンポーネントの一覧と実装順序
- 各コンポーネントの実装概要
- 依存関係（どのコンポーネントを先に実装するか）

### Step 5: コード生成実行（IG-02）

`prompts/06_code-generation/コード生成実行.md` の指示に従い、tasks.md の計画順にコードを生成する。

各コンポーネントの生成手順：
1. 対応するスケルトンテンプレートを読み込む
2. 詳細設計書の内容をスケルトンに当てはめてコードを生成する
3. `00_rule_directory_structure.md`（R1）に従ってファイルを配置する
4. `00_rule_project_conventions.md`（R7・R8・R9）に準拠していることを確認する

### Step 6: workflow-state.md を「完了」に更新

コード生成が完了したら、該当行を `🔄 作業中` → `✅ 完了` に変更する。

---

## フェーズ完了時の品質チェック

- 生成コードが詳細設計と整合していること
- 命名・構成・責務分割が設計と一致していること
- 実装対象外の未定義項目を推測補完していないこと
- ディレクトリ構造が `00_rule_directory_structure.md`（R1）に準拠していること
- 次の実装・テスト作業へ引き継げる情報が完備していること

合格後、workflow-state.md を以下のように更新する。
- 「品質チェック」列を `✅ 合格` に変更
- 「次アクション待ち状態」を `⏸️ ユーザー指示待ち` に変更

---

## セッション終了時の必須手順（Record Design Decisions）

作業が終了・中断する際（エージェント停止前）に、次セッションへの引き継ぎ情報を
`skills/session-context.md` に上書き更新すること。

記録する内容：
1. 作業中だったタスク・フェーズ（中断した場合は途中状態も含む）
2. このセッションで確定した重要な決定事項（ユーザーが明示的に採用/却下/修正/指示したもの）
3. このセッションで指示されたが、まだ実行されていない未完了の指示

フォーマット：

```markdown
# セッションコンテキスト

## 最終保存日時
YYYY-MM-DD

## 作業中の内容
[フェーズ名・成果物名・進捗状況を簡潔に。作業がなければ「なし」]

## 確定した決定事項
[箇条書きで。なければ「なし」]

## 未完了の指示
[このセッションで指示されたが、まだ実行されていないもの。なければ「なし」]
```

注意：
- 議論中・提案段階のものは記録しない
- 完了済みの指示は記録しない
- ユーザーへのメッセージ出力は不要
