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

## 実行手順

引数からエピソード番号を取得してください。`--max-revisions=N` が指定されていればその値を、なければ3をリビジョン上限とします。

以下の全ステップを**自動的に**順次実行してください。

***

### Step 0: 初期化

**このステップは再開モードではスキップされる（「再開ロジック」参照）。**

1. Glob ツールで `workspace/*.md` と `workspace/*.txt` を検索し、ファイルが存在する場合のみ `rm -f` で削除する（zsh のグロブエラーを回避するため、ファイルが存在しない場合はスキップする）
2. `workspace/revision-log.md` を作成（空テンプレート）:
   ```
   # リビジョン履歴 — 第{番号}話
   ```
3. `workspace/discussion-log.md` を作成（空テンプレート）:
   ```
   # ディスカッションログ — 第{番号}話
   ```
4. `.claude/skills/write-episode/progress-template.md` を Read で読み込み、変数（episode番号、max_revisions、`story/reader-personas.md` のペルソナID一覧）を置換して `workspace/progress.md` を作成する
5. `mkdir -p archive/episode-{番号:2桁}` でアーカイブディレクトリを事前作成する
6. 前話のエピソード（episodes/ 内）が存在するか確認
7. revision_count = 0 として初期化
8. `story/handover-notes.md` を読み込み、`[DEFERRED:ep{今回の番号}]` のタグが付いた項目を `[ACTIVE]` に昇格する（該当項目がなければスキップ）
9. **progress.md を更新**: `current_step: "step0"`, `step_status: "completed"`, step0 を `[x]` に

***

### 共通手順: エージェント出力の検証

各ステップでエージェントの完了報告（idle通知）を受けた後、以下の手順で出力を検証する:

1. Glob ツールで期待されるファイルパスを検索する
2. ファイルが存在する場合、Read ツールで内容を確認し、実質的な内容があるか（空ファイルや数行のテンプレートのみでないか）を検証する
3. 検証成功 → 次のステップへ進む
4. 検証失敗（ファイルが存在しない、または内容が不十分）の場合:
   a. リトライ回数が 2 未満なら、SendMessage で当該エージェントに再指示を送る:
      「{期待ファイル} が確認できません。ファイルを生成して報告してください。」
   b. 再度完了報告を待ち、検証を繰り返す
   c. リトライ回数が 2 に達した場合 → ユーザーにエラーを報告し、ワークフローを中断する

※ Step 5 の並列読者エージェントでは、失敗したエージェントのみリトライする（成功したエージェントは再実行しない）

***

### 共通手順: ディスカッション管理

各ディスカッションフェーズ（Step 2D, 4D, 6.5D）で以下のプロトコルに従う:

1. **招待**: 対象メンバーにトピックとコンテキストを SendMessage で送信。末尾に「特に意見がなければ『問題ありません』と報告してください」を付記する
2. **応答待ち**: 全対象メンバーの idle 通知を待つ
3. **即時合意判定**: 全参加者の応答テキストを確認し、以下の合意キーワードのいずれかのみで応答しているか判定する:
   - 合意キーワード: 「問題なし」「確認しました」「方針了解」「異論なし」「追加情報なし」「問題ありません」
   - **全参加者が合意キーワードで応答** → 即座にディスカッション終了（discussion-log.md に「議論なし（即時合意）」と記録）。ラウンド管理に進まず、次ステップへ
   - **1名でも実質的な意見あり** → 通常のラウンド管理（項目4）に移行
4. **ラウンド管理**: idle 通知のサイクルをラウンドとしてカウント
   - Step 2D / 4D: 最大2ラウンド
   - Step 6.5D: 最大3ラウンド
5. **打ち切り**: 最大ラウンド到達時、全メンバーに「ディスカッション終了。現在の方針/判定で進めます」を SendMessage
6. **成果物確認**: ディスカッションの結果ファイル更新が必要な場合（2D→direction更新、6.5D→consolidated-feedback作成）、担当エージェントに指示し出力を検証
7. **記録**: ディスカッション終了後、workspace/discussion-log.md に以下を追記:
   - 参加者、ラウンド数、概要（2〜3文）、成果物変更の有無
   議論が発生しなかった場合も「議論なし」と記録する

