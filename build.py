# -*- coding: utf-8 -*-
"""
MANMIN LEGAL REVIEW — 정적 사이트 생성기
------------------------------------------------------------------
data/YYYY-MM.json 을 읽어 index.html 및 월별 HTML 을 생성한다.

사용법:
    python build.py

새 호(號) 추가:
    1) data/2026-08.json 파일 생성 (기존 파일 복사 후 수정)
    2) python build.py
    3) git add . && git commit -m "2026-08" && git push
"""

import json
import os
import re
import glob
import urllib.parse
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

SITE_TITLE = "MANMIN LEGAL REVIEW"
SITE_VER = "MANMIN VER-1.0"
SITE_SUB = "만민 법규 검토 요약"
AUTHOR = "김만민 건축사 · ㈜대성건축사사무소"
HOME = "https://manminkim-eng.github.io/KIMMANMIN/"
BLOG = "https://blog.naver.com/manmin72"
YOUTUBE = "https://www.youtube.com/@김만민-x8p"
# GitHub Pages 배포 경로 (전용 저장소 manmin-law — 포털 스코프와 분리해야 PWA 설치 가능)
CANON = "https://manminkim-eng.github.io/manmin-law/"

CATS = ["시행법령", "국회통과", "훈령예규고시", "입법예고", "행정예고", "의원발의", "추가검토"]
CAT_COLOR = {
    "시행법령": "#d4a843",
    "국회통과": "#e0645c",
    "훈령예규고시": "#b98ce0",
    "입법예고": "#4ea8de",
    "행정예고": "#6fc08a",
    "의원발의": "#f0a05a",
    "추가검토": "#8b98b3",
}


def law_link(name: str) -> str:
    """법제처 국가법령정보센터 원문 링크 생성."""
    if not name:
        return ""
    n = re.sub(r"\s+", "", name)
    n = n.replace("·", "ㆍ")
    return "https://www.law.go.kr/법령/" + urllib.parse.quote(n, safe="")


def law_search(name: str) -> str:
    """법령명 통합검색 링크 (제정안·법률안 등 원문 미등록 대비)."""
    return "https://www.law.go.kr/LSW/lsAstSc.do?menuId=390&query=" + urllib.parse.quote(name or "", safe="")


def bill_search(name: str) -> str:
    """국회 의안정보시스템 검색 링크."""
    return ("https://likms.assembly.go.kr/bill/BillSearchResult.do?billName="
            + urllib.parse.quote(name or "", safe=""))


# 법제처 법령 DB에 없는 자료 유형 → 별도 출처 링크
NON_LAW = {
    "KDS": ("국가건설기준센터", "https://www.kcsc.re.kr/StandardCode/Viewer/List"),
    "KCS": ("국가건설기준센터", "https://www.kcsc.re.kr/StandardCode/Viewer/List"),
    "표준시방서": ("국가건설기준센터", "https://www.kcsc.re.kr/StandardCode/Viewer/List"),
    "조달청": ("조달청 나라장터", "https://www.pps.go.kr"),
    "조례": ("자치법규정보시스템", "https://www.elis.go.kr"),
}


# 법제처 '행정규칙'(고시·훈령·예규)으로 등록된 자료 — 법령 경로가 아닌 행정규칙 경로 사용
ADMIN_RULES = {
    "건축물의 에너지절약설계기준",
    "실내건축의 구조·시공방법 등에 관한 기준",
    "건축자재 등 품질인정 및 관리기준",
    "에너지절약형 친환경주택의 건설기준",
    "건축 설계공모 운영지침",
    "다중생활시설 건축기준",
    "녹색건축 인증 기준",
    "위험물안전관리에 관한 세부기준",
    "소화약제의 형식승인 및 제품검사의 기술기준",
    "국가 소방용품 인증 심의위원회 운영 규정",
    "건축공사 감리세부기준",
    "건축구조기준",
}


def rule_link(name: str) -> str:
    n = re.sub(r"\s+", "", name).replace("·", "ㆍ")
    return "https://www.law.go.kr/행정규칙/" + urllib.parse.quote(n, safe="")


def resolve_links(it):
    """항목별 1차/2차 원문 링크 결정."""
    law = it.get("law", "")
    cat = it.get("cat", "")

    if it.get("link"):
        it["primary"] = (it.get("linkLabel", "원문 ↗"), it["link"])
    else:
        hit = next((v for k, v in NON_LAW.items() if k in law), None)
        if law in ADMIN_RULES:
            it["primary"] = ("법제처 행정규칙 ↗", rule_link(law))
        elif hit:
            it["primary"] = (hit[0] + " ↗", hit[1])
        else:
            it["primary"] = ("법제처 원문 ↗", law_link(law))

    if cat in ("의원발의", "국회통과"):
        it["secondary"] = ("의안정보시스템 ↗", bill_search(law))
    elif it.get("deadline"):
        it["secondary"] = ("국민참여입법센터 ↗", "https://opinion.lawmaking.go.kr/gcom/govLm")
    else:
        it["secondary"] = ("법령 검색 ↗", law_search(law))
    return it


def load_issues():
    """data/ 폴더의 YYYY-MM.json 로드 (경로에 [ ] 등 특수문자가 있어도 안전하도록 listdir 사용)."""
    issues = []
    names = sorted((n for n in os.listdir(DATA)
                    if re.fullmatch(r"\d{4}-\d{2}\.json", n)), reverse=True)
    for name in names:
        with open(os.path.join(DATA, name), encoding="utf-8") as fp:
            d = json.load(fp)
        for it in d["items"]:
            resolve_links(it)
        issues.append(d)
    return issues


# ──────────────────────────────────────────────────────────────
# 공통 CSS / JS
# ──────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
 --bg:#0c1120; --panel:#131b2c; --panel2:#182134; --line:#26314a;
 --gold:#d4a843; --txt:#e8edf7; --muted:#8b98b3; --danger:#e0645c;
}
html[data-theme="light"]{
 --bg:#f4f6fa; --panel:#ffffff; --panel2:#f0f3f8; --line:#dbe1ec;
 --gold:#a67c1f; --txt:#151b28; --muted:#5c6883;
}
body{background:var(--bg);color:var(--txt);
 font-family:'Pretendard','Malgun Gothic','맑은 고딕',-apple-system,BlinkMacSystemFont,sans-serif;
 line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}

/* HEADER */
header{border-bottom:1px solid var(--line);background:linear-gradient(180deg,rgba(212,168,67,.07),transparent);
 position:sticky;top:0;z-index:50;backdrop-filter:blur(12px);background-color:var(--bg)}
