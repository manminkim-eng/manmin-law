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
           — 발의는 발의일, 통과는 처리일(PROC_DT) 기준으로 각각 거른다
    를 긁어와 data/_inbox/YYYY-MM_수집.json 초안을 만든다.

    공포·시행 확정분은 LawMCP(국가법령정보센터)로 별도 확인한다. 이 스크립트 범위 밖.

사용법
    python collect.py                # 직전 달 — 첫째 화요일 정규 실행
    python collect.py --month 2026-08
    python collect.py --probe        # 인증·응답 형태만 확인 (필터·저장 안 함)

발행 시점
    매월 첫째 화요일에 '직전 달' 호를 완성본으로 낸다. 당월 호를 당월 초에 내면
    그 달 자료가 며칠치밖에 안 담겨 호별 건수가 개정량과 무관하게 요동친다.
    그래서 인자 없이 실행하면 이번 달이 아니라 직전 달을 수집한다.

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
import http.cookiejar
import json
import os
import re
import sys
import time
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
    # 2026-08호에서 화이트리스트에 안 걸려 수동으로 건진 것들 — 2026-09-01 추가
    ("녹색건축 인증", "건축|기계설비"), ("다중생활시설", "건축|소방"),
    ("소화약제", "소방"), ("소방용품", "소방"),
    ("도로법", "토목"), ("유료도로법", "토목"), ("하수도법", "토목"),
    ("산지관리법", "토목"), ("지하안전관리", "토목"),
    ("전기사업법", "전기"), ("전기안전관리법", "전기"),
    # 법령 정식명칭이 「신에너지 및 재생에너지 개발·이용·보급 촉진법」이라
    # "신재생에너지"로는 부분일치가 되지 않는다. 2026-08 PPT 대조에서 드러난 누락.
    ("신에너지 및 재생에너지", "전기|기계설비"),
    # 2026-08 협회 법규교육 PPT 와 대조해 보태진 것들 — 셋 다 건축 인허가에 걸린다
    ("국유재산법", "건축"),          # 국유지 점유 학교 증·개축 등
    ("농지법", "건축|토목"),          # 농지 내 화장실·주차장 등 편의시설
    ("건축물의 설비기준", "기계설비|건축"),
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


# ── 법제처 접속 대기열 대응 ────────────────────────────────────────────────
#
#   법제처는 접속량이 많으면 XML 대신 'Waitingroom' 대기열 HTML(약 4.4KB)을 돌려준다.
#   2026-09-01 자동 수집이 입법예고·행정예고 0건으로 끝난 원인이 이것이었다.
#   당시 코드는 이걸 "XML 파싱 불가"로만 남기고 0건으로 넘어가, 미수집이
#   '0건 확인'처럼 보였다 — README 2-1 이 막으려던 바로 그 상황이다.
#
#   UA 나 pageSize 로는 회피되지 않는다(둘 다 대기열에 걸림). 브라우저처럼
#   쿠키를 물고 재시도하면 첫 페이지만 뚫으면 이후 페이지는 바로 통과한다.
#   실측: 1페이지 13회 시도 후 통과 → 2·3페이지는 각 1회.
#
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_JAR))
_OPENER.addheaders = [("User-Agent", BROWSER_UA)]

WAITING_TRIES = 40      # 실측 통과까지 13회 — 여유를 둔다
WAITING_WAIT = 2        # 초


def _is_waitingroom(raw):
    return b"Waitingroom" in raw[:2000]


def fetch_queued(url, params, timeout=30, tries=WAITING_TRIES):
    """대기열이면 같은 쿠키 세션으로 재시도한다.

    끝내 못 뚫으면 (full, None) 을 돌려준다. 호출부는 이를 **0건이 아니라
    수집 실패**로 다뤄야 한다.
    """
    q = urllib.parse.urlencode(params, doseq=True)
    full = url + ("&" if "?" in url else "?") + q
    for i in range(1, tries + 1):
        try:
            raw = _OPENER.open(full, timeout=timeout).read()
        except Exception:
            if i >= tries:
                raise
            time.sleep(WAITING_WAIT)
            continue
        if not _is_waitingroom(raw):
            if i > 1:
                print("      (대기열 %d회 재시도 후 통과)" % i)
            return full, raw
        time.sleep(WAITING_WAIT)
    return full, None


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
    """열린국회정보 응답에서 실제 의안 행만 뽑는다.

    응답이 {"nzmimeepazxkubdpn": [{"head": [...]}, {"row": [...]}]} 구조라
    "처음 만난 dict 리스트"를 반환하면 바깥 껍데기 [{head}, {row}] 2개가 잡힌다.
    그 2개에는 PROPOSE_DT 가 없어 모든 행이 걸러졌다 — 수집 결과가 늘 0건이던 원인.
    그래서 'row' 키를 명시적으로 찾는다.
    """
    out = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "row" and isinstance(v, list):
                    out.extend(x for x in v if isinstance(x, dict))
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(data)
    return out