***

### Step 1: チーム作成 + コアメンバースポーン

TeamCreate で `"novel-ep{番号}"` という名前のチームを作成する。

**コアチームメンバー**を一斉にスポーンする（team_name 指定あり）。3名を並列で Task スポーンする。

| チームメイト | subagent_type | name | model | スポーンタイミング |
|------------|---------------|------|-------|--------------------|
| 編集 | novel-editor | editor | opus | Step 1（一斉スポーン） |
| 作者 | novel-author | author | opus | Step 1（一斉スポーン） |
| 担当者 | novel-manager | manager | sonnet | Step 1（一斉スポーン） |

各メンバーの Task prompt:
```
あなたは第{番号}話の執筆チームの{役割}です。
agents/{ファイル}.md を読み込み、チームリーダーからの指示を待ってください。
```

**読者**は Step 3 完了直後にバックグラウンドでスポーンする（詳細は「Step 3 完了時: 読者バックグラウンドスポーン」を参照）。`story/reader-personas.md` を Read で読み込み、定義された全ペルソナの一覧（ID、名前、subagent_type）を取得しておく。

**series-tracker 自動復旧**:

`story/series-tracker.md` について以下を確認する:
- ファイルが存在すること
- 以下の必須セクション見出しが存在すること:
  - `## アクション配分（直近3話）`
  - `## キャラクター登場密度（直近5話）`
  - `## 伏線・要素の進展追跡`
  - `## 表現パターン累積（直近5話）`

欠落または破損（必須見出し不足）の場合:
1. `setup-story` と同じテンプレートで `story/series-tracker.md` を再生成する
2. ユーザーに「series-tracker.md を自動再生成して継続します」と通知する
3. `workspace/discussion-log.md` に再生成の事実を追記する（理由: 欠落/破損）。`discussion-log.md` が存在しない場合はヘッダー付きで新規作成してから追記する

progress.md を更新: step1 を `[x]`、`current_step: "step1"`, `step_status: "completed"`

***

### Step 2: 編集（方針策定）

progress.md を更新: `current_step: "step2"`, `step_status: "in_progress"`

SendMessage で **editor** に以下を指示:

```
第{番号}話の創作方針を策定してください。

以下のファイルを読み込んでください:
- agents/editor.md（あなたの役割定義）
- story/series-tracker.md（横断追跡データ — 最初に読み、警告事項を確認してから方針を組み立てること）
- story/premise.md, story/setting.md, story/characters.md
- story/plot-outline.md, story/writing-guide.md
- story/episode-summaries.md
- story/handover-notes.md（前話からの申し送り事項。存在する場合）
- 前話のエピソード（あれば episodes/ から最新のもの）

agents/editor.md の指示に従い、結果を workspace/current-direction.md に書き出してください。
完了したら報告してください。
```

editor からの完了報告（idle通知）を待ち、`workspace/current-direction.md` について**共通手順: エージェント出力の検証**に従う。

#### 方針固有の構造検証

共通の出力検証に加え、以下の追加検証を行う:

1. `workspace/current-direction.md` を Read で読み、「## アクション配分確認」セクションが存在し、直前2話の区分が具体的に記入されているか確認する
2. 「## エピソードタイプ・文字数」セクションが存在し、A/B/C の指定と文字数目安が記入されているか確認する
3. 「## 伏線・布石」セクション内に「tracker警告への対応」の記載があるか確認する
4. `story/series-tracker.md` を Read で読み、警告事項（「現在の警告」行）と方針の整合性を確認する。警告が出ているのに方針が対応していない場合（例: 未進展2話以上の要素に言及がない、キャラ登場警告が出ているのに出番が設定されていない）、editor に不足箇所を明示して再出力を依頼する

不備がある場合: editor に不足セクションを明示して再出力を依頼する（共通手順のリトライフローに準じる）

progress.md を更新: step2 を `[x]`、`current_step: "step2"`, `step_status: "completed"`

