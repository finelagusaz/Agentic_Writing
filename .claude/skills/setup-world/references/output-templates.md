# 出力ファイル仕様

## コンテンツファイル（ステップの成果物）

| ファイル | 内容 | 生成元 |
|---------|------|-------|
| `story/premise.md` | 作品コンセプト（ジャンル、テーマ、ログライン、トーン、想定話数、文字数目安） | Step 1-2 |
| `story/setting.md` | 世界観・設定 | Step 3 |
| `story/characters.md` | 登場人物（全キャラの詳細 + 口調テンプレート） | Step 4 |
| `story/plot-outline.md` | プロット骨格（三幕構成 + 各話概要） | Step 5 |
| `story/writing-guide.md` | 文体ガイド + AI癖制御ルール（コア制御 + オプション制御） | Step 6 |
| `story/reader-personas.md` | 読者ペルソナ定義（3名分） | Step 7 |

## テンプレートファイル（初期構造のみ）

| ファイル | 初期内容 |
|---------|---------|
| `story/episode-summaries.md` | ヘッダー + 「アーク要約」「直近エピソード詳細」の空セクション |
| `story/handover-notes.md` | ヘッダー + 各セクション（設定整合性/未回収伏線/表現・演出/キャラクター描写/読者からの要望/継続的な指針）の空テンプレート |
| `story/quality-log.md` | ヘッダー + テーブルヘッダーのみ |
| `story/series-tracker.md` | 横断追跡テンプレート（下記参照） |

## `story/series-tracker.md` の初期テンプレート

`.claude/skills/setup-arc/references/series-tracker-template.md` を Read し、その内容で出力する（`/write-episode` Step 1 の必須見出し検証と一致する唯一の正本）。

## 出力後の確認

全ファイル出力後、ユーザーに以下を報告する:
- 生成されたファイル一覧
- 各ファイルの概要（1行ずつ）
- `/edit-story` で後から修正可能であること
- `/setup-arc` でアーク設計を行い、`/write-episode 1` で執筆を開始できること