def _pick(row, keys):
    for k in keys:
        for rk, rv in row.items():
            if rk.lower() == k.lower() and rv:
                return str(rv)
    return ""


def _norm_date(s):
    """YYYYMMDD · YYYY-MM-DD · 'YYYY. M. D.' 를 모두 YYYY-MM-DD 로.

    국민참여입법센터는 월·일을 한 자리로 준다('2026. 7. 31.'). 숫자만 뽑아
    8자리로 자르던 예전 방식은 이걸 7자리로 읽어 날짜를 통째로 버렸다.
    """
    m = re.search(r"(\d{4})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})", s or "")
    if not m:
        return ""
    y, mo, d = m.groups()
    return "%s-%02d-%02d" % (y, int(mo), int(d))


def _to_date(s):
    try:
        return dt.date(*map(int, s.split("-")))
    except Exception:
        return None


def _months_before(d, n):
    y, m = d.year, d.month - n
    while m <= 0:
        m += 12
        y -= 1
    return dt.date(y, m, 1)


def _prev_month(d):
    """첫째 화요일에 내는 호는 '직전 달' 자료다 — 기본 수집 대상."""
    return _months_before(dt.date(d.year, d.month, 1), 1).strftime("%Y-%m")


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
        "detail": "https://opinion.lawmaking.go.kr/gcom/ogLmPp/%s",
    },
    "행정예고": {
        "url": "https://www.lawmaking.go.kr/rest/ptcpAdmPp.xml",
        "name": ["admRulNm"],      # 행정예고명
        "kind": "lsClsNm",         # 행정규칙종류
        "seq": "ogAdmPpSeq",
        "detail": "https://opinion.lawmaking.go.kr/gcom/admpp/%s",
    },
}

MOLEG_PSIZE = 100      # 기본값이 20 이라 명시하지 않으면 한 달치가 잘린다
MOLEG_MAX_PAGES = 30   # 3,000건 — 월 300건 안팎이므로 충분한 여유

# 예고명 앞에 붙는 진행상태 표기: "[진행]유아교육법 시행령 일부개정령안 입법예고"
_STATUS_RE = re.compile(r"^\s*\[([^\]]{1,10})\]\s*")


