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
  author.md              作者エージェント（/write-episode）
  arc-reviewer.md        アークレビュアー（/write-episode）
  editor.md              編集エージェント（/edit-story のみ）
  manager.md             担当者エージェント（旧版・参照用）
  readers/
    reader-template.md   読者テンプレート
story/                   作品資料（/setup-world / /setup-arc で生成）
  premise.md             コンセプト・テーマ
  setting.md             世界観・設定
  characters.md          登場人物
  plot-outline.md        プロット骨格
  writing-guide.md       文体ガイド + AI癖制御
  scenario-arc.md        シナリオアーク（/setup-arc で生成）
  character-arcs.md      キャラクターアーク（/setup-arc で生成）
  reader-personas.md     読者ペルソナ定義
  episode-summaries.md   各話あらすじ
  series-tracker.md      横断追跡（配分・登場密度・伏線進展・表現傾向・乖離チェック）
  handover-notes.md      アーク進行状況・申し送りスレッド
  quality-log.md         品質記録
episodes/                確定済みエピソード
workspace/               作業ディレクトリ
archive/                 過去のドラフト
```

## 利用フロー

1. `/setup-world` — 作品の全設定を対話的に構築
2. `/setup-arc` — 巻のシナリオアーク・キャラクターアークを設計（**執筆前に必須**）
3. `/edit-story` — 資料のレビュー・修正（任意）
4. `/write-episode N` — 第N話を自動執筆

## エージェント構成

| エージェント | 役割 | モデル |
|------------|------|-------|
| 作者 (author) | エピソード本文の執筆・改稿 | opus |
| アークレビュアー (arc-reviewer) | 役割タグ準拠評価・改稿判定 | sonnet |
| 読者×N | ペルソナベースのフィードバック（初稿のみ） | sonnet |

> **編集 (editor)** は `/edit-story` スキルでのみ使用。`/write-episode` では廃止済み。

### モデル非対称性への対策

アークレビュアー（Sonnet）が作者（Opus）に議論で「言い負かされる」リスクを以下で防止:
- **書面先行ルール**: アークレビュアーは `arc-review.md` を書き切ってから議論に参加する
- **判定不変の原則**: 書面に記載した判定は議論で変更しない
- **議論の非対称制限**: 作者→アークレビュアーは「意図の説明」のみ許可。「判定への異議」は禁止

## ルール

### コミュニケーション
- チームメンバー間の会話には **SendMessage** を使用する
- `/write-episode` のコアメンバー（author, arc-reviewer）はチームに所属する
- 読者はサブエージェント（team_name なし）として独立動作する

### ファイル操作
- 各エージェントは自分の担当ファイルのみ出力する
- workspace/ は作業ディレクトリ。エピソード確定時に episodes/ にコピーされる
- story/ のアーク進行更新（character-arcs, handover-notes, series-tracker 等）はオーケストレーターが直接実行する
- `story/series-tracker.md` が欠落・破損している場合、`/write-episode` の Step 1 でテンプレート自動再生成して継続する

### 品質管理
- アークレビュアーの判定は書面（arc-review.md）で確定し、議論で変更しない
- リビジョン上限に達した場合は FORCE_PASS で通過する
- AI癖制御ルール（writing-guide.md に記載）は全エージェントが遵守する

## ワークフロー概要

`/write-episode 〈番号〉` で起動。全ステップ自動実行。前提: `story/scenario-arc.md` と `story/character-arcs.md` が必要（`/setup-arc` で生成）。

1. **初期化 / 再開判定**: workspace 準備・前回進捗の確認
2. **チーム作成**: 作者・アークレビュアーをスポーン
3. **エピソードブリーフ生成**: オーケストレーターが `episode-brief.md` を直接生成（アーク設計から降ろし）
4. **作者（初稿執筆）**: `current-draft.txt` 出力 → 読者をバックグラウンドスポーン（初稿のみ）
5. **アークレビュアー（レビュー）**: `arc-review.md` 出力
6. **ドラフトディスカッション（Step 4D）**: REVISION_NEEDED の場合→ Step 4 へループ（改稿）
7. **読者フィードバック回収**: バックグラウンドの読者結果を回収
8. **判定（Step 6）**: PASS / PASS_WITH_POLISH / FORCE_PASS
9. **確定・保存（Step 7）**: episodes/ に保存、アーク進行更新（character-arcs / handover-notes / series-tracker）
10. **品質ログ（Step 7.5）**: quality-log.md に記録
11. **チームシャットダウン**

## 中断復帰（レジューム）

- 実行中の進捗は `workspace/progress.md` に逐次記録される
- セッション中断後に同じ `/write-episode N` を実行すると、自動的に中断地点から再開する
- 手動で `workspace/progress.md` を削除すると強制的に新規開始できる
