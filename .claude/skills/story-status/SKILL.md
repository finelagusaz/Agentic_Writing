---
name: story-status
description: 作品の執筆進捗・品質傾向・未解決事項を一覧表示するダッシュボード。セッション開始時の状況把握に使う。Use when user says "進捗", "状況", "status", "今どこまで書いた", or at session start.
user-invocable: true
disable-model-invocation: true
---

# /story-status — 作品進捗ダッシュボード

## 概要

作品の現在地を一目で把握するためのダッシュボード。以下の情報を収集して表示する。

## 実行手順

### 1. 基本情報の収集

以下のファイルを Read する:
- `story/premise.md` — タイトル・想定話数
- `story/scenario-arc.md` — 三幕構成・現在の幕
- `story/quality-log.md` — 品質記録
- `story/handover-notes.md` — 未解決事項
- `story/series-tracker.md` — 警告一覧

`episodes/` を Glob して確定済み話数をカウントする。

### 2. ダッシュボード表示

以下の形式で表示する:

```
## 作品ダッシュボード — {タイトル}

### 進捗
- 執筆済み: {N}話 / {想定話数}話（{パーセント}%）
- 現在の幕: {第N幕}「{フェーズ名}」
- 次に書く話: 第{N+1}話（{役割タグ}・{感情強度}）

### 品質傾向（直近5話）
| 話数 | ★平均 | 判定 | 主要指摘 |
（quality-log.md から直近5行を抽出）

- ★平均の推移: {上昇/横ばい/下降}
- 読者間の★差: {最大差と傾向}

### 未解決事項
- MUST-VOL: {N}件
- MUST-THIS: {N}件
- RECURRING: {N}件
- DESIGN-REVIEW: {N}件

### series-tracker 警告
（series-tracker.md の「現在の警告」をそのまま転記）

### 次のアクション
（状況に応じて推奨アクションを表示）
- `/write-episode {N}` で次話を執筆
- `/arc-observe` でアーク観測（幕境界の場合）
- `/edit-story` で設定修正（MUST-VOL が多い場合）
```
