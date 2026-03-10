# 対応計画：design.md レビュー指摘への修正

*2026-02-28*

---

## TODO リスト（グループ A：design.md への反映）

*完了したらチェックを入れる。作業順序は番号順。*

- [x] A-1　I-7：Step 4 節に役割タグ別評価重点リスト（5種）を追加
- [x] A-2　I-5：author-reflections.md 節に上書き方針の理由を追加
- [x] A-3　I-4：表現の多様性管理節に series-tracker テーブル形式サンプルと初回処理注記を追加
- [x] A-4　I-1：`workspace/accent-note.md` 新設節・Step 3 への出力指示・Step 7 への消費指示・シーケンス図の更新
- [x] A-5　I-2：Phase 1 Step 0 に前提確認チェックリストとフォールバック動作を追加
- [x] A-6　I-3：Phase 1 Step 0 に handover-notes 形式チェックと自動変換手順を追加・handover-notes 節に移行注記を追加
- [x] A-7　I-6：Phase 2 節に arc-observer 権限範囲リストを追加
- [x] A-8　I-8：決定事項節に「Phase 1 完了後の課題」（series-tracker 堅牢性）を追記
- [x] A-9　I-9：arc-design-progress.md 節に `archive/phase0/` 自動作成の注記を追加

---

## 前提：設計確定を Phase 1 実装の条件とする

Phase 1 実装を開始する前に、下記の設計補完を design.md に反映させる。
実装者（次セッション以降の Claude）が design.md のみを読んで迷いなく実装できる状態を作ることが、この計画の目的。

---

## 依存関係マップ

```
I-4（series-tracker フォーマット）
  └── I-1（変更メモの情報フロー）← I-4 が確定してから I-1 を詰められる

I-2（writing-guide 相性表）     ← Phase 1 Step 4a の前提
I-3（handover-notes 形式）      ← Phase 1 Step 2 の前提
I-7（「転換」評価基準）          ← arc-reviewer 実装の前提（Phase 1）

以下は Phase 1 実装をブロックしない：
  I-5（author-reflections 上書き意図）← 設計書への注記のみ
  I-6（Phase 2 権限範囲）       ← Phase 2 実装時の前提
  I-8（series-tracker 堅牢性）  ← Phase 1 完了後に検討
  I-9（archive/phase0/ 作成）   ← /setup-arc の小修正で即対応可
```

---

## I-1：変更メモの情報フロー（重大）

### 問題
`作者が示唆から変更した場合、変更理由は Step 7 で series-tracker の変更メモに記録する（オーケストレーターが担当）` と書かれているが、Step 7 の時点でオーケストレーターが「変更の有無」と「変更理由」をどこから得るかの経路が設計にない。

ドラフトと episode-brief の示唆を比較して推測する方法では不確実すぎる（感覚レンズは本文から機械的に判別できない）。

### 解決方針：`workspace/accent-note.md` を新設する

**設計追加の概要:**

- 作者が示唆から変更した場合のみ、`workspace/accent-note.md` を生成する
- 変更がない場合はファイルを生成しない（**ファイルの存在/不在 = 変更の有無**）
- Step 7 でオーケストレーターがこのファイルを読み、series-tracker の変更メモ列に記録する

**ファイル形式（design.md に追加するテンプレート）:**

```markdown
## アクセント変更メモ（第N話）
（示唆から変更した項目のみ記載する。変更なし項目は省略）

### 構成パターン（該当する場合のみ）
- 示唆：〇〇型
- 実使用：〇〇型
- 変更理由：（一文）

### 感覚レンズ（該当する場合のみ）
- 示唆：〇〇
- 実使用：〇〇
- 変更理由：（一文）
```

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — Phase 1 Step 3 の作者指示部分 | 「示唆から変更した場合は `workspace/accent-note.md` を生成する」を追加 |
| design.md — Phase 1 Step 7 | 「accent-note.md が存在する場合、その内容を series-tracker の変更メモ列に記録し、ファイルを削除する」を追加 |
| design.md — `workspace/episode-brief.md` テンプレート節 | 補足注記不要（ファイル定義は Step 3 側に置く） |
| design.md — `workspace/accent-note.md` 新設節 | ファイル定義・形式・生成条件を追加 |
| agents/author.md（Phase 1 実装時） | accent-note の生成仕様を作者エージェント定義に追加 |
| シーケンス図（L130-156） | `A-->>O: accent-note.md（変更時のみ）` を追加 |

