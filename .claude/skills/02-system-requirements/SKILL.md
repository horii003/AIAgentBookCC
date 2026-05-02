---
name: strands-02-system-requirements
description: Strands Agents SDKのAIエージェント開発ワークフローのシステム要件定義フェーズ（02_system-requirements）を実行するスキル。「機能要件一覧を作って」「エージェント一覧を作成したい」「機能ツール一覧を書いて」「自律度・権限定義を作りたい」「会話フロー一覧を作って」「システム構成図を書いて」「ガードレール要件定義を作って」「評価指標一覧を書いて」など、システム要件定義フェーズの成果物作成に関する指示があれば必ずこのスキルを使用する。AIエージェント開発、Strands、システム要件、エージェント設計のキーワードが出た場合にも積極的にこのスキルを適用する。
---

# 02_system-requirements フェーズ スキル

Strands Agents SDKのAIエージェント開発ワークフローにおけるシステム要件定義フェーズの成果物を、
prompt・templateに基づいて作成するスキル。

パスはすべて `.claude/skills/` からの相対パスで記載する。

---

## セッション開始時の必須手順

このスキルが呼び出されたら、作業開始前に必ず以下を実行すること。

1. `.claude/skills/workflow-state.md` を読み込む
2. `.claude/skills/session-context.md` を読み込む
3. **「次アクション待ち状態」欄を最初に確認する**
   - `⏸️ ユーザー指示待ち` の場合 → **作業を一切開始しない**。現在の状態を報告して指示を待つ
   - `⏸️ ユーザー指示待ち（第2周確認）` の場合 → **作業を一切開始しない**。「第1周が完了しています。第2周（未定義項目の補完）に進みますか？」と確認して指示を待つ
   - `▶️ 作業中` の場合 → 次のステップへ進む
4. 「現在のフェーズ」と各成果物の状態を確認する
5. `✅ 完了` の成果物は再作成しない
6. `🔲 未着手` または `🔄 作業中` の成果物のみを作業対象とする

> **重要**: session-context.md の「次のステップ」に次フェーズの作業が記載されていても、
> workflow-state.md の「次アクション待ち状態」が `⏸️ ユーザー指示待ち` であれば作業を開始してはならない。
> workflow-state.md の記載が最終的な判断根拠である。

---

## 成果物と参照ファイル一覧

作成順序は `default_sequence`（下表の順）を厳守すること。

