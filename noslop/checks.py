"""규칙 실행. rules.yaml의 regex / structural / stat 항목을 텍스트에 적용해 hit 목록을 만든다."""
import re
import statistics
from . import text as T

CONNECTIVE_COMMA = re.compile(r"(?:고|며|지만|면서|어서|아서|는데|은데|니까|으니|이니|면|으면|려면|더니|자마자),")
ENDING = re.compile(r"([가-힣]{2})[.!?]*$")  # 마지막 두 음절을 종결 형태로 본다 (했다/이다/됩니다/어요 를 구분)
KOR_NUM = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9, "열": 10}
NUMTOK = r"(?<![A-Za-z0-9~.])(?:[0-9][0-9,]*|한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)"
ORDER_UNITS = set("부장절차회항호기편")
ANNOUNCE = re.compile(r"(" + NUMTOK + r")\s*([가-힣]{1,2})[가-힣\s]{0,14}?(?:있|들어|따라|된다|이다|입니다|나눠|나뉜|남는)")
TITLE_NUM = re.compile(NUMTOK + r"\s*[가-힣]")
COLON_HEAD = re.compile(r"^.{1,40}[:：]\s*.{1,60}$")


def _val(tok):
    if tok in KOR_NUM:
        return KOR_NUM[tok]
    try:
        return int(tok.replace(",", ""))
    except ValueError:
        return None


class Hit(dict):
    def __init__(self, sev, rid, name, loc, excerpt, note=""):
        super().__init__(sev=sev, id=rid, rule=name, loc=loc, text=excerpt[:120], note=note)


# ---------- 구조 판정 ----------

def announce_then_enumerate(line):
    """개수를 선언하고 곧바로 그만큼 늘어놓는 구조만 잡는다. 순서 표기는 뺀다."""
    for m in ANNOUNCE.finditer(line):
        unit = m.group(2)
        if unit[0] in ORDER_UNITS:
            continue
        num = _val(m.group(1))
        if num is None or not 2 <= num <= 9:
            continue
        tail = line[m.end():m.end() + 160]
        if len(re.findall(r"[,·/]|\s및\s|\s그리고\s", tail)) >= num - 1:
            return True
    return False


def title_number(heading):
    for m in TITLE_NUM.finditer(heading):
        before = heading[:m.start()]
        if re.search(r"[(（]\s*$", before):
            continue
        unit = heading[m.end() - 1]
        if unit in ORDER_UNITS:
            continue
        return True
    return False


def colon_headings(lines):
    return [l for l in lines if T.is_heading(l) and COLON_HEAD.match(T.heading_text(l))]


def heading_echo(lines):
    """헤딩 바로 아래 첫 문장이 헤딩 어절의 60% 이상을 다시 쓰면 반복."""
    out = []
    for i, l in enumerate(lines):
        if not T.is_heading(l):
            continue
        h = set(re.findall(r"[가-힣A-Za-z]{2,}", T.heading_text(l)))
        if len(h) < 3:
            continue
        for j in range(i + 1, min(i + 4, len(lines))):
            nxt = T.strip_markup(lines[j])
            if not nxt:
                continue
            w = set(re.findall(r"[가-힣A-Za-z]{2,}", nxt[:80]))
            if len(h & w) / len(h) >= 0.7:
                out.append((i + 1, nxt))
            break
    return out


# ---------- 통계 ----------

def stats(sents, text):
    commas = text.count(",") + text.count("，")
    cc = len(CONNECTIVE_COMMA.findall(text))
    with_comma = sum(1 for s in sents if "," in s or "，" in s)
    endings = []
    for s in sents:
        m = ENDING.search(s)
        endings.append(m.group(1) if m else "")
    run, best = 1, 1
    for a, b in zip(endings, endings[1:]):
        run = run + 1 if a and a == b else 1
        best = max(best, run)
    lens = [len(s) for s in sents]
    cv = (statistics.pstdev(lens) / statistics.mean(lens)) if len(lens) >= 2 and statistics.mean(lens) else 1.0
    return dict(commas=commas, connective_commas=cc,
                connective_comma_rate=(cc / commas) if commas else 0.0,
                comma_sentence_ratio=(with_comma / len(sents)) if sents else 0.0,
                ending_run=best, length_cv=cv, n_sentences=len(sents), chars=len(re.sub(r"\s", "", text)))


def decoration(lines):
    body = [l for l in lines if l.strip() and not T.is_heading(l)]
    bullets = sum(1 for l in body if T.BULLET.match(l))
    bold = sum(len(re.findall(r"\*\*[^*]+\*\*", l)) for l in body)
    emoji = sum(len(T.EMOJI.findall(l)) for l in body)
    return dict(bullet_ratio=(bullets / len(body)) if body else 0.0, bold=bold, emoji=emoji)


def single_sentence_paragraphs(text):
    ps = T.paragraphs(text)
    if not ps:
        return 0.0, 0
    single = sum(1 for p in ps if len(T.sentences(p)) == 1 and "\n" not in p.strip())
    return single / len(ps), len(ps)