***

### Step 2D: 方針ディスカッション

progress.md を更新: `current_step: "step2d"`, `step_status: "in_progress"`

**共通手順: ディスカッション管理**に従い、以下の招待メッセージを送信する:

**author** に SendMessage:
```
workspace/current-direction.md を読んでください。
作者として、執筆の実現可能性や構成について意見はありますか？
特に気になる点があれば editor にメッセージしてください。
特になければ『方針了解』と報告してください。
```

**manager** に SendMessage:
```
workspace/current-direction.md を読んでください。
品質・設定整合性の観点から、事前に懸念される点はありますか？
特に気になる点があれば editor にメッセージしてください。
特になければ『問題なし』と報告してください。
```

**ディスカッション管理**:
- 全員「問題なし」系 → 即 Step 3 へ
- 意見あり → エージェント間の直接メッセージを許容（**最大2ラウンド**）
- 打ち切り: 「方針を確定します。次のステップに進みます。」
- editor が direction を更新した場合、出力を検証する

discussion-log.md に記録を追記し、progress.md を更新: step2d を `[x]`、`current_step: "step2d"`, `step_status: "completed"`

***

### Step 3: 作者（執筆 / 改稿）

progress.md を更新: `current_step: "step3"`, `step_status: "in_progress"`

**初稿の場合（revision_count == 0）** — SendMessage で **author** に以下を指示:

```
第{番号}話を執筆してください。

以下のファイルを読み込んでください:
- agents/author.md（あなたの役割定義）
- workspace/current-direction.md（編集の方針 — 最優先）
- story/premise.md, story/setting.md, story/characters.md
- story/writing-guide.md, story/episode-summaries.md（「直近エピソード詳細」セクションのみ）
- 前話のエピソード（あれば episodes/ から最新のもの）

agents/author.md の指示に従い、第{番号}話を執筆してください。
結果を workspace/current-draft.txt に書き出してください。
本文のみを出力し、メタ情報やコメントは含めないでください。
完了したら報告してください。
```

**リビジョンの場合（revision_count > 0）** — SendMessage で **author** に以下を指示:

```
改稿を行ってください。

以下のファイルを読み込んでください:
- agents/author.md（あなたの役割定義）
- workspace/current-direction.md（編集の方針）
- workspace/current-draft.txt（前回のドラフト）
- workspace/consolidated-feedback.md（編集が統合したフィードバック — これが改稿の主要な指針です）
- workspace/revision-log.md

workspace/consolidated-feedback.md の指示に従って改稿してください。
結果を workspace/current-draft.txt に上書きしてください。
本文のみを出力し、メタ情報やコメントは含めないでください。
完了したら報告してください。
```

author からの完了報告を待ち、`workspace/current-draft.txt` について**共通手順: エージェント出力の検証**に従う。

progress.md を更新: step3 を `[x]`、`current_step: "step3"`, `step_status: "completed"`

#### Step 3 完了時: 読者バックグラウンドスポーン

Step 3 の出力検証が成功した直後、読者をバックグラウンドでスポーンする。Step 4（レビュー）/ Step 4D（議論）はドラフトを変更しないため、読者はレビュー・議論と並行して安全にフィードバックを生成できる。

**事前準備**: `story/reader-personas.md` を Read で読み込み、定義されたペルソナの一覧（ID、名前、評価視点）を取得する。

読者は **team_name なし**、**run_in_background: true** のサブエージェントとしてスポーンする。各ペルソナを並列で Task スポーンする。各読者の `subagent_type` と `name`（`reader-{ペルソナID}`）は `story/reader-personas.md` の定義に従う（ペルソナ数は固定3名とは限らない）。

**各読者ペルソナ** に（Task、team_name なし、run_in_background: true）:
```
workspace/current-draft.txt を読んで、story/reader-personas.md のペルソナ{N}（{ペルソナ名}）としてフィードバックを書いてください。
agents/readers/reader-template.md の指示に従ってください。
{ペルソナ3（設定整合性担当）の場合は以下を追加:}
story/setting.md, story/characters.md, story/episode-summaries.md（アーク要約＋直近エピソード詳細の両方）も参照し、
さらに story/handover-notes.md と workspace/current-direction.md も参照してください（設定整合性チェック時に、既知の計画済み要素を誤検出しないため）。
結果を workspace/reader-feedback-{ペルソナID}.md に書き出してください。
完了したら報告してください。
```

