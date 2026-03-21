---
name: write-episode
description: Web小説のエピソードを自動執筆するスキル。作者・アークレビュアー・読者エージェントによるマルチエージェント協調で、執筆・レビュー・改稿・品質判定・確定保存までを一貫実行する。Use when user says "第N話を書いて", "次の話を執筆", "write episode", "続きを書いて", or specifies an episode number for writing. Do NOT use for story setup (/setup-world), arc design (/setup-arc), or story editing (/edit-story).
argument-hint: "<episode_number> [--max-revisions=N]"
disable-model-invocation: true
---

# /write-episode — Web小説自動執筆スキル（Phase 1）

## 概要

このスキルは、アーク設計（`story/scenario-arc.md` + `story/character-arcs.md`）を起点としてエピソードブリーフを生成し、author と arc-reviewer のチームで第N話を執筆・レビューし、確定後にアーク進行を更新する。

**前提**: `story/scenario-arc.md` と `story/character-arcs.md` が存在すること（`/setup-arc` 完了済み）。

## 入力

- `$ARGUMENTS`: `episode_number`（必須）
- `--max-revisions=N`（任意、デフォルト `3`）

## 動作環境の注意

`TeamCreate` / `SendMessage` / `TeamDelete` が利用できない環境（Windows など）では、チームメンバーのスポーンに `Agent` ツールを使用し、メッセージ交換の代わりに各エージェントへの直接プロンプトで代替する。ディスカッションステップは省略しても構わない（discussion-log.md に「チーム機能非対応環境のため省略」と記録する）。チームシャットダウン（Step 8）は TeamDelete をスキップしてチェックボックスのみ更新する。

## 最初に行うこと（必須）

実行開始時の**最初のアクション**として、`.claude/skills/write-episode/resume-logic.md` を Read し、再開チェック手順を適用する。

## 参照ファイルの読み込み規約

- 常時適用: Step 0 完了後（再開時は再開地点決定後）に `.claude/skills/write-episode/common-procedures.md` を Read し、以降すべてのステップで「出力検証」と「ディスカッション管理」を適用する。
- 判定時のみ: Step 6 開始時に `.claude/skills/write-episode/judgment-logic.md` を Read する。
- 確定処理時のみ: Step 7 開始時に `.claude/skills/write-episode/finalization-details.md` を Read する。

## ワークフロー全体

