# -*- coding: utf-8 -*-
"""
ppt_check.py — 협회 법규교육 PPT 대조  (MANMIN LEGAL REVIEW)

목적
    협회 법규교육 PPT 1쪽 「월 법규교육 요약」에 실린 시행·공포 / 입법예고 / 행정예고
    항목이 우리 사이트(data/*.json 전 호)에 실렸는지 기계적으로 대조한다.

    2026-11-04, 10월 PPT 1번 항목 「건축물관리법 시행령」(2026.9.22. 공포·시행)이
    9월호·10월호 어디에도 없는 것을 사람이 눈으로 대조하다가 찾았다. 8월호에 입법예고만
    싣고 공포는 놓친 것이다. 눈 대조는 매달 빠뜨리기 쉬우므로 스크립트로 남긴다.

사용법
    python publish.py ppt                       참고자료 폴더(하위 폴더 포함)의 가장 최근 PPT — 파일명 (YY년MM월) 기준
    python publish.py ppt --pdf "경로.pdf"       특정 PPT
    python ppt_check.py "경로.pdf" [...]         여러 개 한 번에

판정
    실림        같은 법령·같은 날짜의 항목이 어느 호에든 있다
    실림(언급)  같은 법령 항목 본문에 그 날짜가 언급돼 있다 (예: 공포 때 시행일 안내)
    실림(근사)  PPT 쪽 오탈자·줄임 이름이거나 예고 시작일이 며칠 다름 — 눈으로 한 번 확인
    다음 호     날짜가 마지막 발행 호보다 뒤 — 다음 호에서 다룰 것
    제외        domain_filter.json 의 excluded (예: 농지법)
    범위 밖?    화이트리스트에 없는 법령 (예: 국가재정법 시행령) — 실을지 사람이 판단
    누락?       위 어디에도 해당하지 않음 — 사람이 확인해서 보완하거나 제외 사유를 남긴다

한계
    PPT 1쪽 글자 추출(pypdf)에 기댄다. 법령명은 우리가 아는 이름(전 호 law·title,
    감시목록)에서 찾고, 못 찾으면 '이름 추정'으로 표시한다. 판정은 보조 수단이며
    최종 확인은 사람이 한다.
"""

import datetime as dt
import difflib
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
REF = os.path.normpath(os.path.join(HERE, "..", "참고자료"))

SUFFIX = re.compile(r"(일부|전부)?개정(법률|령|고시|규칙)?안$|제정(령|고시)?안$|개정안$|고시안$|령안$")
SECTIONS = (("행정예고", r"행 ?정 ?예 ?고"), ("입법예고", r"입 ?법 ?예 ?고"), ("시행", r"시 ?행"))


def norm(s):
    s = re.sub(r"[\s「」『』ㆍ·\-]", "", s or "")
    return SUFFIX.sub("", s)


def ymd(s):
    """'26. 06. 23.' · '2026. 09. 22' · '26.09.23' → '2026-06-23'"""
    m = re.match(r"\s*(\d{2,4})\.\s*(\d{1,2})\.\s*(\d{1,2})", s or "")
    if not m:
        return None
    y = int(m.group(1))
    y = y + 2000 if y < 100 else y
    return "%04d-%02d-%02d" % (y, int(m.group(2)), int(m.group(3)))


def load_issues():
    issues = {}
    for f in sorted(glob.glob(os.path.join(glob.escape(DATA), "20[0-9][0-9]-[01][0-9].json"))):
        try:
            issues[os.path.basename(f)[:7]] = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            pass
    return issues


def known_names(issues):
    names = set()
    for d in issues.values():
        for it in d.get("items", []):
            if it.get("law"):
                names.add(it["law"])
    for fn, keys in (("law_snapshot.json", ("batches",)), ("admin_watchlist.json", ("watch",))):
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            continue
        try:
            j = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for k in keys:
            for x in j.get(k, []):
                if isinstance(x, list):
                    names.update(x)
                elif isinstance(x, dict) and x.get("name"):
                    names.add(x["name"])
                elif isinstance(x, str):
                    names.add(x)
    return {norm(n): n for n in names if n}


def parse_ppt(path):
    import pypdf  # 필요할 때만
    t = pypdf.PdfReader(path).pages[0].extract_text() or ""
    t = re.sub(r"\s+", " ", t)
    heads = []
    for name, pat in SECTIONS:
        for m in re.finditer(r"\d ?" + pat + r" ", t):
            heads.append((m.start(), name))
    heads.sort()
    out = []
    for e in re.finditer(r"(시행 ?공포|예고기간|공포|시행)\s*\[\s*(?:\(\s*\)\s*)?([0-9\.\s~]+?)\s*\]", t):
        sec = "시행"
        for pos, name in heads:
            if pos < e.start():
                sec = name
        a, _, b = e.group(2).partition("~")
        out.append({"sec": sec, "pre": t[max(0, e.start() - 90):e.start()].strip(),
                    "start": ymd(a), "end": ymd(b) if b else None})
    return out


def guess_name(pre, names):
    p = norm(pre)
    best = None
    for k, v in names.items():
        if k and p.endswith(k) and (best is None or len(k) > len(best[0])):
            best = (k, v)
    if best:
        return best[1], True
    # 앞 항목 설명문 꼬리·구역 제목을 잘라내고 마지막 법령명 덩어리만 남긴다
    tail = re.split(r"[.,▶)」’”]|\d|(?:임|것|함|음|마련|허용|완화|부여|제외|정비)\s|"
                    r"시 ?행 ?(?:공 ?포 ?)?법 ?령|입 ?법 ?예 ?고|행 ?정 ?예 ?고|&", pre)[-1]
    tail = re.sub(r"\s*(?:(?:일부|전부)?개정\S*안|·)\s*$", "", tail).strip()
    return (tail or pre[-30:]), False


