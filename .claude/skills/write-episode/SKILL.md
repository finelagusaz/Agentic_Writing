---
name: write-episode
description: マルチエージェント（editor/author/manager + reader群）によるWeb小説エピソード自動執筆スキル。執筆・改稿・品質判定・確定保存までをオーケストレーションする。特定話数の執筆、読者フィードバック込みの品質判定、再開実行（resume）時に使用。引数は episode_number、任意で --max-revisions=N。
argument-hint: "<episode_number> [--max-revisions=N]"
disable-model-invocation: true
---

# /write-episode — Web小説自動執筆スキル

## 概要

このスキルは、チーム協調で第N話を執筆し、レビューと読者反応を統合して最終稿を保存する。
実行は Step 0〜8 を順次進め、判定に応じてポリッシュまたは改稿ループへ遷移する。
既存の再開状態がある場合は resume ロジックを優先し、中断地点から安全に復帰する。

## 入力

- `$ARGUMENTS`: `episode_number`（必須）
- `--max-revisions=N`（任意、デフォルト `3`）

## 最初に行うこと（必須）

実行開始時の**最初のアクション**として、`.claude/skills/write-episode/resume-logic.md` を Read し、再開チェック手順を適用する。

## 参照ファイルの読み込み規約

- 常時適用: Step 0 完了後（再開時は再開地点の決定直後、最初のステップ実行前）に `.claude/skills/write-episode/common-procedures.md` を Read し、以降すべてのステップで「出力検証」と「ディスカッション管理」を適用する。
- 判定時のみ: Step 6 開始時に `.claude/skills/write-episode/judgment-logic.md` を Read する。
- 確定処理時のみ: Step 7 開始時に `.claude/skills/write-episode/finalization-details.md` を Read する。

## ワークフロー全体

```text
Step 0:  初期化（workspace準備、progress.md作成）
Step 1:  チーム作成 + コアメンバースポーン（editor/author/manager）
Step 2:  編集（方針策定）→ current-direction.md
 └ 2D:  方針ディスカッション（author+manager、最大2ラウンド）
Step 3:  作者（執筆/改稿）→ current-draft.txt → 読者バックグラウンドスポーン
Step 4:  担当者（レビュー）→ manager-review.md
 └ 4D:  ドラフトディスカッション（author+editor、最大2ラウンド）
Step 5:  読者フィードバック回収
Step 6:  判定 → PASS / PASS_WITH_POLISH / REVISION_NEEDED / FORCE_PASS
 ├ 6.5P: ポリッシュ（PASS_WITH_POLISH時のみ）→ Step 7へ
 └ 6.5D: リビジョンディスカッション（REVISION時、最大3ラウンド）→ Step 3へ戻る
Step 7:  確定・保存（episodes/へコピー、summaries/tracker更新）
 ├ 7.5: 申し送り事項更新（editor委任）
 └ 7.6: プロット更新ディスカッション + 品質ログ記録
Step 8:  チームシャットダウン + workspace アーカイブ
```

## 実行規約

- 引数から `episode_number` を取得する。
- `--max-revisions=N` 指定時は `N` を、未指定時は `3` を `max_revisions` とする。
- 以下のステップを自動で順次実行する。
- 各ステップで `progress.md` の `current_step` / `step_status` / チェックボックスを更新する。

---

### Step 0: 初期化

開始条件:
- 再開モードではこのステップをスキップする（`resume-logic.md` に従う）。

実行:
1. `workspace/*.md` と `workspace/*.txt` を探索し、存在するファイルのみ削除する。
2. `workspace/revision-log.md` を作成する（見出し: `# リビジョン履歴 — 第{番号}話`）。
3. `workspace/discussion-log.md` を作成する（見出し: `# ディスカッションログ — 第{番号}話`）。
4. `.claude/skills/write-episode/progress-template.md` を Read し、変数（episode番号、max_revisions、`story/reader-personas.md` のペルソナID一覧）を置換して `workspace/progress.md` を作成する。
5. `archive/episode-{番号:2桁}` を作成する。
6. 前話のエピソード（`episodes/`）の存在を確認する。
7. `revision_count = 0` を初期化する。
8. `story/handover-notes.md` を読み、`[DEFERRED:ep{今回の番号}]` を `[ACTIVE]` に昇格する（該当なしならスキップ）。