```text
Step 0:  初期化（workspace準備、progress.md作成）
Step 1:  チーム作成 + コアメンバースポーン（author/arc-reviewer）
Step 2:  エピソードブリーフ生成（オーケストレーター直接実行）→ episode-brief.md
 └ 2Q:  迷いを設計者に問う（optional）
Step 3:  作者（執筆/改稿）→ current-draft.txt → author-reflections.md 一言 → 読者バックグラウンドスポーン（初稿時のみ）
Step 4:  アークレビュー → arc-review.md
 └ 4D:  ドラフトディスカッション（author+arc-reviewer、最大2ラウンド）
         REVISION_NEEDED の場合 → Step 3 に戻る（max_revisions まで）
Step 5:  読者フィードバック回収
Step 6:  判定 → PASS / PASS_WITH_POLISH / FORCE_PASS
 └ 6.5P: ポリッシュ（PASS_WITH_POLISH時のみ）→ Step 7へ
Step 7:  確定・保存・アーク進行更新
 └ 7.5: 品質ログ記録
 └ 7.6: エピソードレトロ（KPT → 設計者にTryを提案）
Step 8:  チームシャットダウン
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
8. **アーク設計の存在確認**: `story/scenario-arc.md` と `story/character-arcs.md` を Glob で確認する。どちらか欠落している場合はユーザーにエラーを報告し中断する（「`/setup-arc` を先に実行してください」）。
9. **前提確認チェック（警告のみ・中断しない）**:
   - `story/writing-guide.md` に「構成パターン × 役割タグ 推奨相性」セクションが存在するか確認する。存在しない場合、`progress.md` に `accent_phase_fallback: true` を記録する（Step 2 の 4a で相性表照合をスキップしてフォールバック動作を使用する）。
   - `story/handover-notes.md` が存在する場合、`[MUST-THIS]` / `[MUST-VOL]` 等のタグが含まれているか確認する。タグが存在しない場合（旧形式の可能性）、`progress.md` に `handover_legacy_format: true` を記録し、Step 2 でトリアージ処理の代わりに全スレッドを `[MUST-VOL]` として扱う。ユーザーに「handover-notes.md が旧形式の可能性があります。`/edit-story` で移行を推奨します」と通知する。
9. `story/premise.md` を Read し、想定話数を取得する。取得できない場合は `planned_episodes = null` として以降の計算をスキップする。
10. 終盤変数を計算する:
    - `remaining_episodes = planned_episodes - episode_number`（null の場合は null）
    - `is_finale = (remaining_episodes == 0)`
11. `story/scenario-arc.md` を Read し、三幕構成の幕境界話数を取得する。今話（`episode_number`）が幕の境界に当たるか判定し、`arc_phase_boundary` に記録する（境界の場合は幕番号も）。

完了条件:
- `progress.md`: `current_step: "step0"`, `step_status: "completed"`, `step0` を `[x]`。YAMLブロックに `arc_phase_boundary`（true/false と幕番号）を含む終盤変数を記録済み。

---

### Step 1: チーム作成 + コアメンバースポーン

実行:
1. TeamCreate で `novel-ep{番号}` チームを作成する。
2. **コアメンバーは Step 1 ではスポーンしない**。各メンバーは使用するステップで遅延スポーンする（指示をプロンプトに直接含める方式。空スポーン＋SendMessage 方式は応答率が低いため廃止）。

| チームメイト | subagent_type | name | model | スポーンタイミング |
|---|---|---|---|---|
| 作者 | novel-author | author | opus | **Step 3**（執筆指示をプロンプトに直接含める） |
| アークレビュアー | novel-arc-reviewer | arc-reviewer | sonnet | **Step 4**（レビュー指示をプロンプトに直接含める） |
4. `story/reader-personas.md` を Read し、全ペルソナ（ID・名前・subagent_type）を取得する。
5. `story/series-tracker.md` の存在と必須見出しを検証する。
   - `## アクション配分（直近3話）`
   - `## キャラクター登場密度（直近5話）`
   - `## 伏線・要素の進展追跡`
   - `## 表現パターン累積（直近5話）`
   - `### 構成パターン履歴`（表現の多様性管理用。以下2つは同時に存在すること）
   - `### 感覚レンズ履歴`
   - `## 主人公の能動性追跡（直近5話）`
   - `## テンポプロファイル履歴（直近5話）`
6. 欠落/破損時はテンプレートで再生成し、ユーザー通知と `discussion-log.md` 追記を行う（未作成時はヘッダー付きで新規作成してから追記）。構成パターン履歴・感覚レンズ履歴が欠落している場合は以下のテーブルを末尾に追記する:

   ```markdown
   ### 構成パターン履歴
   | 話数 | 推奨パターン | 実使用パターン | 変更メモ |
   |------|------------|--------------|---------|

   ### 感覚レンズ履歴
   | 話数 | 推奨レンズ | 実使用レンズ | 変更メモ |
   |------|----------|------------|---------|

   ## 主人公の能動性追跡（直近5話）
   | 話数 | 選択の型 | 内容 | 選ばなかった選択肢 |
   |------|---------|------|-----------------|

   ## テンポプロファイル履歴（直近5話）
   | 話数 | プロファイル | 引きの型 |
   |------|------------|---------|
   ```

完了条件:
- `progress.md`: `step1` を `[x]`, `current_step: "step1"`, `step_status: "completed"`。

---

### Step 2: エピソードブリーフ生成

**このステップはオーケストレーター（あなた自身）が直接実行する。エージェントには委任しない。**

実行:
1. `progress.md` を `step2 in_progress` に更新する。
2. `story/scenario-arc.md` を Read し、以下を取得する:
   - 今話（`episode_number`）の役割タグと感情強度（頂点比）
   - 今話が属する幕と感情の方向
