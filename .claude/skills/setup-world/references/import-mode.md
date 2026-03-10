# インポートモード

`story/` に既存ファイルがある場合は、上書き前に `archive/import-backup/` へのバックアップを行う。

インポートモードは **Phase 1（設定ファイル生成）** と **Phase 2（アーク設計）** の2段階で構成される。完了後は直接 `/write-episode N` で執筆を開始できる。

## 中断復帰

Phase 1 の中断復帰は `story/` 内の既存ファイルで進捗を判定する:

| ファイルの存在 | 判定 |
|-------------|-----|
| `premise.md` | Step I-1 完了 |
| `setting.md` | Step I-2 完了 |
| `characters.md` | Step I-3 完了 |
| `plot-outline.md` | Step I-4 完了 |
| `writing-guide.md` | Step I-5 完了 |
| `reader-personas.md` | Step I-6 完了 |
| `episode-summaries.md`（アーク要約が空でない） | Step I-7 完了 → Phase 2 へ |

Phase 2 の中断復帰は `story/arc-design-progress.md` による `/setup-arc` 既存のメカニズムをそのまま使用する。

---

## Phase 1: 設定ファイル生成

***

### Step I-0: 素材アセスメント

ユーザーに以下を問う:

```
既存作品について教えてください。

問い1　何話まで書いていますか？

問い2　参照できる素材はありますか？
  A. テキストファイルがある（パスを教えてください）
  B. 設定メモ・キャラ表などがある（パスを教えてください）
  C. ファイルはない — 対話で説明する
  D. A+B の両方ある
```

- ファイルが提供された場合 → Read で読み込み、内部コンテキストとして保持する
- 対話の場合 → 各ステップでユーザーに口頭説明を求める

内部変数 `total_existing_episodes`（既存話数）を記録する。Phase 2 終了後の通知で使用する。

***

### Step I-1: コンセプト抽出（premise.md）

**素材ありの場合:**
- 素材からジャンル・テーマ・ログライン・トーンを抽出して提示する
- 「この理解で合っていますか？修正があればどうぞ」と確認する

**対話の場合:**
- 「作品のジャンルは何ですか？」「テーマを一言で表すと？」等を問う
- 新規モードのリコメンド提示は省略し、ユーザーの回答から構成する

**追加の確認（新規モードにない項目）:**
- 想定される全体話数（既存+今後）
- 1話あたりの文字数（既存作品に揃える）

**出力:** `story/premise.md`（新規と同じフォーマット）

***

### Step I-2: 世界観抽出（setting.md）

- 素材から世界観・設定を抽出して提示する
- 対話の場合はジャンルに応じた重点設定項目で聞き取る
- 新規モードの「差別化ポイント3案」は省略する（既に確立済みのため）

**出力:** `story/setting.md`

***

### Step I-3: キャラクター抽出（characters.md）

**最重要ステップ** — 口調テンプレートの精度が執筆品質に直結する。

- 素材からキャラクター情報を抽出する
- **口調テンプレート**はエピソード本文のセリフから3例以上抽出して提示する
  - 本文がない場合は「このキャラの典型的なセリフ例を3つ以上教えてください」とユーザーに求める
- 各キャラの**現在の状態**（既に成長・変化している部分）も確認する

**出力:** `story/characters.md`（現在の状態を反映）

***

### Step I-4: プロット骨格（plot-outline.md）

**既存エピソードの反映が必要:**
- 既存話は「実際に起きた展開」として記載する（概要1〜2行ずつ）
  - ユーザーに「各話のあらすじを簡潔に教えてください」と求める
  - または素材から抽出する
- 今後の話は「予定」として記載する（TBD 可）
- 三幕構成は既存+今後を通したものを提案する

**伏線の扱い:**
- 既存の伏線で未回収のものを列挙する
- 今後の回収予定を確認する

**出力:** `story/plot-outline.md`

***

### Step I-5: 文体ガイド（writing-guide.md）

