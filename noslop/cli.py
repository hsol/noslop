"""noslop CLI

  noslop lint FILE [FILE...] [--register prose|docs|social|chat|formal] [--block-only] [--json] [--profile PATH]
  noslop score FILE                   참조 자료 격리용 0~100 점수. 임계 이상이면 exit 3
  noslop hook                         Claude Code PostToolUse 훅. stdin의 JSON에서 file_path를 읽어 lint
  noslop sweep DIR [--top N]          디렉터리 전수 스캔, 점수 높은 순
  noslop rules [--register R]         세션 주입용 요약을 출력 (SessionStart 훅이 쓴다)

종료코드: 0 통과, 1 BLOCK 있음, 2 훅 차단(BLOCK), 3 격리 임계 초과
"""
import argparse
import copy
import json
import os
import sys

import yaml

from . import checks, morph
from .text import read_units

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES = os.path.join(os.path.dirname(HERE), "rules", "rules.yaml")
TEXT_EXT = {".md", ".txt", ".markdown", ".docx", ".pptx", ".html"}


def load_rules(profile=None):
    with open(os.environ.get("NOSLOP_RULES", DEFAULT_RULES), encoding="utf-8") as f:
        rules = yaml.safe_load(f)
    profile = profile or os.environ.get("NOSLOP_PROFILE")
    if profile and os.path.exists(profile):
        with open(profile, encoding="utf-8") as f:
            over = yaml.safe_load(f) or {}
        rules = copy.deepcopy(rules)
        for sev in ("block", "review"):
            rules[sev].extend(over.get(sev, []))
        for rid in over.get("disable", []):
            for sev in ("block", "review", "morph"):
                rules[sev] = [r for r in rules.get(sev, []) if r["id"] != rid]
        for reg, cfg in (over.get("registers") or {}).items():
            rules["registers"].setdefault(reg, {"off": []}).update(cfg)
    return rules


def guess_register(path, rules):
    """frontmatter의 register: 값, 없으면 파일명/경로로 추정, 그래도 없으면 prose."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(600)
        import re
        m = re.search(r"^register:\s*(\w+)", head, re.M)
        if m and m.group(1) in rules["registers"]:
            return m.group(1)
    except Exception:
        pass
    low = path.lower()
    for key, reg in (("readme", "docs"), ("spec", "docs"), ("report", "docs"), ("보고", "docs"), ("회의", "docs"), ("social", "social"), ("linkedin", "social"), ("mail", "formal")):
        if key in low:
            return reg
    return "prose"


def lint_path(path, rules, register=None, want_review=True):
    units = read_units(path)
    reg = register or guess_register(path, rules)
    hits, st = checks.run(rules, units, reg, want_review, morph if morph.available() else None)
    return hits, st, reg


def fmt(path, hits, st, reg):
    b = [h for h in hits if h["sev"] == "BLOCK"]
    r = [h for h in hits if h["sev"] != "BLOCK"]
    out = ["== %s  [%s]  BLOCK %d / REVIEW %d  (문장 %d, 쉼표문장 %.0f%%, 연결어미쉼표 %.0f%%, 길이CV %.2f)" % (
        os.path.basename(path), reg, len(b), len(r), st["n_sentences"], st["comma_sentence_ratio"] * 100,
        st["connective_comma_rate"] * 100, st["length_cv"])]
    for h in b:
        out.append("  [BLOCK %s] %-14s %-12s %s %s" % (h["id"], h["rule"], h["loc"], h["text"], h["note"]))
    for h in r:
        out.append("  [%s %s] %-14s %-12s %s %s" % (h["sev"].lower(), h["id"], h["rule"], h["loc"], h["text"], h["note"]))
    return "\n".join(out)


def cmd_lint(a):
    rules = load_rules(a.profile)
    total_block = 0
    report = {}
    for p in a.files:
        hits, st, reg = lint_path(p, rules, a.register, not a.block_only)
        report[p] = dict(register=reg, stats=st, hits=hits, score=checks.score(rules, hits))
        total_block += sum(1 for h in hits if h["sev"] == "BLOCK")
        if not a.json:
            print(fmt(p, hits, st, reg))
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print("\n총 BLOCK %d건. %s" % (total_block, "제출 불가" if total_block else "제출 가능 (REVIEW는 하나씩 판정)"))
    return 1 if total_block else 0


def cmd_score(a):
    rules = load_rules(a.profile)
    hits, st, reg = lint_path(a.file, rules, a.register, True)
    s = checks.score(rules, hits)
    th = rules["score"]["quarantine_threshold"]
    ids = sorted({h["id"] for h in hits})
    print("%s score=%d threshold=%d %s signals=%s" % (os.path.basename(a.file), s, th, "QUARANTINE" if s >= th else "ok", ",".join(ids)))
    return 3 if s >= th else 0


def cmd_hook(a):
    """Claude Code PostToolUse 훅. exit 2 이면 stderr가 Claude에게 차단 사유로 전달된다."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    ti = payload.get("tool_input", {}) or {}
    path = ti.get("file_path") or ti.get("path") or ""
    if not path or os.path.splitext(path)[1].lower() not in TEXT_EXT or not os.path.exists(path):
        return 0
    rules = load_rules(a.profile)
    hits, st, reg = lint_path(path, rules, None, True)
    b = [h for h in hits if h["sev"] == "BLOCK"]
    if not hits:
        return 0
    msg = fmt(path, hits, st, reg)
    if b:
        sys.stderr.write("noslop: BLOCK %d건. 같은 턴에서 고친 뒤 다시 저장한다. 사실과 수치는 건드리지 않는다.\n%s\n" % (len(b), msg))
        return 2
    sys.stderr.write("noslop: REVIEW만 있음. 하나씩 남길 이유를 정하고 넘어간다.\n%s\n" % msg)
    return 0