3. `story/character-arcs.md` を Read し、各キャラクターについて以下を取得する:
   - 現在ステージと次トリガー（前話の `character-arcs.md` が更新済みであれば反映済みのはず）
   - 意図的に未解決を保つ期間（解決してはいけない要素）
4. `story/handover-notes.md` を Read し、スレッドをトリアージする:
   - `progress.md` の `handover_legacy_format` が `true` の場合（旧形式）: 各未解決項目を `[MUST-VOL]` として仮分類する。Step 2Q で設計者に分類の確認を求める（この場合 Step 2Q は省略しない）
   - `[MUST-THIS]`: 今話で扱う（episode-brief に明示）
   - `[TRY-NEXT]`: 前話のエピソードレトロで承認された改善提案。episode-brief の該当セクション（反パターン制約、蓮の選択場面、アクセント等）に反映する。反映後、タグを `[RESOLVED]` に変更する
   - `[MUST-VOL]` 以下: 参考として記録するに留め、今話で処理しない
5. `story/plot-outline.md` を Read し、今話のプロット骨格を確認する:
   - 今話で予定されているイベント・登場キャラクター
   - **series-tracker の警告（キャラクター登場密度・伏線未進展）と plot-outline の計画が矛盾する場合は、plot-outline を優先する**。series-tracker の警告は「計画的な不在」を区別できないため、plot-outline で後の話に配置されたイベントを前倒しで消費してはならない
6. 前話エピソード（`episodes/`）が存在する場合は Read し、直前の文脈を把握する。
7. `workspace/episode-brief.md` を作成する:

```markdown
## アーク上の位置

- 今話の役割タグ: {タグ名}
- 感情強度（頂点比）: {比率}
- 今話で進めるキャラクターアーク: {キャラクター名と進行内容}
- 今話で進めてはいけないもの: {意図的未解決期間中の要素}

## 今話の焦点

（役割タグと感情の方向から導かれる具体的な方針）

## 書かないことリスト

（アーク上の理由を明記して、今話では扱わない項目を列挙する）

## 今話で扱うスレッド（MUST-THIS のみ）

（handover-notes.md の [MUST-THIS] スレッド。該当なしの場合は「なし」）

## 反パターン制約（実装重複回避）

（`story/series-tracker.md` の「シーン構造パターン」テーブルから直近3話の主要シーン構造・冒頭の入り方・食事場面を取得し、重複する実装パターンを明示的に禁止する）

- やってはいけない主構造：（直近3話で繰り返された構造。例:「移動中の歩行シーンを主構造にしない」）
- やってはいけない冒頭：（直前話と同じ入り方。例:「前話の場面の延長から始めない」）
- 回避すべき要素：（直近で過剰な要素。例:「食事場面を含めない」）

## 蓮の選択場面（必須）

- 蓮がこの話で下す判断/決断：（アーク設計と今話の焦点から具体的に設計する）
- 選ばなかった選択肢：（選択の重みを生む「もう一つの道」を設計する）
- 選択の型：（判断 or 決断。反応のみは不可）

## シーン構成・文字数目安

（役割タグに応じた構成案と `story/premise.md` の想定文字数）

## この話の一文（頂点回のみ）

（※役割タグが「頂点」の場合のみ記載する。それ以外の回では省略する）

この話は、この一文のために存在する:

> {設計者が指定する、この話の核となる一文}

この一文が最大の衝撃を持つように全体を構成すること。この一文に至るまでの蓄積を逆算し、この一文の後の余韻を設計すること。他のすべての描写は、この一文を支えるために存在する。
```

**手順 3b（頂点回の「この一文」設計。役割タグが「頂点」の場合のみ）**:

今話の役割タグが「頂点」の場合、episode-brief に「この話の一文」セクションを追記する。
- `story/plot-outline.md` と `story/scenario-arc.md` の感情頂点の記述を参照し、この話の核となる一文を設計する
- 一文は設計者（ユーザー）に提示して確認を得る。設計者が別の一文を指定した場合はそれを採用する
- 「この一文」は author のスポーンプロンプトにも転記し、執筆の核として明示する
- 頂点以外の役割タグの場合、このセクションは省略する

