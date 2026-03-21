# Agentic Writing

**Claude Codeのマルチエージェント機能を活用した、Web小説の自律執筆フレームワーク**

[![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-blue.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

「設定を渡せば、AIチームが議論・執筆・推敲をすべて担う」
ジャンルを問わず、自然な日本語で書かれた小説を出力します。

---

## これは何？

Agentic Writingは、**作者・アークレビュアー・読者ペルソナ**の役割を持つAIエージェントたちが、チームとして小説を執筆するフレームワークです。

- **対話形式で設定を作るだけ**で、あとはエピソードを自動生成
- 「AI特有のくどい言い回し（AI臭）」を抑える**文体制御機能**を内蔵
- 品質が基準を満たさない場合は、エージェント同士で**自動的にリビジョン（改稿）**を行います

## 主な特徴

- **マルチエージェントによる品質管理**: 作者(Opus)が書き、アークレビュアー(Sonnet)が役割タグ準拠で評価し、読者ペルソナ(Sonnet)がフィードバック
- **アーク駆動の執筆**: シナリオアーク・キャラクターアークから各話のブリーフを自動生成。物語全体の一貫性を保証
- **あらゆるジャンルに対応**: ライトノベル、ミステリー、SFから、なろう系、ラブコメまで幅広くカバー
- **高度な「AI癖」コントロール**: Show, don't tell の徹底、文末バリエーション、過剰な比喩の制限など
- **テンポ・構造の多様性保証**: テンポプロファイル6種、構成パターン10種、引きの4類型、反パターン制約で実装レベルの均質化を防止
- **手放しで進む自動改稿サイクル**: 最大3回の自動リビジョンを通じてクオリティを高めます

## クイックスタート

### 前提条件
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) がインストールされ、利用可能であること
- Claude の `opus` モデルと `sonnet` モデルが利用できること

### 導入手順

1. このリポジトリをクローンまたはダウンロードし、ディレクトリに移動します
2. ディレクトリ内で Claude Code を起動します
   ```bash
   claude
   ```
3. 以下のコマンドをチャットに入力するだけで、すぐに執筆体験が始まります

```bash
# 1. 作品のセットアップ（対話形式の7ステップで世界観やプロットを構築）
/setup-world

# 2. アーク設計（三幕構成・役割タグ・キャラクターアークを設計）
/setup-arc

# 3. エピソードの執筆（執筆→レビュー→改稿が全自動で進行）
/write-episode 1
```

> [!TIP]
> 設定を後から変更したい場合は `/edit-story 主人公の年齢を20歳にしたい` のように自然言語で指示できます。波及する影響もAIが自動で分析・修正します。

---

## 執筆の裏側

<details>
<summary><b>AIチームの構成と執筆フローを見る（クリックして展開）</b></summary>

### エージェント構成
```text
┌─────────────────────────────────────┐
│       オーケストレーター（あなた）       │
│    ブリーフ生成・判定・アーク進行管理     │
├──────────────┬──────────────────────┤
│    作者       │   アークレビュアー     │
│   (opus)     │     (sonnet)        │
│   執筆・改稿  │  役割タグ準拠レビュー   │
├──────────────┴──────────────────────┤
│     読者ペルソナ1・2・3 (sonnet)       │
│     バックグラウンドでフィードバック      │
└─────────────────────────────────────┘
```

### 自動執筆ワークフロー

```text
ブリーフ生成 → 作者スポーン → 執筆 → レビュー → 議論 → 読者FB → 判定
    │                                                       │
    │  ← ← ← ← ← リビジョン（最大3回） ← ← ← ← ← ← ← ←  │
    │                                                       │
    └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ 確定 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```
</details>

<details>
<summary><b>ディレクトリ構成を見る（クリックして展開）</b></summary>

```text
Agentic_Writing/
├── CLAUDE.md                 # システム設定
├── .claude/
│   ├── skills/               # スキル定義 (setup-world, setup-arc, edit-story, write-episode, arc-observe)
│   └── agents/               # サブエージェント定義
├── agents/                   # エージェント役割定義 (author, arc-reviewer, readers)
├── story/                    # 作品資料（/setup-world で自動生成）
│   ├── premise.md            # コンセプト・テーマ
│   ├── setting.md            # 世界観・設定
│   ├── characters.md         # 登場人物
│   ├── plot-outline.md       # プロット骨格（伏線テーブル含む）
│   ├── writing-guide.md      # 文体ガイド + AI癖制御 + テンポプロファイル
│   ├── scenario-arc.md       # シナリオアーク（/setup-arc で生成）
│   ├── character-arcs.md     # キャラクターアーク（/setup-arc で生成）
│   ├── reader-personas.md    # 読者ペルソナ
│   ├── author-reflections.md # 作者の気づき（話ごとの一言メモ）
│   ├── episode-summaries.md  # 各話あらすじ
│   ├── series-tracker.md     # 横断追跡（配分・登場密度・伏線・表現・テンポ・能動性・シーン構造）
│   ├── handover-notes.md     # アーク進行状況・申し送りスレッド
│   └── quality-log.md        # 品質記録
├── episodes/                 # 確定済みエピソード
├── workspace/                # 作業ディレクトリ
└── archive/                  # 過去ドラフト
```
</details>

## コマンド（スキル）一覧

| コマンド | 説明 |
|----------|------|
| `/setup-world` | 7ステップの対話形式で作品を初期構築。既存作品のインポートにも対応 |
| `/setup-arc` | 巻のシナリオアーク・キャラクターアークを設計。執筆前に必須 |
| `/edit-story` | 自然言語で作品設定を修正。整合性を保って資料を更新 |
| `/write-episode N` | 第N話を自動執筆。レビュー・フィードバック・リビジョンが自動実行 |
| `/arc-observe` | 幕の境界で全エピソードを通読し、アーク乖離を検出・修正 |

## 仕様ドキュメント

- 全体仕様: [`SPEC.md`](SPEC.md)
- 手順詳細・Mermaid: [`docs/workflows.md`](docs/workflows.md)
