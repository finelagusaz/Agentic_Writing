# 再開（レジュメ）ロジック

実行手順の**最初のアクション**として、以下の再開チェックを行う:

1. `workspace/progress.md` を Glob で検索する
2. **ファイルが存在しない場合**: 通常の新規開始（Step 0 へ）
3. **ファイルが存在する場合**: Read で読み込み、YAML ブロックから `episode` と `current_step` を確認:
   a. **episode が引数と一致する場合 → 再開モード**
      - ユーザーに「既存の進捗を検出しました。第{N}話の {current_step} から再開します」と表示
      - Step 0 を**スキップ**（workspace のクリーンを行わない）
      - Step 1（チーム作成 + コアメンバースポーン）は**必ず実行**（チームはセッション間で維持されない）
      - `current_step` と `step_status` から再開地点を決定:
        - `step_status` が `completed` → 次のステップから再開
        - `step_status` が `in_progress` → そのステップを再実行（Step 5 は部分完了を考慮）
      - ディスカッションステップ（step4d）は状態が非永続。中断時はディスカッション全体を再実行
      - 再開前に、再開先ステップの前提ファイルが存在・有効か Glob + Read で検証する。欠落時はユーザーに警告し新規開始にフォールバック
      - `revision_count` と `force_pass` を progress.md の値で復元
   b. **episode が引数と異なる場合 → 警告モード**
      - ユーザーに確認: 「workspace に第{M}話の進捗が残っています。第{N}話を開始すると失われます。続行しますか？」
      - 承認 → 通常の新規開始（Step 0 へ） / 拒否 → 中断
4. **progress.md の形式が不正な場合**: ユーザーに警告し、新規開始にフォールバック

## 前提ファイル一覧（再開時の検証用）

| 再開先 | 必須ファイル |
|-------|------------|
| Step 2 | `story/scenario-arc.md`, `story/character-arcs.md` |
| Step 2Q | `workspace/episode-brief.md` |
| Step 3 | `workspace/episode-brief.md`。revision_count > 0 の場合は `workspace/arc-review.md` も |
| Step 4 | `workspace/episode-brief.md`, `workspace/current-draft.txt` |
| Step 4D | `workspace/episode-brief.md`, `workspace/current-draft.txt`, `workspace/arc-review.md` |
| Step 5 | `workspace/current-draft.txt` |
| Step 6 | `workspace/arc-review.md`, `workspace/reader-feedback-*.md`（全読者分） |
| Step 6.5P | `workspace/current-draft.txt` |
| Step 7 | `workspace/current-draft.txt`, `workspace/episode-brief.md` |
| Step 7.5 | `episodes/{番号:2桁}_{タイトル}.txt`（Step 7 で保存済み） |
| Step 8 | （なし — チームシャットダウンのみ） |
