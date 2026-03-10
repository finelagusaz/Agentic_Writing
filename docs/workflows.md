# Agentic Writing ワークフロー詳細

## 1. 全体フロー（高レベル）

```mermaid
flowchart TD
    SW["/setup-world"] --> SA["/setup-arc（Phase 0）"]
    SA --> W["/write-episode N（Phase 1）"]
    W --> J{"判定"}
    J -->|PASS| F["確定保存"]
    J -->|PASS_WITH_POLISH| P["軽微修正"]
    P --> F
    J -->|REVISION_NEEDED| R["ディスカッション → 改稿"]
    R --> W
    J -->|FORCE_PASS| F
    F --> B{"幕の境界?"}
    B -->|Yes| AO["/arc-observe（Phase 2）"]
    AO --> W
    B -->|No| W
```

## 2. `/setup-world` 詳細

### 2.1 モード
| モード | 選択肢 | 流れ |
|-------|--------|-----|
| 新規作成 | A | Steps 1〜7 → `story/` 出力。その後 `/setup-arc` へ |
| 既存作品インポート | B | Steps I-0〜I-7（設定生成）→ Phase 2（アーク設計）→ `/write-episode N` へ |

### 2.2 新規作成ステップ
1. Step 1: カテゴリ・ジャンル選択
2. Step 2: テーマ・コンセプト
3. Step 3: 世界観・設定
4. Step 4: キャラクター
5. Step 5: プロット骨格
6. Step 6: 文体ガイド + AI癖制御（構成パターン推奨相性表・感覚レンズを含む）
7. Step 7: 読者ペルソナ
8. 出力: `story/` 一括生成

### 2.3 インポートモードステップ

**Phase 1 — 設定ファイル生成:**
| Step | 出力ファイル |
|------|------------|
| I-0 | — （素材確認・既存話数記録） |
| I-1 | `premise.md` |
| I-2 | `setting.md` |
| I-3 | `characters.md` |
| I-4 | `plot-outline.md` |
| I-5 | `writing-guide.md` |
| I-6 | `reader-personas.md` |
| I-7 | `episode-summaries.md`, `handover-notes.md`, `series-tracker.md`, `quality-log.md` |

**Phase 2 — アーク設計:** `/setup-arc` Steps A〜G を実行（Step 0 はスキップ）

### 2.4 中断復帰（インポートモード）
`story/` 内のファイル存在で進捗を判定し、未生成ファイルに対応するステップから再開する。

### 2.5 出力契約
- コンテンツ系: `premise.md`, `setting.md`, `characters.md`, `plot-outline.md`, `writing-guide.md`, `reader-personas.md`
- テンプレート系: `episode-summaries.md`, `handover-notes.md`, `quality-log.md`, `series-tracker.md`

## 3. `/setup-arc` 詳細（Phase 0）

### 3.1 ステップ

```
Step 0  初期化（中断復帰チェック / 新規・続巻・インポート継続の確認）
Step A  テーマの言語化（感情命題に向けた対話）
Step B  シナリオアーク草案生成 + チェックリスト初期化
Step C  Claude が問いを提示（選択肢5択形式）→ 設計者が回答 → 草案更新
        ※ 構造的完全性チェック全項目完了まで繰り返す
Step D  キャラクターアーク草案生成
Step E  同上ループ（追加チェック完了まで）
Step F  エピソード役割マップ完成（全話に役割タグを割り当て）
Step G  設計者承認 → アーク設計ロック（執筆解禁）
```

### 3.2 役割タグ定義
| タグ | 定義 |
|-----|------|
| **頂点** | 幕の感情的クライマックス。一つの主題に集中 |
| **助走** | 次の頂点に向けて緊張を高める |
| **余韻** | 頂点の感情を沈殿させる。未解決項目の処理禁止 |
| **転換** | 物語の方向を変える。新情報は一つだけ |
| **蓄積** | 世界観・関係性を積み上げる |

### 3.3 出力契約
| ファイル | 内容 |
|---------|------|
| `story/scenario-arc.md` | 感情命題・三幕構成・感情頂点・書かないこと宣言・役割マップ |
| `story/character-arcs.md` | 変容ステージ・合流ポイント・意図的未解決期間 |
| `story/arc-design-progress.md` | チェックリスト状態（LOCKED で執筆解禁） |