progress.md の「Step 5 Detail」を初期化（全ペルソナを `[ ]` に設定）。各読者の Task ID を記録しておく（Step 5 での回収に使用）。

***

### Step 4: 担当者（レビュー）

progress.md を更新: `current_step: "step4"`, `step_status: "in_progress"`

SendMessage で **manager** に以下を指示:

**初稿の場合（revision_count == 0）**:

```
ドラフトを評価してください。

以下のファイルを読み込んでください:
- agents/manager.md（あなたの役割定義）
- workspace/current-direction.md（編集の方針）
- workspace/current-draft.txt（評価対象のドラフト）
- story/premise.md, story/setting.md, story/characters.md
- story/writing-guide.md, story/episode-summaries.md
- story/handover-notes.md（申し送り事項、あれば）
- story/series-tracker.md（横断追跡データ — 構造多様性/登場密度チェックで参照）
- workspace/revision-log.md（リビジョン履歴、あれば）

agents/manager.md の指示に従い、ドラフトを評価してください。
現在のリビジョン回数は {revision_count} / {max_revisions} です。
結果を workspace/manager-review.md に書き出してください。
完了したら報告してください。
```

**リビジョンの場合（revision_count > 0）**:

```
改稿版のドラフトを再評価してください。

以下のファイルを読み込んでください:
- agents/manager.md（あなたの役割定義）
- workspace/current-direction.md（編集の方針）
- workspace/current-draft.txt（改稿されたドラフト）
- workspace/revision-log.md（リビジョン履歴）
- workspace/consolidated-feedback.md（前回のフィードバック統合）
- story/series-tracker.md（横断追跡データ — 構造多様性/登場密度チェックで参照）

agents/manager.md の指示に従い、改稿版を評価してください。
前回のリビジョン記録と比較し、改善が見られるかも確認してください。
現在のリビジョン回数は {revision_count} / {max_revisions} です。
結果を workspace/manager-review.md に上書きしてください。
完了したら報告してください。
```

manager からの完了報告を待ち、`workspace/manager-review.md` について**共通手順: エージェント出力の検証**に従う。

progress.md を更新: step4 を `[x]`、`current_step: "step4"`, `step_status: "completed"`

***

### Step 4D: ドラフトディスカッション

**書面先行ルール**: `manager-review.md` の出力が検証済みである**後**にのみ本ステップを開始する。

progress.md を更新: `current_step: "step4d"`, `step_status: "in_progress"`

**共通手順: ディスカッション管理**に従い、以下の招待メッセージを送信する:

**author** に SendMessage:
```
担当者のレビューが出ました。workspace/manager-review.md を読んでください。
指摘事項について意図の説明が必要な場合は、manager にメッセージしてください。
※ 判定への異議ではなく、意図の説明・補足に留めてください。
特になければ『確認しました』と報告してください。
```

**editor** に SendMessage:
```
workspace/manager-review.md を読んでください。
方針との整合性について気づいた点があれば共有してください。
特になければ『確認しました』と報告してください。
```

**ディスカッション管理**:
- 全員「確認しました」→ 即 Step 5 へ
- 意見交換 → 最大2ラウンド
- **重要**: 担当者の判定は変更しない（書面先行ルール）

discussion-log.md に記録を追記し、progress.md を更新: step4d を `[x]`、`current_step: "step4d"`, `step_status: "completed"`

***

### Step 5: 読者フィードバック回収

読者は Step 3 完了時にバックグラウンドでスポーン済み。このステップでは結果の回収と検証のみを行う。

progress.md を更新: `current_step: "step5"`, `step_status: "in_progress"`

#### 通常フロー（Step 3 でスポーン済みの場合）

