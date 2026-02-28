# progress.md テンプレート

Step 0 で以下の内容で `workspace/progress.md` を作成する。
`{変数}` は実際の値に置換すること。

```
# Progress Tracker — Episode {番号:2桁}

```yaml
episode: {番号}
max_revisions: {上限}
revision_count: 0
planned_episodes: {想定話数 or null}
remaining_episodes: {残り話数 or null}
is_finale: {true/false/null}
arc_phase_boundary: {true/false（幕境界の場合は "true: 第N幕"）}
force_pass: false
current_step: "step0"
step_status: "completed"
```

## Completed Steps

- [x] step0: Initialize
- [ ] step1: Create Team + Spawn Core
- [ ] step2: Episode Brief Generation
- [ ] step2q: Designer Query (optional)
- [ ] step3: Author Draft
- [ ] step4: Arc Review
- [ ] step4d: Draft Discussion
- [ ] step5: Reader Feedback (Collect)
- [ ] step6: Judgment
- [ ] step6.5p: Polish (conditional)
- [ ] step7: Finalize + Arc Progress Update
- [ ] step7.5: Quality Log
- [ ] step8: Team Shutdown

## Step 5 Detail

（story/reader-personas.md に定義された各ペルソナIDを動的に列挙する。以下は例）
- [ ] {ペルソナ1のID}
- [ ] {ペルソナ2のID}
- [ ] {ペルソナ3のID}
...（ペルソナ数に応じて列挙。reader-personas.md の実際のIDを使用すること）

## Revision History

（なし）
```
