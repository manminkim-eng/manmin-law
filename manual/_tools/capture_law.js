// 만민 법규 검토 요약 매뉴얼 화면 캡처 — usage: node capture_law.js <repoDir> <outDir>
// 규격 1440×900 · DSF 1.25 · serviceWorkers block · 캡처 기준일 = 실행일(D-day 는 실행일 기준으로 칠해짐)
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');const {server,setup}=require('./common');
const repo=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);fs.mkdirSync(out,{recursive:true});
const VW=+(process.env.MM_VW||1440),VH=+(process.env.MM_VH||900),DSF=+(process.env.MM_DSF||1.25),PORT=8932;
const HIDE='.ibar,.toast,#top{display:none!important} *{animation:none!important;transition:none!important}';
const HELP=`window.__vis=e=>e&&e.getClientRects().length>0;
window.__find=sel=>{
 if(sel.startsWith('txt:')){const [q,t]=sel.slice(4).split('|');return [...document.querySelectorAll(q)].find(e=>__vis(e)&&e.textContent.includes(t))||null;}
 if(sel.startsWith('nth:')){const [q,i]=sel.slice(4).split('|');return [...document.querySelectorAll(q)].filter(__vis)[+i]||null;}
 for(const s of sel.split(',')){const e=[...document.querySelectorAll(s)].find(__vis);if(e)return e;}return null;};
window.__chip=(g,v)=>{const e=[...document.querySelectorAll('.chip[data-g="'+g+'"]')].find(c=>c.getAttribute('onclick').includes("'"+v+"'"));setChip(g,v,e);};`;
const P=f=>`http://127.0.0.1:${PORT}/${f}`;
const SHOTS=[
 {id:'s01_index',url:'index.html',clip:'viewport',m:[['.brand','사이트 이름 · Ver-1.0'],['.hdbtns select','월별 아카이브 이동'],['#btnInstall','웹에 추가'],['txt:.hdbtns .btn|◐','밝게 · 어둡게'],['.hero h1','만민 법규 검토 요약'],['.hero .meta','편집 · 최신호 · 누적 · 갱신'],['.hero .btn.gold','최신호 보기'],['txt:.hero .btn|유튜브','유튜브'],['txt:.hero .btn|매뉴얼','📘 매뉴얼']]},
 {id:'s02_chips',url:'index.html',clip:'.hero .chips',pad:12,m:[['.hero .btn.gold','최신호 보기'],['txt:.hero .btn|링크 공유','링크 공유'],['txt:.hero .btn|네이버','네이버 블로그'],['txt:.hero .btn|유튜브','유튜브'],['txt:.hero .btn|매뉴얼','📘 매뉴얼 — 이 문서']]},
 {id:'s03_watch',url:'index.html',clip:'nth:main .sec|0',to:'nth:main .sec .card|2',m:[['nth:main .sec .sech|0','지금 챙겨야 할 일정'],['nth:main .sec .card .tag|0','단계'],['nth:main .sec .card .dday|0','마감 D-day'],['nth:main .sec .card .anchor|0','마감 · 시행일'],['nth:main .sec .card .lawrow|0','근거 · 원문 · 해당 호']]},
 {id:'s04_archive',url:'index.html',clip:'txt:main .sec|월별 아카이브',m:[['nth:.acard|0','최신호'],['nth:.acard i|0','호 번호'],['nth:.acard p|0','머리기사']]},
 {id:'s05_issue_hero',url:'2026-09.html',clip:'.hero',m:[['.hero .eyebrow','호 번호 · 판'],['.hero h1','호 제목'],['.hero .lead','머리기사'],['txt:.hero .meta span|발행','발행일'],['txt:.hero .meta span|출처','수집 출처'],['.hero .stats','단계별 건수']]},
 {id:'s06_toolbar',url:'2026-09.html',clip:'.toolbar',m:[['#q','검색 (단축키 /)'],['nth:.toolbar .chips|0','단계 필터'],['nth:.toolbar .chips|1','분야 필터'],['#bAll','전체 펼치기'],['txt:.toolbar .btn|인쇄','인쇄 · PDF'],['txt:.toolbar .btn|공유','공유'],['txt:.toolbar .btn|원고','블로그 · 유튜브 원고'],['#cnt','표시 건수']]},
 {id:'s07_card',url:'2026-09.html',pre:"document.querySelector('#i03 details').open=true",clip:'#i03',m:[['#i03 .tag','단계'],['#i03 .field','분야'],['#i03 .lawrow','날짜 · 근거 · 원문'],['#i03 .sum','요약 — 번호 · 공포 · 시행'],['#i03 .reason','제안이유 및 주요내용'],['#i03 details','세부 개정내용'],['#i03 .cmplink','신 · 구조문 대비'],['#i03 .impact','실무 영향'],['txt:#i03 *|링크','항목 링크 복사']]},
 {id:'s08_notice',url:'2026-09.html',pre:"__chip('cat','입법예고')",clip:'nth:.card|0',to:'nth:.card|1',post:"__chip('cat','ALL')",m:[['nth:.card .tag|0','입법예고'],['nth:.card .dday|0','마감 · 종료 표시'],['nth:.card .lawrow|0','입법예고 원문']]},
 {id:'s09_filter',url:'2026-09.html',pre:"__chip('field','소방');window.scrollTo(0,document.querySelector('.toolbar').getBoundingClientRect().top+scrollY-10)",clip:'viewport',post:"__chip('field','ALL')",m:[['txt:.chip.on|소방','분야 = 소방'],['#cnt','표시 건수']]},
 {id:'s10_text',url:'2026-09.html',pre:"openText('blog')",clip:'.modal',fixed:true,post:"closeModal()",m:[['txt:#mtabs .chip|블로그','네이버 블로그용'],['txt:#mtabs .chip|유튜브','유튜브 대본용'],['#ta','원고'],['txt:.mfoot .btn|복사','전체 복사']]},
 {id:'s11_light',url:'index.html',pre:"toggleTheme()",clip:'viewport',post:"toggleTheme()",m:[]},
];
(async()=>{
 const s=await server(repo,PORT);const b=await chromium.launch();
 const ctx=await b.newContext({viewport:{width:VW,height:VH},deviceScaleFactor:DSF,serviceWorkers:'block',locale:'ko-KR'});await setup(ctx);
 const pg=await ctx.newPage();const errs=[];pg.on('pageerror',e=>errs.push(e.message));pg.on('dialog',d=>{errs.push('dialog '+d.message());d.dismiss();});
 let cur='';const meta={};
 for(const S of SHOTS){
  if(S.url!==cur){await pg.goto(P(S.url));await pg.evaluate(()=>document.fonts.ready);await pg.waitForTimeout(700);await pg.addStyleTag({content:HIDE});await pg.evaluate(HELP);cur=S.url;}
  await pg.evaluate(()=>window.scrollTo(0,0));
  if(S.pre){try{await pg.evaluate(S.pre);}catch(e){errs.push(S.id+' pre '+e.message);}}
  await pg.waitForTimeout(S.wait||400);
  const info=await pg.evaluate(({S,VW,VH})=>{
   const abs=e=>{const r=e.getBoundingClientRect();return {x:r.left+scrollX,y:r.top+scrollY,w:r.width,h:r.height};};
   let clip;
   if(S.clip==='viewport'){clip={x:0,y:scrollY,width:VW,height:VH};}
   else{const el=__find(S.clip);if(!el)return {err:'clip '+S.clip};const a=abs(el);const P=S.fixed?0:(S.pad??10);clip={x:Math.max(0,a.x-P),y:Math.max(0,a.y-P),width:a.w+2*P,height:a.h+2*P};
     if(S.to){const t=__find(S.to);if(t){const r=abs(t);clip.height=r.y+r.h+P-clip.y;}}}
   const marks=[];(S.m||[]).forEach(([sel,label],i)=>{const e=__find(sel);if(!e){marks.push({n:i+1,label,miss:sel});return;}const a=abs(e);
     marks.push({n:i+1,label,x:+((a.x-clip.x)/clip.width*100).toFixed(2),y:+((a.y-clip.y)/clip.height*100).toFixed(2),w:+(Math.min(a.w,clip.x+clip.width-a.x)/clip.width*100).toFixed(2),h:+(Math.min(a.h,clip.y+clip.height-a.y)/clip.height*100).toFixed(2)});});
   return {clip,marks};},{S,VW,VH});
  if(info.err){errs.push(S.id+' '+info.err);continue;}
  const c=info.clip;const cl={x:Math.max(0,c.x),y:Math.max(0,c.y),width:Math.min(c.width,VW-Math.max(0,c.x)),height:c.height};
  if(S.clip==='viewport'){await pg.screenshot({path:path.join(out,S.id+'.png'),clip:{x:0,y:0,width:VW,height:VH}});}
  else if(S.fixed){const sy=await pg.evaluate(()=>scrollY);await pg.screenshot({path:path.join(out,S.id+'.png'),clip:{x:c.x,y:c.y-sy,width:c.width,height:Math.min(c.height,VH)}});}
  else{await pg.screenshot({path:path.join(out,S.id+'.png'),clip:cl,fullPage:true});}
  meta[S.id]={w:Math.round(cl.width),h:Math.round(S.fixed?Math.min(cl.height,VH):cl.height),marks:info.marks};
  if(S.post){try{await pg.evaluate(S.post);}catch(e){errs.push(S.id+' post '+e.message);}await pg.waitForTimeout(250);}
 }
 // 인쇄 화면(첫 쪽) — media print 흉내
 await pg.goto(P('2026-09.html'));await pg.waitForTimeout(600);await pg.emulateMedia({media:'print'});await pg.setViewportSize({width:794,height:1123});await pg.waitForTimeout(400);
 await pg.screenshot({path:path.join(out,'s12_print.png')});meta['s12_print']={w:794,h:1123,marks:[]};await pg.emulateMedia({media:'screen'});await pg.setViewportSize({width:VW,height:VH});
 // 휴대전화
 const mctx=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,serviceWorkers:'block',isMobile:true,hasTouch:true,locale:'ko-KR'});await setup(mctx);
 const mp=await mctx.newPage();mp.on('pageerror',e=>errs.push('m '+e.message));
 await mp.goto(P('index.html'));await mp.waitForTimeout(800);await mp.addStyleTag({content:HIDE});
 await mp.screenshot({path:path.join(out,'s13_mobile_index.png')});meta['s13_mobile_index']={w:390,h:844,marks:[]};
 const mob={index:await mp.evaluate(()=>document.documentElement.scrollWidth)};
 await mp.goto(P('2026-09.html#i03'));await mp.waitForTimeout(800);await mp.addStyleTag({content:HIDE});await mp.evaluate(()=>{const e=document.getElementById('i03');window.scrollTo(0,e.getBoundingClientRect().top+scrollY-8);});await mp.waitForTimeout(300);
 await mp.screenshot({path:path.join(out,'s14_mobile_card.png')});meta['s14_mobile_card']={w:390,h:844,marks:[]};
 mob.issue=await mp.evaluate(()=>document.documentElement.scrollWidth);
 fs.writeFileSync(path.join(out,'_marks.json'),JSON.stringify(meta,null,1));
 const miss=[];Object.entries(meta).forEach(([k,v])=>v.marks.forEach(m=>{if(m.miss)miss.push(k+':'+m.miss);else if(m.x<0||m.y<0||m.x+m.w>100.5||m.y+m.h>100.5||m.w<=0||m.h<=0)miss.push(k+':OUT '+m.label+' '+[m.x,m.y,m.w,m.h]);}));
 console.log(JSON.stringify({mob,sizes:Object.fromEntries(Object.entries(meta).map(([k,v])=>[k,v.w+'x'+v.h])),miss,errs},null,1));
 await b.close();s.close();
})();