**手順 4a（執筆のアクセント生成）**:

`progress.md` の `accent_phase_fallback` が `true` の場合（相性表なし）はフォールバック動作を使用する。

`story/series-tracker.md` の「構成パターン履歴」「感覚レンズ履歴」テーブルから直近5話分のデータを取得し、以下を決定する:

- **構成パターン推奨**: 直近5話で最も使用頻度の低いパターンを候補とする。`accent_phase_fallback` が `false` の場合は `story/writing-guide.md` の推奨相性表で今話の役割タグとの親和性を照合して最終決定する。`true` の場合は頻度の低いパターンをそのまま推奨とする。
- **感覚レンズ推奨**: 直近5話で最も使用頻度の低いレンズを推奨する。全レンズが同頻度の場合は最終使用が最も古いレンズを優先する。
- **テンポプロファイル選定**: `story/series-tracker.md` の「テンポプロファイル履歴」から直前2話のプロファイルを取得し、それと異なるプロファイルを選定する。`story/writing-guide.md` のテンポ強度カーブ（§7.5）で今話の役割タグとの親和性を参照して最終決定する。
- **蓮の選択場面設計（必須）**: `story/scenario-arc.md` と `story/character-arcs.md` から今話の焦点を踏まえ、蓮が下す「判断」または「決断」を具体的に設計する。`story/series-tracker.md` の「主人公の能動性追跡」で直近の選択パターンを確認し、同じ型の繰り返しを避ける。「選ばなかった選択肢」も必ず設計する。
- **引きの型選定**: `story/series-tracker.md` の「テンポプロファイル履歴」から直前2話の引きの型を取得し、それと異なる型を `story/writing-guide.md` の引きの4類型から選定する。
- **反パターン制約生成（必須）**: `story/series-tracker.md` の「シーン構造パターン」テーブルから直近3話の主要シーン構造・冒頭の入り方・食事場面を取得し、重複する実装パターンを episode-brief の「反パターン制約」セクションに明示的な禁止事項として記載する。テーブルが存在しない場合（第1話等）はこのセクションを省略する。
- 履歴データが存在しない場合（第1話）は「執筆のアクセント」セクションを省略する（`accent_note_applicable: false` を `progress.md` に記録）。ただし「蓮の選択場面」セクションは episode-brief 本体に必ず含める。

アクセントが決定したら episode-brief.md の末尾に以下のセクションを追記する:

```markdown
## 執筆のアクセント（示唆）

### 構成パターン推奨
- 推奨：{パターン名}
- 根拠：（直近5話の使用頻度から導出）
- 参考：（今話の役割タグとの親和性）

### 感覚レンズ推奨
- 推奨：{レンズ名}
- 根拠：（直近5話の使用頻度から導出）
- 参考：（今話の主要場面との相性）

### テンポプロファイル
- プロファイル：{圧縮型/展開型/加速型/衝撃型/減速型/波動型} — {根拠一行}
- 直前2話：{第N-2話: 型名}, {第N-1話: 型名}（重複回避の確認）

### 引きの型
- 型：{明示的謎/不安の種/感情の残響/選択の予感}
- 直前2話：{第N-2話: 型名}, {第N-1話: 型名}（重複回避の確認）

物語的必然性があれば変更してよい。
```

完了条件:
- `workspace/episode-brief.md` が存在し、「アーク上の位置」「書かないことリスト」「蓮の選択場面（必須）」が記載されている。
- 第2話以降かつ series-tracker に履歴がある場合、「執筆のアクセント」セクション（テンポプロファイル・引きの型を含む）が追記されている。
- `progress.md`: `step2` を `[x]`, `current_step: "step2"`, `step_status: "completed"`。

---

### Step 2Q: 設計者への問い（optional）

実行:
- Step 2 で episode-brief.md を生成する過程で **仮定で埋めざるを得なかった箇所** が2〜3点あれば、設計者に問う。
- **制約**: 問いは「アーク設計の解釈」に限定する（例: 「この役割タグをどう具体化するか」）。アーク設計自体の変更を要する問いが浮上した場合は、episode-brief には仮判断で進め、`story/handover-notes.md` に `[DESIGN-REVIEW]` タグ付きスレッドとして記録する。
- 問いがない場合（アーク設計が十分に詳細）はこのステップをスキップする。
- 設計者の回答を episode-brief.md に反映して確定する。
- `discussion-log.md` に記録する。

