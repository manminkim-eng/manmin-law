# -*- coding: utf-8 -*-
"""
collect.py — 예고·발의 단계 자동 수집기  (MANMIN LEGAL REVIEW)

목적
    build.py 는 data/YYYY-MM.json 을 HTML 로 바꿀 뿐, 자료 수집은 사람이 했다.
    그 결과 PPT 기반 호(7~18건)와 LawMCP 조사 호(4~5건)의 수집 범위가 달라
    "7월에 법이 많이 바뀐 것처럼" 보이는 왜곡이 생겼다.

    이 스크립트는 매월 동일한 기준으로
        ① 입법예고   (법제처 국민참여입법센터)
        ② 행정예고   (법제처 국민참여입법센터)
        ③ 의원발의 · 국회통과 (열린국회정보 의안 API)
    를 긁어와 data/_inbox/YYYY-MM_수집.json 초안을 만든다.

    공포·시행 확정분은 LawMCP(국가법령정보센터)로 별도 확인한다. 이 스크립트 범위 밖.

사용법
    python collect.py                # 이번 달
    python collect.py --month 2026-08
    python collect.py --probe        # 인증·응답 형태만 확인 (필터·저장 안 함)

설정
    같은 폴더에 config.local.json 을 만든다. (git 에 올리지 말 것 — .gitignore 등록됨)
    {
      "assembly": { "key": "열린국회정보 인증키", "age": "22" }   // 22대 국회,
      "moleg":    { "oc": "국민참여입법센터 정보공개 신청 계정 ID 의 @ 앞부분" }
    }
    OC 는 opinion.lawmaking.go.kr 에서 정식 회원가입 후
    도움말 > 서비스 안내 및 정보공개 > 정보공개활용 > [정보공개 신청정보] 에서 신청·승인받는다.
    비어 있으면 해당 소스는 건너뛴다.
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.local.json")
INBOX = os.path.join(HERE, "data", "_inbox")

# ── 분야 분류 ──────────────────────────────────────────────────────────────
# 키워드 부분일치는 오탐이 심하다(기초연금법→"기초", 전기통신사업법→"전기",
# 농어촌구조개선→"구조", 국제형사사법 공조법→"공조", 도로교통법→"도로").
# 그래서 실무 관련 법령명을 화이트리스트로 명시하고, 혼동되는 법령은 DENY 로 끊는다.
# 새 법령이 나오면 LAWS 에 (법령명조각, "분야|분야") 형태로 추가한다.
LAWS = [
    ("건축법", "건축"), ("건축물관리법", "건축"), ("건축물의 분양", "건축"),
    ("건축서비스산업", "건축"), ("건축사법", "건축"),
    ("건축물의 피난", "건축|구조|소방"), ("건축물의 설비기준", "기계설비"),
    ("건축물의 구조기준", "구조"),
    ("주택법", "건축"), ("주택건설기준", "건축"), ("공동주택관리법", "건축"),
    ("공공주택 특별법", "건축"), ("빈집 및 소규모주택", "건축"),
    ("도시 및 주거환경정비", "건축"), ("국토의 계획 및 이용", "건축"),
    ("개발제한구역", "건축"), ("특정건축물 정리", "건축"),
    ("공사중단 장기방치 건축물", "건축"), ("모듈러 건축", "건축"), ("혁신건축", "건축"),
    ("녹색건축물", "건축|기계설비"), ("장애인·노인·임산부", "건축"),
    ("장애인등편의", "건축"), ("승강기 안전관리", "건축"), ("옥외광고물", "건축"),
    ("학교시설사업", "건축"), ("주차장법", "건축|토목"), ("다중이용업소", "건축|소방"),
    ("실내공기질", "기계설비"), ("기계설비법", "기계설비"), ("에너지이용 합리화", "기계설비"),
    ("시설물의 안전 및 유지관리", "구조"), ("건설기술 진흥", "구조"),
    ("지진·화산재해대책", "구조"),
    ("소방시설 설치 및 관리", "소방"), ("소방시설공사업", "소방"), ("소방기본법", "소방"),
    ("화재의 예방 및 안전관리", "소방"), ("위험물안전관리", "소방"),
    ("도로법", "토목"), ("유료도로법", "토목"), ("하수도법", "토목"),
    ("산지관리법", "토목"), ("지하안전관리", "토목"),
    ("전기사업법", "전기"), ("전기안전관리법", "전기"), ("신재생에너지", "전기"),
]

# 이름이 비슷해 걸려드는 무관 법령 — 화이트리스트보다 우선 적용
DENY = ["도로교통법", "전기통신", "기초연금", "국민기초생활", "농어촌구조개선",
        "119구조", "소방공무원", "주택임대차", "국제형사", "사립대학", "지진해일",
        "주택도시기금", "장기공공임대주택", "농어촌 전기공급", "전기용품"]


def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit("config.local.json 이 없습니다. README 의 'API 인증키 설정' 절을 참고해\n  %s\n에 만들어 주세요." % CONFIG_PATH)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def fetch(url, params, timeout=20):
    q = urllib.parse.urlencode(params, doseq=True)
    full = url + ("&" if "?" in url else "?") + q
    req = urllib.request.Request(full, headers={"User-Agent": "manmin-law-collector/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return full, raw


def match_fields(title):
    """법령명 화이트리스트로 분야 판정. 해당 없으면 None(수집 제외)."""
    if any(d in title for d in DENY):
        return None
    hit = []
    for key, fields in LAWS:
        if key in title:
            for f in fields.split("|"):
                if f not in hit:
                    hit.append(f)
    return hit or None


def month_range(month):
    y, m = map(int, month.split("-"))
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    return first, last


def _dig_rows(data):
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for v in data.values():
            got = _dig_rows(v)
            if got:
                return got
    return []


def _pick(row, keys):
    for k in keys:
        for rk, rv in row.items():
            if rk.lower() == k.lower() and rv:
                return str(rv)
    return ""


def _norm_date(s):
    d = re.sub(r"\D", "", s or "")
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8]) if len(d) >= 8 else ""


def _base_law(title):
    t = re.sub(r"\s*(일부|전부)?\s*(개정|제정|폐지)(법률|령|규칙)?안?.*$", "", title).strip()
    return t or title.strip()


# ── ① · ② 법제처 입법예고 · 행정예고 (국민참여입법센터) ──────────────────
#
#   입법예고 목록 : https://www.lawmaking.go.kr/rest/ogLmPp.xml
#   행정예고 목록 : https://www.lawmaking.go.kr/rest/ptcpAdmPp.xml
#   인증          : OC = 국민참여입법센터 정보공개 신청 계정 ID 의 @ 앞부분
#   응답          : XML 전용 (JSON 미지원)
#   날짜 형식     : stYdFmt / edYdFmt = "YYYY. M. D."  (공백 포함)
#   미승인 계정   : <result><retMsg>401</retMsg></result> 반환
#
MOLEG = {
    "입법예고": {
        "url": "https://www.lawmaking.go.kr/rest/ogLmPp.xml",
        "name": ["lsNm"],          # 입법예고명
        "kind": "lsClsNm",         # 법령종류
        "seq": "ogLmPpSeq",
    },
    "행정예고": {
        "url": "https://www.lawmaking.go.kr/rest/ptcpAdmPp.xml",
        "name": ["admRulNm"],      # 행정예고명
        "kind": "lsClsNm",         # 행정규칙종류
        "seq": "ogAdmPpSeq",
    },
}


def _fmt_ymd(d):
    """국민참여입법센터 날짜 포맷 — 'YYYY. M. D.'"""
    return "%d. %d. %d." % (d.year, d.month, d.day)


def _txt(node, tag):
    e = node.find(tag)
    return (e.text or "").strip() if e is not None and e.text else ""


def collect_moleg(cfg, month, cat, probe=False):
    m = cfg.get("moleg", {})
    oc = (m.get("oc") or "").strip()
    if not oc:
        print("  [건너뜀] moleg.oc 미설정 — 국민참여입법센터 정보공개 신청 후 계정 ID(@ 앞부분) 입력")
        return []
    spec = MOLEG[cat]
    first, last = month_range(month)
    params = {"OC": oc, "stYdFmt": _fmt_ymd(first), "edYdFmt": _fmt_ymd(last)}
    try:
        full, raw = fetch(spec["url"], params)
    except Exception as e:
        print("  [실패] %s — %s" % (cat, e))
        return []
    body = raw.decode("utf-8", "replace")
    if probe:
        print("  요청: %s" % full)
        print("  응답(앞 600자): %s" % body[:600])
        return []
    try:
        root = ET.fromstring(body)
    except Exception:
        print("  [실패] %s — XML 파싱 불가" % cat)
        return []
    ret = root.find("retMsg")
    if ret is not None and (ret.text or "").strip() == "401":
        print("  [인증실패] %s — OC 계정이 승인되지 않았습니다. 정보공개 신청 상태를 확인하세요." % cat)
        return []

    out = []
    for node in root.iter():
        title = ""
        for tag in spec["name"]:
            title = _txt(node, tag)
            if title:
                break
        if not title:
            continue
        fields = match_fields(title)
        if not fields:
            continue
        out.append({
            "cat": cat,
            "field": fields,
            "law": _base_law(title),
            "title": title,
            "dateLabel": "예고",
            "date": _norm_date(_txt(node, "pntcDt") or _txt(node, "stYd")),
            "deadline": _norm_date(_txt(node, "edYd")),
            "summary": "",
            "reason": "",
            "_kind": _txt(node, spec["kind"]),
            "_org": _txt(node, "asndOfiNm"),
            "_pntcNo": _txt(node, "pntcNo"),
            "_seq": _txt(node, spec["seq"]),
            "_src": cat,
        })
    return out


# ── ③ 열린국회정보 의안(발의·처리) ─────────────────────────────────────────
ASSEMBLY_URL = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
PASSED = ("원안가결", "수정가결", "대안반영폐기")


def collect_assembly(cfg, month, probe=False):
    a = cfg.get("assembly", {})
    key = (a.get("key") or "").strip()
    if not key:
        print("  [건너뜀] assembly.key 미설정")
        return []
    first, last = month_range(month)
    out, page = [], 1
    while page <= 20:
        params = {"KEY": key, "Type": "json", "pIndex": page, "pSize": 100, "AGE": a.get("age", "22")}
        try:
            full, raw = fetch(ASSEMBLY_URL, params)
        except Exception as e:
            print("  [실패] 의안 — %s" % e)
            break
        if probe:
            print("  요청: %s" % full)
            print("  응답(앞 600자): %s" % raw[:600].decode("utf-8", "replace"))
            return []
        try:
            data = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            print("  [실패] 의안 — JSON 파싱 불가. 인증키를 확인하세요.")
            break
        rows = _dig_rows(data)
        if not rows:
            break
        stop = False
        for r in rows:
            d = _norm_date(_pick(r, ["PROPOSE_DT", "propose_dt"]))
            if not d:
                continue
            dd = dt.date(*map(int, d.split("-")))
            if dd < first:
                stop = True
                continue
            if dd > last:
                continue
            title = _pick(r, ["BILL_NAME", "bill_name"])
            fields = match_fields(title)
            if not fields:
                continue
            result = _pick(r, ["PROC_RESULT", "proc_result"])
            out.append({
                "cat": "국회통과" if any(p in result for p in PASSED) else "의원발의",
                "field": fields, "law": _base_law(title), "title": title.strip(),
                "dateLabel": "발의", "date": d, "summary": "", "reason": "",
                "link": _pick(r, ["DETAIL_LINK", "detail_link", "LINK_URL"]),
                "_proposer": _pick(r, ["PROPOSER", "proposer"]),
                "_committee": _pick(r, ["COMMITTEE", "committee"]),
                "_result": result, "_src": "의안",
            })
        if stop:
            break
        page += 1
    return out


def dedupe(items, month):
    seen, out = set(), []
    for it in items:
        k = (it["law"], re.sub(r"\s+", "", it["title"])[:40])
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    prev = set()
    for root, _, files in os.walk(os.path.join(HERE, "data")):
        for f in files:
            if not f.endswith(".json") or f.startswith(month):
                continue
            try:
                d = json.load(open(os.path.join(root, f), encoding="utf-8"))
            except Exception:
                continue
            for it in d.get("items", []):
                prev.add((it.get("law", ""), re.sub(r"\s+", "", it.get("title", ""))[:40]))
    fresh = [it for it in out if (it["law"], re.sub(r"\s+", "", it["title"])[:40]) not in prev]
    if len(out) - len(fresh):
        print("  기존 호와 중복 %d건 제외" % (len(out) - len(fresh)))
    return fresh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default=dt.date.today().strftime("%Y-%m"))
    ap.add_argument("--probe", action="store_true", help="인증·응답 형태만 확인")
    args = ap.parse_args()

    cfg = load_config()
    month = args.month
    print("수집 대상: %s" % month)

    items = []
    print(" ① 입법예고")
    items += collect_moleg(cfg, month, "입법예고", args.probe)
    print(" ② 행정예고")
    items += collect_moleg(cfg, month, "행정예고", args.probe)
    print(" ③ 의원발의·국회통과")
    items += collect_assembly(cfg, month, args.probe)

    if args.probe:
        print("\nprobe 모드 — 저장하지 않았습니다.")
        return

    items = dedupe(items, month)
    by_cat = {}
    for it in items:
        by_cat[it["cat"]] = by_cat.get(it["cat"], 0) + 1

    os.makedirs(INBOX, exist_ok=True)
    path = os.path.join(INBOX, "%s_수집.json" % month)
    payload = {"issue": month,
               "collected": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
               "scope": "입법예고 · 행정예고 · 의원발의 · 국회통과 (공포·시행 확정분은 LawMCP 로 별도 확인)",
               "counts": by_cat, "items": items}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("\n총 %d건 — %s" % (len(items), by_cat or "없음"))
    print("저장: %s" % path)
    print("\n다음 단계")
    print("  1) 초안을 검토해 실무 영향 있는 항목만 고른다")
    print("  2) summary·reason·impact 를 채워 data/%s.json 의 items 에 붙인다" % month)
    print("  3) LawMCP 로 공포·시행 확정분(시행법령·훈령예규고시)을 추가한다")
    print("  4) python build.py")


if __name__ == "__main__":
    main()