Step 3 で記録した各読者の Task ID を使い、TaskOutput で完了を待つ（block: true）。3名を並列で待機する。

#### 再開フォールバック（読者未スポーンの場合）

セッション再開時など、読者がスポーンされていない場合（progress.md の「Step 5 Detail」が全て `[ ]` かつ Task ID が不明な場合）は、ここで読者をスポーンする。Step 3 完了時と同じ手順で `story/reader-personas.md` を読み込み、各ペルソナをスポーンする。

**再開時の部分完了対応**: progress.md の「Step 5 Detail」を確認し、
`[x]` のペルソナは出力ファイルを Glob + Read で検証する。
検証成功なら再スポーンしない。未完了 `[ ]` のペルソナのみスポーンする。

#### 共通: 出力検証

全ペルソナからの完了報告（または TaskOutput の結果）を待ち、各 `workspace/reader-feedback-{ペルソナID}.md` を個別に検証する。

各ファイルについて**共通手順: エージェント出力の検証**に従う。
失敗したエージェントのみリトライし、成功したエージェントには再指示を送らない。

各ペルソナの検証成功時に progress.md の「Step 5 Detail」で該当ペルソナを `[x]` に更新する。
全員の検証完了後、progress.md を更新: step5 を `[x]`、`current_step: "step5"`, `step_status: "completed"`

***

### Step 6: 判定

progress.md を更新: `current_step: "step6"`, `step_status: "in_progress"`

リーダー（あなた自身）が以下を直接実行する:

0. **自動スキャン**: `workspace/current-draft.txt` に対し以下の Grep チェックを行う:
   - `第\d+話` パターンが1行目（タイトル行）以外に存在しないか確認
   - パターン検出時: 該当箇所をユーザーに警告表示し、**自動的に REVISION_NEEDED** として扱う（Manager判定に関わらず）。revision-log.md に「メタナラティブ表現の自動検出」を記録する

1. `workspace/manager-review.md` を Read で読み、判定（OK / REVISION_NEEDED / MAJOR_REVISION）を確認
2. `workspace/reader-feedback-*.md` を Glob で検索し全読者フィードバックを Read で読み、各読者の総合評価★を確認して平均と中央値を算出
3. 判定ロジック:
   - **revision_count ≥ max_revisions** → **FORCE_PASS**（Step 7へ、警告付き）
   - **Manager判定が OK** かつ **読者平均★ ≥ 3.5** → **PASS** または **PASS_WITH_POLISH**（下記参照）
   - **Manager判定が OK** だが **読者平均★ < 3.5** → **REVISION_NEEDED**
   - **Manager判定が REVISION_NEEDED** または **MAJOR_REVISION** → **REVISION_NEEDED**

3a. **PASS_WITH_POLISH 判定**（PASS 条件を満たした場合に追加チェック）:
   PASS 条件を満たした場合、以下のいずれかに該当するか確認する:
   - `manager-review.md` に「軽微な指摘」「細かい点」等の軽微な問題が **2件以上** ある
   - Step 4D で editor が方針との齟齬を指摘した箇所がある（discussion-log.md を参照）
   - 読者フィードバック3名のうち **2名以上が共通して** 指摘している箇所がある
   いずれかに該当 → **PASS_WITH_POLISH**（Step 6.5P へ）
   いずれにも該当しない → **PASS**（Step 7 へ）

3b. **読者フィードバック差分分析**:
   読者間の★評価差が **2★以上** ある場合、以下の分析を行う:
   - 高評価者と低評価者の主要な評価軸の違いを特定する
   - 低評価者の具体的な不満点を抽出する
   - `story/handover-notes.md` の「読者からの要望」セクションに差分分析を追記する
     （例: 「ペルソナ1★3 vs ペルソナ2★5: テンポ vs 感情描写の深さでトレードオフ」）
   この分析は判定結果（PASS/PASS_WITH_POLISH/REVISION_NEEDED）に関わらず実行する。

