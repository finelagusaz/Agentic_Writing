---
name: write-episode
description: マルチエージェント（author + arc-reviewer + reader群）によるWeb小説エピソード自動執筆スキル。アーク設計を起点にエピソードブリーフを生成し、執筆・改稿・品質判定・確定保存・アーク進行更新までをオーケストレーションする。引数は episode_number、任意で --max-revisions=N。
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
2. コア2名を `team_name` 指定ありで並列 Task スポーンする。

| チームメイト | subagent_type | name | model |
|---|---|---|---|
| 作者 | novel-author | author | opus |
| アークレビュアー | novel-arc-reviewer | arc-reviewer | sonnet |

3. 各メンバーの prompt:
   - 「あなたは第{番号}話の執筆チームの{役割}です。agents/{ファイル}.md を読み込み、チームリーダーからの指示を待ってください。」
4. `story/reader-personas.md` を Read し、全ペルソナ（ID・名前・subagent_type）を取得する。
5. `story/series-tracker.md` の存在と必須見出しを検証する。
   - `## アクション配分（直近3話）`
   - `## キャラクター登場密度（直近5話）`
   - `## 伏線・要素の進展追跡`
   - `## 表現パターン累積（直近5話）`
6. 欠落/破損時はテンプレートで再生成し、ユーザー通知と `discussion-log.md` 追記を行う（未作成時はヘッダー付きで新規作成してから追記）。

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
   - `[MUST-THIS]`: 今話で扱う（episode-brief に明示）
   - `[MUST-VOL]` 以下: 参考として記録するに留め、今話で処理しない
5. 前話エピソード（`episodes/`）が存在する場合は Read し、直前の文脈を把握する。
6. `workspace/episode-brief.md` を作成する:

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

## シーン構成・文字数目安

（役割タグに応じた構成案と `story/premise.md` の想定文字数）
```

完了条件:
- `workspace/episode-brief.md` が存在し、「アーク上の位置」「書かないことリスト」が記載されている。
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
2. author に SendMessage する。
   - 初稿（`revision_count == 0`）:
     - `agents/author.md` に従い、`workspace/episode-brief.md`（最優先）と `story/` 主要資料・前話を参照する。
     - `workspace/current-draft.txt` に本文のみ出力する。
   - 改稿（`revision_count > 0`）:
     - `workspace/episode-brief.md` と `workspace/arc-review.md` を参照して改稿する。
     - `workspace/current-draft.txt` を上書きし、本文のみ出力する。
3. 完了報告を待ち、出力検証する。
4. author に `story/author-reflections.md` への記録を指示する:
   - 今話を書いて**驚いたこと**を一言だけ記録する（予定通りだったことは書かない）。
   - ファイルが存在しない場合は `## 第{番号}話` 見出しで新規作成する。存在する場合は末尾に追記する。
   - 驚くべき点がなければスキップ（記録を強制しない）。

完了条件:
- `progress.md`: `step3` を `[x]`, `current_step: "step3"`, `step_status: "completed"`。

#### Step 3 完了直後: 読者バックグラウンドスポーン

実行:
1. **初稿（`revision_count == 0`）のみ**実行する。改稿時はスキップする。
2. `story/reader-personas.md` から各ペルソナを取得し、`team_name` なし・`run_in_background: true` で並列 Task スポーンする。
3. 各読者 prompt:
   - `workspace/current-draft.txt` を読み、`agents/readers/reader-template.md` に従って `workspace/reader-feedback-{ペルソナID}.md` に出力する。
   - 設定整合性担当ペルソナには `story/setting.md`, `story/characters.md`, `story/episode-summaries.md`, `story/handover-notes.md`, `workspace/episode-brief.md` も参照させる。
4. `progress.md` の「Step 5 Detail」を全ペルソナ `[ ]` で初期化し、各読者 Task ID を記録する。

---

### Step 4: アークレビュー

実行:
1. `progress.md` を `step4 in_progress` に更新する。
2. arc-reviewer に SendMessage する。
   - `agents/arc-reviewer.md` に従い、`workspace/episode-brief.md` と `workspace/current-draft.txt` を参照する。
   - `story/character-arcs.md` も参照して意図的未解決期間の確認を行う。
   - 現在のリビジョン回数 `{revision_count}/{max_revisions}` を明示する。
   - `workspace/arc-review.md` に出力する。
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
2. `.claude/skills/write-episode/finalization-details.md` を Read し、「確定・保存」と「アーク進行更新」に従って実行する。

---

### Step 7.5: 品質ログ記録

実行:
1. `progress.md` を `step7.5 in_progress` に更新する。
2. `finalization-details.md` の「Step 7.5: 品質ログ記録」に従い、`story/quality-log.md` を更新する。

---

### Step 8: チームシャットダウン

実行:
1. `progress.md` を `step8 in_progress` に更新する。
2. コアメンバー（author, arc-reviewer）へ `shutdown_request` を送る。
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
- アークレビュアーの最終判定
- 読者評価（全ペルソナの★と平均・中央値）
- ディスカッション発生回数（議論が発生したフェーズ一覧）
- ポリッシュ発動の有無（Step 6.5P 実行有無と修正箇所数）
- arc-observer スポーンの有無（幕境界到達時）
- `FORCE_PASS` の場合は警告メッセージ
