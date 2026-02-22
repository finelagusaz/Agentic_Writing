# Agentic Writing 仕様書（SPEC）

## 1. 主目的

### 1.1 主目的
`/setup-story`・`/edit-story`・`/write-episode` の3コマンドを通じて、Web小説制作の初期設定、継続的な設定更新、エピソード執筆と品質管理を再現可能な手順として提供する。

### 1.2 成功条件
- 作品資料（`story/`）が整合性を維持して生成・更新される。
- エピソード本文（`episodes/`）がレビューと読者評価を経て確定される。
- 執筆中断時に `workspace/progress.md` から再開できる。
- 品質記録（`story/quality-log.md`）と運用履歴（`archive/`）が残る。

## 2. 概要

### 2.1 システム概要
Agentic Writing は、複数エージェントの役割分担により小説執筆を進行するオーケストレーション仕様である。

- `editor`（編集）: 方針策定、フィードバック統合、申し送り管理
- `author`（作者）: 本文執筆・改稿
- `manager`（担当者）: 品質レビュー・判定
- `reader-*`（読者）: ペルソナ別感想・評価

### 2.2 ドキュメント責務
- `SPEC.md`: 目的、契約、成果物、判定基準などの正規仕様
- `docs/workflows.md`: 手順詳細、分岐、レジューム、Mermaid 詳細図

## 3. スコープ

### 3.1 対象
- `/setup-story`: 7ステップ対話で `story/` の初期資料を生成
- `/edit-story <自然言語指示>`: 既存資料の更新と波及影響管理
- `/write-episode <話数> [--max-revisions=N]`: 執筆、評価、改稿ループ、確定保存

### 3.2 スコープ外
- モデル課金や実行基盤運用
- 外部公開プラットフォーム連携
- UI 実装

## 4. 公開インターフェース

### 4.1 コマンド I/F
| コマンド | 入力 | 出力 |
| --- | --- | --- |
| `/setup-story` | 対話回答（ジャンル・設定・文体等） | `story/*.md`（初期資料） |
| `/edit-story` | 自然言語変更指示 | 対象 `story/*.md` の更新 |
| `/write-episode` | 話数、任意で `--max-revisions` | `episodes/*.txt` + `story/` 更新 + `archive/` 保存 |

### 4.2 判定 I/F
- manager 判定（`workspace/manager-review.md`）  
  `OK | REVISION_NEEDED | MAJOR_REVISION`
- リーダー最終判定（Step 6）  
  `PASS | PASS_WITH_POLISH | REVISION_NEEDED | FORCE_PASS`

### 4.3 進捗 I/F
`workspace/progress.md` を実行状態の唯一の復帰点として扱う。最低限次を保持する。
- `episode`
- `max_revisions`
- `revision_count`
- `current_step`
- `step_status`

## 5. 全体の処理の流れ

### 5.1 初期構築フロー（`/setup-story`）
1. カテゴリ・ジャンル選択
2. テーマ・コンセプト確定
3. 世界観設定
4. キャラクター定義
5. プロット骨格定義
6. 文体ガイド・AI癖制御定義
7. 読者ペルソナ定義
8. `story/` への一括出力

### 5.2 編集フロー（`/edit-story`）
1. 指示解析（対象・変更内容・規模）
2. 対象/関連ファイル読込
3. 波及影響分析
4. ユーザー承認
5. 変更反映
6. 変更レポート

### 5.3 執筆フロー（`/write-episode`）
1. 再開判定（`progress.md`）
2. Step 0-8 の順次実行
3. 条件付き分岐
   - `step2d`: 方針ディスカッション
   - `step4d`: レビュー後ディスカッション
   - `step6.5p`: PASS_WITH_POLISH 時の軽微修正
   - `step6.5d`: REVISION_NEEDED 時の改稿方針統合
   - `step7.5`: 申し送り更新
   - `step7.6`: プロット更新ディスカッション
4. ループ
   - REVISION_NEEDED 時は Step 3 に戻る
   - `revision_count >= max_revisions` で `FORCE_PASS`

### 5.4 再開・復旧フロー
- 同一話数の `progress.md` があれば再開
- 異なる話数の `progress.md` があれば確認のうえ新規開始
- `progress.md` 破損時は警告して新規開始へフォールバック
- `story/series-tracker.md` 欠落/破損時はテンプレート再生成して継続

## 6. 途中生成物

