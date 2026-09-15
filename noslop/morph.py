"""kiwipiepy가 설치돼 있을 때만 켜지는 형태소 기반 규칙. 없으면 available()이 False를 돌려주고 전부 건너뛴다."""
import re
from .checks import Hit

try:
    from kiwipiepy import Kiwi
    _kiwi = Kiwi()
except Exception:  # 설치 안 됨
    _kiwi = None


def available():
    return _kiwi is not None


def run(rules, text):
    if _kiwi is None or not rules:
        return []
    toks = [t for t in _kiwi.tokenize(text) if not t.tag.startswith("S")]  # 기호 제외
    hits = []
    for r in rules:
        if r["stat"] == "verb_ratio" and len(toks) >= r["min_tokens"]:
            verbs = sum(1 for t in toks if t.tag.startswith("V"))
            ratio = verbs / len(toks)
            if ratio < r["threshold"]:
                hits.append(Hit("MORPH", r["id"], r["name"], "문서 전체", "", "용언 %.1f%%" % (ratio * 100)))
        elif r["stat"] == "noun_pile":
            run_len, start = 0, None
            for i, t in enumerate(toks):
                if t.tag.startswith("NN"):
                    if run_len == 0:
                        start = t.start
                    run_len += 1
                else:
                    if run_len >= r["min_run"]:
                        hits.append(Hit("MORPH", r["id"], r["name"], "위치 %d" % start, text[start:toks[i - 1].start + toks[i - 1].len]))
                    run_len = 0
            if run_len >= r["min_run"]:
                hits.append(Hit("MORPH", r["id"], r["name"], "위치 %d" % start, text[start:start + 60]))
    return hits