| # | 成果物名 | ID | prompt | template | 出力先 |
|---|---|---|---|---|---|
| 1 | 機能要件一覧 | SR-03 | `prompts/02_system-requirements/機能要件一覧.md` | `templates/02_system-requirements/機能要件一覧.md` | `../artifacts/02_system-requirements/outputs/機能要件一覧.md` |
| 2 | エージェント一覧 | SR-04 | `prompts/02_system-requirements/エージェント一覧.md` | `templates/02_system-requirements/エージェント一覧.md` | `../artifacts/02_system-requirements/outputs/エージェント一覧.md` |
| 3 | 機能ツール一覧 | SR-17 | `prompts/02_system-requirements/機能ツール一覧.md` | `templates/02_system-requirements/機能ツール一覧.md` | `../artifacts/02_system-requirements/outputs/機能ツール一覧.md` |
| 4 | 自律度・権限定義 | SR-05 | `prompts/02_system-requirements/自律度・権限定義.md` | `templates/02_system-requirements/自律度・権限定義.md` | `../artifacts/02_system-requirements/outputs/自律度・権限定義.md` |
| 5 | 根拠提示方針 | SR-07 | `prompts/02_system-requirements/根拠提示方針.md` | `templates/02_system-requirements/根拠提示方針.md` | `../artifacts/02_system-requirements/outputs/根拠提示方針.md` |
| 6 | 会話フロー一覧 | SR-09 | `prompts/02_system-requirements/会話フロー一覧.md` | `templates/02_system-requirements/会話フロー一覧.md` | `../artifacts/02_system-requirements/outputs/会話フロー一覧.md` |
| 7 | アウトプット一覧 | SR-08 | `prompts/02_system-requirements/アウトプット一覧.md` | `templates/02_system-requirements/アウトプット一覧.md` | `../artifacts/02_system-requirements/outputs/アウトプット一覧.md` |
| 8 | データ一覧 | SR-10 | `prompts/02_system-requirements/データ一覧.md` | `templates/02_system-requirements/データ一覧.md` | `../artifacts/02_system-requirements/outputs/データ一覧.md` |
| 9 | テーブル一覧 | SR-11 | `prompts/02_system-requirements/テーブル一覧.md` | `templates/02_system-requirements/テーブル一覧.md` | `../artifacts/02_system-requirements/outputs/テーブル一覧.md` |
| 10 | ナレッジ一覧 | SR-12 | `prompts/02_system-requirements/ナレッジ一覧.md` | `templates/02_system-requirements/ナレッジ一覧.md` | `../artifacts/02_system-requirements/outputs/ナレッジ一覧.md` |
| 11 | 業務ルール定義 | SR-16 | `prompts/02_system-requirements/業務ルール定義.md` | `templates/02_system-requirements/業務ルール定義.md` | `../artifacts/02_system-requirements/outputs/業務ルール定義.md` |
| 12 | エージェント間連携定義 | SR-06 | `prompts/02_system-requirements/エージェント間連携定義.md` | `templates/02_system-requirements/エージェント間連携定義.md` | `../artifacts/02_system-requirements/outputs/エージェント間連携定義.md` |
| 13 | 外部システム機能一覧 | SR-15 | `prompts/02_system-requirements/外部システム機能一覧.md` | `templates/02_system-requirements/外部システム機能一覧.md` | `../artifacts/02_system-requirements/outputs/外部システム機能一覧.md` |
| 14 | システム構成図 | SR-01 | `prompts/02_system-requirements/システム構成図.md` | `templates/02_system-requirements/システム構成図.md` | `../artifacts/02_system-requirements/outputs/システム構成図.md` |
| 15 | システム構成図の構成要素一覧 | SR-02 | `prompts/02_system-requirements/システム構成図の構成要素一覧.md` | `templates/02_system-requirements/システム構成図の構成要素一覧.md` | `../artifacts/02_system-requirements/outputs/システム構成図の構成要素一覧.md` |
| 16 | ログ出力要件定義 | SR-14 | `prompts/02_system-requirements/ログ出力要件定義.md` | `templates/02_system-requirements/ログ出力要件定義.md` | `../artifacts/02_system-requirements/outputs/ログ出力要件定義.md` |
| 17 | ガードレール要件定義 | SR-13 | `prompts/02_system-requirements/ガードレール要件定義.md` | `templates/02_system-requirements/ガードレール要件定義.md` | `../artifacts/02_system-requirements/outputs/ガードレール要件定義.md` |
| 18 | 評価指標一覧 | SR-19 | `prompts/02_system-requirements/評価指標一覧.md` | `templates/02_system-requirements/評価指標一覧.md` | `../artifacts/02_system-requirements/outputs/評価指標一覧.md` |
| 19 | 画面一覧（GUIアプリの場合のみ） | SR-18 | `prompts/02_system-requirements/画面一覧.md` | `templates/02_system-requirements/画面一覧.md` | `../artifacts/02_system-requirements/outputs/画面一覧.md` |
| 99 | フェーズ品質チェック | SR-PHASE-REVIEW | — | — | `../artifacts/02_system-requirements/reviews/フェーズ品質チェック_review.md` |

> **注意**: 画面一覧（SR-18）はGUIアプリの場合のみ作成する。CLIやAPIのみのシステムでは省略する。

### 主な依存関係（前フェーズ）

このフェーズの全成果物は 01_business-requirements の成果物（BR-01〜BR-07）に依存する。
また、フェーズ内では SR-03 → SR-04 → SR-17, SR-05, SR-07, SR-08, SR-09 → ... の順に依存が連鎖する。

---

## 基本方針

### 0. 不明点は必ずユーザーに確認すること
- 指示が不明確・曖昧な場合は、推測や補完を行わず、必ずユーザーに確認してから作業を開始する

### 1. 失敗時はユーザーに報告して停止すること
- 処理が失敗した場合は、即座に作業を停止する
- 自動リトライや続行は行わず、必ずユーザーの指示を待つ