完了条件:
- `progress.md`: `current_step: "step0"`, `step_status: "completed"`, `step0` を `[x]`。

---

### Step 1: チーム作成 + コアメンバースポーン

実行:
1. TeamCreate で `novel-ep{番号}` チームを作成する。
2. コア3名を `team_name` 指定ありで並列 Task スポーンする。

| チームメイト | subagent_type | name | model |
|---|---|---|---|
| 編集 | novel-editor | editor | opus |
| 作者 | novel-author | author | opus |
| 担当者 | novel-manager | manager | sonnet |

3. 各メンバーの prompt:
   - 「あなたは第{番号}話の執筆チームの{役割}です。agents/{ファイル}.md を読み込み、チームリーダーからの指示を待ってください。」
4. `story/reader-personas.md` を Read し、全ペルソナ（ID・名前・subagent_type）を取得する。
5. `story/series-tracker.md` の存在と必須見出しを検証する。
   - `## アクション配分（直近3話）`
   - `## キャラクター登場密度（直近5話）`
   - `## 伏線・要素の進展追跡`
   - `## 表現パターン累積（直近5話）`
6. 欠落/破損時は setup-story と同じテンプレートで再生成し、ユーザー通知と `discussion-log.md` 追記を行う（未作成時はヘッダー付きで新規作成してから追記）。

完了条件:
- `progress.md`: `step1` を `[x]`, `current_step: "step1"`, `step_status: "completed"`。

---

### Step 2: 編集（方針策定）

実行:
1. `progress.md` を `step2 in_progress` に更新する。
2. editor に SendMessage する。
   - 目的: 第{番号}話の創作方針策定
   - 参照: `agents/editor.md`、`story/` 主要資料（`series-tracker.md` を最初に読む）、前話エピソード
   - 出力: `workspace/current-direction.md`
3. 完了報告を待ち、出力検証する。
4. 方針固有の構造検証を行う。
   - 「## アクション配分確認」に直前2話の区分がある。
   - 「## エピソードタイプ・文字数」にA/B/C指定と文字数目安がある。
   - 「## 伏線・布石」に「tracker警告への対応」がある。
   - `story/series-tracker.md` の警告事項と整合する（不足時は editor に再出力依頼）。

完了条件:
- `progress.md`: `step2` を `[x]`, `current_step: "step2"`, `step_status: "completed"`。

---

### Step 2D: 方針ディスカッション

実行:
1. `progress.md` を `step2d in_progress` に更新する。
2. 共通手順のディスカッション管理に従って招待する。
   - author: `workspace/current-direction.md` を確認し、実現可能性・構成観点の意見を共有。なければ「方針了解」。
   - manager: `workspace/current-direction.md` を確認し、品質・設定整合性観点の意見を共有。なければ「問題なし」。
3. 最大2ラウンド実施する。
4. editor が direction を更新した場合は出力検証する。
5. `discussion-log.md` に記録する。

完了条件:
- `progress.md`: `step2d` を `[x]`, `current_step: "step2d"`, `step_status: "completed"`。

---

### Step 3: 作者（執筆 / 改稿）

実行:
1. `progress.md` を `step3 in_progress` に更新する。
2. author に SendMessage する。
   - 初稿（`revision_count == 0`）:
     - `agents/author.md` に従い、`workspace/current-direction.md`（最優先）と `story/` 主要資料・前話を参照する。
     - `workspace/current-draft.txt` に本文のみ出力する。
   - 改稿（`revision_count > 0`）:
     - `workspace/current-draft.txt` と `workspace/consolidated-feedback.md` を参照して改稿する。
     - `workspace/current-draft.txt` を上書きし、本文のみ出力する。
3. 完了報告を待ち、出力検証する。

完了条件:
- `progress.md`: `step3` を `[x]`, `current_step: "step3"`, `step_status: "completed"`。

#### Step 3 完了直後: 読者バックグラウンドスポーン

