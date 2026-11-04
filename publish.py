# -*- coding: utf-8 -*-
"""
publish.py — 월간호 발행 파이프라인  (MANMIN LEGAL REVIEW)

목적
    수집(collect.py) · 점검 · 빌드(build.py) · 커밋 · 푸시를 한 자리에서 돌린다.
    핵심은 빌드가 아니라 **점검**이다. README 의 발행 규칙은 지금까지 사람이
    기억해서 지켜야 했고, 실제로 2026-08호에서 두 번 무너졌다.

        · source 에 "6단계 완주"라고 적었으나 훈령예규고시는 훑지 못했다
        · 예고 10건의 reason 을 원문 없이 추정으로 썼다

    이 스크립트는 그런 상태를 발행 전에 막는다.

사용법
    python publish.py collect                 직전 달 수집 (인자 없으면 전월)
    python publish.py check                   발행 전 점검만
    python publish.py build                   빌드만
    python publish.py release                 점검 → 빌드 → 커밋
    python publish.py release --push          위 + 푸시
    python publish.py release --month 2026-09 특정 월
    python publish.py ppt                     협회 법규교육 PPT 1쪽 요약을 전 호와 대조
    python publish.py ppt --pdf "경로.pdf"     (기본: ../참고자료 의 가장 최근 PPT)

    python 은 PATH 에 없을 수 있다. 이 PC 기준:
        C:\\Users\\user\\miniconda3\\python.exe publish.py release

주의
    선별(초안에서 실을 항목 고르기)과 summary·impact 작성은 사람 판단이라
    이 스크립트가 대신하지 않는다. collect 와 check 사이에 사람이 들어간다.
"""

import argparse
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys

# 콘솔 인코딩(cp949 등) 때문에 출력 한 줄이 수집 전체를 죽이는 일이 없도록.
# 2026-09-01 에 대안 안내 문구의 em dash 가 cp949 로 인코딩되지 않아
# UnicodeEncodeError 로 수집이 중단된 적이 있다. 표시 문제로 작업이 죽으면 안 된다.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
INBOX = os.path.join(DATA, "_inbox")
PY = sys.executable

CATS = ("시행법령", "국회통과", "훈령예규고시", "입법예고", "행정예고", "의원발의", "추가검토")
# README 2-1 의 필수 6단계 (추가검토는 선택)
STAGES = ("시행법령", "훈령예규고시", "입법예고", "행정예고", "의원발의", "국회통과")


def prev_month(d=None):
    d = d or dt.date.today()
    y, m = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
    return "%04d-%02d" % (y, m)


def run(cmd, **kw):
    print("  $ %s" % " ".join(cmd[1:] if cmd[0] == PY else cmd))
    return subprocess.run(cmd, cwd=HERE, **kw)


def git(*args, **kw):
    return subprocess.run(["git"] + list(args), cwd=HERE,
                          capture_output=True, text=True, encoding="utf-8", **kw)


# ── 수집 ──────────────────────────────────────────────────────────────────
def step_collect(month):
    print("\n[수집] %s" % month)
    r = run([PY, os.path.join(HERE, "collect.py"), "--month", month])
    if r.returncode != 0:
        print("  수집 실패 (종료코드 %d)" % r.returncode)
        return False
    return True


# ── 점검 ──────────────────────────────────────────────────────────────────
def _report(month, block, warn, info, verbose):
    if verbose:
        print("\n[점검] %s" % month)
        for s in info:
            print("  · %s" % s)
        for s in warn:
            print("  [주의] %s" % s)
        for s in block:
            print("  [차단] %s" % s)
        if not block:
            print("  → 발행 가능%s" % (" (주의 %d건 확인 요망)" % len(warn) if warn else ""))
    return block, warn, info


def norm_law(s):
    """법령명 비교용 — 공백·낫표·가운뎃점(ㆍ/·) 차이를 없앤다."""
    return re.sub(r"[\s「」ㆍ·]", "", s or "")


def _issues_upto(month):
    out = {}
    for name in sorted(os.listdir(DATA)):
        if re.fullmatch(r"\d{4}-\d{2}\.json", name) and name[:7] <= month:
            try:
                out[name[:7]] = json.load(io.open(os.path.join(DATA, name), encoding="utf-8"))
            except Exception:
                pass
    return out