.hd{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 0;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.markchip{flex:none;height:46px;width:auto;border-radius:10px;overflow:hidden;
 display:flex;align-items:center;justify-content:center;padding:4px 8px;
 background:#f0ead9;border:1.5px solid rgba(212,168,67,.55);
 box-shadow:0 1px 6px rgba(0,0,0,.25)}
.brandmark{height:100%;width:auto;max-width:none;object-fit:contain;display:block}
html[data-theme="light"] .markchip{border-color:rgba(43,58,103,.35);box-shadow:none}
.btn.install{display:none;background:var(--gold);color:#0c1120;border-color:var(--gold);
 font-weight:800;align-items:center;gap:6px;padding:6px 12px 6px 8px}
.btn.install:hover{filter:brightness(1.08);color:#0c1120}
.btn.install.on{display:inline-flex}
.btn.install img{height:19px;width:19px;object-fit:contain;display:block;
 filter:brightness(0) saturate(100%)}
.btn.install span{line-height:1}
.iosgd{position:fixed;left:12px;right:12px;bottom:12px;z-index:150;background:var(--panel);
 border:1px solid var(--gold);border-radius:13px;padding:15px 17px;display:none;
 box-shadow:0 10px 36px rgba(0,0,0,.45)}
.iosgd.on{display:block}
.iosgd b{color:var(--gold);font-size:13px;display:block;margin-bottom:7px}
.iosgd p{font-size:13px;color:var(--txt);line-height:1.7}
.iosgd .x2{position:absolute;top:11px;right:13px;color:var(--muted);cursor:pointer;font-size:15px}
.ver{font-size:10px;font-weight:800;letter-spacing:.09em;color:#0c1120;
 background:var(--gold);padding:3px 8px;border-radius:5px;white-space:nowrap;align-self:center}
.brand b{font-size:19px;letter-spacing:.11em;color:var(--gold);font-weight:800}
.brand span{font-size:12.5px;color:var(--muted);letter-spacing:.02em}
.hdbtns{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.btn{border:1px solid var(--line);background:var(--panel);color:var(--txt);
 padding:7px 12px;border-radius:8px;font-size:12.5px;cursor:pointer;transition:.15s;white-space:nowrap}
.btn:hover{border-color:var(--gold);color:var(--gold)}
.btn.gold{background:var(--gold);color:#0c1120;border-color:var(--gold);font-weight:700}
.btn.gold:hover{filter:brightness(1.1);color:#0c1120}
select.btn{appearance:none;padding-right:26px;
 background-image:linear-gradient(45deg,transparent 50%,var(--muted) 50%),linear-gradient(135deg,var(--muted) 50%,transparent 50%);
 background-position:calc(100% - 14px) 50%,calc(100% - 9px) 50%;background-size:5px 5px,5px 5px;background-repeat:no-repeat}

/* HERO */
.hero{padding:34px 0 22px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:11.5px;letter-spacing:.22em;color:var(--gold);font-weight:700;margin-bottom:9px}
h1{font-size:clamp(22px,4vw,33px);font-weight:800;letter-spacing:-.02em;line-height:1.3}
.lead{color:var(--muted);margin-top:11px;font-size:14.5px;max-width:860px}
.meta{display:flex;gap:16px;flex-wrap:wrap;margin-top:15px;font-size:12px;color:var(--muted)}
.meta b{color:var(--txt);font-weight:600}

/* STATS */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:9px;margin:20px 0 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:11px 13px}
.stat i{display:block;font-style:normal;font-size:10.5px;color:var(--muted);letter-spacing:.05em}
.stat b{display:block;font-size:20px;font-weight:800;margin-top:3px}

/* TOOLBAR */
.toolbar{position:sticky;top:59px;z-index:40;background:var(--bg);
 padding:15px 0 11px;border-bottom:1px solid var(--line)}
.searchbox{position:relative;margin-bottom:11px}
.searchbox input{width:100%;padding:11px 40px 11px 14px;border-radius:10px;
 border:1px solid var(--line);background:var(--panel);color:var(--txt);font-size:14px;outline:none;font-family:inherit}
.searchbox input:focus{border-color:var(--gold)}
.searchbox .x{position:absolute;right:11px;top:50%;transform:translateY(-50%);
 color:var(--muted);cursor:pointer;font-size:16px;display:none}
.chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.chips .lb{font-size:11px;color:var(--muted);margin-right:3px;letter-spacing:.05em}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--muted);
 padding:5px 11px;border-radius:99px;font-size:12px;cursor:pointer;transition:.15s;user-select:none}
.chip:hover{color:var(--txt)}
.chip.on{background:var(--gold);color:#0c1120;border-color:var(--gold);font-weight:700}
.chip .n{opacity:.65;font-size:10.5px;margin-left:3px}
.hint{font-size:11.5px;color:var(--muted);margin-top:9px}

/* CARD */
.list{padding:22px 0 40px;display:flex;flex-direction:column;gap:13px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:13px;
 padding:17px 19px;border-left:4px solid var(--cc,var(--gold));transition:.18s;scroll-margin-top:150px}
.card:hover{border-color:var(--line);box-shadow:0 5px 22px rgba(0,0,0,.22)}
.card.hi{box-shadow:0 0 0 2px var(--gold)}
.ctop{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:9px}
.tag{font-size:10.5px;font-weight:800;padding:3px 9px;border-radius:5px;letter-spacing:.03em;
 background:var(--cc);color:#0c1120}
.field{font-size:10.5px;color:var(--muted);border:1px solid var(--line);padding:2px 7px;border-radius:5px}
.dday{font-size:10.5px;font-weight:800;padding:3px 9px;border-radius:5px;
 background:rgba(224,100,92,.14);color:var(--danger);border:1px solid rgba(224,100,92,.35)}
.dday.soft{background:rgba(139,152,179,.12);color:var(--muted);border-color:var(--line)}
.dday.ok{background:rgba(111,192,138,.13);color:#6fc08a;border-color:rgba(111,192,138,.33)}
.ctop .sp{flex:1}
.anchor{font-size:11px;color:var(--muted);cursor:pointer;opacity:.6}
.anchor:hover{opacity:1;color:var(--gold)}
h3.ct{font-size:16.5px;font-weight:750;letter-spacing:-.01em;line-height:1.45}
.lawrow{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin:7px 0 9px;font-size:12.5px;color:var(--muted)}
.lawrow a{color:var(--gold);border-bottom:1px dotted rgba(212,168,67,.5);padding-bottom:1px}
.lawrow a:hover{border-bottom-style:solid}
.sum{font-size:14px;color:var(--txt);opacity:.93}
details{margin-top:11px}
summary{cursor:pointer;font-size:12.5px;color:var(--gold);list-style:none;
 display:inline-flex;align-items:center;gap:5px;user-select:none;font-weight:600}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸";transition:.15s;display:inline-block}
details[open] summary::before{transform:rotate(90deg)}
.det{margin-top:10px;background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:13px 15px}
.det ul{list-style:none;display:flex;flex-direction:column;gap:7px}
.det li{font-size:13px;padding-left:14px;position:relative;color:var(--txt);opacity:.9}
.det li::before{content:"";position:absolute;left:0;top:8px;width:5px;height:5px;
 border-radius:99px;background:var(--cc);opacity:.75}
.impact{margin-top:11px;padding:10px 13px;border-radius:8px;font-size:12.8px;
 background:rgba(212,168,67,.08);border:1px solid rgba(212,168,67,.25)}
.impact b{color:var(--gold);font-size:10.5px;letter-spacing:.09em;display:block;margin-bottom:4px}
.reason{margin-top:10px;padding:11px 14px;border-radius:8px;font-size:13.2px;
 background:var(--panel2);border:1px solid var(--line);line-height:1.7}
.reason b{color:var(--cc);font-size:10.5px;letter-spacing:.09em;display:block;margin-bottom:5px}
.cmp{width:100%;border-collapse:collapse;font-size:12.3px;margin-top:8px}
.cmp th{background:var(--panel);border:1px solid var(--line);padding:6px 9px;
 font-size:10.8px;letter-spacing:.07em;color:var(--muted);font-weight:700;text-align:left}
.cmp th.new{color:var(--gold)}
.cmp td{border:1px solid var(--line);padding:7px 10px;vertical-align:top;line-height:1.6;width:44%}
.cmp td.art{width:12%;font-weight:700;font-size:11.5px;color:var(--cc);
 background:var(--panel);white-space:nowrap}
.cmp td.new{background:rgba(212,168,67,.05)}
.cmplink{margin-top:8px;font-size:12px;color:var(--muted)}
.cmplink a{color:var(--gold);border-bottom:1px dotted rgba(212,168,67,.5);margin-left:8px}
.empty{text-align:center;padding:56px 20px;color:var(--muted);font-size:14px}

/* ARCHIVE */
.sec{padding:34px 0;border-top:1px solid var(--line)}
.sech{font-size:11.5px;letter-spacing:.2em;color:var(--gold);font-weight:700;margin-bottom:15px}
.arch{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:11px}
.acard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;
 display:block;transition:.18s}
.acard:hover{border-color:var(--gold);transform:translateY(-2px)}
.acard i{font-style:normal;font-size:10.5px;letter-spacing:.14em;color:var(--gold);font-weight:700}
.acard b{display:block;font-size:17px;margin:5px 0 7px;font-weight:750}
.acard p{font-size:12.3px;color:var(--muted);line-height:1.55}
.acard .cnt{margin-top:9px;font-size:11px;color:var(--muted);border-top:1px solid var(--line);padding-top:8px}

/* MODAL */
.mask{position:fixed;inset:0;background:rgba(4,7,14,.78);z-index:100;display:none;
 align-items:center;justify-content:center;padding:20px}
.mask.on{display:flex}
.modal{background:var(--panel);border:1px solid var(--line);border-radius:14px;
 max-width:760px;width:100%;max-height:86vh;display:flex;flex-direction:column}
.mh{padding:15px 19px;border-bottom:1px solid var(--line);display:flex;
 align-items:center;justify-content:space-between;gap:10px}
.mh b{font-size:14.5px}
.mtabs{display:flex;gap:6px;padding:11px 19px 0}
.mbody{padding:13px 19px 19px;overflow:auto;flex:1}
.mbody textarea{width:100%;min-height:340px;background:var(--bg);color:var(--txt);
 border:1px solid var(--line);border-radius:9px;padding:13px;font-size:12.5px;
 line-height:1.75;font-family:'D2Coding','Consolas',monospace;resize:vertical;outline:none}
.mfoot{padding:12px 19px;border-top:1px solid var(--line);display:flex;gap:8px;justify-content:flex-end}

/* TOAST */
.toast{position:fixed;left:50%;bottom:30px;transform:translateX(-50%) translateY(20px);
 background:var(--gold);color:#0c1120;padding:11px 20px;border-radius:9px;font-size:13px;
 font-weight:700;z-index:200;opacity:0;pointer-events:none;transition:.25s}
.toast.on{opacity:1;transform:translateX(-50%) translateY(0)}

/* FOOTER */
footer{border-top:1px solid var(--line);padding:26px 0 40px;font-size:12px;color:var(--muted)}
footer .fl{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:11px}
footer a:hover{color:var(--gold)}
.disc{font-size:11.3px;line-height:1.7;opacity:.8}

/* TOP */
#top{position:fixed;right:20px;bottom:22px;width:42px;height:42px;border-radius:99px;
 background:var(--panel);border:1px solid var(--line);color:var(--gold);cursor:pointer;
 display:none;align-items:center;justify-content:center;font-size:16px;z-index:60}
#top.on{display:flex}

*{-webkit-tap-highlight-color:transparent}
@media(max-width:640px){
 .toolbar{top:0;position:relative}
 header{position:relative}
 .card{padding:15px 14px}
 .hd{gap:9px;padding:11px 0}
 .brand span:not(.ver):not(.markchip){display:none}
 .markchip{height:38px;width:auto;border-radius:8px;padding:3px 6px}
 .brandmark{height:100%;width:auto}
 .brand b{font-size:15.5px}
 .ver{font-size:9px;padding:2px 6px}
 .btn.install{padding:7px 9px}
 .btn.install span{display:none}
 .btn.install img{height:21px;width:21px}
 .searchbox input{font-size:16px;padding:12px 40px 12px 14px}
 .btn{padding:9px 13px;font-size:13px}
 .chip{padding:7px 12px;font-size:12.5px}
 h3.ct{font-size:15.5px}
 .sum{font-size:13.5px}
 .lawrow{font-size:12px;gap:7px}
 .det{overflow-x:auto;-webkit-overflow-scrolling:touch;padding:11px 12px}
 .cmp{min-width:540px}
 .stats{grid-template-columns:repeat(auto-fit,minmax(92px,1fr))}
 .arch{grid-template-columns:1fr}
 .meta{gap:10px;font-size:11.5px}
 .mbody textarea{min-height:240px;font-size:12px}
 .modal{max-height:92vh}
 #top{right:14px;bottom:16px}
}
@media(max-width:400px){
 .hdbtns .btn:not(select){padding:8px 10px;font-size:12px}
 h1{font-size:20px}
}

/* PRINT — A4 */
@media print{
 @page{size:A4;margin:14mm 12mm}
 html,body{background:#fff!important;color:#000!important;font-size:10pt}
 :root{--txt:#000;--muted:#444;--line:#bbb;--panel:#fff;--panel2:#f7f7f7;--gold:#8a6a12}
 header,.toolbar,.hdbtns,#top,.mask,.anchor,summary,.sec.noprint,footer .fl{display:none!important}
 details{display:block!important}
 details>summary{display:none!important}
 .det{background:#f7f7f7!important;border:1px solid #ccc!important;page-break-inside:avoid}
 .card{page-break-inside:avoid;border:1px solid #ccc!important;border-left:3px solid #888!important;
  box-shadow:none!important;margin-bottom:6mm;padding:4mm 5mm}
 .hero{border-bottom:1.5px solid #000;padding:0 0 5mm}
 h1{font-size:16pt}
 .tag{background:#eee!important;color:#000!important;border:1px solid #999}
 .impact{background:#fbf7ec!important;border:1px solid #d8c68e!important}
 a{color:#000!important;border:none!important}
 a[href^="http"]::after{content:" (" attr(href) ")";font-size:7pt;color:#666;word-break:break-all}
 .wrap{max-width:none;padding:0}
 .list{gap:0}
}
"""

JS = r"""
/* ── PWA 설치 ── */
if('serviceWorker' in navigator){
  window.addEventListener('load',function(){
    navigator.serviceWorker.register('sw.js').catch(function(){});
  });
  /* 새 SW 가 활성화되면 1회만 자동 새로고침 — 아이콘·본문 교체가 즉시 반영된다 */
  var _swReloaded=false;
  navigator.serviceWorker.addEventListener('controllerchange',function(){
    if(_swReloaded)return; _swReloaded=true; location.reload();
  });
}
function isStandalone(){
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.matchMedia('(display-mode: minimal-ui)').matches ||
         navigator.standalone===true;
}
function envInfo(){
  var ua=navigator.userAgent;
  return {
    ios: /iPad|iPhone|iPod/.test(ua) && !window.MSStream,
    android: /Android/.test(ua),
    samsung: /SamsungBrowser/.test(ua),
    firefox: /Firefox/.test(ua),
    naver: /NAVER\(inapp/.test(ua) || /whale/i.test(ua),
    kakao: /KAKAOTALK/i.test(ua),
    mobile: /Mobi|Android|iPhone|iPad/.test(ua)
  };
}
/* 이미 설치된 앱인지 감지 — manifest 의 related_applications(webapp) 선언 기반 */
window.__alreadyInstalled=false;
function detectInstalled(){
  if(!navigator.getInstalledRelatedApps) return Promise.resolve(false);
  return navigator.getInstalledRelatedApps()
    .then(function(l){ return !!(l && l.length); })
    .catch(function(){ return false; });
}
/* 설치되지 않았으면 버튼을 항상 노출 — 프롬프트가 없어도 수동 안내로 대응 */
function syncInstallBtn(){
  var b=document.getElementById('btnInstall'); if(!b)return;
  if(isStandalone()||window.__installed){ b.classList.remove('on'); return; }
  b.classList.add('on');
  var s=b.querySelector('span');
  if(window.__alreadyInstalled){
    b.title='이미 설치되어 있습니다 — 설치된 앱을 여는 방법 안내';
    if(s)s.textContent='앱으로 열기';
  }else{
    b.title='앱으로 설치 — 주소창 없는 독립 창으로 열립니다';
    if(s)s.textContent='웹에 추가';
  }
}
window.addEventListener('load',function(){
  detectInstalled().then(function(v){ window.__alreadyInstalled=v; syncInstallBtn(); });
});
window.addEventListener('bip-ready', syncInstallBtn);
window.addEventListener('appinstalled', function(){
  syncInstallBtn(); closeGuide(); toast('홈 화면에 설치되었습니다');
});

function firePrompt(){
  window.__bip.prompt();
  window.__bip.userChoice.then(function(c){
    window.__bip=null;
    if(c.outcome==='accepted'){ window.__installed=true; syncInstallBtn(); }
    else { toast('설치를 취소했습니다 — 다시 누르면 안내가 열립니다'); }
  });
}
/* 프롬프트가 늦게 도착하는 경우가 있어 즉시 안내로 넘기지 않고 최대 2초 기다린다 */
function installApp(){
  if(window.__bip){ firePrompt(); return; }
  if(window.__alreadyInstalled){ openGuide(); return; }
  var b=document.getElementById('btnInstall'), done=false;
  var fin=function(){
    if(done)return; done=true;
    window.removeEventListener('bip-ready',on);
    if(b)b.style.opacity='';
    if(window.__bip) firePrompt(); else openGuide();
  };
  var on=function(){ fin(); };
  window.addEventListener('bip-ready',on);
  if(b)b.style.opacity='.6';
  setTimeout(fin,2000);
}
function openGuide(){
  var e=envInfo(), t='', h='';
  if(e.kakao || e.naver){
    h='먼저 기본 브라우저로 열어주세요';
    t='<b>카카오톡·네이버 앱 내부 화면에서는 설치할 수 없습니다.</b><br><br>' +
      '우측 상단 <b>⋮ 또는 ⋯</b> → <b>“다른 브라우저로 열기”</b>(또는 Chrome·Safari로 열기)를 선택한 뒤 다시 설치를 눌러 주세요.';
  } else if(e.ios){
    h='iPhone · iPad 에서 설치하기';
    t='① 화면 하단(또는 상단)의 <b>공유 버튼 [ ⬆ ]</b> 을 누릅니다.<br>' +
      '② 목록을 내려 <b>“홈 화면에 추가”</b> 를 선택합니다.<br>' +
      '③ 우측 상단 <b>“추가”</b> 를 누르면 완료됩니다.<br><br>' +
      '<span style="color:var(--muted)">※ iOS 는 이 방식이 곧 앱 설치입니다. 홈 화면 아이콘을 누르면 주소창 없이 앱처럼 열립니다.</span><br>' +
      '<span style="color:var(--muted)">※ 사파리(Safari)에서만 가능합니다. 크롬에서는 지원되지 않습니다.</span>';
  } else if(e.samsung){
    h='삼성 인터넷 — 앱으로 설치';
    t='① 하단 <b>메뉴(≡)</b> 를 누릅니다.<br>' +
      '② <b>“현재 페이지 추가”</b> → <b>“홈 화면”</b> 을 선택합니다.<br><br>' +
      '<span style="color:var(--muted)">※ 삼성 인터넷은 이 경로로 앱 형태(WebAPK)로 설치됩니다. ' +
      '더 확실하게 하시려면 <b>Chrome</b> 으로 접속해 주세요.</span>';
  } else if(e.android){
    h='Android — 앱으로 설치하기';
    t='① 우측 상단 <b>⋮</b> 메뉴를 누릅니다.<br>' +
      '② <b>“앱 설치”</b> 를 선택합니다. <span style="color:var(--muted)">(설치형 앱)</span><br><br>' +
      '<span style="color:var(--muted)">※ “앱 설치”가 안 보이고 <b>“홈 화면에 추가”</b>만 있다면 단순 바로가기입니다. ' +
      '페이지를 새로고침하고 10초쯤 머문 뒤 다시 열어 보시면 “앱 설치”로 바뀝니다.</span>';
  } else if(e.firefox){
    h='Firefox 에서 설치하기';
    t='Firefox 데스크톱은 앱 설치를 지원하지 않습니다.<br>' +
      '<b>Chrome · Edge</b> 로 접속하시거나, 이 페이지를 <b>즐겨찾기(Ctrl+D)</b> 에 추가해 주세요.';
  } else {
    h='PC — 앱으로 설치하기';
    t='① 주소창 오른쪽의 <b>설치 아이콘 [ ⊕ ]</b> 또는 모니터 모양 아이콘을 누릅니다.<br>' +
      '② 아이콘이 없으면 <b>⋮ 메뉴 → 캐스트·저장 및 공유 → 페이지를 앱으로 설치</b> 를 선택합니다.<br><br>' +
      '<span style="color:var(--muted)">※ 설치하면 주소창 없는 독립 창으로 열리고 시작 메뉴·작업표시줄에 등록됩니다. ' +
      'Chrome 또는 Edge 에서 지원됩니다.</span>';
  }
  if(window.__alreadyInstalled){
    h='이미 설치되어 있습니다';
    t='이 사이트는 이 기기에 <b>이미 앱으로 설치</b>되어 있어 설치창이 다시 뜨지 않습니다.<br>' +
      '시작 메뉴 · 작업표시줄(휴대폰은 홈 화면)에서 <b>만민법규</b> 아이콘을 실행하세요.<br><br>' +
      '<span style="color:var(--muted)">※ 아이콘 그림이 예전 것이라면 앱을 <b>삭제 후 재설치</b>해야 새 아이콘이 적용됩니다. ' +
      'Android WebAPK · iOS 홈화면 아이콘은 설치 시점의 이미지를 그대로 보관합니다.</span>';
  } else if(!window.__bip && !e.ios && !e.kakao && !e.naver){
    t += '<br><br><b style="color:var(--gold)">설치창이 안 뜨나요?</b><br>' +
      '① 이전에 <b>“설치 안 함”</b> 을 누르면 Chrome 이 한동안 설치창을 다시 띄우지 않습니다.<br>' +
      '② 주소창 왼쪽 <b>🔒 → 사이트 설정 → 권한 재설정</b> 후 새로고침하면 복구됩니다.<br>' +
      '③ <b>chrome://apps</b> 에 이미 설치본이 있으면 삭제한 뒤 다시 시도하세요.<br>' +
      '④ 현재 상태를 확인하려면 주소 끝에 <b>?diag=1</b> 을 붙여 접속하세요.';
  }
  document.getElementById('gdTitle').innerHTML=h;
  document.getElementById('gdBody').innerHTML=t;
  document.getElementById('iosgd').classList.add('on');
}
function closeGuide(){var g=document.getElementById('iosgd'); if(g)g.classList.remove('on');}

/* ── 설치 진단 — 주소 끝에 ?diag=1 ── */
function installDiag(){
  var m=document.querySelector('link[rel=manifest]'), out=[];
  var push=function(k,v,ok){
    out.push('<tr><td style="padding:3px 12px 3px 0;color:var(--muted);white-space:nowrap">'+k+
      '</td><td><b style="color:'+(ok?'#5fbf7a':'var(--danger)')+'">'+v+'</b></td></tr>');
  };
  var swOn=!!(navigator.serviceWorker && navigator.serviceWorker.controller);
  push('HTTPS', isSecureContext?'OK':'실패', isSecureContext);
  push('manifest 링크', m?'OK':'없음', !!m);
  push('Service Worker', swOn?'제어중':'미제어', swOn);
  push('설치 프롬프트', window.__bip?'수신됨':'미수신', !!window.__bip);
  push('이미 설치됨', window.__alreadyInstalled?'예':'아니오', !window.__alreadyInstalled);
  push('독립창 실행', isStandalone()?'예':'아니오', true);
  var job = m ? fetch(m.href).then(function(r){return r.json()}).then(function(j){
      return Promise.all((j.icons||[]).map(function(i){
        return fetch(new URL(i.src,m.href).href,{cache:'reload'})
          .then(function(r){ push('아이콘 '+i.sizes+' · '+(i.purpose||'any'), r.status, r.ok); })
          .catch(function(){ push('아이콘 '+i.sizes, '요청 실패', false); });
      }));
    }).catch(function(){}) : Promise.resolve();
  job.then(function(){
    document.getElementById('gdTitle').innerHTML='PWA 설치 진단';
    document.getElementById('gdBody').innerHTML='<table style="font-size:12.5px">'+out.join('')+'</table>' +
      '<div style="margin-top:10px;color:var(--muted);font-size:11.5px;line-height:1.6">' +
      '“설치 프롬프트 · 미수신” 인데 나머지가 모두 OK 라면 → 이미 설치되었거나, 이전에 설치를 취소해 ' +
      'Chrome 이 프롬프트를 억제하는 중입니다. 사이트 권한 재설정 또는 기존 설치본 삭제 후 재시도하세요.</div>';
    document.getElementById('iosgd').classList.add('on');
  });
}
if(/[?&]diag=1/.test(location.search)){
  window.addEventListener('load',function(){ setTimeout(installDiag,1500); });
}

/* ── 테마 ── */
(function(){var t=localStorage.getItem('mlr-theme');if(t)document.documentElement.dataset.theme=t;})();
function toggleTheme(){var h=document.documentElement;
 var n=h.dataset.theme==='light'?'dark':'light';h.dataset.theme=n;localStorage.setItem('mlr-theme',n);}

/* ── 토스트 ── */
var _tt;
function toast(m){var e=document.getElementById('toast');e.textContent=m;e.classList.add('on');
 clearTimeout(_tt);_tt=setTimeout(function(){e.classList.remove('on')},1900);}

/* ── 복사 ── */
function copyText(t,msg){
 if(navigator.clipboard&&window.isSecureContext){
   navigator.clipboard.writeText(t).then(function(){toast(msg||'복사되었습니다')});
 }else{
   var a=document.createElement('textarea');a.value=t;a.style.position='fixed';a.style.left='-9999px';
   document.body.appendChild(a);a.select();try{document.execCommand('copy');toast(msg||'복사되었습니다')}
   catch(e){toast('복사 실패')}document.body.removeChild(a);
 }}

/* ── 공유 ── */
function share(title){
 var u=location.href;
 if(navigator.share){navigator.share({title:title,url:u}).catch(function(){});}
 else copyText(u,'링크가 복사되었습니다');
}
function copyAnchor(id){
 copyText(location.origin+location.pathname+'#'+id,'항목 링크가 복사되었습니다');
 location.hash=id;
}

/* ── D-day ── */
function dday(iso){
 if(!iso)return null;
 var t=new Date();t.setHours(0,0,0,0);
 var d=new Date(iso+'T00:00:00');
 return Math.round((d-t)/86400000);
}
function paintDday(){
 document.querySelectorAll('[data-dl]').forEach(function(el){
   var n=dday(el.dataset.dl),kind=el.dataset.kind||'예고';
   if(n===null)return;
   if(n<0){el.textContent=kind+' 종료';el.className='dday soft';}
   else if(n===0){el.textContent=kind+' 마감 D-DAY';el.className='dday';}
   else if(n<=10){el.textContent=kind+' 마감 D-'+n;el.className='dday';}
   else {el.textContent=kind+' 마감 D-'+n;el.className='dday soft';}
 });
 document.querySelectorAll('[data-ef]').forEach(function(el){
   var n=dday(el.dataset.ef);
   if(n===null)return;
   if(n>0){el.textContent='시행 D-'+n;el.className='dday ok';}
   else {el.style.display='none';}
 });
}

/* ── 필터 ── */
var F={q:'',cat:'ALL',field:'ALL'};
function applyFilter(){
 var q=F.q.trim().toLowerCase(), n=0;
 document.querySelectorAll('.card').forEach(function(c){
  var okc = F.cat==='ALL' || c.dataset.cat===F.cat;
  var okf = F.field==='ALL' || (c.dataset.field||'').split('|').indexOf(F.field)>=0;
  var okq = !q || (c.dataset.s||'').indexOf(q)>=0;
  var show = okc&&okf&&okq;
  c.style.display = show?'':'none';
  if(show)n++;
 });
 document.getElementById('cnt').textContent=n;
 document.getElementById('empty').style.display = n?'none':'block';
 document.querySelector('.searchbox .x').style.display = F.q?'block':'none';
}
function setChip(g,v,el){
 F[g]=v;
 document.querySelectorAll('.chip[data-g="'+g+'"]').forEach(function(e){e.classList.remove('on')});
 el.classList.add('on');applyFilter();
}
function clearQ(){document.getElementById('q').value='';F.q='';applyFilter();}

/* ── 전체 펼침/접기 ── */
var _open=false;
function toggleAll(){
 _open=!_open;
 document.querySelectorAll('details').forEach(function(d){d.open=_open});
 document.getElementById('bAll').textContent=_open?'전체 접기':'전체 펼치기';
}

/* ── 텍스트 추출 ── */
function buildText(mode){
 var meta=window.__META__, lines=[];
 var vis=[].slice.call(document.querySelectorAll('.card')).filter(function(c){return c.style.display!=='none'});
 if(mode==='blog'){
  lines.push('['+meta.label+' 법규 검토 요약] '+meta.headline);
  lines.push('');
  lines.push('건축사 김만민입니다. '+meta.label+' 건축·설비·소방 분야 법령 개정사항을 정리했습니다.');
  lines.push('');
  var cur='';
  vis.forEach(function(c,i){
   if(c.dataset.cat!==cur){cur=c.dataset.cat;lines.push('');lines.push('■ '+cur);lines.push('');}
   lines.push('▶ '+c.dataset.title);
   lines.push('   · 근거법령 : '+c.dataset.law);
   lines.push('   · '+c.dataset.dlabel+' : '+c.dataset.date.replace(/-/g,'.')+'.');
   lines.push('   · '+c.dataset.sum);
   if(c.dataset.reason)lines.push('   · 제안이유·주요내용 : '+c.dataset.reason);
   var d=c.dataset.detail?JSON.parse(c.dataset.detail):[];
   d.forEach(function(x){lines.push('     - '+x)});
   if(c.dataset.impact)lines.push('     ※ 실무영향 : '+c.dataset.impact);
   lines.push('');
  });
  lines.push('──────────────');
  lines.push('전체 요약본 보기 : '+location.href);
  lines.push('MANMIN 엔지니어링 계산도구 : '+meta.home);
  lines.push('#건축법규 #법규개정 #건축사 #'+meta.label.replace(/\s/g,'')+' #만민법규검토요약');
 } else {
  lines.push('['+meta.label+' 법규 검토 요약 — 유튜브 대본 초안]');
  lines.push('');
  lines.push('(오프닝)');
  lines.push('안녕하세요, 건축사 김만민입니다.');
  lines.push('오늘은 '+meta.label+'에 나온 건축 관련 법규 개정사항 '+vis.length+'건을 정리해 드리겠습니다.');
  lines.push('핵심만 말씀드리면 — '+meta.headline+' 입니다.');
  lines.push('');
  vis.forEach(function(c,i){
   lines.push('── '+(i+1)+'. '+c.dataset.title+' ['+c.dataset.cat+'] ──');
   lines.push('근거는 '+c.dataset.law+'이고, '+c.dataset.dlabel+'은 '+c.dataset.date.replace(/-/g,'.')+'입니다.');
   lines.push(c.dataset.sum);
   var d=c.dataset.detail?JSON.parse(c.dataset.detail):[];
   if(d.length){lines.push('세부 내용은 이렇습니다.');d.forEach(function(x){lines.push('  · '+x)});}
   if(c.dataset.impact)lines.push('실무에서는요, '+c.dataset.impact);
   lines.push('');
  });
  lines.push('(클로징)');
  lines.push('오늘 정리한 내용은 설명란 링크에서 원문과 함께 확인하실 수 있습니다.');
  lines.push('도움이 되셨다면 구독과 좋아요 부탁드립니다. 감사합니다.');
 }
 return lines.join('\n');
}
function openText(mode){
 document.getElementById('mask').classList.add('on');
 setMode(mode);
}
function setMode(mode){
 document.getElementById('ta').value=buildText(mode);
 document.querySelectorAll('#mtabs .chip').forEach(function(e){
   e.classList.toggle('on', e.dataset.m===mode)});
}
function closeModal(){document.getElementById('mask').classList.remove('on')}

/* ── 초기화 ── */
document.addEventListener('DOMContentLoaded',function(){
 paintDday();
 syncInstallBtn();
 var q=document.getElementById('q');
 if(q){q.addEventListener('input',function(){F.q=this.value.toLowerCase();applyFilter()});}
 applyFilter();
 if(location.hash){var el=document.querySelector(location.hash);
   if(el){el.classList.add('hi');setTimeout(function(){el.classList.remove('hi')},2600);}}
 window.addEventListener('scroll',function(){
   document.getElementById('top').classList.toggle('on',window.scrollY>500)});
 document.addEventListener('keydown',function(e){
   if(e.key==='Escape'){closeModal();closeGuide();}
   if(e.key==='/'&&document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'){
     e.preventDefault();if(q)q.focus();}
 });
 var m=document.getElementById('mask');
 if(m)m.addEventListener('click',function(e){if(e.target===m)closeModal()});
});
"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def head(title, desc, canonical):
    return f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script>
window.__bip=null;
window.addEventListener('beforeinstallprompt',function(e){{
  e.preventDefault(); window.__bip=e;
  window.dispatchEvent(new Event('bip-ready'));
}});
window.addEventListener('appinstalled',function(){{ window.__bip=null; window.__installed=true; }});
</script>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{esc(AUTHOR)}">
<meta name="theme-color" content="#0c1120">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
<link rel="manifest" href="manifest.json">
<meta name="application-name" content="만민 건축법규 검토요약">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="만민법규">
<meta name="msapplication-TileColor" content="#0c1120">
<meta name="msapplication-TileImage" content="assets/icon-192.png">
<meta property="og:type" content="article">
<meta property="og:image" content="{CANON}assets/logo-full.png">
<meta property="og:image:alt" content="ARCHITECT KIM MANMIN — 만민 법규 검토 요약">
<meta property="og:site_name" content="{SITE_TITLE} — {SITE_SUB}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image">
<style>{CSS}</style>
</head>
<body>
<div id="toast" class="toast"></div>
<div class="iosgd" id="iosgd">
 <span class="x2" onclick="closeGuide()">✕</span>
 <b id="gdTitle">홈 화면에 추가하기</b>
 <p id="gdBody"></p>
</div>
<button id="top" onclick="scrollTo({{top:0,behavior:'smooth'}})" title="맨 위로">↑</button>
"""


def header_bar(issues, current=None):
    opts = ['<option value="">■ 월별 아카이브 이동</option>']
    opts.append(f'<option value="index.html">{"● " if current is None else ""}전체 목록 (INDEX)</option>')
    for d in issues:
        sel = " selected" if current == d["issue"] else ""
        opts.append(f'<option value="{d["issue"]}.html"{sel}>{esc(d["label"])} ({d["issue"]})</option>')
    return f"""<header><div class="wrap hd">
<a class="brand" href="index.html">
  <span class="markchip"><img class="brandmark" src="assets/logo-full.png" alt="ARCHITECT KIM MANMIN — 건축사 김만민" width="1200" height="867"></span>
  <b>{SITE_TITLE}</b><span class="ver">{SITE_VER}</span><span>{SITE_SUB} · {esc(AUTHOR)}</span>
</a>
<div class="hdbtns">
  <select class="btn" onchange="if(this.value)location.href=this.value">{''.join(opts)}</select>
  <button class="btn install" id="btnInstall" onclick="installApp()" title="앱으로 설치 — 주소창 없는 독립 창으로 열립니다"><img src="assets/mark-trans.png" alt=""><span>웹에 추가</span></button>
  <button class="btn" onclick="toggleTheme()" title="밝게/어둡게">◐</button>
  <a class="btn" href="{HOME}" target="_blank" rel="noopener">MANMIN 계산도구 ↗</a>
</div>
</div></header>
"""


def footer_bar():
    return f"""<footer><div class="wrap">
<div class="fl">
  <a href="{HOME}" target="_blank" rel="noopener">MANMIN 엔지니어링 플랫폼</a>
  <a href="{BLOG}" target="_blank" rel="noopener">네이버 블로그</a>
  <a href="{YOUTUBE}" target="_blank" rel="noopener">유튜브 채널</a>
  <a href="https://www.law.go.kr" target="_blank" rel="noopener">국가법령정보센터</a>
  <a href="https://opinion.lawmaking.go.kr" target="_blank" rel="noopener">국민참여입법센터</a>
  <a href="https://www.kcsc.re.kr" target="_blank" rel="noopener">국가건설기준센터</a>
</div>
<p class="disc">
본 자료는 {esc(AUTHOR)}가 월간 법규교육 자료를 기준으로 정리한 <b>요약본</b>입니다.
실제 인허가·설계·감리 업무에 적용할 때는 반드시 국가법령정보센터의 <b>원문 및 시행일</b>을 직접 확인하시기 바랍니다.
입법예고·의원발의 항목은 확정된 법령이 아니며 심의 과정에서 내용이 변경될 수 있습니다.<br>
KDS·KCS 국가건설기준은 국가건설기준센터(kcsc.re.kr) 공고본을 출처로 합니다.<br>
© {date.today().year} {esc(AUTHOR)}. 무단 전재·상업적 이용을 금합니다. · {SITE_VER}
</p>
</div></footer>
<script>{JS}</script>
</body></html>"""


def render_card(it, idx):
    cc = CAT_COLOR.get(it["cat"], "#8b98b3")
    cid = f"i{idx:02d}"
    fields = it.get("field", [])
    search_blob = " ".join([
        it.get("title", ""), it.get("law", ""), it.get("summary", ""),
        it.get("cat", ""), " ".join(fields), " ".join(it.get("detail", [])),
        it.get("impact", ""), it.get("date", "")
    ]).lower()

    dl = it.get("deadline")
    badges = []
    if dl:
        kind = "행정예고" if it["cat"] == "행정예고" else "입법예고"
        badges.append(f'<span class="dday soft" data-dl="{dl}" data-kind="{kind}">{kind}</span>')
    elif it.get("dateLabel") in ("시행",) and it.get("date"):
        badges.append(f'<span class="dday ok" data-ef="{it["date"]}"></span>')

    fld = "".join(f'<span class="field">{esc(f)}</span>' for f in fields)
    dtxt = it.get("date", "").replace("-", ".")
    dlabel = esc(it.get("dateLabel", ""))

    reason = ""
    if it.get("reason"):
        reason = f'<div class="reason"><b>제안이유 및 주요내용</b>{esc(it["reason"])}</div>'

    det = ""
    if it.get("detail"):
        lis = "".join(f"<li>{esc(x)}</li>" for x in it["detail"])
        det = f'<details><summary>세부 개정내용 {len(it["detail"])}건</summary><div class="det"><ul>{lis}</ul></div></details>'

    cmp_html = ""
    cmp_link = (f'<div class="cmplink">전체 대비표·원문<a href="{it["primary"][1]}" target="_blank" '
                f'rel="noopener">{it["primary"][0]}</a><a href="{it["secondary"][1]}" '
                f'target="_blank" rel="noopener">{it["secondary"][0]}</a></div>')
    if it.get("compare"):
        rows = "".join(
            f'<tr><td class="art">{esc(r.get("a",""))}</td>'
            f'<td>{esc(r.get("o",""))}</td>'
            f'<td class="new">{esc(r.get("n",""))}</td></tr>'
            for r in it["compare"])
        cmp_html = (f'<details><summary>신·구조문 대비 {len(it["compare"])}건</summary>'
                    f'<div class="det"><table class="cmp">'
                    f'<tr><th>조문</th><th>현행(개정 전)</th><th class="new">개정(안)</th></tr>'
                    f'{rows}</table>{cmp_link}</div></details>')
    elif it.get("compareNote"):
        cmp_html = (f'<div class="cmplink">신·구조문 대비 — {esc(it["compareNote"])}'
                    f'<a href="{it["primary"][1]}" target="_blank" rel="noopener">{it["primary"][0]}</a>'
                    f'<a href="{it["secondary"][1]}" target="_blank" rel="noopener">{it["secondary"][0]}</a></div>')

    imp = ""
    if it.get("impact"):
        imp = f'<div class="impact"><b>실무 영향</b>{esc(it["impact"])}</div>'

    return f"""<article class="card" id="{cid}" style="--cc:{cc}"
 data-cat="{esc(it['cat'])}" data-field="{esc('|'.join(fields))}" data-s="{esc(search_blob)}"
 data-title="{esc(it['title'])}" data-law="{esc(it.get('law',''))}" data-sum="{esc(it.get('summary',''))}"
 data-date="{esc(it.get('date',''))}" data-dlabel="{dlabel}"
 data-detail="{esc(json.dumps(it.get('detail',[]), ensure_ascii=False))}"
 data-reason="{esc(it.get('reason',''))}"
 data-impact="{esc(it.get('impact',''))}">
 <div class="ctop">
  <span class="tag">{esc(it['cat'])}</span>{fld}{''.join(badges)}
  <span class="sp"></span>
  <span class="anchor" onclick="copyAnchor('{cid}')" title="이 항목 링크 복사">🔗 링크</span>
 </div>
 <h3 class="ct">{esc(it['title'])}</h3>
 <div class="lawrow">
  <span>{dlabel} <b style="color:var(--txt)">{dtxt}</b></span>
  <span>·</span>
  <span>근거 {esc(it.get('law',''))}</span>
  <a href="{it['primary'][1]}" target="_blank" rel="noopener">{it['primary'][0]}</a>
  <a href="{it['secondary'][1]}" target="_blank" rel="noopener">{it['secondary'][0]}</a>
 </div>
 <p class="sum">{esc(it.get('summary',''))}</p>
 {reason}{det}{cmp_html}{imp}
</article>"""


def render_issue(d, issues):
    order = {c: i for i, c in enumerate(CATS)}
    items = sorted(d["items"], key=lambda x: (order.get(x["cat"], 99), x.get("date", "")))

    counts = {}
    for it in items:
        counts[it["cat"]] = counts.get(it["cat"], 0) + 1
    fields = []
    for it in items:
        for f in it.get("field", []):
            if f not in fields:
                fields.append(f)

    cat_chips = ['<span class="lb">구분</span>',
                 '<span class="chip on" data-g="cat" onclick="setChip(\'cat\',\'ALL\',this)">전체'
                 f'<span class="n">{len(items)}</span></span>']
    for c in CATS:
        if c in counts:
            cat_chips.append(f'<span class="chip" data-g="cat" onclick="setChip(\'cat\',\'{c}\',this)">'
                             f'{c}<span class="n">{counts[c]}</span></span>')
    fld_chips = ['<span class="lb">분야</span>',
                 '<span class="chip on" data-g="field" onclick="setChip(\'field\',\'ALL\',this)">전체</span>']
    for f in fields:
        fld_chips.append(f'<span class="chip" data-g="field" onclick="setChip(\'field\',\'{f}\',this)">{f}</span>')

    cards = "\n".join(render_card(it, i + 1) for i, it in enumerate(items))
    title = f"{d['label']} 법규 검토 요약 — {SITE_TITLE}"
    desc = d["headline"]
    canon = CANON + d["issue"] + ".html"

    meta_js = json.dumps({"label": d["label"], "headline": d["headline"],
                          "issue": d["issue"], "home": HOME}, ensure_ascii=False)

    return head(title, desc, canon) + header_bar(issues, d["issue"]) + f"""
<script>window.__META__={meta_js};</script>
<section class="hero"><div class="wrap">
 <div class="eyebrow">MONTHLY LEGAL REVIEW · {d['issue']} · {SITE_VER}</div>
 <h1>{esc(d['label'])} 법규 검토 요약</h1>
 <p class="lead">{esc(d['headline'])}</p>
 <div class="meta">
   <span>작성 <b>{esc(AUTHOR)}</b></span>
   <span>발행 <b>{d['published'].replace('-', '.')}</b></span>
   <span>출처 <b>{esc(d.get('source',''))}</b></span>
   <span>총 <b>{len(items)}건</b></span>
 </div>
 <div class="stats">
   {''.join(f'<div class="stat"><i>{c}</i><b>{n}</b></div>' for c, n in
            sorted(counts.items(), key=lambda x: order.get(x[0], 99)))}
 </div>
</div></section>

<div class="toolbar"><div class="wrap">
 <div class="searchbox">
   <input id="q" type="search" placeholder="법령명 · 조문 · 키워드 검색   (단축키 /)" autocomplete="off">
   <span class="x" onclick="clearQ()">✕</span>
 </div>
 <div class="chips">{''.join(cat_chips)}</div>
 <div class="chips" style="margin-top:6px">{''.join(fld_chips)}</div>
 <div class="chips" style="margin-top:9px">
   <button class="btn" id="bAll" onclick="toggleAll()">전체 펼치기</button>
   <button class="btn" onclick="window.print()">🖨 인쇄 · PDF 저장</button>
   <button class="btn" onclick="share('{esc(d['label'])} 법규 검토 요약')">🔗 공유</button>
   <button class="btn gold" onclick="openText('blog')">📝 블로그·유튜브 원고</button>
   <span style="flex:1"></span>
   <span class="hint" style="margin:0">표시 <b id="cnt" style="color:var(--gold)">0</b>건</span>
 </div>
</div></div>

<main class="wrap">
 <div class="list">{cards}</div>
 <div class="empty" id="empty" style="display:none">검색 조건에 맞는 항목이 없습니다.</div>
</main>

<div class="mask" id="mask">
 <div class="modal">
  <div class="mh"><b>블로그 · 유튜브 원고 추출</b>
    <button class="btn" onclick="closeModal()">닫기 ✕</button></div>
  <div class="mtabs" id="mtabs">
    <span class="chip on" data-m="blog" onclick="setMode('blog')">네이버 블로그용</span>
    <span class="chip" data-m="yt" onclick="setMode('yt')">유튜브 대본용</span>
    <span style="flex:1"></span>
    <span class="hint" style="margin:0">현재 필터에 표시된 항목만 추출됩니다</span>
  </div>
  <div class="mbody"><textarea id="ta" spellcheck="false"></textarea></div>
  <div class="mfoot">
    <button class="btn" onclick="copyText(document.getElementById('ta').value,'원고가 복사되었습니다')">전체 복사</button>
    <button class="btn gold" onclick="window.open('{BLOG}','_blank')">블로그 열기 ↗</button>
  </div>
 </div>
</div>
""" + footer_bar()


def render_index(issues):
    latest = issues[0]
    total = sum(len(d["items"]) for d in issues)

    # 임박 항목 (예고 마감 30일 이내 + 시행 예정)
    watch = []
    for d in issues:
        for it in d["items"]:
            if it.get("deadline"):
                watch.append((it["deadline"], "예고마감", it, d))
            elif it.get("dateLabel") == "시행" and it.get("date", "") >= date.today().isoformat():
                watch.append((it["date"], "시행예정", it, d))
    watch.sort(key=lambda x: x[0])
    today = date.today().isoformat()
    watch = [w for w in watch if w[0] >= today][:8]

    wrows = ""
    for dt, kind, it, d in watch:
        cc = CAT_COLOR.get(it["cat"], "#8b98b3")
        badge = (f'<span class="dday soft" data-dl="{dt}" data-kind="{it["cat"]}"></span>'
                 if kind == "예고마감" else f'<span class="dday ok" data-ef="{dt}"></span>')
        wrows += f"""<article class="card" style="--cc:{cc}">
  <div class="ctop"><span class="tag">{esc(it['cat'])}</span>{badge}
   <span class="sp"></span><span class="anchor">{dt.replace('-','.')}</span></div>
  <h3 class="ct"><a href="{d['issue']}.html">{esc(it['title'])}</a></h3>
  <div class="lawrow"><span>근거 {esc(it.get('law',''))}</span>
   <a href="{it['primary'][1]}" target="_blank" rel="noopener">{it['primary'][0]}</a>
   <a href="{d['issue']}.html">{esc(d['label'])}호 보기 →</a></div>
  <p class="sum">{esc(it.get('summary',''))}</p></article>"""

    acards = ""
    for d in issues:
        acards += f"""<a class="acard" href="{d['issue']}.html">
  <i>{d['issue']}</i><b>{esc(d['label'])}</b>
  <p>{esc(d['headline'])}</p>
  <div class="cnt">{len(d['items'])}건 · 발행 {d['published'].replace('-','.')}</div></a>"""

    title = f"{SITE_TITLE} — {SITE_SUB}"
    desc = f"건축사 김만민이 매월 정리하는 건축·구조·기계설비·소방·토목 법규 개정 요약. 최신호 {latest['label']} — {latest['headline']}"

    return head(title, desc, CANON) + header_bar(issues, None) + f"""
<section class="hero"><div class="wrap">
 <div class="eyebrow">MANMIN LEGAL REVIEW · MONTHLY · {SITE_VER}</div>
 <h1>만민 법규 검토 요약</h1>
 <p class="lead">건축 · 구조 · 기계설비 · 소방 · 토목 분야 법령 개정사항을 매월 첫째 주 화요일에 정리해 공유합니다.
 각 항목은 법제처 국가법령정보센터 원문으로 바로 연결되며, 입법예고 마감일은 자동으로 D-day가 계산됩니다.</p>
 <div class="meta">
  <span>편집 <b>{esc(AUTHOR)}</b></span>
  <span>최신호 <b>{esc(latest['label'])}</b></span>
  <span>누적 <b>{len(issues)}개호 · {total}건</b></span>
  <span>갱신 <b>매월 첫째 주 화요일</b></span>
 </div>
 <div class="chips" style="margin-top:18px">
  <a class="btn gold" href="{latest['issue']}.html">최신호 {esc(latest['label'])} 보기 →</a>
  <button class="btn" onclick="share('만민 법규 검토 요약')">🔗 링크 공유</button>
  <a class="btn" href="{BLOG}" target="_blank" rel="noopener">네이버 블로그 ↗</a>
  <a class="btn" href="{YOUTUBE}" target="_blank" rel="noopener">유튜브 ↗</a>
 </div>
</div></section>

<main class="wrap">
 <section class="sec" style="border-top:none">
  <div class="sech">■ 지금 챙겨야 할 일정 — 예고 마감 · 시행 예정</div>
  <div class="list" style="padding-top:0">{wrows or '<div class="empty">예정된 일정이 없습니다.</div>'}</div>
 </section>

 <section class="sec">
  <div class="sech">■ 월별 아카이브</div>
  <div class="arch">{acards}</div>
 </section>

 <section class="sec">
  <div class="sech">■ 자주 쓰는 법규 사이트</div>
  <div class="arch">
   <a class="acard" href="https://www.law.go.kr" target="_blank" rel="noopener">
     <i>LAW.GO.KR</i><b>국가법령정보센터</b><p>법률·시행령·시행규칙·고시·훈령·예규·자치법규·판례 원문 조회</p></a>
   <a class="acard" href="https://opinion.lawmaking.go.kr" target="_blank" rel="noopener">
     <i>LAWMAKING</i><b>국민참여입법센터</b><p>입법예고·행정예고 전문 및 의견 제출</p></a>
   <a class="acard" href="https://likms.assembly.go.kr/bill/main.do" target="_blank" rel="noopener">
     <i>ASSEMBLY</i><b>의안정보시스템</b><p>의원발의 법률안 원문·처리경과 확인</p></a>
   <a class="acard" href="https://www.kcsc.re.kr" target="_blank" rel="noopener">
     <i>KCSC</i><b>국가건설기준센터</b><p>KDS 설계기준 · KCS 표준시방서 공고본</p></a>
   <a class="acard" href="https://www.eais.go.kr" target="_blank" rel="noopener">
     <i>SEUMTER</i><b>건축행정시스템 세움터</b><p>건축물대장·인허가 민원</p></a>
   <a class="acard" href="https://www.hub.go.kr" target="_blank" rel="noopener">
     <i>ARCH HUB</i><b>건축HUB</b><p>설계공모 공고·심사결과 통합 공개(2027.1.1.~)</p></a>
  </div>
 </section>
</main>
""" + footer_bar()


def main():
    issues = load_issues()
    if not issues:
        print("[!] data/*.json 이 없습니다.")
        return
    # newline="\n" — 윈도우 기본값(CRLF)으로 쓰면 내용이 같아도 전 파일이
    # 바뀐 것으로 잡혀 매달 커밋 이력이 무의미해진다. 저장소는 LF 로 통일한다.
    for d in issues:
        p = os.path.join(BASE, d["issue"] + ".html")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_issue(d, issues))
        print(f"  생성  {d['issue']}.html   ({len(d['items'])}건)")
    with open(os.path.join(BASE, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_index(issues))
    print(f"  생성  index.html      (총 {len(issues)}개호)")
    print("\n완료. 로컬에서 index.html 을 열어 확인하세요.")


if __name__ == "__main__":
    main()