実行:
1. Step 3 の出力検証成功直後に読者をスポーンする（Step 4/4D と並行安全）。
2. `story/reader-personas.md` から各ペルソナを取得し、`team_name` なし・`run_in_background: true` で並列 Task スポーンする。
3. 各読者の `subagent_type` と `name`（`reader-{ペルソナID}`）は `reader-personas.md` に従う。
4. 各読者 prompt:
   - `workspace/current-draft.txt` を読み、`agents/readers/reader-template.md` に従って `workspace/reader-feedback-{ペルソナID}.md` に出力する。
   - 設定整合性担当ペルソナには `story/setting.md`, `story/characters.md`, `story/episode-summaries.md`（アーク要約 + 直近エピソード詳細）, `story/handover-notes.md`, `workspace/current-direction.md` も参照させる。
5. `progress.md` の「Step 5 Detail」を全ペルソナ `[ ]` で初期化し、各読者 Task ID を記録する。

---

### Step 4: 担当者（レビュー）

実行:
1. `progress.md` を `step4 in_progress` に更新する。
2. manager に SendMessage する。
   - 初稿（`revision_count == 0`）:
     - `agents/manager.md` に従い、`workspace/current-direction.md`, `workspace/current-draft.txt`, `story/` 主要資料, `story/series-tracker.md` を参照する。
     - 現在の回数 `{revision_count}/{max_revisions}` を明示する。
     - `workspace/manager-review.md` に出力する。
   - 改稿（`revision_count > 0`）:
     - 上記に加え `workspace/revision-log.md`, `workspace/consolidated-feedback.md` を参照し、改善確認を行う。
     - `workspace/manager-review.md` に上書き出力する。
3. 完了報告を待ち、出力検証する。

完了条件:
- `progress.md`: `step4` を `[x]`, `current_step: "step4"`, `step_status: "completed"`。

---

### Step 4D: ドラフトディスカッション

開始条件:
- `workspace/manager-review.md` の出力検証が完了している。

実行:
1. `progress.md` を `step4d in_progress` に更新する。
2. 共通手順のディスカッション管理に従って招待する。
   - author: `workspace/manager-review.md` を確認し、必要時のみ意図説明（判定への異議は行わない）。なければ「確認しました」。
   - editor: `workspace/manager-review.md` を確認し、方針整合の気づきを共有。なければ「確認しました」。
3. 最大2ラウンド実施する。
4. **manager の判定は変更しない**（書面先行ルール）。
5. `discussion-log.md` に記録する。

完了条件:
- `progress.md`: `step4d` を `[x]`, `current_step: "step4d"`, `step_status: "completed"`。

---

### Step 5: 読者フィードバック回収

実行:
1. `progress.md` を `step5 in_progress` に更新する。
2. 通常フロー:
   - Step 3 で記録した各読者 Task ID を使い、TaskOutput（`block: true`）で完了を待つ。
   - 全ペルソナを並列で待機する。
3. 再開フォールバック:
   - 再開時などで未スポーンなら、Step 3 完了時と同手順で未完了分のみスポーンする。
   - `progress.md` の「Step 5 Detail」で `[x]` ペルソナは Glob + Read で検証成功なら再スポーンしない。
4. 共通検証:
   - 各 `workspace/reader-feedback-{ペルソナID}.md` を個別検証する。
   - 失敗分のみリトライする。
   - 検証成功したペルソナから「Step 5 Detail」を `[x]` に更新する。

完了条件:
- `progress.md`: `step5` を `[x]`, `current_step: "step5"`, `step_status: "completed"`。

---

### Step 6: 判定

実行:
1. `progress.md` を `step6 in_progress` に更新する。
2. `.claude/skills/write-episode/judgment-logic.md` を Read し、「Step 6: 判定ロジック」を実行する。
3. 判定に応じて遷移する。
   - `PASS` -> Step 7
   - `PASS_WITH_POLISH` -> Step 6.5P
   - `FORCE_PASS` -> Step 7（警告付き）
   - `REVISION_NEEDED` -> Step 6.5D

---