### 3.4 中断復帰
`story/arc-design-progress.md` の状態から再開。LOCKED ならアーク設計完了。

## 4. `/edit-story` 詳細

### 4.1 ステップ
1. 指示解析
2. 対象ファイル読込
3. 波及影響分析
4. 承認取得
5. 変更反映
6. 変更レポート

### 4.2 分岐
- 全承認: 提案どおり更新
- 部分承認: 対象限定で更新
- 却下: 変更なし
- 再提案: 修正後に再承認

## 5. `/write-episode` 詳細（Phase 1）

### 5.1 基本ステップ
| Step | 名称 | 主担当 | 主な出力 |
| --- | --- | --- | --- |
| 0 | 初期化 | オーケストレーター | `progress.md`, `revision-log.md`, `discussion-log.md` |
| 1 | チーム作成 | オーケストレーター | 実行環境、必要時 `series-tracker.md` 復旧 |
| 2 | エピソードブリーフ生成 | オーケストレーター | `episode-brief.md`（アーク設計から導出・執筆アクセント含む） |
| 3 | 作者執筆 | author (Opus) | `current-draft.txt`、`story/author-reflections.md`、`workspace/accent-note.md`（変更時のみ） |
| 4 | アークレビュー | arc-reviewer (Sonnet) | `arc-review.md` |
| 4D | ドラフトディスカッション（条件付き） | author / arc-reviewer | `discussion-log.md` |
| 5 | 読者フィードバック回収 | reader-* | `reader-feedback-*.md` |
| 6 | 判定 | オーケストレーター | PASS 系 / REVISION 判定、`revision-log.md` 追記 |
| 6.5P | ポリッシュ（条件付き） | author | `current-draft.txt` 軽微修正 |
| 7 | 確定・保存・アーク進行更新 | オーケストレーター | `episodes/*.txt` + `story/` 各種更新 |
| 7.5 | 品質ログ記録 | オーケストレーター | `story/quality-log.md` |
| 8 | チームシャットダウン | オーケストレーター | `workspace/` 最終退避 |

### 5.2 条件付きステップの要点
- `step4d`: REVISION_NEEDED 時のみ。arc-reviewer レビューに対する意図確認（判定は不変）
- `step6.5p`: PASS_WITH_POLISH 時のみ、最大3点の軽微修正
- Step 3 ループ: REVISION_NEEDED 時 Step 3 に戻る（`revision_count >= max_revisions` で FORCE_PASS）

### 5.3 Step 2 の執筆アクセント
`series-tracker.md` の直近5話履歴から以下を `episode-brief.md` に追記（**示唆。変更可**）:
- **構成パターン推奨**: 6型（単線・並走・交差・回想・圧縮・余白）から重複回避して推奨
- **感覚レンズ推奨**: 4分類（視覚・聴覚・触覚・嗅覚味覚）から重複回避して推奨

変更した場合は `workspace/accent-note.md` を生成 → Step 7 で `series-tracker.md` の変更メモ列に転記後削除。

### 5.4 Step 7 のアーク進行更新
確定後にオーケストレーターが直接実行:
- `story/character-arcs.md`: 今話でトリガーが発動したキャラの現在ステージを更新
- `story/handover-notes.md`: アーク進行状況テーブル・スレッドタグ再評価
- `story/series-tracker.md`: 全テーブル更新
- 幕の境界であれば `handover-notes.md` に `[DESIGN-REVIEW]` タグを追加しユーザーに `/arc-observe` を通知

## 6. 判定分岐と改稿ループ

```mermaid
flowchart TD
    A["Step 3-5 完了"] --> B["Step 6 判定"]
    B --> C{"revision_count >= max_revisions?"}
    C -->|Yes| FP["FORCE_PASS"]
    C -->|No| D{"arc-reviewer=PASS かつ Reader平均>=3.5?"}
    D -->|No| R["REVISION_NEEDED"]
    D -->|Yes| E{"軽微課題あり?"}
    E -->|Yes| PWP["PASS_WITH_POLISH"]
    E -->|No| PASS["PASS"]

    R --> RD["Step 4D ディスカッション"]
    RD --> LOOP["Step 3 へ戻る"]
    PWP --> POL["Step 6.5P 軽微修正"]
    POL --> FIN["Step 7 へ"]
    PASS --> FIN
    FP --> FIN
```