---

### Step 3: 作者（執筆 / 改稿）

実行:
1. `progress.md` を `step3 in_progress` に更新する。
2. **author をスポーン（または再スポーン）する**。`team_name: novel-ep{番号}`, `name: author`, `subagent_type: novel-author`, `model: opus` で Agent スポーンし、**プロンプトに執筆指示を直接含める**（SendMessage ではなくスポーン時プロンプトで渡す。opus モデルの応答率改善のため）。
   - 初稿（`revision_count == 0`）のプロンプト:
     - 「あなたは第{番号}話の作者です。`agents/author.md` を読み込み、`workspace/episode-brief.md`（最優先）と `story/` 主要資料・前話を参照して、`workspace/current-draft.txt` に本文のみ出力してください。」に加え、episode-brief の要点（役割タグ、テンポプロファイル、構成パターン、感覚レンズ、蓮の選択場面、引きの型）をプロンプト本文に転記する。
   - 改稿（`revision_count > 0`）のプロンプト:
     - 「あなたは第{番号}話の作者です。`agents/author.md` を読み込み、`workspace/episode-brief.md` と `workspace/arc-review.md` を参照して改稿し、`workspace/current-draft.txt` を上書きしてください。」に加え、arc-review の指摘事項要約をプロンプトに転記する。
   - **改稿時の旧 author 処理**: 改稿で再スポーンする場合、旧 author がまだ存在する可能性がある。旧 author に `shutdown_request` を送ってからスポーンし、上書き競合を防ぐ（CLAUDE.md Gotchas 参照）。
3. 完了報告を待ち、出力検証する。
4. author に `story/author-reflections.md` への記録を指示する:
   - 今話を書いて**驚いたこと**を一言だけ記録する（予定通りだったことは書かない）。
   - ファイルが存在しない場合は `## 第{番号}話` 見出しで新規作成する。存在する場合は末尾に追記する。
   - 驚くべき点がなければスキップ（記録を強制しない）。
   - **改稿時（`revision_count > 0`）は上書きする**（追記しない）。最終稿の印象のみを残す。
5. `progress.md` の `accent_note_applicable` が `true`（第2話以降で履歴あり）の場合、accent-note.md の生成を確認する:
   - `workspace/accent-note.md` が存在するか Glob で確認する。
   - 存在する場合: `progress.md` に `accent_changed: true` を記録する。
   - 存在しない場合: `progress.md` に `accent_changed: false` を記録する（変更なし）。

完了条件:
- `progress.md`: `step3` を `[x]`, `current_step: "step3"`, `step_status: "completed"`。

#### Step 3 完了直後: 読者バックグラウンドスポーン

実行:
1. **初稿（`revision_count == 0`）のみ**実行する。改稿時はスキップする。
2. `story/reader-personas.md` から各ペルソナを取得し、`team_name` なし・`run_in_background: true` で並列 Task スポーンする。
3. 各読者 prompt:
   - `workspace/current-draft.txt` を読み、`agents/readers/reader-template.md` に従って `workspace/reader-feedback-{ペルソナID}.md` に出力する。
   - **全読者共通**で `story/episode-summaries.md`（既読の蓄積）と `story/scenario-arc.md` のエピソード役割マップ（今話の位置把握）も参照させる。
   - **全読者共通**で前話の本文（`episodes/{N-1:2桁}_{タイトル}.txt`）も参照させる。第1話の場合はスキップ。前話の本文を読むことで、連続する2話間の感情の落差・蓄積の回収・テンポの変化を体験として評価できる。あらすじだけでは伝わらない「前話を読んだ直後にこの話を読む」体験を再現する。
   - `story/quality-log.md` が存在する場合のみ、**全読者共通**で直近3話分の記録（各ペルソナの★と主要指摘）を参照させ、「前話からの改善/後退」という相対評価軸も含めるよう指示する。存在しない場合（第1話等）はこの参照をスキップする。
   - 設定整合性担当ペルソナにはさらに `story/setting.md`, `story/characters.md`, `story/handover-notes.md`, `workspace/episode-brief.md` も参照させる。
