# Agentic Writing — AI小説執筆プラットフォーム

## プロジェクト概要

マルチエージェントアーキテクチャによるWeb小説の自動執筆システム。ジャンルに依存しない汎用フレームワークで、対話的セットアップにより任意の作品を執筆できる。

## ディレクトリ構成

```
.claude/skills/          スキル定義
  setup-world/           作品セットアップ（対話的7ステップ）
  edit-story/            資料編集
  write-episode/         エピソード執筆（マルチエージェント）
  story-status/          作品進捗ダッシュボード
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
  author-reflections.md  作者の気づき（話ごとの一言メモ）
  episode-summaries.md   各話あらすじ
  series-tracker.md      横断追跡（配分・登場密度・伏線進展・表現傾向・乖離チェック）
  handover-notes.md      アーク進行状況・申し送りスレッド
  quality-log.md         品質記録
episodes/                確定済みエピソード
workspace/               作業ディレクトリ
archive/                 過去のドラフト
```

## 利用フロー

### 新規作成
1. `/setup-world` — 作品の全設定を対話的に構築（新規作成モード）
2. `/setup-arc` — 巻のシナリオアーク・キャラクターアークを設計（**執筆前に必須**）
3. `/edit-story` — 資料のレビュー・修正（任意）
4. `/write-episode N` — 第N話を自動執筆
5. `/arc-observe` — 幕の境界でアーク観測（設計と実際の乖離検出・修正）

### 既存作品インポート
1. `/setup-world` — インポートモードを選択。設定ファイル生成 + アーク設計を一気通貫で実行
2. `/edit-story` — 資料のレビュー・修正（任意）
3. `/write-episode N` — 第N話を自動執筆

## エージェント構成

| エージェント | 役割 | モデル | 起動タイミング |
|------------|------|-------|-------------|
| 作者 (author) | エピソード本文の執筆・改稿 | opus | `/write-episode` 毎話 |
| アークレビュアー (arc-reviewer) | 役割タグ準拠評価・改稿判定 | sonnet | `/write-episode` 毎話 |
| 読者×N | ペルソナベースのフィードバック（初稿のみ） | sonnet | `/write-episode` 初稿時 |
| アークオブザーバー (arc-observer) | 全エピソード通読・アーク乖離検出・修正提案 | — | `/arc-observe`（幕境界） |

> **編集 (editor)** は `/edit-story` スキルでのみ使用。`/write-episode` では廃止済み。

### モデル非対称性への対策

アークレビュアー（Sonnet）が作者（Opus）に議論で「言い負かされる」リスクを防止するため、**書面先行ルール**（判定は arc-review.md で確定し議論で変更しない）を採用。詳細は `agents/arc-reviewer.md` に記載。

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
2. **チーム作成（Step 1）**: TeamCreate のみ。コアメンバーは使用ステップで遅延スポーン
3. **エピソードブリーフ生成（Step 2）**: オーケストレーターが `episode-brief.md` を直接生成（アーク設計から降ろし）
4. **作者スポーン＋初稿執筆（Step 3）**: author を指示付きでスポーン → `current-draft.txt` 出力 → 読者をバックグラウンドスポーン（初稿のみ）
5. **アークレビュアースポーン＋レビュー（Step 4）**: arc-reviewer を指示付きでスポーン → `arc-review.md` 出力
6. **ドラフトディスカッション（Step 4D）**: REVISION_NEEDED の場合→ Step 3 へループ（改稿）
7. **読者フィードバック回収（Step 5）**: バックグラウンドの読者結果を回収
8. **判定（Step 6）**: PASS / PASS_WITH_POLISH / FORCE_PASS
9. **確定・保存（Step 7）**: episodes/ に保存、アーク進行更新、プロット消費監査
10. **品質ログ（Step 7.5）**: quality-log.md に記録
11. **チームシャットダウン（Step 8）**

## 中断復帰（レジューム）

- 実行中の進捗は `workspace/progress.md` に逐次記録される
- セッション中断後に同じ `/write-episode N` を実行すると、自動的に中断地点から再開する
- 手動で `workspace/progress.md` を削除すると強制的に新規開始できる

## Gotchas

- **エージェント空スポーン問題（対策済み）**: 「指示待ち」で空スポーン → SendMessage で指示送信、という2段階方式ではメッセージが拾われないことがある（author/arc-reviewer 両方で発生）。**対策: 全コアメンバーのスポーンを使用ステップに遅延し、スポーン時プロンプトに指示を直接含める**。Step 1 ではチーム作成のみ。author は Step 3、arc-reviewer は Step 4 でスポーンする
- **複数 author の上書き競合**: リスポーン時に旧 author が生き残っていると、後から出力して `current-draft.txt` を上書きする場合がある。リスポーン後は旧 author にシャットダウンリクエストを送ること
- **FORCE_PASS のユーザー確認**: リビジョン上限到達時、FORCE_PASS は自動確定せずユーザーに確認を求める。ユーザーが追加指示を出した場合は revision_count をリセットして1回追加改稿を許可する
- **読者は team_name なし**: 読者エージェントは `run_in_background: true` のバックグラウンドエージェントとして独立スポーンする。チームに所属しないため TeamDelete の影響を受けない（自動終了する）
- **質感マーカー（`〈質感〉`タグ）**: `story/plot-outline.md` の一部のエピソード記述に `〈質感〉` タグで演出指示が付与されている。これは第二部のテーマ（選択）の言葉で書かれた演出指示であり、オーケストレーターが episode-brief 生成時に参照する。author には第三部の設計意図を開示しない（情報の非対称性を意図的に維持）
- **第三部構想**: `story/plot-outline.md` に第三部（構想）セクションが存在する。贈与を設計原理とした全体構造。第二部執筆時のオーケストレーターは参照できるが、author には開示しない