**注意:** accent-note.md は作者が出力し、オーケストレーターが消費する一方向の情報渡し。arc-reviewer は読まない（評価軸に入れないという既存の設計と整合）。

---

## I-2：writing-guide.md の推奨相性表が未実装（重大）

### 問題
Phase 1 Step 4a で「今話の役割タグとの自然な親和性（writing-guide の推奨相性表）を照合して推奨を決定する」とあるが、推奨相性表が writing-guide.md に存在しない場合、このステップは参照先なしで空振りになる。

### 解決方針：Phase 1 Step 0 の前提確認チェックに追加する

**design.md の Phase 1 Step 0 に以下を追記:**

```
Step 0  初期化
  ...（既存の確認事項）
  - [ ] writing-guide.md に「構成パターン × 役割タグ 推奨相性」セクションが存在するか
        → 存在しない場合：writing-guide.md への相性表追加（design.md 末尾の設計案を使用）を
          設計者に促してから Step 1 に進む
```

**推奨相性表が存在しない場合のフォールバック動作も明記する:**

> 推奨相性表が存在しない場合は、構成パターンの推奨を「直近5話で最も使用頻度の低いパターン」のみで決定する（役割タグとの照合ステップはスキップ）。

これにより、writing-guide.md が未整備でも Phase 1 は動作する。

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — Phase 1 Step 0 | 前提確認チェックリストを追加（上記） |
| design.md — 表現の多様性管理節 | フォールバック動作の記述を追加 |
| writing-guide.md（別途作業） | 相性表セクションを追加（`/edit-story` で実施。Phase 1 実装の事前タスクとして管理） |

---

## I-3：handover-notes.md 形式変更の非互換（重大）

### 問題
Phase 1 Step 2 は新形式の handover-notes.md（`[MUST-THIS]` 等のタグ付きスレッド）を前提にしているが、既存ファイルが旧形式（未解決項目リスト）の場合にトリアージロジックが機能しない。

### 解決方針：Phase 1 Step 0 に形式チェックと移行手順を組み込む

**Phase 1 Step 0 に以下を追記:**

```
Step 0  初期化
  ...
  - [ ] handover-notes.md が新形式（アーク進行記録形式）であるか
        → 旧形式（未解決項目リスト）の場合：
          オーケストレーターが自動変換を試みる。
          変換規則：旧形式の未解決項目を [MUST-VOL] または [MUST-THIS] として分類する。
          分類の判断が難しい項目は [MUST-VOL] として仮置きし、Step 2 の設計者問いで確認する。
```

**また、「変更：story/handover-notes.md」節に移行時の注意を追加:**

> **旧形式からの移行**: Phase 1 の Step 0 で自動変換を行うが、MUST-THIS / MUST-VOL の分類は機械的に行えない部分がある。初回実行時にオーケストレーターが分類案を提示し、設計者の確認を経て確定する。

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — Phase 1 Step 0 | 形式チェックと自動変換の手順を追加 |
| design.md — handover-notes.md 変更節 | 旧形式移行の注意を追加 |
| `/edit-story` スキル（別途） | 手動移行のための `/edit-story` 実行を「Phase 1 前の任意準備作業」として案内 |

---

## I-4：series-tracker の追跡テーブル形式が未定義（中程度）

### 問題
「構成パターン履歴・感覚レンズ履歴には変更メモ列のみ設ける」とあるが、実際のテーブル形式が design.md に存在しない。Phase 1 実装時に実装者が形式をその場で決める。

