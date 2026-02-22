---
name: write-episode
description: マルチエージェントチームでWeb小説のエピソードを自動執筆する。引数にエピソード番号を指定（例: /write-episode 1）
argument-hint: "<episode_number> [--max-revisions=N]"
disable-model-invocation: true
---

# /write-episode — Web小説自動執筆スキル

## 概要

エージェントチーム機能を活用し、コアメンバー（編集・作者・担当者）がSendMessageで議論しながらエピソードを執筆するオーケストレーション。読者3名はサブエージェントとして生の読者反応を提供する。

## 引数

- `$ARGUMENTS` — エピソード番号（例: `1`）。オプションで `--max-revisions=N`（デフォルト3）

## 再開（レジュメ）ロジック

実行手順の**最初のアクション**として、`.claude/skills/write-episode/resume-logic.md` を Read で読み込み、記載された再開チェック手順に従う。

## ワークフローチェックリスト

```
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

## 参照ファイル

以下の参照ファイルは、該当タイミングで Read で読み込む:

| ファイル | 読むタイミング |
|---------|--------------|
| `common-procedures.md` | Step 0 完了後（以降全ステップで適用） |
| `judgment-logic.md` | Step 6 開始時 |
| `finalization-details.md` | Step 7 の詳細処理時 |

## 実行手順

引数からエピソード番号を取得してください。`--max-revisions=N` が指定されていればその値を、なければ3をリビジョン上限とします。

以下の全ステップを**自動的に**順次実行してください。

***

### 共通手順

`.claude/skills/write-episode/common-procedures.md` を Read で読み込み、以降全ステップで「エージェント出力の検証」「ディスカッション管理」の手順を適用する。

***

### Step 0: 初期化

**このステップは再開モードではスキップされる（「再開ロジック」参照）。**

1. Glob で `workspace/*.md` と `workspace/*.txt` を検索し、存在するファイルのみ `rm -f` で削除
2. `workspace/revision-log.md` を作成: `# リビジョン履歴 — 第{番号}話`
3. `workspace/discussion-log.md` を作成: `# ディスカッションログ — 第{番号}話`
4. `.claude/skills/write-episode/progress-template.md` を Read で読み込み、変数（episode番号、max_revisions、`story/reader-personas.md` のペルソナID一覧）を置換して `workspace/progress.md` を作成
5. `mkdir -p archive/episode-{番号:2桁}` でアーカイブディレクトリを事前作成
6. 前話のエピソード（episodes/ 内）が存在するか確認
7. revision_count = 0 として初期化
8. `story/handover-notes.md` を読み込み、`[DEFERRED:ep{今回の番号}]` タグ付き項目を `[ACTIVE]` に昇格（該当なしならスキップ）
9. **progress.md を更新**: `current_step: "step0"`, `step_status: "completed"`, step0 を `[x]` に

***

### Step 1: チーム作成 + コアメンバースポーン

TeamCreate で `"novel-ep{番号}"` チームを作成し、コアメンバー3名を並列で Task スポーンする（team_name 指定あり）:

| チームメイト | subagent_type | name | model |
|------------|---------------|------|-------|
| 編集 | novel-editor | editor | opus |
| 作者 | novel-author | author | opus |
| 担当者 | novel-manager | manager | sonnet |

各メンバーの prompt: 「あなたは第{番号}話の執筆チームの{役割}です。agents/{ファイル}.md を読み込み、チームリーダーからの指示を待ってください。」

`story/reader-personas.md` を Read で読み込み、全ペルソナの一覧（ID、名前、subagent_type）を取得しておく。

**series-tracker 自動復旧**: `story/series-tracker.md` の存在と必須セクション見出し（`## アクション配分（直近3話）`, `## キャラクター登場密度（直近5話）`, `## 伏線・要素の進展追跡`, `## 表現パターン累積（直近5話）`）を確認。欠落・破損時は setup-story と同じテンプレートで再生成し、ユーザーに通知、discussion-log.md に再生成の事実を追記する（discussion-log.md が存在しない場合はヘッダー付きで新規作成してから追記）。

progress.md を更新: step1 を `[x]`、`current_step: "step1"`, `step_status: "completed"`

***

### Step 2: 編集（方針策定）

progress.md を更新: `current_step: "step2"`, `step_status: "in_progress"`

SendMessage で **editor** に指示: 第{番号}話の創作方針を策定。agents/editor.md に従い、story/ の主要資料（series-tracker.md を最初に読むこと）と前話エピソードを参照し、`workspace/current-direction.md` に出力。完了報告を待ち出力を検証。

#### 方針固有の構造検証

共通の出力検証に加え、以下を確認:
1. 「## アクション配分確認」セクションに直前2話の区分が記入されているか
2. 「## エピソードタイプ・文字数」セクションにA/B/C指定と文字数目安があるか
3. 「## 伏線・布石」セクションに「tracker警告への対応」の記載があるか
4. `story/series-tracker.md` の警告事項と方針の整合性（警告への対応が欠けていればeditorに再出力依頼）

progress.md を更新: step2 を `[x]`、`current_step: "step2"`, `step_status: "completed"`

***

### Step 2D: 方針ディスカッション

progress.md を更新: `current_step: "step2d"`, `step_status: "in_progress"`

**共通手順: ディスカッション管理**に従い招待:
- **author** に SendMessage: `workspace/current-direction.md` を確認。執筆の実現可能性・構成の観点から意見を共有。なければ「方針了解」と報告。
- **manager** に SendMessage: `workspace/current-direction.md` を確認。品質・設定整合性の観点から意見を共有。なければ「問題なし」と報告。

最大2ラウンド。editor が direction を更新した場合は出力を検証。discussion-log.md に記録。

progress.md を更新: step2d を `[x]`、`current_step: "step2d"`, `step_status: "completed"`

***

### Step 3: 作者（執筆 / 改稿）

progress.md を更新: `current_step: "step3"`, `step_status: "in_progress"`

SendMessage で **author** に指示:
- **初稿**（revision_count == 0）: 第{番号}話を執筆。agents/author.md に従い、`workspace/current-direction.md`（最優先）と story/ の主要資料・前話エピソードを参照し、`workspace/current-draft.txt` に本文のみ出力。
- **改稿**（revision_count > 0）: `workspace/current-draft.txt`（現行ドラフト）と `workspace/consolidated-feedback.md`（主要な指針）を読み込み改稿。`workspace/current-draft.txt` を上書き。本文のみ出力。

完了報告を待ち出力を検証。progress.md を更新: step3 を `[x]`、`current_step: "step3"`, `step_status: "completed"`

#### Step 3 完了時: 読者バックグラウンドスポーン

Step 3 の出力検証成功直後、読者をバックグラウンドスポーンする（Step 4/4D はドラフト不変のため並行安全）。

`story/reader-personas.md` から各ペルソナを取得し、**team_name なし**、**run_in_background: true** で並列 Task スポーン。各読者の subagent_type と name（`reader-{ペルソナID}`）は reader-personas.md に従う。

各読者への prompt: `workspace/current-draft.txt` を読み、agents/readers/reader-template.md に従いフィードバックを `workspace/reader-feedback-{ペルソナID}.md` に出力。設定整合性担当ペルソナには story/setting.md, characters.md, episode-summaries.md（アーク要約＋直近エピソード詳細の両方）, handover-notes.md, current-direction.md も参照させる。

progress.md の「Step 5 Detail」を初期化（全ペルソナ `[ ]`）。各読者の Task ID を記録。

***

### Step 4: 担当者（レビュー）

progress.md を更新: `current_step: "step4"`, `step_status: "in_progress"`

SendMessage で **manager** に指示:
- **初稿**（revision_count == 0）: ドラフトを評価。agents/manager.md に従い、`workspace/current-direction.md`, `workspace/current-draft.txt`, story/ の主要資料, `story/series-tracker.md` を参照。現在のリビジョン回数は {revision_count}/{max_revisions}。`workspace/manager-review.md` に出力。
- **改稿**（revision_count > 0）: 改稿版を再評価。`workspace/revision-log.md`, `workspace/consolidated-feedback.md` も参照し前回との改善を確認。`workspace/manager-review.md` に上書き。

完了報告を待ち出力を検証。progress.md を更新: step4 を `[x]`、`current_step: "step4"`, `step_status: "completed"`

***

### Step 4D: ドラフトディスカッション

**書面先行ルール**: `manager-review.md` の出力検証済み後にのみ開始。

progress.md を更新: `current_step: "step4d"`, `step_status: "in_progress"`

**共通手順: ディスカッション管理**に従い招待:
- **author** に SendMessage: `workspace/manager-review.md` を確認。指摘への意図の説明が必要なら manager にメッセージ（判定への異議ではなく意図の説明に留める）。なければ「確認しました」と報告。
- **editor** に SendMessage: `workspace/manager-review.md` を確認。方針との整合性で気づいた点を共有。なければ「確認しました」と報告。

最大2ラウンド。**担当者の判定は変更しない**（書面先行ルール）。discussion-log.md に記録。

progress.md を更新: step4d を `[x]`、`current_step: "step4d"`, `step_status: "completed"`

***

### Step 5: 読者フィードバック回収

読者は Step 3 完了時にバックグラウンドスポーン済み。このステップでは回収と検証のみ。

progress.md を更新: `current_step: "step5"`, `step_status: "in_progress"`

#### 通常フロー

Step 3 で記録した各読者の Task ID を使い、TaskOutput で完了を待つ（block: true）。全ペルソナを並列で待機。

#### 再開フォールバック

セッション再開時など読者未スポーンの場合は、ここでスポーン（Step 3 完了時と同じ手順）。progress.md の「Step 5 Detail」で `[x]` のペルソナは Glob + Read で検証し、成功なら再スポーンしない。未完了 `[ ]` のペルソナのみスポーン。

#### 共通: 出力検証

各 `workspace/reader-feedback-{ペルソナID}.md` を個別に検証（共通手順に従う）。失敗分のみリトライ。各ペルソナの検証成功時に progress.md の「Step 5 Detail」を `[x]` に更新。

progress.md を更新: step5 を `[x]`、`current_step: "step5"`, `step_status: "completed"`

***

### Step 6: 判定

progress.md を更新: `current_step: "step6"`, `step_status: "in_progress"`

`.claude/skills/write-episode/judgment-logic.md` を Read で読み込み、「Step 6: 判定ロジック」に従って判定を実行する。

判定結果に応じた遷移:
- **PASS** → Step 7
- **PASS_WITH_POLISH** → Step 6.5P
- **FORCE_PASS** → Step 7（警告付き）
- **REVISION_NEEDED** → Step 6.5D

***

### Step 6.5P: ポリッシュ【PASS_WITH_POLISH 時のみ】

`.claude/skills/write-episode/judgment-logic.md` の「Step 6.5P」セクションに従って実行する。完了後 **Step 7 へ**。

***

### Step 6.5D: リビジョンディスカッション【REVISION時のみ】

Step 6 で REVISION_NEEDED と判定された場合にのみ実行。

**共通手順: ディスカッション管理**に従い、全コアメンバーに以下を送信:

**editor** に SendMessage: リビジョン必要（{revision_count}/{max_revisions}回目）。判定: Manager={judgment}, 読者={各ペルソナ名}★{N}（平均★{avg}）, 深刻度={通常改稿/重大改稿}。`workspace/manager-review.md` と `workspace/reader-feedback-*.md` を確認し、agents/editor.md の「リビジョン時の対応」に従い改稿の優先順位を検討、author/manager と議論の上 `workspace/consolidated-feedback.md` を作成。方針修正が必要なら `workspace/current-direction.md` も更新。

**author** に SendMessage: リビジョン必要（{revision_count}/{max_revisions}回目）。判定: Manager={judgment}, 読者={各ペルソナ名}★{N}（平均★{avg}）。フィードバックファイルを確認し、改稿の実現可能性の観点から意見。editor と議論に協力。なければ「確認しました」と報告。

**manager** に SendMessage: リビジョン必要（{revision_count}/{max_revisions}回目）。判定: Manager={judgment}, 読者={各ペルソナ名}★{N}（平均★{avg}）。レビュー重点の補足があれば共有。editor/author と議論に参加。なければ「追加情報なし」と報告。

最大3ラウンド。editor が `consolidated-feedback.md` を出力した時点で終了。出力を検証。discussion-log.md に記録。

progress.md を更新: `current_step: "step6.5d"`, `step_status: "completed"`

**Step 3 に戻る**（改稿）。

***

### Step 7: 確定・保存

progress.md を更新: `current_step: "step7"`, `step_status: "in_progress"`

リーダー（あなた自身）が直接実行する:

1. エピソードタイトルを `workspace/current-direction.md` から取得
2. `workspace/current-draft.txt` を `episodes/{番号:2桁}_{タイトル}.txt` にコピー
3. `.claude/skills/write-episode/finalization-details.md` を Read で読み込み、「episode-summaries.md 更新ルール」と「series-tracker.md 更新ルール」に従って更新

progress.md を更新: step7 を `[x]`、`current_step: "step7"`, `step_status: "completed"`

> **順序保証**: workspace のアーカイブ/クリーンは Step 8 の終盤で実行する。Step 7.5 は workspace/ のファイルを参照するため。

→ Step 7.5, 7.6 を実行（`finalization-details.md` の該当セクションに従う）

***

### Step 7.5: 申し送り事項更新

progress.md を更新: `current_step: "step7.5"`, `step_status: "in_progress"`

`finalization-details.md` の「Step 7.5」セクションに従い、editor に申し送り事項更新を委任する。

***

### Step 7.6: プロット更新ディスカッション + 品質ログ

progress.md を更新: `current_step: "step7.6"`, `step_status: "in_progress"`

`finalization-details.md` の「Step 7.6」セクションに従い、プロット更新ディスカッションと品質ログ記録を実行する。

***

### Step 8: チームシャットダウン

progress.md を更新: `current_step: "step8"`, `step_status: "in_progress"`

全コアチームメイト（editor, author, manager）に `shutdown_request` を送り、全員がシャットダウンしたことを確認してから TeamDelete を実行する。

progress.md を更新: step8 を `[x]`、`current_step: "step8"`, `step_status: "completed"`

1. workspace/ の全ファイルを `archive/episode-{番号:2桁}/` にコピー（progress.md, discussion-log.md を含む）
2. workspace/ をクリーン（アーカイブ完了後に全ファイルを削除）

***

### 完了報告

以下の情報をユーザーに報告:
- エピソードタイトル
- 保存先ファイルパス
- リビジョン回数
- 最終の担当者判定
- 読者評価（3名分の★と平均・中央値）
- ディスカッション発生回数（議論が発生したフェーズの一覧）
- ポリッシュ発動の有無（Step 6.5P の実行有無と修正箇所数）
- プロット更新の有無（Step 7.6 で plot-outline.md が更新されたか）
- FORCE_PASS の場合は警告メッセージ
