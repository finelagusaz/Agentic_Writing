# 判定・ポリッシュロジック

## 目次

- [Step 6: 判定ロジック](#step-6-判定ロジック)
- [Step 6.5P: ポリッシュ（軽微修正）](#step-65p-ポリッシュ軽微修正)

---

## Step 6: 判定ロジック

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
     - Step 5 Detail の全ペルソナも `[ ]` にリセット
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

---

## Step 6.5P: ポリッシュ（軽微修正）

Step 6 で PASS_WITH_POLISH と判定された場合にのみ実行する。

progress.md を更新: `current_step: "step6.5p"`, `step_status: "in_progress"`

リーダー（あなた自身）が以下を実行する:

1. **指摘箇所の抽出**: Step 6 で特定した軽微な指摘を **最大3件** にまとめる。以下の優先順位で選定:
   - 担当者と読者が共通して指摘した箇所（最優先）
   - Step 4D で editor が指摘した方針との齟齬
   - 読者2名以上が共通して指摘した箇所

2. **author に部分修正を依頼**: SendMessage で author に修正箇所（最大3件）を明示し、全体構成は変更せず `workspace/current-draft.txt` を上書きするよう指示する。完了報告を待ち出力を検証する。

3. **担当者の再レビューは不要**（軽微修正のため）
4. **読者の再評価も不要**（スコアは初回評価を使用）

progress.md を更新: step6.5p を `[x]`、`current_step: "step6.5p"`, `step_status: "completed"`

**Step 7 へ進む**。
