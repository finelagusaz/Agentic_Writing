# Agentic Writing — AI小説執筆プラットフォーム

## プロジェクト概要

マルチエージェントアーキテクチャによるWeb小説の自動執筆システム。ジャンルに依存しない汎用フレームワークで、対話的セットアップにより任意の作品を執筆できる。

## ディレクトリ構成

```
.claude/skills/          スキル定義
  setup-world/           作品セットアップ（対話的7ステップ）
  edit-story/            資料編集
  write-episode/         エピソード執筆（マルチエージェント）
.claude/agents/          サブエージェント定義
agents/                  エージェント役割定義
  editor.md              編集エージェント
  author.md              作者エージェント
  manager.md             担当者エージェント
  readers/
    reader-template.md   読者テンプレート
story/                   作品資料（/setup-world で生成）
  premise.md             コンセプト・テーマ
  setting.md             世界観・設定
  characters.md          登場人物
  plot-outline.md        プロット骨格
  writing-guide.md       文体ガイド + AI癖制御
  reader-personas.md     読者ペルソナ定義
  episode-summaries.md   各話あらすじ
  series-tracker.md      横断追跡（配分・登場密度・伏線進展・表現傾向）
  handover-notes.md      申し送り事項
  quality-log.md         品質記録
episodes/                確定済みエピソード
workspace/               作業ディレクトリ
archive/                 過去のドラフト
```

## 利用フロー

1. `/setup-world` — 作品の全設定を対話的に構築
2. `/edit-story` — 資料のレビュー・修正（任意）
3. `/write-episode N` — 第N話を自動執筆

## エージェント構成

| エージェント | 役割 | モデル |
|------------|------|-------|
| 編集 (editor) | 創作方針の策定、フィードバック統合 | opus |
| 作者 (author) | エピソード本文の執筆・改稿 | opus |
| 担当者 (manager) | 品質レビュー・合否判定 | sonnet |
| 読者×3 | ペルソナベースのフィードバック | sonnet |

### モデル非対称性への対策

担当者（Sonnet）が作者（Opus）に議論で「言い負かされる」リスクを以下で防止:
- **書面先行ルール**: 担当者は `manager-review.md` を書き切ってから議論に参加する
- **判定不変の原則**: 書面に記載した判定は議論で変更しない
- **議論の非対称制限**: 作者→担当者は「意図の説明」のみ許可。「判定への異議」は禁止

## ルール

### コミュニケーション
- チームメンバー間の会話には **SendMessage** を使用する
- コアメンバー（editor, author, manager）はチームに所属する
- 読者はサブエージェント（team_name なし）として独立動作する

### ファイル操作
- 各エージェントは自分の担当ファイルのみ出力する
- workspace/ は作業ディレクトリ。エピソード確定時に archive/ にコピーされる
- story/ の更新は editor が担当（handover-notes, plot-outline 等）
- `story/series-tracker.md` が欠落・破損している場合、`/write-episode` の Step 1 でテンプレート自動再生成して継続する

### 品質管理
- 担当者のレビュー判定は書面で確定し、議論で変更しない
- リビジョン上限に達した場合は FORCE_PASS で通過する
- AI癖制御ルール（writing-guide.md に記載）は全エージェントが遵守する

## ワークフロー概要

`/write-episode 〈番号〉` で起動。全ステップ自動実行。

1. **初期化 / 再開判定**: workspace 準備・前回進捗の確認
2. **チーム作成**: 編集・作者・担当者を一斉スポーン
3. **編集（方針策定）**: current-direction.md 出力
4. **方針ディスカッション**: 作者・担当者が方針に意見する場合
5. **作者（執筆/改稿）**: current-draft.txt 出力 → 読者をバックグラウンドスポーン
6. **担当者（レビュー）**: manager-review.md 出力
7. **ドラフトディスカッション**: レビュー所見に対し意見交換
8. **読者フィードバック回収**: バックグラウンドの読者結果を回収
9. **判定**: PASS / PASS_WITH_POLISH / REVISION_NEEDED / FORCE_PASS
10. **確定・保存**: episodes/ に保存、各記録更新
11. **プロット更新ディスカッション**: plot-outline.md の更新要否を検討
12. **チームシャットダウン**

## 中断復帰（レジューム）

- 実行中の進捗は `workspace/progress.md` に逐次記録される
- セッション中断後に同じ `/write-episode N` を実行すると、自動的に中断地点から再開する
- 手動で `workspace/progress.md` を削除すると強制的に新規開始できる