def step_check(month, verbose=True):
    """발행 가능 여부를 판정한다. (차단사유, 경고, 참고) 반환."""
    block, warn, info = [], [], []
    path = os.path.join(DATA, "%s.json" % month)

    if not os.path.exists(path):
        block.append("data/%s.json 이 없습니다. 초안에서 항목을 골라 먼저 만드십시오." % month)
        return _report(month, block, warn, info, verbose)

    try:
        d = json.load(io.open(path, encoding="utf-8"))
    except Exception as e:
        block.append("data/%s.json 을 읽을 수 없습니다 — %s" % (month, e))
        return _report(month, block, warn, info, verbose)

    items = d.get("items", [])
    if not items:
        block.append("항목이 하나도 없습니다.")

    # 1) 메타 — 발행 시점 규칙
    if d.get("issue") != month:
        block.append("issue 가 파일명과 다릅니다 (%r != %r)" % (d.get("issue"), month))
    y, m = month.split("-")
    want_label = "%s년 %d월" % (y, int(m))
    if d.get("label") != want_label:
        warn.append("label 이 %r 입니다. 통상 %r 입니다." % (d.get("label"), want_label))
    pub = d.get("published", "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pub or ""):
        block.append("published 가 비었거나 형식이 아닙니다 (%r)" % pub)
    elif pub <= "%s-31" % month:
        warn.append("published(%s) 가 대상 월 안입니다. 첫째 화요일에 '직전 달' 호를 내는 "
                    "규칙이라면 다음 달 날짜여야 합니다." % pub)

    # 2) 필수 필드
    miss_core, miss_reason, bad_cat = [], [], []
    for i, it in enumerate(items):
        title = (it.get("title") or "").strip()
        for k in ("cat", "law", "title", "date", "summary"):
            if not (it.get(k) or "").strip():
                miss_core.append("items[%d] %s — %s 없음" % (i, title[:24] or "(제목없음)", k))
        if not (it.get("reason") or "").strip():
            miss_reason.append("items[%d] %s" % (i, title[:34]))
        if it.get("cat") not in CATS:
            bad_cat.append("items[%d] cat=%r" % (i, it.get("cat")))
    if miss_core:
        block += miss_core[:10]
        if len(miss_core) > 10:
            block.append("... 필수 필드 누락 %d건 더" % (len(miss_core) - 10))
    if bad_cat:
        block += bad_cat
    if miss_reason:
        # reason 은 원문 전재가 원칙(README 3 절) — 비어 있으면 발행하지 않는다
        block.append("reason 이 빈 항목 %d건: %s" % (len(miss_reason), " / ".join(miss_reason[:4])))

    # 3) 단계 커버리지
    by = {}
    for it in items:
        by[it.get("cat")] = by.get(it.get("cat"), 0) + 1
    empty = [s for s in STAGES if not by.get(s)]
    if empty:
        warn.append("0건인 단계: %s — '훑고 0건'인지 '못 훑음'인지 source 에 밝히십시오."
                    % " · ".join(empty))

    # 4) 수집 실패 기록 — 미수집을 0건으로 넘기는 것을 막는다
    ipath = os.path.join(INBOX, "%s_수집.json" % month)
    if os.path.exists(ipath):
        try:
            inbox = json.load(io.open(ipath, encoding="utf-8"))
            failed = inbox.get("failed") or []
            if failed:
                block.append("수집 단계 실패가 기록돼 있습니다: %s. 다시 수집하거나 "
                             "source 에 미수집 사실을 명시하십시오." % " · ".join(failed))
        except Exception:
            warn.append("수집 초안(%s)을 읽지 못했습니다." % os.path.basename(ipath))
    else:
        warn.append("수집 초안이 없습니다 (%s). 수집을 건너뛰었습니까?" % os.path.basename(ipath))

    # 5) source 에 감시목록 한계 표기
    src = d.get("source") or ""
    if not src.strip():
        block.append("source 가 비었습니다.")
    elif by.get("시행법령") or by.get("훈령예규고시"):
        if not re.search(r"전수|감시목록|명칭 기반|개별 조회", src):
            warn.append("시행법령·훈령예규고시는 감시목록 기반이라 전수가 아닙니다. "
                        "source 에 그 사실을 적으십시오.")

    # 6) billId — 다음 달 중복 재수집 방지
    #    위원장 대안은 열린국회정보 목록에 billId 없이 '원안 N건 대안반영폐기'로만 나오고
    #    의결일로 걸러져 다음 달에 다시 오지 않으므로 대상에서 뺀다.
    nobill = [it for it in items
              if it.get("cat") in ("의원발의", "국회통과") and not it.get("billId")
              and "대안" not in (it.get("title") or "")]
    if nobill:
        warn.append("billId 가 없는 의안 항목 %d건 — 다음 달 초안에 다시 올라옵니다."
                    % len(nobill))

    # 7) 화이트리스트 건강도 — 죽은 항목은 조용히 자료를 빠뜨린다
    fpath = os.path.join(DATA, "domain_filter.json")
    spath = os.path.join(DATA, "domain_filter_stats.json")
    if os.path.exists(fpath) and os.path.exists(spath):
        try:
            entries = json.load(io.open(fpath, encoding="utf-8"))["laws"]
            st = json.load(io.open(spath, encoding="utf-8"))
            counts, runs = st.get("counts") or {}, int(st.get("runs") or 0)
            zero = [e for e in entries if not counts.get(e["match"])]
            dead = [e["match"] for e in zero if not e.get("제명확인")]
            quiet = [e["match"] for e in zero if e.get("제명확인")]
            if quiet:
                info.append("제명 확인된 저빈도 항목 %d개는 이번에도 0회 (정상 — 개정이 드묾): %s"
                            % (len(quiet), " / ".join(quiet)))
            if dead and runs >= 3:
                warn.append("화이트리스트에서 %d회 실행 동안 한 번도 걸리지 않은 항목 %d개: %s "
                            "— 제명이 틀렸을 수 있습니다."
                            % (runs, len(dead), " / ".join(dead[:5])))
            elif dead:
                info.append("화이트리스트 미매칭 항목 %d개 (누적 %d회 실행 — 판단하기엔 이릅니다)"
                            % (len(dead), runs))
        except Exception:
            warn.append("domain_filter 통계를 읽지 못했습니다.")

    # 8) 예고 → 공포 후속 추적
    #    2026-08호에 「건축물관리법 시행령」 입법예고를 싣고 9.22. 공포·시행은 9월호·10월호
    #    모두 놓쳤다(2026-11-04 협회 PPT 대조로 발견). 예고 마감이 지났는데 같은 법령의
    #    시행·공포 항목이 그 뒤 어느 호에도 없으면 LawMCP 로 공포 여부를 확인하게 한다.
    #    같은 법령의 다른 개정이 실려도 '확인됨'으로 치는 느슨한 대조라 놓친 것만 잡는 용도다.
    issues = _issues_upto(month)
    shown = [(norm_law(it.get("law")), it.get("date") or "")
             for d2 in issues.values() for it in d2.get("items", [])
             if it.get("cat") in ("시행법령", "추가검토")]
    first = "%s-01" % month
    window = "%04d-%02d" % (int(y) - (1 if int(m) <= 6 else 0), (int(m) - 7) % 12 + 1)
    open_ = []
    for mon2, d2 in issues.items():
        if mon2 < window:
            continue
        for it in d2.get("items", []):
            if it.get("cat") != "입법예고":
                continue
            dl = it.get("deadline") or it.get("date") or ""
            if dl >= first:
                continue
            law = norm_law(it.get("law"))
            if not any(l == law and dd >= (it.get("date") or "") for l, dd in shown):
                open_.append("%s(%s호 예고, 마감 %s)" % (it.get("law"), mon2, dl))
    if open_:
        warn.append("예고 마감 후 공포·시행이 어느 호에도 없는 법령 %d건 — LawMCP 로 공포 여부를 "
                    "확인하십시오(미공포면 정상): %s" % (len(open_), " / ".join(open_)))

    # 9) 스냅샷 감시 범위 — 이번 호 법령이 law_snapshot.json 에 없으면 다음 개정을 못 본다
    #    (소방기본법이 감시목록 밖이라 2026.9.3. 시행을 놓쳤다)
    try:
        snap = json.load(io.open(os.path.join(DATA, "law_snapshot.json"), encoding="utf-8"))
        watched = {norm_law(n) for b in snap.get("batches", []) for n in b}
        unwatched = sorted({it.get("law") for it in items
                            if it.get("cat") in ("시행법령", "입법예고", "국회통과")
                            and norm_law(it.get("law")) not in watched})
        if unwatched:
            warn.append("law_snapshot.json 감시 밖 법령 %d개: %s — 발행 커밋 때 batches·snapshot 에 "
                        "법률·시행령·시행규칙 정확한 제명으로 추가하십시오(미시행 제정법은 시행 후)."
                        % (len(unwatched), " / ".join(unwatched)))
    except Exception:
        warn.append("law_snapshot.json 을 읽지 못했습니다.")

    # 10) 조문 번호 — 2026-11-04 검토에서 시행·예고 7건이 개정문의 조문(제61조제2항 재편,
    #     제19조의4 용어 변경, 별표 8~10 등)을 빠뜨리거나 절차를 뭉뚱그린 것이 지적됐다.
    #     제·개정이유만 보고 쓰면 생긴다. 개정문(조문안)을 열어 detail 에 조문 번호를 적게 한다.
    noart = [it.get("law") for it in items
             if it.get("cat") in ("시행법령", "입법예고", "행정예고")
             and not re.search(r"제\d+조|별표|별지|부칙",
                               " ".join(it.get("detail") or []) + " " + (it.get("summary") or ""))]
    if noart:
        warn.append("조문 번호(제N조·별표·부칙)가 summary·detail 어디에도 없는 항목 %d건: %s — "
                    "개정문·조문안을 열어 바뀐 조문을 적으십시오." % (len(noart), " / ".join(noart)))

    # 11) 참고 정보
    today = dt.date.today().isoformat()
    past = [it for it in items if it.get("deadline") and it["deadline"] < today]
    if past:
        info.append("마감이 지난 예고 %d건 — 사이트에는 '종료'로 표시됩니다." % len(past))
    info.append("구분별: " + " / ".join("%s %d" % (k, v) for k, v in sorted(by.items())))
    info.append("총 %d건" % len(items))

    return _report(month, block, warn, info, verbose)


# ── 빌드 ──────────────────────────────────────────────────────────────────
def step_build():
    print("\n[빌드]")
    return run([PY, os.path.join(HERE, "build.py")]).returncode == 0


# ── 커밋·푸시 ─────────────────────────────────────────────────────────────
def step_release(month, message, push):
    print("\n[변경 내용]")
    st = git("status", "--short")
    if not (st.stdout or "").strip():
        print("  변경 없음 — 커밋할 것이 없습니다.")
        return True
    print(st.stdout.rstrip())
    print(git("diff", "--stat").stdout.rstrip())

    msg = message or "%s호 발행" % month
    git("add", "-A")
    c = git("commit", "-m", msg)
    print("\n[커밋] %s" % (c.stdout or c.stderr).strip().splitlines()[0])

    if not push:
        print("  푸시하지 않았습니다. 올리려면 --push 또는 git push")
        return True
    p = git("push", "origin", "main")
    out = (p.stdout + p.stderr).strip()
    print("[푸시] %s" % (out.splitlines()[-1] if out else "완료"))
    if p.returncode != 0:
        print("  푸시 실패. 원격이 앞서 있으면 git pull 후 다시 시도하십시오.")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="MANMIN LEGAL REVIEW 발행 파이프라인")
    ap.add_argument("step", choices=["collect", "check", "build", "release", "ppt"])
    ap.add_argument("--month", default=None, help="대상 월 YYYY-MM (기본: 직전 달)")
    ap.add_argument("--pdf", default=None, help="ppt: 협회 법규교육 PPT 경로 (기본: 참고자료 폴더 최신)")
    ap.add_argument("--push", action="store_true", help="release 에서 푸시까지")
    ap.add_argument("-m", "--message", default=None, help="커밋 메시지")
    ap.add_argument("--force", action="store_true", help="점검 차단을 무시하고 진행")
    args = ap.parse_args()
    month = args.month or prev_month()

    if args.step == "collect":
        sys.exit(0 if step_collect(month) else 1)

    if args.step == "build":
        sys.exit(0 if step_build() else 1)

    if args.step == "ppt":
        import ppt_check
        pdf = args.pdf or ppt_check.latest_ppt()
        if not pdf or not os.path.exists(pdf):
            print("PPT 를 찾지 못했습니다: %r (--pdf 로 지정)" % pdf)
            sys.exit(2)
        rows = ppt_check.check(pdf)
        sys.exit(1 if any(r[5] == "누락?" for r in rows) else 0)

    block, warn, _ = step_check(month)

    if args.step == "check":
        sys.exit(1 if block else 0)

    # release
    if block and not args.force:
        print("\n발행을 중단했습니다. 위 [차단] 항목을 해결한 뒤 다시 실행하십시오.")
        print("정말 이대로 내야 한다면 --force 를 주십시오(권하지 않습니다).")
        sys.exit(1)
    if block:
        print("\n[경고] --force 로 차단을 무시하고 진행합니다.")
    if not step_build():
        sys.exit(1)
    sys.exit(0 if step_release(month, args.message, args.push) else 1)


if __name__ == "__main__":
    main()