# ---------- 실행 ----------

def run(rules, units, register="prose", want_review=True, morph=None):
    off = set(rules["registers"].get(register, rules["registers"]["prose"]).get("off", []))
    emoji_max = rules["registers"].get(register, {}).get("emoji_max")
    hits = []
    whole_parts = []
    for loc, raw in units:
        txt = T.mask_protected(raw, rules.get("protect", []))
        whole_parts.append(txt)
        ls = T.lines(txt)
        for n, line in enumerate(ls, 1):
            s = line.strip()
            if not s or s.startswith("|") or re.match(r"^[-=*_]{3,}$", s):
                continue
            where = "%s L%d" % (loc, n)
            for r in rules["block"]:
                if r["id"] in off:
                    continue
                if "regex" in r and re.search(r["regex"], s):
                    hits.append(Hit("BLOCK", r["id"], r["name"], where, T.strip_markup(s)))
                elif r.get("structural") == "announce_then_enumerate" and announce_then_enumerate(s):
                    hits.append(Hit("BLOCK", r["id"], r["name"], where, T.strip_markup(s)))
            if want_review:
                for r in rules["review"]:
                    if r["id"] in off:
                        continue
                    if "regex" in r and "stat" not in r and re.search(r["regex"], s):
                        hits.append(Hit("REVIEW", r["id"], r["name"], where, T.strip_markup(s)))
                    if r.get("structural") == "title_number" and T.is_heading(line) and title_number(T.heading_text(line)):
                        hits.append(Hit("REVIEW", r["id"], r["name"], where, T.heading_text(line)))
        # 문서 구조 규칙
        for r in rules["block"]:
            if r["id"] in off:
                continue
            if r.get("structural") == "colon_heading_repeat":
                ch = colon_headings(ls)
                if len(ch) >= r.get("min", 3):
                    hits.append(Hit("BLOCK", r["id"], r["name"], loc, " / ".join(T.heading_text(x) for x in ch[:3]), "%d개" % len(ch)))
            if r.get("structural") == "heading_echo":
                for ln, s in heading_echo(ls):
                    hits.append(Hit("BLOCK", r["id"], r["name"], "%s L%d" % (loc, ln), s))
    whole = "\n".join(whole_parts)
    sents = T.sentences(whole)
    st = stats(sents, whole)
    if want_review:
        for r in rules["review"]:
            if r["id"] in off or "stat" not in r:
                continue
            sid = r["stat"]
            if sid == "connective_comma_rate" and st["commas"] >= r["min_commas"] and st["connective_comma_rate"] >= r["threshold"]:
                hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", "%.0f%% (%d/%d)" % (st["connective_comma_rate"] * 100, st["connective_commas"], st["commas"])))
            elif sid == "comma_sentence_ratio" and st["n_sentences"] >= r["min_sentences"] and st["comma_sentence_ratio"] >= r["threshold"]:
                hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", "%.0f%%" % (st["comma_sentence_ratio"] * 100)))
            elif sid == "ending_run" and st["ending_run"] >= r["threshold"]:
                hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", "%d연속" % st["ending_run"]))
            elif sid == "length_cv" and st["n_sentences"] >= r["min_sentences"] and st["length_cv"] < r["threshold"]:
                hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", "CV %.2f" % st["length_cv"]))
            elif sid in ("density", "sentence_initial_conjunction"):
                n = len(re.findall(r["regex"], whole))
                per = n / max(st["chars"], 1) * 1000
                if st["chars"] >= 300 and per >= r["per_1000"]:
                    hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", "1000자당 %.1f회 (%d회)" % (per, n)))
            elif sid == "count":
                n = len(re.findall(r["regex"], whole))
                if n > r["max"]:
                    hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", "%d회 (기준 %d)" % (n, r["max"])))
            elif sid == "decoration":
                d = decoration(T.lines(whole))
                emax = emoji_max if emoji_max is not None else r["emoji_max"]
                bad = []
                if d["bold"] > r["bold_max"]:
                    bad.append("볼드 %d" % d["bold"])
                if d["bullet_ratio"] > r["bullet_ratio_max"]:
                    bad.append("불릿 %.0f%%" % (d["bullet_ratio"] * 100))
                if d["emoji"] > emax:
                    bad.append("이모지 %d" % d["emoji"])
                if bad:
                    hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", ", ".join(bad)))
            elif sid == "single_sentence_paragraphs":
                ratio, n = single_sentence_paragraphs(whole)
                if n >= r["min_paragraphs"] and ratio >= r["threshold"]:
                    hits.append(Hit("REVIEW", r["id"], r["name"], "문서 전체", "", "%.0f%%" % (ratio * 100)))
    if morph is not None:
        hits.extend(morph.run(rules.get("morph", []), whole))
    return hits, st


def score(rules, hits):
    w = rules["score"]["weights"]
    s = 0
    for h in hits:
        s += w.get({"BLOCK": "block", "REVIEW": "review", "MORPH": "morph"}[h["sev"]], 0)
    return min(s, rules["score"]["cap"])
