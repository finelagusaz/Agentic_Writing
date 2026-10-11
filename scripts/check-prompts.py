#!/usr/bin/env python3
"""実行層（skills / agents / CLAUDE.md）のファイル間契約を検査する。

実行層は「生成する側」と「読む側」が別ファイルに分かれている。
片方だけを書き換えると参照先が空になり、エラーも出ずに機能が止まる
（例: arc-review に無い「気になった点」を判定ロジックが数え続けていた）。
このスクリプトはその種の不整合を機械的に検出する。

使い方:
  python3 scripts/check-prompts.py          手動実行（問題があれば終了コード 1）
  python3 scripts/check-prompts.py --hook   Claude Code の PostToolUse hook 用。
      stdin の tool_input.file_path が実行層のときだけ検査し、問題があれば
      stderr に出して終了コード 2（編集した Claude にそのまま差し戻される）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 検査対象（実行層）。archive/ や story/ は対象外。
EXEC_LAYER = [
    *sorted((ROOT / ".claude/skills").rglob("*.md")),
    *sorted((ROOT / ".claude/agents").glob("*.md")),
    *sorted((ROOT / "agents").rglob("*.md")),
    ROOT / "CLAUDE.md",
]

SKILL = ROOT / ".claude/skills/write-episode/SKILL.md"
ARC_REVIEWER = ROOT / "agents/arc-reviewer.md"
WG_SPEC = ROOT / ".claude/skills/setup-world/references/writing-guide-spec.md"
TRACKER_TEMPLATE = ROOT / ".claude/skills/setup-arc/references/series-tracker-template.md"

# 退役した語。見つかったら置き換え先を案内する。
RETIRED_TERMS: list[tuple[str, str]] = [
    (r"(?<!current-)(?<!/)\bdraft\.txt", "workspace/current-draft.txt"),
    (r"担当者", "退役した manager の呼称。arc-reviewer / オーケストレーター等の現役名へ"),
    (r"編集エージェント|novel-editor|novel-manager", "editor/manager は退役済み（archive/legacy-agents/）"),
    (r"novel-reader-(ym|af|vet)", "novel-reader に統合済み"),
    (r"コアメンバースポーン", "コアメンバーは Step 3・4 で遅延スポーン"),
]

problems: list[str] = []


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def report(path: Path, lineno: int, msg: str) -> None:
    problems.append(f"{rel(path)}:{lineno}: {msg}")


def lines_of(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def headings(path: Path) -> list[str]:
    return [re.sub(r"^#+\s*", "", l).strip() for l in lines_of(path) if re.match(r"^\s*#{2,4}\s", l)]


def strip_note(s: str) -> str:
    """「蓄積（示唆）」→「蓄積」のように括弧書きを落とす。"""
    return re.sub(r"[（(].*?[）)]", "", s).strip()


def defined_in(ref: str, path: Path) -> bool:
    """ref が path の見出し、または「- ref:」形式のキーとして定義されているか。"""
    key = strip_note(ref.split(":")[0].split("：")[0])
    if any(strip_note(h).startswith(key) for h in headings(path)):
        return True
    # 箇条書き（- X: / - **X**）と番号付き項目（10. **X**）も定義とみなす
    item = re.compile(rf"^\s*(?:[-*]|\d+(?:\.\d+)?\.)\s*\**{re.escape(key)}")
    return any(item.match(l) for l in lines_of(path))


# --- 1. 退役語 ---------------------------------------------------------------
def check_retired_terms() -> None:
    for path in EXEC_LAYER:
        for i, line in enumerate(lines_of(path), 1):
            if "legacy-agents" in line:  # 退役そのものを説明する行は許容
                continue
            for pat, hint in RETIRED_TERMS:
                if re.search(pat, line):
                    report(path, i, f"退役語 /{pat}/ → {hint}")


# --- 2. セクション参照の生成元があるか ---------------------------------------
# 「<ファイル> の「<セクション>」」という参照を拾い、生成元に定義があるか見る。
REF_PRODUCERS = {
    "arc-review": [ARC_REVIEWER],
    "episode-brief": [SKILL],
    "series-tracker": [TRACKER_TEMPLATE],
    "writing-guide": [WG_SPEC],
}


def check_section_refs() -> None:
    pat = re.compile(r"(arc-review|episode-brief|series-tracker|writing-guide)(?:\.md)?`?\s?(?:の|に)「([^」]+)」")
    for path in EXEC_LAYER:
        for i, line in enumerate(lines_of(path), 1):
            for m in pat.finditer(line):
                target, ref = m.group(1), m.group(2)
                producers = REF_PRODUCERS[target]
                if path in producers:
                    continue
                if not any(defined_in(ref, p) for p in producers):
                    names = ", ".join(rel(p) for p in producers)
                    report(path, i, f"{target} の「{ref}」が生成元（{names}）に定義されていない")
            # writing-guide の §番号参照（SPEC.md など他文書の § は対象外）
            if "writing-guide" not in line:
                continue
            for m in re.finditer(r"§(\d+(?:\.\d+)?)", line):
                num = m.group(1)
                if not any(re.match(rf"^{re.escape(num)}\.\s", l) for l in lines_of(WG_SPEC)):
                    report(path, i, f"§{num} が {rel(WG_SPEC)} の必須セクションに無い")


# --- 3. series-tracker の必須見出しとテンプレートの一致 ------------------------
def check_tracker_headings() -> None:
    text = SKILL.read_text(encoding="utf-8")
    step1 = text.split("### Step 1", 1)[1].split("### Step 2", 1)[0]
    required = re.findall(r"^\s*- `(#{2,3} [^`]+)`", step1, flags=re.M)
    if not required:
        report(SKILL, 1, "Step 1 から series-tracker の必須見出しリストを読み取れない")
        return
    template_lines = {l.strip() for l in lines_of(TRACKER_TEMPLATE)}
    for h in required:
        if h not in template_lines:
            report(TRACKER_TEMPLATE, 1, f"Step 1 の必須見出し `{h}` がテンプレートに無い")
    # テンプレートの複製が他に無いこと（正本は1つ）
    marker = "## アクション配分（直近3話）"
    for path in EXEC_LAYER:
        if path != TRACKER_TEMPLATE and path != SKILL and marker in path.read_text(encoding="utf-8"):
            report(path, 1, f"series-tracker テンプレートの複製。正本 {rel(TRACKER_TEMPLATE)} を参照すること")


# --- 4. 実行層が名指しするファイルが存在するか -------------------------------
def check_paths() -> None:
    pat = re.compile(r"`((?:\.claude|agents)/[^`\s{}*]+\.md)`")
    for path in EXEC_LAYER:
        for i, line in enumerate(lines_of(path), 1):
            for m in pat.finditer(line):
                if not (ROOT / m.group(1)).exists():
                    report(path, i, f"存在しないファイル `{m.group(1)}`")


# --- 5. 作品固有の固有名詞が汎用フレームワークに漏れていないか ---------------
def character_names() -> list[str]:
    """story/characters.md の「### 九条 蓮（くじょう れん）/ レン」形式の見出しから名前を取る。"""
    src = ROOT / "story/characters.md"
    if not src.exists():
        return []
    # 「## メインキャラクター」等の「キャラクター」を含む ## 節の直下にある ### 見出しだけを人物とみなす
    names: list[str] = []
    in_cast = False
    for line in lines_of(src):
        if line.startswith("## "):
            in_cast = "キャラクター" in line
        elif in_cast and line.startswith("### "):
            base = strip_note(line[4:])
            names += [part for part in re.split(r"[/／\s]+", base) if part]
    return names