def _split_status(title):
    """'[진행]OO법 …' → ('진행', 'OO법 …')"""
    m = _STATUS_RE.match(title or "")
    if not m:
        return "", (title or "").strip()
    return m.group(1), _STATUS_RE.sub("", title, count=1).strip()


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
    base = {"OC": oc, "stYdFmt": _fmt_ymd(first), "edYdFmt": _fmt_ymd(last)}

    out, scanned, total, page = [], 0, None, 1
    while page <= MOLEG_MAX_PAGES:
        params = dict(base, pageIndex=page, pageSize=MOLEG_PSIZE)
        try:
            full, raw = fetch_queued(spec["url"], params,
                                     tries=1 if probe else WAITING_TRIES)
        except Exception as e:
            print("  [실패] %s — %s" % (cat, e))
            return None
        if raw is None:
            print("  [실패] %s — 법제처 접속 대기열을 %d회 시도했으나 통과하지 못했습니다."
                  % (cat, WAITING_TRIES))
            print("           이것은 0건이 아니라 '수집 못 함'입니다. 잠시 후 다시 실행하십시오.")
            return None
        body = raw.decode("utf-8", "replace")
        if probe:
            print("  요청: %s" % full)
            print("  응답(앞 600자): %s" % body[:600])
            return []
        try:
            root = ET.fromstring(body)
        except Exception:
            if _is_waitingroom(raw):
                print("  [실패] %s — 접속 대기열. 0건이 아니라 수집 실패입니다." % cat)
            else:
                print("  [실패] %s — XML 파싱 불가 (응답 앞 200자: %s)" % (cat, body[:200]))
            return None
        ret = root.find("retMsg")
        if ret is not None and (ret.text or "").strip() == "401":
            print("  [인증실패] %s — OC 계정이 승인되지 않았습니다. 정보공개 신청 상태를 확인하세요." % cat)
            print("             전에는 되던 수집이 갑자기 401 이면 공인 IP 변경을 먼저 의심하십시오.")
            print("             신청서에 등록한 IP 와 달라졌을 수 있습니다 (curl -s https://api.ipify.org).")
            return None
        if total is None:
            t = root.find("totalCnt")
            total = int(t.text) if t is not None and (t.text or "").strip().isdigit() else 0

        rows = 0
        for node in root.iter():
            title = ""
            for tag in spec["name"]:
                title = _txt(node, tag)
                if title:
                    break
            if not title:
                continue
            rows += 1
            status, title = _split_status(title)   # "[진행]" 등 상태 표기 분리
            fields = match_fields(title)
            if not fields:
                continue
            seq = _txt(node, spec["seq"])
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
                "link": (spec["detail"] % seq) if seq else "",
                "_kind": _txt(node, spec["kind"]),
                "_org": _txt(node, "asndOfiNm"),
                "_pntcNo": _txt(node, "pntcNo"),
                "_seq": seq,
                "_status": status,
                "_src": cat,
            })
        scanned += rows
        if rows == 0 or scanned >= (total or 0):
            break
        page += 1
    else:
        print("  [경고] %s — 페이지 상한(%d쪽 × %d건)에 걸렸습니다. MOLEG_MAX_PAGES 를 늘리십시오."
              % (cat, MOLEG_MAX_PAGES, MOLEG_PSIZE))

    print("  훑은 예고 %d건 (공고 전체 %s건) → 해당 %d건" % (scanned, total, len(out)))
    return out


# ── ③ 열린국회정보 의안(발의·처리) ─────────────────────────────────────────
ASSEMBLY_URL = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
PASSED = ("원안가결", "수정가결")   # 본회의 의결 = 국회통과
ALT_MERGED = "대안반영폐기"         # 원안 폐기 + 내용은 위원장 대안으로 이관 = 사실상 개정 성립
#
#   대안반영폐기를 버리면 안 된다. 위원장 대안(「OO법 일부개정법률안(대안)」)은
#   의원발의 목록인 이 API 에 아예 잡히지 않는다. 실제로 2026-07-23 건축법 개정은
#   원안 4건이 전부 '대안반영폐기'로만 남아 있어, 이를 버리면 개정 사실이 통째로 사라진다.
#   그래서 같은 (법령, 처리일) 끼리 묶어 대안 1건으로 만들어 둔다.
ASSEMBLY_PSIZE = 1000               # API 상한 확인됨
ASSEMBLY_MAX_PAGES = 40             # 40,000건 — 22대 전체(약 1.9만) 대비 여유
LOOKBACK_MONTHS = 24                # 통과분 역추적 범위 (발의는 한참 전일 수 있다)


