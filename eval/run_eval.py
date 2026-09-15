#!/usr/bin/env python3
"""골든 코퍼스(사람이 쓴 글)로 규칙별 오탐률을 잰다.

  python3 eval/run_eval.py [eval/golden] [--register prose]

eval/golden/ 에 본인이 직접 쓴 글(md/txt)을 넣는다. 파일이 많을수록 임계값이 정확해진다.
출력: 규칙 ID 별로 걸린 파일 수와 비율. BLOCK 규칙이 1% 를 넘으면 경고한다.
"""
import collections
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from noslop.cli import load_rules, lint_path  # noqa: E402


def main():
    d = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(os.path.dirname(__file__), "golden")
    reg = None
    if "--register" in sys.argv:
        reg = sys.argv[sys.argv.index("--register") + 1]
    rules = load_rules()
    files = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.lower().endswith((".md", ".txt"))]
    if not files:
        print("골든 코퍼스가 비어 있다. eval/golden/ 에 본인이 쓴 글을 넣는다.")
        return 1
    per_rule = collections.Counter()
    sev = {}
    lines_total = 0
    for p in files:
        hits, st, _ = lint_path(p, rules, reg, True)
        lines_total += st["n_sentences"]
        for rid in {h["id"] for h in hits}:
            per_rule[rid] += 1
        for h in hits:
            sev[h["id"]] = h["sev"]
    n = len(files)
    print("골든 파일 %d개, 문장 %d개\n" % (n, lines_total))
    print("%-6s %-6s %5s  %s" % ("ID", "SEV", "files", "rate"))
    warn = []
    for rid, c in sorted(per_rule.items(), key=lambda x: -x[1]):
        rate = c / n
        print("%-6s %-6s %5d  %.1f%%" % (rid, sev[rid], c, rate * 100))
        if sev[rid] == "BLOCK" and rate > 0.01:
            warn.append(rid)
    if warn:
        print("\n경고: BLOCK 규칙 %s 의 오탐률이 1%% 를 넘는다. rules.yaml 에서 REVIEW 로 내리거나 패턴을 좁힌다." % ", ".join(warn))
    return 0


if __name__ == "__main__":
    sys.exit(main())