4. `progress.md` の「Step 5 Detail」を全ペルソナ `[ ]` で初期化し、各読者 Task ID を記録する。

---

### Step 4: アークレビュー

実行:
1. `progress.md` を `step4 in_progress` に更新する。
2. **arc-reviewer をスポーンする**。`team_name: novel-ep{番号}`, `name: arc-reviewer`, `subagent_type: novel-arc-reviewer`, `model: sonnet` で Agent スポーンし、**プロンプトにレビュー指示を直接含める**（SendMessage ではなくスポーン時プロンプトで渡す）。
   - プロンプト: 「あなたは第{番号}話のアークレビュアーです。`agents/arc-reviewer.md` を読み込み、`workspace/episode-brief.md`（評価基準の起点）と `workspace/current-draft.txt`（評価対象）を参照してレビューしてください。`story/character-arcs.md` で意図的未解決期間を確認し、`story/writing-guide.md` と `story/characters.md` も参照してください。リビジョン回数: {revision_count}/{max_revisions}。`workspace/arc-review.md` に出力してください。」
   - **改稿ループでの再レビュー時**: 旧 arc-reviewer に `shutdown_request` を送ってから再スポーンする。
3. 完了報告を待ち、出力検証する。

完了条件:
- `progress.md`: `step4` を `[x]`, `current_step: "step4"`, `step_status: "completed"`。

---

### Step 4D: ドラフトディスカッション

開始条件:
- `workspace/arc-review.md` の出力検証が完了している。

実行:
1. `progress.md` を `step4d in_progress` に更新する。
2. 共通手順のディスカッション管理に従って招待する。
   - author: `workspace/arc-review.md` を確認し、必要時のみ執筆意図を説明する（判定への異議は行わない）。なければ「確認しました」。
   - arc-reviewer: author の意図説明を受けた上で、補足情報があれば共有する。なければ「確認しました」。
3. 最大2ラウンド実施する。
4. **arc-reviewer の判定は変更しない**（書面先行ルール）。
5. `discussion-log.md` に記録する。

完了条件:
- `progress.md`: `step4d` を `[x]`, `current_step: "step4d"`, `step_status: "completed"`。

遷移:
- **REVISION_NEEDED または MAJOR_REVISION** かつ `revision_count < max_revisions`:
  - `revision_count` を +1
  - `progress.md` の `revision_count` を更新し、step3/step4/step4d のチェックを `[ ]` にリセット
  - `workspace/revision-log.md` にリビジョン記録を追記:
    ```
    ## リビジョン {回数}
    - アークレビュー判定: {判定}
    - 主な指摘: {arc-review.md の指摘事項要約}
    ```
  - 現在のドラフトを `archive/episode-{番号:2桁}/draft-v{revision_count}.txt` にバックアップ
  - **Step 3 に戻る**
- **REVISION_NEEDED** かつ `revision_count >= max_revisions`:
  - `progress.md` に `force_pass: true` を記録する
  - **Step 5 へ進む**
- **OK**:
  - **Step 5 へ進む**

---

### Step 5: 読者フィードバック回収

実行:
1. `progress.md` を `step5 in_progress` に更新する。
2. 通常フロー:
   - Step 3 で記録した各読者 Task ID を使い、TaskOutput（`block: true`）で完了を待つ。
   - 全ペルソナを並列で待機する。
3. 再開フォールバック:
   - 再開時などで未スポーンなら、Step 3 完了時と同手順で未完了分のみスポーンする。
   - `progress.md` の「Step 5 Detail」で `[x]` のペルソナは再スポーンしない。
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

---

### Step 6.5P: ポリッシュ（PASS_WITH_POLISH のみ）

実行:
1. `.claude/skills/write-episode/judgment-logic.md` の「Step 6.5P」に従う。
2. 完了後 Step 7 へ進む。

---

### Step 7: 確定・保存・アーク進行更新

