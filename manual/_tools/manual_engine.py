# -*- coding: utf-8 -*-
"""공통 매뉴얼 엔진 (RTS-MANMIN 매뉴얼에서 분리) — CSS·JS·fig()
   캡처 좌표(images/_marks.json)를 읽어 번호 배지를 HTML 위에 겹쳐 그린다(재캡처 시 재생성만 하면 됨)."""
import json, os, html
B = os.environ.get('MANUAL_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MARKS = json.load(open(os.path.join(B, 'images', '_marks.json'), encoding='utf-8'))

def esc(s): return html.escape(s, quote=True)

def fig(sid, caption, legend=None, alt=None, narrow=False):
    m = MARKS.get(sid, {'w': 1600, 'h': 900, 'marks': []})
    pins = []
    for k in m['marks']:
        if 'x' not in k: continue
        x = min(97.0, max(1.5, k['x'] + 0.4))
        y = min(96.0, max(2.0, k['y'] + (0.8 if k['h'] < 15 else min(k['h'], 6) / 2)))
        pins.append(f'<span class="pin" style="left:{x:.2f}%;top:{y:.2f}%">{k["n"]}</span>')
    leg = ''
    if legend:
        items = ''.join(f'<li><b>{i+1}</b><span>{t}</span></li>' for i, t in enumerate(legend))
        leg = f'<ol class="legend">{items}</ol>'
    cls = 'shot narrow' if narrow else 'shot'
    return (f'<figure class="{cls}" id="fig-{sid}"><div class="frame">'
            f'<img src="images/{sid}.webp" width="{m["w"]}" height="{m["h"]}" loading="lazy" alt="{esc(alt or caption)}">'
            + ''.join(pins) + f'</div><figcaption><span class="fno">{sid[:3].upper()}</span>{caption}</figcaption>{leg}</figure>')

CSS = r"""
:root{
  --navy:#2D3A8C;--navy-d:#1F2A6B;--navy-l:#E9ECF8;--accent:#F4A261;--accent-d:#C97A3A;--accent-l:#FDF1E7;
  --bg:#F8F9FA;--card:#FFFFFF;--text:#1A1A2E;--text2:#4A4F66;--line:#DDE1EA;--ok:#0F766E;--ng:#B42318;
  --r:12px;--pad:24px;--shadow:0 4px 20px rgba(0,0,0,.08);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--font-sans);font-size:16px;line-height:1.75;word-break:keep-all;overflow-wrap:anywhere}
a{color:var(--navy)}a:hover{color:var(--accent-d)}
code,kbd,.mono{font-family:var(--font-mono);font-size:.9em}
code{background:var(--navy-l);color:var(--navy-d);padding:1px 6px;border-radius:5px}
kbd{border:1px solid var(--line);border-bottom-width:2px;border-radius:5px;padding:0 6px;background:#fff}
/* 상단 */
.top{background:linear-gradient(135deg,var(--navy-d),var(--navy));color:#fff}
.top-in{max-width:1240px;margin:0 auto;padding:44px 24px 36px}
.eyebrow{font-family:var(--font-brand);font-weight:700;font-size:12px;letter-spacing:.18em;opacity:.85}
.top h1{font-size:28px;font-weight:900;margin:8px 0 6px;line-height:1.35}
.top .sub{opacity:.9;margin:0}
.badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
.badge{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:4px 12px;font-size:13px}
a.badge{color:#fff;text-decoration:none}a.badge:hover{background:rgba(255,255,255,.24);color:#fff}
.badge.acc{background:var(--accent);border-color:var(--accent);color:#1A1A2E;font-weight:700}
/* 레이아웃 */
.wrap{max-width:1240px;margin:0 auto;padding:28px 24px 80px;display:grid;grid-template-columns:260px minmax(0,1fr);gap:32px}
nav.toc{position:sticky;top:16px;align-self:start;max-height:calc(100vh - 32px);overflow:auto;background:var(--card);border-radius:var(--r);box-shadow:var(--shadow);padding:18px 16px;font-size:14px}
nav.toc h2{font-size:13px;letter-spacing:.12em;color:var(--text2);margin:0 0 8px}
nav.toc ol{list-style:none;margin:0;padding:0}
nav.toc li a{display:block;padding:5px 8px;border-radius:8px;text-decoration:none;color:var(--text)}
nav.toc li a:hover,nav.toc li a.on{background:var(--navy-l);color:var(--navy)}
nav.toc li.sub a{padding-left:20px;font-size:13px;color:var(--text2)}
main{min-width:0}
section.ch{background:var(--card);border-radius:var(--r);box-shadow:var(--shadow);padding:var(--pad) calc(var(--pad) + 8px);margin-bottom:28px}
section.ch>h2{font-size:24px;font-weight:700;color:var(--navy);margin:0 0 4px;display:flex;align-items:baseline;gap:10px}
section.ch>h2 .n{font-family:var(--font-brand);font-weight:700;font-size:14px;color:#fff;background:var(--navy);border-radius:8px;padding:2px 9px}
section.ch>.lead{color:var(--text2);margin:0 0 18px}
h3{font-size:19px;color:var(--navy-d);margin:34px 0 10px;padding-top:6px;border-top:1px solid var(--line)}
h3:first-of-type{border-top:0}
h4{font-size:16px;margin:22px 0 8px}
p{margin:8px 0}
ul,ol{padding-left:22px}
.note,.tip,.warn{border-radius:10px;padding:12px 16px;margin:14px 0;font-size:15px}
.note{background:var(--navy-l);border-left:4px solid var(--navy)}
.tip{background:var(--accent-l);border-left:4px solid var(--accent)}
.warn{background:#FEF3F2;border-left:4px solid var(--ng)}
.note b:first-child,.tip b:first-child,.warn b:first-child{margin-right:6px}
/* 표 */
.tbl{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--navy-l);color:var(--navy-d);font-weight:700;white-space:nowrap}
tr:last-child td{border-bottom:0}
td.num,th.num{text-align:right;font-family:var(--font-mono);white-space:nowrap}
.ok{color:var(--ok);font-weight:700}.ng{color:var(--ng);font-weight:700}
/* 그림 */
figure.shot{margin:18px 0 26px}
figure.shot .frame{position:relative;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff;cursor:zoom-in}
figure.shot img{display:block;width:100%;height:auto}
figure.narrow{max-width:420px}
.pin{position:absolute;transform:translate(-50%,-50%);width:26px;height:26px;border-radius:50%;background:var(--accent);color:#1A1A2E;font:700 13px/26px var(--font-mono);text-align:center;box-shadow:0 0 0 3px #fff,0 2px 8px rgba(0,0,0,.35);pointer-events:none}
figcaption{font-size:14px;color:var(--text2);margin-top:8px}
.fno{font-family:var(--font-mono);font-size:11px;background:var(--navy);color:#fff;border-radius:6px;padding:1px 7px;margin-right:8px}
ol.legend{list-style:none;padding:0;margin:10px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:6px 16px;font-size:14px}
ol.legend li{display:flex;gap:8px;align-items:flex-start}
ol.legend b{flex:0 0 22px;height:22px;border-radius:50%;background:var(--accent);font:700 12px/22px var(--font-mono);text-align:center}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}
/* 단계 */
.steps{counter-reset:st;list-style:none;padding:0;margin:16px 0}
.steps>li{counter-increment:st;position:relative;padding:4px 0 18px 54px;border-left:2px solid var(--line);margin-left:18px}
.steps>li:last-child{border-left-color:transparent}
.steps>li::before{content:counter(st);position:absolute;left:-19px;top:0;width:36px;height:36px;border-radius:50%;background:var(--navy);color:#fff;font:700 15px/36px var(--font-mono);text-align:center;box-shadow:0 0 0 4px var(--bg)}
.steps>li>b.t{display:block;font-size:17px;color:var(--navy-d);margin-bottom:2px}
/* 수식 */
.eq{font-family:var(--font-mono);background:#0F1630;color:#E8ECFF;border-radius:10px;padding:14px 18px;margin:12px 0;overflow-x:auto;font-size:14px;line-height:1.9;white-space:pre}
.eq .c{color:#9AA6D6}
.svgbox{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px;margin:14px 0;overflow-x:auto}
.svgbox svg{display:block;width:100%;min-width:640px;height:auto}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin:14px 0}
.card{border:1px solid var(--line);border-radius:var(--r);padding:16px;background:#fff}
.card h5{margin:0 0 4px;font-size:15px;color:var(--navy)}
.card p{margin:0;font-size:14px;color:var(--text2)}
footer.foot{max-width:1240px;margin:0 auto;padding:0 24px 40px;color:var(--text2);font-size:13px}
/* 라이트박스 */
#lb{position:fixed;inset:0;background:rgba(10,14,30,.88);display:none;align-items:center;justify-content:center;z-index:99;cursor:zoom-out;padding:16px}
#lb.open{display:flex}#lb img{max-width:100%;max-height:100%;border-radius:8px;background:#fff}
.totop{position:fixed;right:18px;bottom:18px;width:44px;height:44px;border-radius:50%;background:var(--navy);color:#fff;border:0;font-size:18px;box-shadow:var(--shadow);cursor:pointer}
/* 반응형 5단계 */
@media (max-width:1240px){.wrap{grid-template-columns:230px minmax(0,1fr);gap:24px}}
@media (max-width:1024px){.wrap{grid-template-columns:1fr}nav.toc{position:static;max-height:none}nav.toc ol{columns:2}}
@media (max-width:760px){.pair{grid-template-columns:1fr}section.ch{padding:20px 18px}.top h1{font-size:24px}}
@media (max-width:640px){nav.toc ol{columns:1}body{font-size:15px}}
@media (max-width:480px){.wrap,.top-in{padding-left:16px;padding-right:16px}.pin{width:22px;height:22px;font-size:11px;line-height:22px}}
@media (max-width:400px){section.ch>h2{font-size:20px}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
/* A4 인쇄 */
@page{size:A4;margin:14mm 12mm 14mm}
@media print{
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  body{background:#fff;font-size:10.5pt}
  nav.toc,.totop,#lb{display:none!important}
  .wrap{display:block;padding:0}
  section.ch{box-shadow:none;padding:0 0 8mm;margin:0;break-before:page}
  main{padding-bottom:8mm}
  section.ch:first-of-type{break-before:auto}
  figure.shot,.tbl,.eq,.svgbox,.note,.tip,.warn,.steps>li{break-inside:avoid}
  h3,h4{break-after:avoid}
  .top{border-radius:0}
  .pfoot{position:fixed;bottom:0;left:0;right:0;height:6mm;background:#fff;font-size:8pt;color:#666;border-top:1px solid #ccc;padding-top:1.5mm;display:flex;justify-content:space-between}
}
.pfoot{display:none}
@media print{.pfoot{display:flex}}
/* ── 좁은 화면 대응(r1 · 2026-10-12) : 화면 전용 — 인쇄·PDF에는 영향 없음 ── */
@media screen and (max-width:640px){
  .k1 td:first-child,.k1 th:first-child{white-space:normal}
  /* 글 표(숫자 칸 없는 표) → 행마다 카드로 쌓기 */
  .tbl.stack{border:0;border-radius:0;overflow:visible}
  .tbl.stack table,.tbl.stack tbody,.tbl.stack tr,.tbl.stack td{display:block;width:auto}
  .tbl.stack thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .tbl.stack table{background:transparent}
  .tbl.stack tr{border:1px solid var(--line);border-radius:10px;background:#fff;margin:0 0 10px;overflow:hidden}
  .tbl.stack td{border-bottom:1px solid var(--line);padding:8px 12px}
  .tbl.stack tr td:last-child{border-bottom:0}
  .tbl.stack td:first-child{background:var(--navy-l);color:var(--navy-d);font-weight:700}
  .tbl.stack td[data-th]:not(:first-child)::before{content:attr(data-th);display:block;font-size:12px;font-weight:700;color:var(--text2);margin-bottom:2px}
  .tbl.stack.c2 td[data-th]:not(:first-child)::before{display:none}
  .tbl.stack td:empty{display:none}
  /* 숫자 표 → 표 모양 유지, 글자·여백 축소, 넘치면 좌우로 밀기(오른쪽 그림자로 표시) */
  .tbl:not(.stack){background:linear-gradient(to right,#fff 30%,rgba(255,255,255,0)) left/40px 100% no-repeat local,linear-gradient(to left,#fff 30%,rgba(255,255,255,0)) right/40px 100% no-repeat local,radial-gradient(farthest-side at 100% 50%,rgba(26,26,46,.22),transparent) right/12px 100% no-repeat scroll,#fff}
  .tbl:not(.stack) table{font-size:13px;background:transparent}
  .tbl:not(.stack) th,.tbl:not(.stack) td{padding:7px 8px}
  /* 수식 → 줄바꿈 허용 */
  .eq{white-space:pre-wrap;word-break:keep-all;font-size:13px;line-height:1.75;padding:12px 14px}
  .eq .c{display:block;padding-left:1em}
  .svgbox{position:relative}
  .svgbox::after{content:"← 좌우로 밀어서 보기 →";display:block;text-align:center;font-size:12px;color:var(--text2);margin-top:6px;position:sticky;left:0}
  ol.legend{grid-template-columns:1fr}
  .steps>li{padding-left:34px;margin-left:14px}
}
.rev{white-space:nowrap}
@media print{.rev{display:none}}
"""

JS = r"""
(function(){
  var lb=document.getElementById('lb'),li=lb.querySelector('img');
  document.querySelectorAll('figure.shot .frame').forEach(function(f){f.addEventListener('click',function(){li.src=f.querySelector('img').src;li.alt=f.querySelector('img').alt;lb.classList.add('open');});});
  lb.addEventListener('click',function(){lb.classList.remove('open');li.removeAttribute('src');});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')lb.classList.remove('open');});
  document.querySelector('.totop').addEventListener('click',function(){window.scrollTo(0,0);});
  var links=[].slice.call(document.querySelectorAll('nav.toc a'));
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(a){a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id);});}});},{rootMargin:'0px 0px -70% 0px'});
    document.querySelectorAll('section.ch,h3[id]').forEach(function(s){io.observe(s);});
  }
})();
/* 좁은 화면 표 쌓기 준비: 숫자 칸이 없는 표에 stack 표시, 각 칸에 머리글(data-th) 복사 */
(function(){document.querySelectorAll('.tbl').forEach(function(t){var tb=t.querySelector('table');if(!tb||!tb.tHead)return;
 if(tb.querySelector('td.num,th.num'))return;var hs=[].map.call(tb.tHead.rows[0].cells,function(c){return c.textContent.trim()});
 [].forEach.call(tb.tBodies[0].rows,function(r){[].forEach.call(r.cells,function(c,i){if(hs[i])c.setAttribute('data-th',hs[i])})});t.classList.add('stack');if(hs.length===2)t.classList.add('c2')})})();
"""


def T(rows, head, num_cols=()):
    h = ''.join(f'<th class="{"num" if i in num_cols else ""}">{c}</th>' for i, c in enumerate(head))
    b = ''.join('<tr>' + ''.join(f'<td class="{"num" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<div class="tbl"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


def toc_html(TOC):
    out = []
    for cid, t, subs in TOC:
        out.append(f'<li><a href="#{cid}">{t}</a></li>')
        out += [f'<li class="sub"><a href="#{sid}">{st}</a></li>' for sid, st in subs]
    return '<nav class="toc" aria-label="목차"><h2>목차</h2><ol>' + ''.join(out) + '</ol></nav>'

def render(*, title, desc, eyebrow, h1, sub, ver, date, app_name, pdf, toc, sections, foot_note):
    tpl = """<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta name="author" content="김만민 건축사 · ㈜대성건축사사무소">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;600&family=Orbitron:wght@700;900&display=swap">
<link rel="stylesheet" href="./assets/fonts/manmin-fonts.css">
<style>__CSS__</style>
</head><body>
<header class="top"><div class="top-in">
<div class="eyebrow">__EYEBROW__</div>
<h1>__H1__</h1>
<p class="sub">__SUB__</p>
<div class="badges"><span class="badge acc">매뉴얼 <span style="font-family:var(--font-brand)">__VER__</span></span><a class="badge" href="../index.html">▶ __APP__ 열기</a><a class="badge" href="__PDF__" download>⤓ PDF</a><span class="badge">__DATE__</span><span class="badge">김만민 건축사 · ㈜대성건축사사무소</span></div>
</div></header>
<div class="wrap">__TOC__<main>__BODY__</main></div>
<footer class="foot">© 2026 김만민 건축사 · ㈜대성건축사사무소 · __H1__ __VER__ · __FOOT__ <span class="rev">· 화면 대응 개정 2026-10-12</span></footer>
<div class="pfoot"><span>__H1__ __VER__</span><span>__DATE__</span></div>
<div id="lb" role="dialog" aria-label="그림 확대"><img alt=""></div>
<button class="totop" aria-label="맨 위로">↑</button>
<script>__JS__</script>
</body></html>"""
    rep = {'__TITLE__':title,'__DESC__':desc,'__EYEBROW__':eyebrow,'__H1__':h1,'__SUB__':sub,'__VER__':ver,'__APP__':app_name,'__PDF__':pdf,'__DATE__':date,'__FOOT__':foot_note,'__CSS__':CSS,'__TOC__':toc_html(toc),'__BODY__':'\n'.join(sections),'__JS__':JS}
    for k,v in rep.items(): tpl = tpl.replace(k, v)
    return tpl