4. PASS の場合: progress.md を更新: step6 を `[x]`、`current_step: "step6"`, `step_status: "completed"`。Step 7 へ。
4a. PASS_WITH_POLISH の場合: progress.md を更新: step6 を `[x]`、`current_step: "step6"`, `step_status: "completed"`。Step 6.5P へ。
4b. FORCE_PASS の場合: progress.md を更新: step6 を `[x]`、`current_step: "step6"`, `step_status: "completed"`。Step 7 へ（Step 6.5P はスキップ）。

5. REVISION_NEEDED の場合:
   - revision_count を +1
   - progress.md を更新:
     - `revision_count` を +1 した値に更新
     - `current_step: "step6.5d"`, `step_status: "in_progress"`
     - step3, step4, step4d, step5, step6, step6.5p のチェックを `[ ]` にリセット
     - Step 5 Detail の3リーダーも `[ ]` にリセット
     - 「Revision History」セクションにリビジョン記録を追記
   - `workspace/revision-log.md` にリビジョン記録を追記:
     ```
     ## リビジョン {回数}
     - Manager判定: {判定}
     - 深刻度: {通常改稿 / 重大改稿}
      - 読者評価: {各ペルソナ名}★{N}（全ペルソナ分を列挙）
      - 読者平均★: {平均} / 中央値★: {中央値}
      - 主な指摘: {要約}
     ```
     深刻度判定ルール: Manager判定が MAJOR_REVISION → 重大改稿、それ以外 → 通常改稿
   - 現在のドラフトを `archive/episode-{番号:2桁}/draft-v{回数}.txt` にバックアップ
   - **Step 6.5D へ進む**

6. 判定結果とステータスをユーザーに表示する

***

### Step 6.5P: ポリッシュ（軽微修正）【PASS_WITH_POLISH 時のみ】

Step 6 で PASS_WITH_POLISH と判定された場合にのみ実行する。

progress.md を更新: `current_step: "step6.5p"`, `step_status: "in_progress"`

リーダー（あなた自身）が以下を実行する:

1. **指摘箇所の抽出**: Step 6 で特定した軽微な指摘を **最大3件** にまとめる。以下の優先順位で選定:
   - 担当者と読者が共通して指摘した箇所（最優先）
   - Step 4D で editor が指摘した方針との齟齬
   - 読者2名以上が共通して指摘した箇所

2. **author に部分修正を依頼**: SendMessage で author に以下を送信:
   ```
   判定はPASSですが、以下の軽微な箇所のみ修正してください。
   全体の構成は変更しないでください。

   修正箇所:
   1. {指摘1: 箇所と修正内容}
   2. {指摘2: 箇所と修正内容}
   3. {指摘3: 箇所と修正内容}（あれば）

   修正後、workspace/current-draft.txt を上書きしてください。
   完了したら報告してください。
   ```

3. author からの完了報告を待ち、`workspace/current-draft.txt` について**共通手順: エージェント出力の検証**に従う。

4. **担当者の再レビューは不要**（軽微修正のため）
5. **読者の再評価も不要**（スコアは初回評価を使用）

progress.md を更新: step6.5p を `[x]`、`current_step: "step6.5p"`, `step_status: "completed"`

**Step 7 へ進む**。

***

### Step 6.5D: リビジョンディスカッション【REVISION時のみ】

Step 6 で REVISION_NEEDED と判定された場合にのみ実行する。

**共通手順: ディスカッション管理**に従い、全コアメンバーに以下のメッセージを送信する:

**editor** に SendMessage:
```
リビジョンが必要です（{revision_count}/{max_revisions}回目）。

判定結果:
- Manager判定: {judgment}
- 読者: {各ペルソナ名}★{N}（全ペルソナ分）（平均★{avg}）

以下のフィードバックファイルを確認してください:
- workspace/manager-review.md
- workspace/reader-feedback-*.md（全読者分）

全フィードバックを読み、改稿の優先順位について所見を共有してください。
author, manager と議論の上、workspace/consolidated-feedback.md を作成してください。
agents/editor.md の「リビジョン時の対応」セクションに従ってください。
第{番号}話、リビジョン{revision_count}回目です。
深刻度は「{通常改稿 / 重大改稿}」です。

方針の修正が必要な場合は workspace/current-direction.md も更新してください。
```