### Step 6.5P: ポリッシュ（PASS_WITH_POLISH のみ）

実行:
1. `.claude/skills/write-episode/judgment-logic.md` の「Step 6.5P」に従う。
2. 完了後 Step 7 へ進む。

---

### Step 6.5D: リビジョンディスカッション（REVISION_NEEDED のみ）

実行:
1. 共通手順のディスカッション管理に従い、全コアメンバーへ送信する。
2. editor への SendMessage:
   - リビジョン必要（`{revision_count}/{max_revisions}` 回目）。
   - 判定情報: `Manager={judgment}`, 読者 `★`（各ペルソナ + 平均）、深刻度（通常改稿/重大改稿）。
   - `workspace/manager-review.md` と `workspace/reader-feedback-*.md` を確認させる。
   - `agents/editor.md` の「リビジョン時の対応」に従って優先順位を検討させる。
   - author/manager と議論し `workspace/consolidated-feedback.md` を作成させる。
   - 方針修正が必要なら `workspace/current-direction.md` も更新させる。
3. author への SendMessage:
   - 判定情報を共有し、改稿実現可能性の観点で意見を求める。
   - editor との議論協力を依頼し、なければ「確認しました」。
4. manager への SendMessage:
   - 判定情報を共有し、レビュー重点の補足を求める。
   - editor/author との議論参加を依頼し、なければ「追加情報なし」。
5. 最大3ラウンド実施する。
6. editor が `workspace/consolidated-feedback.md` を出力した時点で終了し、出力検証する。
7. `discussion-log.md` に記録する。
8. `progress.md` を `current_step: "step6.5d"`, `step_status: "completed"` に更新する。

遷移:
- Step 3 に戻って改稿する。

---

### Step 7: 確定・保存

実行:
1. `progress.md` を `step7 in_progress` に更新する。
2. リーダー（あなた自身）が直接実行する。
   - `workspace/current-direction.md` からエピソードタイトルを取得する。
   - `workspace/current-draft.txt` を `episodes/{番号:2桁}_{タイトル}.txt` へコピーする。
   - `.claude/skills/write-episode/finalization-details.md` を Read し、「episode-summaries.md 更新ルール」と「series-tracker.md 更新ルール」に従って更新する。
3. `progress.md` を `step7 completed` に更新する。
4. Step 7.5 と Step 7.6 を `finalization-details.md` の該当セクションに従って実行する。

順序保証:
- workspace のアーカイブ/クリーンは Step 8 終盤で実施する（Step 7.5 が workspace を参照するため）。

---

### Step 7.5: 申し送り事項更新

実行:
1. `progress.md` を `step7.5 in_progress` に更新する。
2. `finalization-details.md` の「Step 7.5」に従い、editor に申し送り事項更新を委任する。

---

### Step 7.6: プロット更新ディスカッション + 品質ログ

実行:
1. `progress.md` を `step7.6 in_progress` に更新する。
2. `finalization-details.md` の「Step 7.6」に従い、プロット更新ディスカッションと品質ログ記録を行う。

---

### Step 8: チームシャットダウン

実行:
1. `progress.md` を `step8 in_progress` に更新する。
2. 全コアメンバー（editor, author, manager）へ `shutdown_request` を送る。
3. 全員のシャットダウン確認後に TeamDelete を実行する。
4. `progress.md` を `step8 completed` に更新する。
5. `workspace/` の全ファイル（`progress.md`, `discussion-log.md` を含む）を `archive/episode-{番号:2桁}/` にコピーする。
6. アーカイブ完了後に `workspace/` をクリーンアップする。

---

### 完了報告（ユーザー向け）

以下を必ず報告する。

- エピソードタイトル
- 保存先ファイルパス
- リビジョン回数
- 最終の担当者判定
- 読者評価（3名分の★と平均・中央値）
- ディスカッション発生回数（議論が発生したフェーズ一覧）
- ポリッシュ発動の有無（Step 6.5P 実行有無と修正箇所数）
- プロット更新の有無（Step 7.6 で `plot-outline.md` を更新したか）
- `FORCE_PASS` の場合は警告メッセージ