### 6.1 実行中生成物（`workspace/`）
| ファイル | 生成/更新タイミング | 役割 |
| --- | --- | --- |
| `workspace/current-direction.md` | Step 2（必要時に再更新） | 編集方針 |
| `workspace/current-draft.txt` | Step 3（改稿ごとに更新） | 執筆本文 |
| `workspace/manager-review.md` | Step 4 | 担当者レビュー |
| `workspace/reader-feedback-*.md` | Step 3後バックグラウンド生成、Step 5回収 | 読者FB |
| `workspace/consolidated-feedback.md` | Step 6.5D | 統合改稿指示 |
| `workspace/revision-log.md` | Step 0 初期化、Step 6追記 | 改稿履歴 |
| `workspace/discussion-log.md` | Step 0 初期化、各ディスカッション追記 | 議論記録 |
| `workspace/progress.md` | Step 0 作成、全ステップで更新 | 再開制御 |

### 6.2 初期資料生成物（`/setup-story`）
| ファイル | 役割 |
| --- | --- |
| `story/premise.md` | コンセプト・テーマ・想定話数 |
| `story/setting.md` | 世界観 |
| `story/characters.md` | 登場人物・口調 |
| `story/plot-outline.md` | プロット骨格 |
| `story/writing-guide.md` | 文体・AI癖制御 |
| `story/reader-personas.md` | 読者ペルソナ |
| `story/episode-summaries.md` | 要約テンプレート |
| `story/handover-notes.md` | 申し送りテンプレート |
| `story/quality-log.md` | 品質ログテンプレート |
| `story/series-tracker.md` | 横断追跡テンプレート |

## 7. 最終生成物

| ファイル | 出力タイミング | 役割 |
| --- | --- | --- |
| `episodes/{番号:2桁}_{タイトル}.txt` | Step 7 | 確定本文 |
| `story/episode-summaries.md` | Step 7 | 直近話/アーク要約更新 |
| `story/handover-notes.md` | Step 7.5 | 次話向け申し送り |
| `story/plot-outline.md` | Step 7.6（必要時） | 近未来プロット微修正 |
| `story/quality-log.md` | Step 7.6 | 品質記録 |
| `story/series-tracker.md` | Step 7 | 横断指標更新 |
| `archive/episode-{番号:2桁}/` | Step 8 終盤 | 監査・再検証用保存（`workspace/` 退避） |

## 8. 品質判定仕様

### 8.1 判定ロジック（Step 6）
1. manager 判定と reader 評価（平均・中央値）を集計
2. `revision_count >= max_revisions` は `FORCE_PASS`
3. manager が `OK` かつ reader 平均が閾値以上で `PASS` もしくは `PASS_WITH_POLISH`
4. manager が `REVISION_NEEDED` / `MAJOR_REVISION` の場合は `REVISION_NEEDED`

### 8.2 書面先行・判定不変
- `manager-review.md` 検証完了後にのみ Step 4D を開始する
- ディスカッションは判定変更を目的にしない

### 8.3 軽微修正（PASS_WITH_POLISH）
- 修正対象は最大3件
- 全体構成は変更しない
- manager 再レビュー・reader 再評価は行わない

## 9. 失敗時挙動・復旧

### 9.1 エージェント出力検証失敗
- 期待ファイル不存在または内容不足は同一エージェントへ再指示
- リトライ上限2回
- 上限到達時はワークフロー中断

### 9.2 データ欠落/破損
- `series-tracker.md` 欠落/必須見出し不足は自動再生成
- `progress.md` 不正は新規開始にフォールバック

### 9.3 途中中断
- `progress.md` の `current_step` と `step_status` を基準に再開先を決定
- ディスカッションステップは非永続のため再実行する

## 10. 制約・運用原則

- `workspace/` は実行中の一時領域、確定後は `archive/` へ退避する
- `story/` は中長期の正本資料として扱う
- `episodes/` は公開対象の確定本文のみを置く
- 読者ペルソナ数は `story/reader-personas.md` 定義に従い可変

## 11. ワークフロー（Mermaid）

```mermaid
flowchart TD
    A["/setup-story<br/>初期資料を作成"] --> B["/edit-story（任意）<br/>設定を更新"]
    B --> C["/write-episode N 開始"]
    C --> D["Step 0-2<br/>初期化/方針策定"]
    D --> E["Step 3-5<br/>執筆/レビュー/読者回収"]
    E --> F{"Step 6 判定"}
    F -->|PASS| G["Step 7-8<br/>確定・保存・終了"]
    F -->|PASS_WITH_POLISH| P["Step 6.5P<br/>軽微修正"]
    P --> G
    F -->|REVISION_NEEDED| R["Step 6.5D<br/>統合フィードバック"]
    R --> E
    F -->|FORCE_PASS| G
```

詳細手順・分岐図・レジューム状態遷移は `docs/workflows.md` を参照する。