**author** に SendMessage:
```
リビジョンが必要です（{revision_count}/{max_revisions}回目）。

判定結果:
- Manager判定: {judgment}
- 読者: {各ペルソナ名}★{N}（全ペルソナ分）（平均★{avg}）

以下のフィードバックファイルを確認してください:
- workspace/manager-review.md
- workspace/reader-feedback-*.md（全読者分）

改稿の実現可能性の観点から意見を出してください。
editor と議論し、改稿方針の策定に協力してください。
特になければ『確認しました』と報告してください。
```

**manager** に SendMessage:
```
リビジョンが必要です（{revision_count}/{max_revisions}回目）。

判定結果:
- Manager判定: {judgment}
- 読者: {各ペルソナ名}★{N}（全ペルソナ分）（平均★{avg}）

レビューの重点について補足があれば共有してください。
editor, author と議論に参加してください。
特に補足がなければ『追加情報なし』と報告してください。
```

**ディスカッション管理**:
- 最大3ラウンド
- editor が `consolidated-feedback.md` を書き出した時点で終了
- editor の出力について**共通手順: エージェント出力の検証**に従う

discussion-log.md に記録を追記し、progress.md を更新: `current_step: "step6.5d"`, `step_status: "completed"`

**Step 3 に戻る**（改稿）。

***

### Step 7: 確定・保存

progress.md を更新: `current_step: "step7"`, `step_status: "in_progress"`

リーダー（あなた自身）が直接実行する:

1. エピソードタイトルを `workspace/current-direction.md` から取得
2. `workspace/current-draft.txt` を `episodes/{番号:2桁}_{タイトル}.txt` にコピー
3. `story/episode-summaries.md` を更新する:
   a. 「直近エピソード詳細」セクションに今話のあらすじを追記（100〜150字）
   b. 直近エピソード詳細が5話を超えた場合:
      - 最も古い話を「直近エピソード詳細」から削除する
      （アーク要約に含まれているため詳細は不要）
   c. アーク境界に達した場合（`story/plot-outline.md` の幕区分を参照）:
      - 当該アークの全話を6〜8行のアーク要約に圧縮する
      - 「アーク要約」セクションの末尾（`<!-- ↑ アークが閉じるたびにここに追加される -->` コメントの直前）に追加する
      - 【主な伏線】にアーク内で張られた重要伏線を列挙する
      - 圧縮後、該当話の詳細あらすじを「直近エピソード詳細」から削除する
      - 長い幕は自然な区切りでサブアークに分割してよい

3a. `story/series-tracker.md` を更新する:
   - **アクション配分**: テーブルをスライドし、最も古い行を削除して今話の行を追加。「次話の制約」を今話を含む直近3話の配分から再計算して更新する
   - **キャラクター登場密度**: 今話の列を追加し、最も古い列（5話より前）を削除する。テーブルに存在しないキャラで、今話に登場したキャラまたは次話以降も追跡が必要なキャラがいれば行を追加する（既存列は `—` で初期化し、今話列のみ評価記号を記入）。各キャラの「薄い回連続」を再計算する。2話連続△以下のキャラがいれば「現在の警告」を更新する
   - **伏線・要素の進展追跡**: 今話で進展した要素の「最終進展話」「最終進展の具体的内容」を更新し「未進展話数」を0にリセットする。進展しなかった要素の「未進展話数」を+1する。2話以上未進展の要素があれば「現在の警告」を更新する。新たに追跡すべき要素があれば行を追加する
   - **表現パターン累積**: 確定したエピソード本文を Grep で走査し、今話の「身体部位比喩（抽象）」と「ダッシュ（——）」の回数をカウントして更新する。最も古い話のカウントを削除し5話合計を再計算する。さらに各行の「状態」を更新する（`1話上限` が数値なら「今話回数 > 上限」で `要分散`、それ以外は `正常`。`1話上限` が `—` の行は「5話合計 >= 10」で `要分散`、未満は `正常`）