def collect_assembly(cfg, month, probe=False):
    """당월 의원발의 + 당월 국회통과를 함께 수집한다.

    통과분은 발의일이 아니라 처리일(PROC_DT) 기준이다. 당월 발의분만 훑으면
    "6월 발의 → 8월 본회의 통과" 같은 건이 영구히 잡히지 않으므로,
    최근 LOOKBACK_MONTHS 개월치를 훑어 PROC_DT 로 따로 거른다.
    """
    a = cfg.get("assembly", {})
    key = (a.get("key") or "").strip()
    if not key:
        print("  [건너뜀] assembly.key 미설정")
        return []
    first, last = month_range(month)
    scan_from = _months_before(first, LOOKBACK_MONTHS)

    picked, alt_groups = {}, {}
    page, scanned, truncated, reached = 1, 0, False, False
    while True:
        if page > ASSEMBLY_MAX_PAGES:
            truncated = True
            break
        params = {"KEY": key, "Type": "json", "pIndex": page,
                  "pSize": ASSEMBLY_PSIZE, "AGE": a.get("age", "22")}
        try:
            full, raw = fetch(ASSEMBLY_URL, params, timeout=60)
        except Exception as e:
            print("  [실패] 의안 — %s" % e)
            break
        if probe:
            print("  요청: %s" % re.sub(r"KEY=[^&]*", "KEY=***", full))
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
        scanned += len(rows)
        for r in rows:
            pd = _to_date(_norm_date(_pick(r, ["PROPOSE_DT", "propose_dt"])))
            cd = _to_date(_norm_date(_pick(r, ["PROC_DT", "proc_dt"])))
            if pd and pd < scan_from:
                reached = True          # 발의일 내림차순 — 이 뒤는 범위 밖
            title = _pick(r, ["BILL_NAME", "bill_name"]).strip()
            if not title:
                continue
            fields = match_fields(title)
            if not fields:
                continue
            result = _pick(r, ["PROC_RESULT", "proc_result"]).strip()
            if result == ALT_MERGED and cd and first <= cd <= last:
                # 원안은 죽었지만 내용은 대안으로 살아 있다 — 법령·처리일 단위로 묶는다
                g = alt_groups.setdefault((_base_law(title), cd),
                                          {"fields": [], "from": []})
                for f in fields:
                    if f not in g["fields"]:
                        g["fields"].append(f)
                g["from"].append("%s (%s)" % (title, _pick(r, ["PROPOSER", "proposer"])))
                continue
            passed = bool(result in PASSED and cd and first <= cd <= last)
            proposed = bool(pd and first <= pd <= last)
            if not (passed or proposed):
                continue
            item = {
                "cat": "국회통과" if passed else "의원발의",
                "field": fields, "law": _base_law(title), "title": title,
                "dateLabel": "의결" if passed else "발의",
                "date": (cd if passed else pd).strftime("%Y-%m-%d"),
                "summary": "", "reason": "",
                "link": _pick(r, ["DETAIL_LINK", "detail_link", "LINK_URL"]),
                "_proposer": _pick(r, ["PROPOSER", "proposer"]),
                "_committee": _pick(r, ["COMMITTEE", "committee"]),
                "_proposeDt": pd.strftime("%Y-%m-%d") if pd else "",
                "_procDt": cd.strftime("%Y-%m-%d") if cd else "",
                "_result": result, "_src": "의안",
            }
            item["_billId"] = _pick(r, ["BILL_ID", "bill_id"])
            bid = item["_billId"] or title
            prev = picked.get(bid)
            if prev is None or (passed and prev["cat"] != "국회통과"):
                picked[bid] = item      # 같은 의안이면 통과 상태를 우선
        if reached:
            break
        page += 1

    if truncated:
        print("  [경고] 페이지 상한(%d쪽 × %d건)에 걸려 끝까지 훑지 못했습니다."
              " ASSEMBLY_MAX_PAGES 를 늘리십시오." % (ASSEMBLY_MAX_PAGES, ASSEMBLY_PSIZE))
    for (law, cd), g in sorted(alt_groups.items(), key=lambda x: (x[0][1], x[0][0])):
        picked["alt:%s:%s" % (law, cd)] = {
            "cat": "국회통과",
            "field": g["fields"],
            "law": law,
            "title": "%s 일부개정법률안(대안)" % law,
            "dateLabel": "대안반영",
            "date": cd.strftime("%Y-%m-%d"),
            "summary": "", "reason": "",
            "link": "",
            "_result": ALT_MERGED,
            "_altMergedFrom": g["from"],
            "_note": "원안 %d건이 위원회 대안에 반영되어 폐기됐습니다. 대안 본문은 이 API"
                     "(의원발의 목록)에 없으니 의안정보시스템에서 조문을 확인하십시오." % len(g["from"]),
            "_src": "의안",
        }
        print("  [대안] %s %s — 원안 %d건 통합" % (cd, law, len(g["from"])))
    print("  훑은 의안 %d건 (%s 이후 발의분) → 해당 %d건" % (scanned, scan_from, len(picked)))
    return list(picked.values())


