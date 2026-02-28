# 判定・ポリッシュロジック

## 目次

- [Step 6: 判定ロジック](#step-6-判定ロジック)
- [Step 6.5P: ポリッシュ（軽微修正）](#step-65p-ポリッシュ軽微修正)

---

## Step 6: 判定ロジック

リーダー（あなた自身）が以下を直接実行する:

0. **自動スキャン**: `workspace/current-draft.txt` に対し以下の Grep チェックを行う:
   - `第\d+話` パターンが1行目（タイトル行）以外に存在しないか確認
   - パターン検出時: 該当箇所をユーザーに警告表示し、**自動的に FORCE_PASS** として扱う（アークレビュアー判定に関わらず）。revision-log.md に「メタナラティブ表現の自動検出」を記録する

1. **FORCE_PASS チェック**: `progress.md` の YAML ブロックに `force_pass: true` が記録されている場合 → **FORCE_PASS**（Step 7へ、警告付き）

2. `workspace/arc-review.md` を Read し、最終判定（OK / REVISION_NEEDED / MAJOR_REVISION）を確認する。
   - ここで REVISION_NEEDED が残っている場合（再開フローなどで稀に発生）→ **FORCE_PASS**

3. `workspace/reader-feedback-*.md` を Glob で検索し全読者フィードバックを Read で読み、各読者の総合評価★を確認して平均と中央値を算出する。

4. 判定ロジック（arc-reviewer が OK の場合）:
   - **PASS_WITH_POLISH 条件確認**（下記 4a 参照）:
     - いずれかに該当 → **PASS_WITH_POLISH**（Step 6.5P へ）
     - いずれにも該当しない → **PASS**（Step 7 へ）

4a. **PASS_WITH_POLISH 判定**（PASS 条件を満たした後の追加チェック）:
   - `arc-review.md` に「気になった点」等の軽微な問題が **2件以上** ある
   - 読者フィードバック3名のうち **2名以上が共通して** 指摘している箇所がある
   - 読者平均★ が **3.0 未満**（アーク役割は果たしているが読書体験として粗い）

4b. **読者フィードバック差分分析**:
   読者間の★評価差が **2★以上** ある場合、以下の分析を行う:
   - 高評価者と低評価者の主要な評価軸の違いを特定する
   - 低評価者の具体的な不満点を抽出する
   - `story/handover-notes.md` の適切なスレッドに記録する（例: 「読者評価差：ペルソナ1★3 vs ペルソナ2★5: テンポ vs 感情描写のトレードオフ」）
   この分析は判定結果（PASS/PASS_WITH_POLISH/FORCE_PASS）に関わらず実行する。

5. PASS の場合: progress.md を更新: step6 を `[x]`、`current_step: "step6"`, `step_status: "completed"`。Step 7 へ。
5a. PASS_WITH_POLISH の場合: progress.md を更新: step6 を `[x]`、`current_step: "step6"`, `step_status: "completed"`。Step 6.5P へ。
5b. FORCE_PASS の場合: progress.md を更新: step6 を `[x]`、`current_step: "step6"`, `step_status: "completed"`。Step 7 へ（Step 6.5P はスキップ）。

6. 判定結果とステータスをユーザーに表示する。

---

## Step 6.5P: ポリッシュ（軽微修正）

Step 6 で PASS_WITH_POLISH と判定された場合にのみ実行する。

progress.md を更新: `current_step: "step6.5p"`, `step_status: "in_progress"`

リーダー（あなた自身）が以下を実行する:

1. **指摘箇所の抽出**: Step 6 で特定した軽微な指摘を **最大3件** にまとめる。以下の優先順位で選定:
   - arc-reviewer と読者が共通して指摘した箇所（最優先）
   - 読者2名以上が共通して指摘した箇所
   - arc-review.md の「気になった点」

2. **author に部分修正を依頼**: SendMessage で author に修正箇所（最大3件）を明示し、全体構成は変更せず `workspace/current-draft.txt` を上書きするよう指示する。完了報告を待ち出力を検証する。

3. **arc-reviewer の再レビューは不要**（軽微修正のため）
4. **読者の再評価も不要**（スコアは初回評価を使用）

progress.md を更新: step6.5p を `[x]`、`current_step: "step6.5p"`, `step_status: "completed"`

**Step 7 へ進む**。