progress.md を更新: step7 を `[x]`、`current_step: "step7"`, `step_status: "completed"`

→ **Step 7.5 を実行**（editor に申し送り事項更新を委任）
→ **Step 7.6 を実行**（プロット更新ディスカッション）

> **順序保証**: workspace のアーカイブ/クリーンは **Step 8 の終盤**で実行する。Step 7.5 は `workspace/manager-review.md` と `workspace/reader-feedback-*.md` を参照し、Step 7.6 は `discussion-log.md` を更新するため。

***

### Step 7.5: 編集（申し送り事項更新）

progress.md を更新: `current_step: "step7.5"`, `step_status: "in_progress"`

SendMessage で **editor** に以下を指示:

```
第{番号}話の確定を受けて、申し送り事項を更新してください。

以下のファイルを読み込んでください:
- agents/editor.md（「申し送り事項の管理」セクション）
- episodes/{番号:2桁}_{タイトル}.txt（確定した本文）
- workspace/manager-review.md
- workspace/reader-feedback-*.md（全読者分）
- story/handover-notes.md

story/handover-notes.md を更新してください。
見出しの話番号を「第{番号+1}話より」に更新してください。
完了したら報告してください。
```

editor からの完了報告を待つ。

progress.md を更新: step7.5 を `[x]`、`current_step: "step7.5"`, `step_status: "completed"`

***

### Step 7.6: プロット更新ディスカッション

第{番号}話の確定・申し送り事項更新の後、editor と manager が `story/plot-outline.md` の更新要否を検討する。

progress.md を更新: `current_step: "step7.6"`, `step_status: "in_progress"`

**editor** に SendMessage:
```
第{番号}話の確定を受けて、plot-outline.md の更新が必要か検討してください。

以下のファイルを読み込んでください:
- story/plot-outline.md（現在のプロット）
- story/handover-notes.md（更新済みの申し送り事項）
- story/episode-summaries.md（直近エピソード詳細）

確認事項:
1. 今話で実際に描かれた展開が plot-outline.md の記述と乖離していないか
2. handover-notes.md の [DEFERRED] 項目が未来の話の展開に影響するか
3. 未来の話（特に次話〜3話先）のプロット概要に追記・修正すべき点はあるか

agents/editor.md の「プロット更新の管理」セクションのガイドラインに従ってください。
修正が必要な場合は manager と相談の上、plot-outline.md を更新してください。
修正不要であれば『プロット変更なし』と報告してください。
```

**manager** に SendMessage:
```
editor がプロットの更新を検討しています。
story/plot-outline.md を読んでください。
設定整合性の観点から、editor のプロット変更案に問題がないか確認してください。
editor からメッセージがあれば議論に参加してください。
特になければ『確認しました』と報告してください。
```

**ディスカッション管理**:
- 最大2ラウンド
- editor が「プロット変更なし」と報告 → 即終了
- editor が `plot-outline.md` を更新した場合、Read で内容を確認し、`agents/editor.md` の「プロット更新の管理」ガイドラインに違反していないか検証する
  - 違反がある場合（大筋の変更、4話以上先の大幅変更）→ editor に差し戻し、該当箇所の削除を指示
- discussion-log.md に記録を追記

**ディスカッション完了後**、`story/quality-log.md` に品質記録を追記する
（ファイルが存在しない場合はヘッダー付きで新規作成）
記録する列:
- 話数、タイトル、リビジョン回数、Manager判定
- 各ペルソナ★（全ペルソナ分）、平均★、中央値★
- 議論回数（ディスカッションが発生したフェーズ数。discussion-log.md で「議論なし」以外のエントリを数える。**Step 7.6 の議論も含む**）
- ポリッシュ（Step 6.5P が発動したか: `○` / `-`）
- 主要指摘（最も頻出した指摘カテゴリを1語で: テンポ/描写/整合性/構成/表現/なし 等）
- 判定（PASS / PASS_WITH_POLISH / FORCE_PASS）

progress.md を更新: step7.6 を `[x]`、`current_step: "step7.6"`, `step_status: "completed"`

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