## 7. `/arc-observe` 詳細（Phase 2）

### 7.1 起動条件
Step 7 確定後、`progress.md` の `arc_phase_boundary = true` の場合、オーケストレーターがユーザーに通知し手動起動を促す。

### 7.2 ステップ
| Step | 内容 |
|------|------|
| 1 | `episodes/` 内の全 `.txt` を話数順に通読 |
| 2 | `story/author-reflections.md` を通読（存在する場合） |
| 3 | `story/scenario-arc.md`・`story/character-arcs.md` と照合 → `workspace/arc-observation-report.md` 生成 |
| 4 | 細部修正を自律実施。大筋修正は設計者に問い（A.承認/B.却下/C.修正）で確認後実施 |
| 5 | 承認された変更を `story/` に反映 → `archive/arc-observe-vol{N}-act{N}/` にレポート保存 |

### 7.3 提案権限
| 区分 | 内容 |
|-----|------|
| **細部**（設計者確認不要） | 合流ポイントの話数 ±2 話以内移動 / 「書かないことの宣言」への項目追加 / handover-notes スレッドタグ再評価 |
| **大筋**（設計者確認が必要） | 感情頂点の話数移動 / 三幕構成幕境界変更 / キャラクターアーク変容ステージ追加・削除 / 感情命題修正 / 「書かないことの宣言」からの項目削除 |

## 8. レジューム（再開）状態遷移

```mermaid
stateDiagram-v2
    [*] --> CheckProgress
    CheckProgress --> FreshStart: progressなし
    CheckProgress --> ResumeSameEpisode: episode一致
    CheckProgress --> AskConfirm: episode不一致
    CheckProgress --> FallbackFresh: progress破損

    AskConfirm --> FreshStart: 続行
    AskConfirm --> Abort: 中断
    ResumeSameEpisode --> Step1TeamRecreate: Step1は必ず再実行
    Step1TeamRecreate --> ResumeAtCurrent: current_step/step_statusで再開
    ResumeAtCurrent --> [*]
    FreshStart --> [*]
    FallbackFresh --> [*]
    Abort --> [*]
```

## 9. Step 別のファイル生成タイムライン

| フェーズ | 追加/更新される主ファイル |
| --- | --- |
| `/setup-world` 完了時 | `story/*.md` 一式（設定ファイル + テンプレート） |
| `/setup-arc` 完了時 | `story/scenario-arc.md`, `story/character-arcs.md`, `story/arc-design-progress.md` |
| Step 0 | `workspace/progress.md`, `workspace/revision-log.md`, `workspace/discussion-log.md` |
| Step 2 | `workspace/episode-brief.md` |
| Step 3 | `workspace/current-draft.txt`, `story/author-reflections.md`, `workspace/accent-note.md`（変更時のみ） |
| Step 4 | `workspace/arc-review.md` |
| Step 5 | `workspace/reader-feedback-*.md` |
| Step 7 | `episodes/{番号:2桁}_{タイトル}.txt`, `story/episode-summaries.md`, `story/character-arcs.md`, `story/handover-notes.md`, `story/series-tracker.md` |
| Step 7.5 | `story/quality-log.md` |
| Step 8 終盤 | `archive/episode-{番号:2桁}/` へ `workspace/` 退避後クリーン |
| `/arc-observe` Step 5 | `story/scenario-arc.md`（変更時）, `story/character-arcs.md`（変更時）, `story/handover-notes.md`, `archive/arc-observe-vol{N}-act{N}/` |

## 10. 重要な運用ルール

- `arc-review.md` の検証完了前に Step 4D を開始しない（書面先行ルール）。
- arc-reviewer は `arc-review.md` に記載した判定を議論で変更しない（判定不変の原則）。
- Step 5 は読者ごとの個別検証・個別リトライを行う。
- Step 8 の `workspace` 退避/クリーンは Step 7.5 完了後、`progress.md` の Step 8 完了更新後に実行する。
- `series-tracker.md` 欠落または必須見出し不足時は再生成して継続する。
- `story/scenario-arc.md` と `story/character-arcs.md` がなければ `/write-episode` は開始しない。