def _days(a, b):
    try:
        return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days)
    except Exception:
        return 9999


def judge(entry, name, issues, excluded, scope, last_month):
    n = norm(name)
    cats = {"시행": ("시행법령", "훈령예규고시", "추가검토", "국회통과"),
            "입법예고": ("입법예고", "추가검토"),
            "행정예고": ("행정예고", "훈령예규고시", "추가검토")}[entry["sec"]]
    start, end = entry["start"] or "", entry["end"] or ""
    for ex in excluded:
        if norm(ex) and norm(ex) in n:
            return "제외", "domain_filter excluded (%s)" % ex
    same, mention, near = [], [], []
    for mon, d in issues.items():
        for it in d.get("items", []):
            if it.get("cat") not in cats:
                continue
            law, title = norm(it.get("law")), norm(it.get("title"))
            hit = law == n or (entry["sec"] == "행정예고" and n and (n in title or (law and law in n)))
            if not hit:
                # PPT 쪽 오탈자·줄임(예: '기부체납', '피난 방화구조 등에 관한 규칙')을 위한 근사 일치.
                # 이름이 75% 이상 닮고 날짜(시작 또는 마감)가 같아야 한다.
                sim = difflib.SequenceMatcher(None, law, n).ratio() if law and n else 0
                if sim >= 0.75 and (it.get("date") == start or (end and it.get("deadline") == end)):
                    near.append("%s %s「%s」(%s, 이름 유사)" % (mon, it.get("cat"), it.get("law"), it.get("date")))
                continue
            if it.get("date") == start:
                same.append("%s %s" % (mon, it.get("cat")))
                continue
            y, m, dd = start.split("-") if start else ("", "", "")
            blob = " ".join(str(it.get(k) or "") for k in ("title", "summary", "detail", "impact"))
            if start and re.search(r"%s\.\s*%d\.\s*%d\." % (y, int(m), int(dd)), blob):
                mention.append("%s %s(%s)" % (mon, it.get("cat"), it.get("date")))
            elif entry["sec"] != "시행" and (_days(it.get("date"), start) <= 14
                                              or (end and it.get("deadline") == end)):
                # 예고는 PPT 와 국민참여입법센터의 시작일이 며칠 어긋나는 일이 잦다
                near.append("%s %s(%s~%s, 날짜 다름)" % (mon, it.get("cat"), it.get("date"),
                                                      it.get("deadline") or ""))
    if same:
        return "실림", " · ".join(same)
    if mention:
        return "실림(언급)", " · ".join(mention)
    if near:
        return "실림(근사)", " · ".join(near)
    if start and start[:7] > last_month:
        return "다음 호", "%s호 이후 대상" % start[:7]
    if scope and not any(s in n for s in scope):
        return "범위 밖?", "domain_filter 화이트리스트에 없는 법령 — 실을지 판단"
    return "누락?", ""


def check(path, verbose=True):
    issues = load_issues()
    names = known_names(issues)
    try:
        flt = json.load(io.open(os.path.join(DATA, "domain_filter.json"), encoding="utf-8"))
        excluded = [x["match"] for x in flt.get("excluded", [])]
        scope = [norm(x["match"]) for x in flt.get("laws", []) if x.get("match")]
    except Exception:
        excluded, scope = [], []
    last = max(issues) if issues else "0000-00"
    rows = []
    for e in parse_ppt(path):
        name, sure = guess_name(e["pre"], names)
        verdict, note = judge(e, name, issues, excluded, scope, last)
        rows.append((e["sec"], name, sure, e["start"], e["end"], verdict, note))
    if verbose:
        print("\n[PPT 대조] %s  (발행 호: ~%s)" % (os.path.basename(path), last))
        for sec, name, sure, a, b, v, note in rows:
            mark = {"실림": "  ", "실림(언급)": "  ", "실림(근사)": "~ ", "다음 호": "→ ",
                    "제외": "- ", "범위 밖?": "? "}.get(v, "!!")
            print("  %s%-6s %-4s %s%s  %s%s  %s" % (
                mark, v, sec[:4], name, "" if sure else " (이름 추정)",
                a or "?", ("~" + b) if b else "", note))
        miss = [r for r in rows if r[5] == "누락?"]
        print("  → 누락 의심 %d건%s" % (len(miss), " — 확인 후 보완하거나 제외 사유를 남기십시오." if miss else ""))
    return rows


def _ppt_key(path):
    """파일명의 '(26년10월)' 을 (2026, 10) 으로 — 없으면 수정 시각. 폴더를 옮기면 mtime 이 바뀔 수 있어 이름을 우선한다."""
    m = re.search(r"(\d{2,4})\s*년\s*(\d{1,2})\s*월", os.path.basename(path))
    if m:
        y = int(m.group(1))
        return (1, y + 2000 if y < 100 else y, int(m.group(2)), os.path.getmtime(path))
    return (0, 0, 0, os.path.getmtime(path))


def latest_ppt():
    # 참고자료 바로 아래와 하위 폴더(예: 참고자료\26년10월\) 모두 찾는다 (2026-11-04)
    c = glob.glob(os.path.join(glob.escape(REF), "**", "*PPT*.pdf"), recursive=True)
    c = sorted(set(os.path.normpath(p) for p in c), key=_ppt_key)
    return c[-1] if c else None


if __name__ == "__main__":
    paths = sys.argv[1:] or [latest_ppt()]
    bad = 0
    for p in paths:
        if not p or not os.path.exists(p):
            print("PPT 를 찾지 못했습니다: %r" % p)
            sys.exit(2)
        bad += sum(1 for r in check(p) if r[5] == "누락?")
    sys.exit(1 if bad else 0)