### 解決方針：「記録形式」段落の直後にテーブル仕様を追加する

**design.md の「記録形式」節に追加するサンプル:**

```markdown
**series-tracker の追加テーブル形式（表現の多様性管理分）:**

### 構成パターン履歴
| 話数 | 推奨パターン | 実使用パターン | 変更メモ |
|------|------------|--------------|---------|
| 1   | 余白型 | 余白型 | |
| 2   | 単線型 | 並走型 | 二つの視点が交互に必要だった |

### 感覚レンズ履歴
| 話数 | 推奨レンズ | 実使用レンズ | 変更メモ |
|------|----------|------------|---------|
| 1   | 触覚 | 視覚 | 冒頭の空間描写が先行した |
| 2   | 嗅覚・味覚 | 嗅覚・味覚 | |
```

**変更メモ列の記入ルール（明文化が必要）:**
- 示唆通りに実行した場合：空欄
- 示唆から変更した場合：`accent-note.md` の記述から転記（一文）
- 初回実行時（series-tracker にまだ履歴がない場合）：推奨は生成せず、episode-brief のアクセント節を省略する

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — 表現の多様性管理節「記録形式」段落 | テーブル形式サンプルと初回処理の注記を追加 |
| story/series-tracker.md（テンプレート） | 上記テーブルのセクションを追加（/setup-world または Phase 1 Step 0 で自動生成） |

---

## I-5：author-reflections の改稿時上書きの意図（中程度）

### 問題
改稿ループ中に `author-reflections.md 更新（上書き）` とあるが、なぜ追記でなく上書きなのかの理由が設計書にない。

### 解決方針：`author-reflections.md` 節に補足を追加する

**design.md の author-reflections.md 節に追加する文:**

> **改稿時の更新方針**: 改稿によって上書きする（追記しない）。理由：author-reflections は「最終稿を書いた時点の印象」を Phase 2 に届けることが目的であり、初稿の印象が有効であるなら最終稿でも同じ驚きを感じているはず。初稿での驚きが最終稿で消えた場合（改稿で解消した場合）、それは驚きではなく問題の解決であり、記録する価値が下がる。上書きにより「書き直すに値した驚き」のみが蓄積される。

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — author-reflections.md 節 | 上書き方針と理由を追加 |
| シーケンス図のコメント（任意） | `（上書き）` に `（改稿時は最終印象に更新）` という注記を追加 |

---

## I-6：Phase 2 アーク微修正の権限範囲（中程度）

### 問題
「大筋の変更は設計者判断が必要、細部はPhase 2で対応できる」という境界が曖昧。arc-observer が実装されたとき、自律提案の範囲を毎回都度判断することになる。

### 解決方針：Phase 2 節に権限範囲の具体的リストを追加する

**design.md の Phase 2 節に追加:**

```
#### arc-observer の提案権限

**設計者の確認なしに提案・実施できる（細部）:**
- 合流ポイント（CP）の話数を ±2 話以内で移動する
- 「書かないことの宣言」に項目を追加する（削除は不可）
- handover-notes のスレッドタグを再評価する

**設計者の確認を経てから実施する（大筋）:**
- 感情頂点の話数の移動
- 三幕構成の幕境界の変更（話数範囲の再定義）
- キャラクターアークの変容ステージの追加・削除
- 感情命題（テーマ）の修正
- 「書かないことの宣言」からの項目削除

判断に迷う場合は設計者確認を優先する。
```

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — Phase 2 節 | 権限範囲リストを追加 |
| agents/arc-observer.md（Phase 2 実装時） | 上記リストを行動制約として反映 |

---

## I-7：「転換」タグの評価基準（中程度）

### 問題
Step 4 の追加評価項目で各役割タグの評価基準が書かれているが、「転換」の評価文が存在しない。

### 解決方針：Step 4 節に転換タグの評価文を追加する

**design.md の Step 4 節（追加評価項目の直後）に追加:**