def is_framework_leak(name: str, line: str, path: Path) -> bool:
    # TODO(設計者): 作品固有名の「漏れ」とみなす範囲を決める。
    #   いまは実行層に名前が現れたら一律で漏れとする（最も厳しい既定）。
    #   例示（「模範例: …」行）や CLAUDE.md の Gotchas を許容するかはここで判断する。
    # カタカナ名は前後がカタカナでないときだけ一致させる（レン ≠ レンズ・リファレンス）
    kana = "ァ-ヴー"
    return re.search(rf"(?<![{kana}]){re.escape(name)}(?![{kana}])", line) is not None


def check_work_specific_names() -> None:
    names = character_names()
    for path in EXEC_LAYER:
        for i, line in enumerate(lines_of(path), 1):
            for name in names:
                if is_framework_leak(name, line, path):
                    report(path, i, f"作品固有の名前「{name}」（汎用の実行層では「主人公」等に置き換える）")


def touches_exec_layer(file_path: str) -> bool:
    try:
        p = Path(file_path).resolve().relative_to(ROOT)
    except ValueError:
        return False
    s = p.as_posix()
    return s == "CLAUDE.md" or s.startswith((".claude/skills/", ".claude/agents/", "agents/"))


def main() -> int:
    hook = "--hook" in sys.argv
    if hook:
        try:
            payload = json.load(sys.stdin)
        except ValueError:
            return 0
        tool_input = payload.get("tool_input", {})
        if payload.get("tool_name") == "Bash":
            # sed -i や heredoc による実行層の書き換えも拾う（読むだけのコマンドは対象外）
            cmd = tool_input.get("command", "")
            names_exec = re.search(r"\.claude/(skills|agents)/|(^|[\s/'\"])agents/|CLAUDE\.md", cmd)
            writes = re.search(r"sed -i|>|\btee\b|\bmv\b|\bcp\b|\brm\b|\bpython3?\b|git (apply|checkout|restore|am|mv|rm)", cmd)
            if not (names_exec and writes):
                return 0
        elif not touches_exec_layer(tool_input.get("file_path", "")):
            return 0
    check_retired_terms()
    check_section_refs()
    check_tracker_headings()
    check_paths()
    check_work_specific_names()
    out = sys.stderr if hook else sys.stdout
    for p in problems:
        print(p, file=out)
    if problems:
        print(f"\n{len(problems)} 件の不整合（scripts/check-prompts.py）。"
              "生成側と参照側の両方を直すこと", file=sys.stderr)
        return 2 if hook else 1
    if hook:
        return 0
    print("実行層のファイル間契約: 問題なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