def _dedupe_key(it):
    """중복 판정 키.

    · cat 을 넣는다 — 빼면 '6월 의원발의'로 실린 법안이 8월에 통과해도
      '기존 호와 중복'으로 잘려 단계 전환이 영영 안 잡힌다.
    · date 를 넣는다 — 「건축법 일부개정법률안」처럼 이름이 같은 의안이
      발의자만 달리해 여러 건 올라오므로, 법령명+제목만으로는 서로를 지운다.
    같은 의안을 두 번 싣는 것보다 다른 의안을 놓치는 쪽이 나쁘므로 느슨하게 잡는다.
    """
    return (it.get("cat") or "", it.get("law") or "",
            re.sub(r"\s+", "", it.get("title") or "")[:40], it.get("date") or "")


def dedupe(items, month):
    seen, out = set(), []
    for it in items:
        # 같은 배치 안에서는 의안 고유번호가 있으면 그것으로 판정한다
        k = it.get("_billId") or _dedupe_key(it)
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    # 발행할 때 제목을 실무 표현으로 바꿔 쓰기 때문에(의안명 「건축물관리법 일부개정법률안」
    # → 「공장·창고 화재위험등급 평가 의무」) 제목 기반 판정은 다음 달에 샌다.
    # data/*.json 항목에 billId 를 남겨 두면 제목이 달라져도 확실히 걸러진다.
    prev, prev_ids = set(), set()
    for root, _, files in os.walk(os.path.join(HERE, "data")):
        for f in files:
            if not f.endswith(".json") or f.startswith(month):
                continue
            try:
                d = json.load(open(os.path.join(root, f), encoding="utf-8"))
            except Exception:
                continue
            for it in d.get("items", []):
                prev.add(_dedupe_key(it))
                if it.get("billId"):
                    prev_ids.add(str(it["billId"]).strip())
    fresh = [it for it in out
             if _dedupe_key(it) not in prev
             and str(it.get("_billId") or "").strip() not in prev_ids]
    if len(out) - len(fresh):
        print("  기존 호와 중복 %d건 제외 (의안번호 대조 %d건 등록)"
              % (len(out) - len(fresh), len(prev_ids)))
    return fresh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default=_prev_month(dt.date.today()),
                    help="수집 대상 월(YYYY-MM). 생략하면 직전 달 — 첫째 화요일 정규 실행")
    ap.add_argument("--probe", action="store_true", help="인증·응답 형태만 확인")
    args = ap.parse_args()

    cfg = load_config()
    month = args.month
    print("수집 대상: %s" % month)

    items, failed = [], []
    for label, cat in ((" ① 입법예고", "입법예고"), (" ② 행정예고", "행정예고")):
        print(label)
        got = collect_moleg(cfg, month, cat, args.probe)
        if got is None:          # 수집 실패 — 0건과 구분해야 한다
            failed.append(cat)
        else:
            items += got
    print(" ③ 의원발의·국회통과")
    items += collect_assembly(cfg, month, args.probe) or []

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
               "failed": failed,
               "counts": by_cat, "items": items}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("\n총 %d건 — %s" % (len(items), by_cat or "없음"))
    print("저장: %s" % path)
    if failed:
        print("\n" + "!" * 68)
        print("[경고] 수집하지 못한 단계: %s" % " · ".join(failed))
        print("       이 단계는 '0건 확인'이 아니라 '못 훑음'입니다.")
        print("       README 2-1 에 따라 이 상태로는 발행하지 마십시오.")
        print("       잠시 후 다시 실행하거나, 부득이하면 그 호 source 에 미수집 사실을 명시하십시오.")
        print("!" * 68)
    print("\n다음 단계")
    print("  1) 초안을 검토해 실무 영향 있는 항목만 고른다")
    print("  2) summary·reason·impact 를 채워 data/%s.json 의 items 에 붙인다" % month)
    print("     이때 초안의 _billId 값을 billId 필드로 옮겨 둔다 — 제목을 바꿔 써도")
    print("     다음 달 수집에서 같은 의안이 다시 올라오지 않는다")
    print("  3) LawMCP 로 공포·시행 확정분(시행법령·훈령예규고시)을 추가한다")
    print("  4) python build.py")


if __name__ == "__main__":
    main()