**素材（エピソード本文）ありの場合:**
- 文体を分析する（視点、文長、会話比率、トーン）
- 分析結果をもとに文体定義案を提示する
- AI癖制御のオプション値を提案する

**対話の場合:**
- 新規モードと同じフロー（デフォルト提示 → ユーザー調整）

**必須セクション構成は新規モードと同一**（11セクション全て）。構成パターン×役割タグ推奨相性表と感覚レンズは、ジャンルに依存しないデフォルト値をそのまま使用する。

**出力:** `story/writing-guide.md`

***

### Step I-6: 読者ペルソナ（reader-personas.md）

新規モード（Step 7）と同一フロー。ジャンル・トーンからの自動生成 → ユーザー確認。

**出力:** `story/reader-personas.md`

***

### Step I-7: ストーリー状態の初期化

新規モードにないインポート専用のステップ。`/write-episode` が参照する追跡ファイルを初期化する。

ユーザーに以下を問う:

```
問い1　これまでの物語のあらすじを教えてください。
      幕ごとに区切れる場合は分けて記述してください。
      （episode-summaries.md の「アーク要約」に使用します）

問い2　現在進行中のスレッドを教えてください。
      例: 未回収の伏線、発展途中のキャラクター関係、未解決の課題
      （handover-notes.md の初期スレッドに使用します）
```

**出力:**
- `story/episode-summaries.md`
  - 「アーク要約」にユーザー提供のあらすじを記載する
  - 「直近エピソード詳細」は空（エピソードを取り込んでいないため）
- `story/handover-notes.md`
  - ユーザー提供のスレッドを `[MUST-VOL]`（暫定分類）として記載する
  - Phase 2 のアーク設計でトリアージされる
- `story/series-tracker.md` — 新規モードと同じ空テンプレート
- `story/quality-log.md` — 新規モードと同じ空テンプレート

---

## Phase 2 への遷移

Phase 1 完了後、以下を表示してから Phase 2 に進む:

```
設定ファイルの準備が完了しました。
続いて、次の巻（第{total_existing_episodes + 1}話〜）のアーク設計に入ります。
```

---

## Phase 2: アーク設計

`/setup-arc` の Steps A〜G をそのまま実行する。ただし以下を修正する:

**Step 0（初期化）をスキップ** — 「新規/続巻」の選択は不要。前巻アークファイルの代わりに Phase 1 の出力を参照する:
- `story/episode-summaries.md` のアーク要約 → 前巻の流れとして参照
- `story/handover-notes.md` → 引き継ぎスレッドとして参照
- `story/characters.md` の「現在の状態」 → 発展済みキャラクターとして参照

**Step A（テーマ）の修正:**
- `story/premise.md`（Phase 1 で生成済み）のテーマを提示する
- 「この巻でテーマを深める方向、または新しい角度はありますか？」と問う
- 前巻との連続性確認は `story/episode-summaries.md` のアーク要約を参照する

**Step B〜G は `/setup-arc` SKILL.md と同じ手順で実行する。**
`characters.md` の「現在の状態」を前提にキャラクターアークを設計する。

**Step G 完了時:**
- `story/arc-design-progress.md` に LOCKED を記録する
- `archive/phase0/` が存在しない場合は自動作成する
- `story/arc-design-progress.md` を `archive/phase0/arc-design-progress.md` としてコピーする

---

## インポートモードの出力後の通知

Phase 2 完了後、以下を表示する:

```
インポートとアーク設計が完了しました。

📄 設定ファイル:
  - story/premise.md, setting.md, characters.md,
    plot-outline.md, writing-guide.md, reader-personas.md

📊 追跡ファイル:
  - story/episode-summaries.md（アーク要約あり）
  - story/handover-notes.md（初期スレッドあり）
  - story/series-tracker.md, quality-log.md

🎯 アーク設計:
  - story/scenario-arc.md, character-arcs.md（LOCKED）

/edit-story で後から修正可能です。
/write-episode {total_existing_episodes + 1} で執筆を開始できます。
```