実行:
1. `progress.md` を `step7 in_progress` に更新する。
2. **ユーザー確認**: 確定前にユーザーに以下を提示して承認を得る:
   - 判定結果（PASS / PASS_WITH_POLISH / FORCE_PASS）
   - 最終ドラフトのタイトル（1行目）
   - リビジョン回数と読者平均★
   - 「`episodes/` に保存してよろしいですか？ ドラフトを確認したい場合はお知らせください。」
   - ユーザーが確認を希望した場合は `workspace/current-draft.txt` の内容を提示し、承認後に進む
3. `.claude/skills/write-episode/finalization-details.md` を Read し、「確定・保存」と「アーク進行更新」に従って実行する。

---

### Step 7.5: 品質ログ記録

実行:
1. `progress.md` を `step7.5 in_progress` に更新する。
2. `finalization-details.md` の「Step 7.5: 品質ログ記録」に従い、`story/quality-log.md` を更新する。

---

### Step 7.6: エピソードレトロ

実行:
1. `progress.md` を `step7.6 in_progress` に更新する。
2. 以下のデータソースを収集する:
   - `workspace/arc-review.md` の判定・補足
   - `workspace/reader-feedback-*.md` の各ペルソナの指摘（archive 前に読む）
   - `story/author-reflections.md` の今話の記録
   - `story/series-tracker.md` の「現在の警告」
3. KPT を自動生成し、設計者に提示する:

```
### エピソードレトロ — 第{番号}話

**Keep**（今話で機能した要素）
- （arc-review の補足、読者の高評価ポイント、author の驚きから抽出）

**Problem**（今話の課題）
- （読者の共通指摘、series-tracker の警告、handover の未解決項目のうち関連するもの）

**Try**（次話で試すこと — 最大1件）
- （Keep/Problem から導かれる具体的な改善提案。1件に絞る）
```

4. 設計者に **Try** の承認を求める:
   - **承認** → `story/handover-notes.md` に `[TRY-NEXT]` タグでスレッドを追加する。次話の Step 2 で episode-brief に反映する
   - **却下** → 記録のみ（`discussion-log.md` に「Try 却下: {理由}」を追記）
   - **修正** → 設計者の修正版を `[TRY-NEXT]` として追加
   - **Try なし**（改善提案が不要な場合）→ スキップ
5. `progress.md` を更新: step7.6 を `[x]`、`current_step: "step7.6"`, `step_status: "completed"`

---

### Step 8: チームシャットダウン

実行:
1. `progress.md` を `step8 in_progress` に更新する。
2. コアメンバー（author, arc-reviewer）へ `shutdown_request` を送る（チーム機能非対応環境ではスキップ）。
3. **読者エージェントの終了**: `progress.md` の「Step 5 Detail」に記録された全読者ペルソナに対し、`SendMessage` で `shutdown_request` を送る。読者はバックグラウンドスポーンだが、チームに所属しているため明示的なシャットダウンが必要（tmux セッション内で idle 状態のまま残留するため）。読者が既に終了している場合は送信エラーを無視する。
4. 全員のシャットダウン確認後に TeamDelete を実行する（チーム機能非対応環境ではスキップ）。
5. `progress.md` を `step8 completed` に更新する（**チーム機能の有無にかかわらず必ず実行すること**）。
6. `workspace/` の全ファイル（`progress.md`, `discussion-log.md` を含む）を `archive/episode-{番号:2桁}/` にコピーする（progress.md に完了状態が記録されてからコピーすること）。
7. アーカイブ完了後に `workspace/` をクリーンアップする。

---

### 完了報告（ユーザー向け）

以下を必ず報告する。

- エピソードタイトル
- 保存先ファイルパス
- リビジョン回数
- アークレビュアーの最終判定
- 読者評価（全ペルソナの★と平均・中央値）
- ディスカッション発生回数（議論が発生したフェーズ一覧）
- ポリッシュ発動の有無（Step 6.5P 実行有無と修正箇所数）
- arc-observer スポーンの有無（幕境界到達時）
- `FORCE_PASS` の場合は警告メッセージ