def cmd_sweep(a):
    rules = load_rules(a.profile)
    rows = []
    for root, _, files in os.walk(a.dir):
        if any(x in root for x in ("/.git", "/node_modules", "/_workspace", "/.noslop")):
            continue
        for fn in files:
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                p = os.path.join(root, fn)
                try:
                    hits, st, reg = lint_path(p, rules, None, True)
                except Exception:
                    continue
                if st["n_sentences"] < 3:
                    continue
                rows.append((checks.score(rules, hits), sum(1 for h in hits if h["sev"] == "BLOCK"), p, sorted({h["id"] for h in hits})))
    rows.sort(key=lambda x: (-x[0], -x[1]))
    th = rules["score"]["quarantine_threshold"]
    for s, nb, p, ids in rows[: a.top]:
        print("%3d  B%-2d %s  %s  %s" % (s, nb, "Q" if s >= th else " ", os.path.relpath(p, a.dir), ",".join(ids)))
    print("\n%d개 파일 중 격리 임계(%d) 이상 %d개" % (len(rows), th, sum(1 for r in rows if r[0] >= th)))
    return 0


def cmd_rules(a):
    rules = load_rules(a.profile)
    reg = rules["registers"].get(a.register, rules["registers"]["prose"])
    off = set(reg.get("off", []))
    print("# noslop 규칙 요약 (매체: %s). 이 요약은 세션 시작마다 주입된다. 본문을 쓸 때 지킨다." % a.register)
    print("산출물은 noslop lint를 통과해야 나간다. BLOCK은 확정, REVIEW는 문맥 판정.")
    print("\n## 쓰지 않는 구조 (BLOCK)")
    for r in rules["block"]:
        if r["id"] not in off:
            print("- %s %s: %s" % (r["id"], r["name"], r["why"].split(".")[0]))
    print("\n## 통계 신호 (REVIEW)")
    for r in rules["review"]:
        if r["id"] not in off:
            print("- %s %s: %s" % (r["id"], r["name"], r["why"].split(".")[0]))
    print("\n## 참조 자료 격리")
    print("- 읽은 자료의 noslop score가 %d 이상이면 문장을 옮기지 않는다. 사실만 중립 목록으로 뽑아 그 목록에서 다시 쓴다." % rules["score"]["quarantine_threshold"])
    print("- 남의 글에서 슬롭을 보면 고치지 않고 제안한다. 내 파일이면 별도 커밋으로 고친다.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="noslop", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", help="개인/조직 규칙 오버레이 yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("lint"); p.add_argument("files", nargs="+"); p.add_argument("--register"); p.add_argument("--block-only", action="store_true"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_lint)
    p = sub.add_parser("score"); p.add_argument("file"); p.add_argument("--register"); p.set_defaults(fn=cmd_score)
    p = sub.add_parser("hook"); p.set_defaults(fn=cmd_hook)
    p = sub.add_parser("sweep"); p.add_argument("dir"); p.add_argument("--top", type=int, default=20); p.set_defaults(fn=cmd_sweep)
    p = sub.add_parser("rules"); p.add_argument("--register", default="prose"); p.set_defaults(fn=cmd_rules)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