```
役割タグ別の評価重点：
- **頂点**：一つの主題への集中が保たれているか。感情強度が他話より際立っているか
- **助走**：次話または頂点に向けた緊張・期待の蓄積が機能しているか
- **余韻**：前話の感情が沈殿しているか。感情強度の低さは減点しない
- **蓄積**：キャラクターや関係性の地層が積み重なっているか。単独では地味でも積み上げとして機能しているか
- **転換**：前話までの方向から感情的または状況的な反転が起きているか。
           かつその反転が唐突でなく、これまでの助走・蓄積に根拠を持つか
           （反転の有無と反転の根拠の両方を評価する）
```

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — Step 4 節 | 役割タグ別の評価重点リストを追加 |
| agents/arc-reviewer.md（Phase 1 実装時） | 上記評価基準を評価指針として反映 |

---

## I-8：series-tracker 堅牢性の未追跡（軽微）

### 問題
「Phase 1 実装時に検討する」のまま。チェックリスト項目にもなっておらず、実装が終わっても追跡されない。

### 解決方針：「決定事項」節に「Phase 1 完了後の課題」として明示する

**design.md の決定事項節に追加:**

> 5. **series-tracker の堅牢性**（Phase 1 完了後の検討事項）: `series-tracker.md` 単体への依存は破損リスクを持つ。Phase 1 の最初の数話を実行して series-tracker の運用感を確認した後、`episodes/` 配下へのメタデータスナップショット保存の可否を判断する。

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — 決定事項節 | 項目5として追記 |

---

## I-9：archive/phase0/ ディレクトリの作成要否（軽微）

### 問題
`/setup-arc` の Step G 完了時に `archive/phase0/` にアーカイブするとあるが、ディレクトリが存在しない場合の処理が未定義。

### 解決方針：`/setup-arc` スキルの Step G 実装時に自動作成を明記

**design.md の Phase 0 ドキュメント節（arc-design-progress.md 節）に注記追加:**

> `archive/phase0/` が存在しない場合は自動作成する。

**影響箇所:**

| 箇所 | 変更内容 |
|------|---------|
| design.md — arc-design-progress.md 節 | 自動作成の注記を追加 |
| `.claude/skills/setup-arc/` （実装時） | Step G でのアーカイブ処理に `mkdir -p` 相当の作成を含める |

---

## 実施順序と担当

### グループ A：Phase 1 実装前に design.md に反映する（今すぐ）

以下をすべて design.md に追記・修正する。影響範囲が design.md のみ（または design.md が変更されてから他ファイルに波及するもの）。

| # | 対象 | 変更内容の要点 |
|---|------|--------------|
| 1 | I-7 | Step 4 節に役割タグ別評価重点リストを追加 |
| 2 | I-5 | author-reflections.md 節に上書き方針の理由を追加 |
| 3 | I-4 | 表現の多様性管理節にテーブル形式サンプルと初回処理注記を追加 |
| 4 | I-1 | accent-note.md 新設節・Step 3 への出力指示・Step 7 への消費指示・シーケンス図の更新 |
| 5 | I-2 | Phase 1 Step 0 に前提確認チェックとフォールバック動作を追加 |
| 6 | I-3 | Phase 1 Step 0 に形式チェックと自動変換手順を追加・handover-notes 節に移行注記 |
| 7 | I-6 | Phase 2 節に arc-observer の権限範囲リストを追加 |
| 8 | I-8 | 決定事項節に「Phase 1 完了後の課題」として追記 |
| 9 | I-9 | arc-design-progress.md 節に自動作成の注記を追加 |

### グループ B：Phase 1 実装の直前に実施する（他ファイルへの波及）

| # | 対象ファイル | 作業内容 | 手段 |
|---|------------|---------|------|
| 1 | `story/writing-guide.md` | 構成パターン × 役割タグ 推奨相性表を追加 | `/edit-story` |
| 2 | `story/handover-notes.md` | 旧形式から新形式への移行 | `/edit-story` |
| 3 | `story/series-tracker.md` | 構成パターン履歴・感覚レンズ履歴テーブルを追加 | `/edit-story` |