### 2. 出力は日本語・テンプレート準拠で行うこと
- すべての出力は日本語で記述する
- コードの識別子（変数名・関数名・クラス名など）は英語、コメントは日本語
- 成果物の本文には、テンプレートに定義されていない解説・補足・注釈を混在させない

### 3. フェーズ間の自動進行禁止（最重要）
- このフェーズが完了しても、次フェーズ（03_system-design）へ自動的に進んではならない
- フェーズ完了後は以下のメッセージを提示して待機する

```
✅ 02_system-requirements が完了しました。
次フェーズ（03_system-design）を開始する場合は、その旨を指示してください。
```

---

## 成果物作成手順

### Step 1: 前フェーズ成果物の確認

`../artifacts/01_business-requirements/outputs/` 配下の全成果物が揃っていることを確認する。
不足がある場合はユーザーに報告して停止する。

### Step 2: 依存成果物の未定義項目チェック

作業対象成果物の依存成果物を読み込み、以下のパターンを検索する。
- `要件上未定義`
- `〇〇フェーズで定義`
- `TBD`

発見した場合は即座に停止し、以下の形式で報告する。

```
⚠️ 作業開始不可：依存成果物に未定義項目があります

| ファイル | 項目 | 記載内容 |
|---|---|---|
| [ファイル名] | [項目名] | [記載内容] |

上記を定義・解決してから再度依頼してください。
未定義のまま進める場合は、その旨を明示的に指示してください。
```

ただし、**フェーズ内の第1周作業中**で依存先が同フェーズの未作成成果物の場合は、
ユーザー確認なしで続行してよい（`要件上未定義` として記載する）。

### Step 3: workflow-state.md を「作業中」に更新

成果物の作成開始直前に、該当行を `🔲 未着手` → `🔄 作業中` に変更する。

### Step 4: prompt と template の読み込み

1. 対象成果物の **prompt ファイル** を読み込む（作成指示・観点を把握）
2. 対象成果物の **template ファイル** を読み込む（出力形式を把握）
- 次の成果物の prompt / template は、その成果物の作成開始時に初めて読み込む
- フェーズ開始時に全成果物の prompt / template を一括読み込みしてはならない

### Step 5: 成果物の生成

- template の全セクションを含めて作成する（省略・独自形式は禁止）
- prompt に記載された指示・観点に従って内容を記述する
- 依存成果物に `要件上未定義` とある項目は `要件上未定義` のまま引き継ぐ（推測・補完禁止）

### Step 6: 個別品質チェック

作成完了後に、prompt に記載された受入基準のみを確認する。
prompt に記載されていない独自のチェック項目を追加してはならない。

### Step 7: workflow-state.md を「完了」に更新

成果物を1件作成完了したら、該当行を `🔄 作業中` → `✅ 完了` に変更する。

### Step 8: 複数周回の判断

フェーズ内の全成果物の第1周作成が完了したら、以下の両条件を確認する。

- 条件1: フェーズ内の成果物が**同フェーズ内の別の成果物**を `depends_on` に持つ
- 条件2: その依存先成果物が、1周目の作成時点でまだ未作成だった（`要件上未定義` が存在する）

**両条件を満たす場合のみ**第2周が必要。workflow-state.md を更新し、以下を確認する。

```
✅ 第1周完了：フェーズ内の全成果物を一巡しました。
第2周（未定義項目の補完）に進みますか？
```

両条件を満たさない場合は、確認メッセージを出さずに品質チェックへ直接進む。

---

## フェーズ完了時の品質チェック

フェーズ内の全成果物が作成完了した後にまとめて確認する。個別作成中には実施しない。

- すべての成果物がテンプレートに準拠していること
- 業務要件との整合性が保たれていること
- 次フェーズへの引き継ぎ情報が完備していること

品質チェック結果は `../artifacts/02_system-requirements/reviews/フェーズ品質チェック_review.md` に保存する。

合格後、workflow-state.md を以下のように更新する。
- 「品質チェック」列を `✅ 合格` に変更
- 「現在のフェーズ」を `03_system-design` に更新
- 「次アクション待ち状態」を `⏸️ ユーザー指示待ち` に変更

---

## セッション終了時の必須手順（Record Design Decisions）

作業が終了・中断する際（エージェント停止前）に、次セッションへの引き継ぎ情報を
`.claude/skills/session-context.md` に上書き更新すること。

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