### グループ C：Phase 1 実装時に組み込む（スキル・エージェント定義）

| # | 対象ファイル | 作業内容 |
|---|------------|---------|
| 1 | `agents/arc-reviewer.md` | 転換タグの評価基準に「反転の根拠」を追加 |
| 2 | `agents/author.md` | accent-note.md 生成仕様を追加 |
| 3 | `write-episode/SKILL.md` | Step 0 前提確認チェック追加 |
| 4 | `write-episode/SKILL.md` | Step 2 に「執筆のアクセント」生成（4a）追加 + episode-brief テンプレート更新 |
| 5 | `write-episode/SKILL.md` | Step 3 に accent-note.md 出力指示追加 |
| 6 | `write-episode/SKILL.md` | Step 1 の series-tracker 検証に新テーブル確認を追加 |
| 7 | `write-episode/finalization-details.md` | series-tracker アクセント追跡テーブル更新 + accent-note.md 消費処理追加 |

**グループ B 補足**: `story/` ファイルはまだ存在しないため直接変更は行わない。グループ C の Step 0 改修で「初回実行時に新形式・アクセント追跡テーブル付きで自動生成」を組み込むことで実質カバーする。`story/writing-guide.md` の相性表追加は、同ファイルが `/setup-world` で生成された後に `/edit-story` で実施する。

### グループ D：今すぐ実施可能な小修正

| # | 対象ファイル | 作業内容 |
|---|------------|---------|
| 1 | `.claude/skills/setup-arc/SKILL.md` | Step G でのアーカイブ時に `archive/phase0/` 自動作成を追加 |

## TODO リスト（グループ C・D：実装フェーズ）

*完了したらチェックを入れる。作業順序は番号順。*

- [x] C-1　`agents/arc-reviewer.md`：転換タグの評価基準に「反転の根拠も評価する」を追加
- [x] C-2　`agents/author.md`：accent-note.md の生成仕様（生成条件・フォーマット）を追加
- [x] C-3　`write-episode/SKILL.md` Step 0：前提確認チェックリスト（writing-guide.md 相性表・handover-notes 形式）を追加
- [x] C-4　`write-episode/SKILL.md` Step 2：4a「執筆のアクセント生成」処理と episode-brief テンプレートの「執筆のアクセント」セクションを追加
- [x] C-5　`write-episode/SKILL.md` Step 3：accent-note.md 出力指示を追加
- [x] C-6　`write-episode/SKILL.md` Step 1：series-tracker 検証に構成パターン履歴・感覚レンズ履歴テーブルの確認を追加
- [x] C-7　`write-episode/finalization-details.md`：series-tracker のアクセント追跡テーブル更新処理と accent-note.md 消費処理を追加
- [x] D-1　`setup-arc/SKILL.md` Step G：`archive/phase0/` 自動作成を追加

---

## 変更後の design.md 構造チェックリスト

Phase 1 実装を開始してよい条件：

- [x] Phase 1 Step 0 に前提確認チェックリストが追加されている（A-5, A-6） ✅ L118-129
- [x] `workspace/accent-note.md` の定義と生成条件が記述されている（A-4） ✅ L375-394
- [x] Step 3 に accent-note 生成指示が追加されている（A-4） ✅ L132
- [x] Step 7 に accent-note 読み取りと series-tracker への転記が追加されている（A-4） ✅ L550
- [x] series-tracker の追跡テーブル形式が定義されている（A-3） ✅ L568-582
- [x] 役割タグ別の評価重点リスト（転換を含む5種）が Step 4 節に存在する（A-1） ✅ L536-542
- [x] Phase 2 の arc-observer 権限範囲リストが存在する（A-7） ✅ L184-197
- [x] author-reflections の上書き方針の理由が記述されている（A-2） ✅ L338
