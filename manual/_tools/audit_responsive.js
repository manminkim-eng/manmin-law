// 매뉴얼 반응형 점검 — usage: node audit.js <manual/index.html> [폭...]
const {chromium}=require(process.env.MM_PW||'playwright');const path=require('path');
(async()=>{const f=path.resolve(process.argv[2]);const W=(process.argv.slice(3).length?process.argv.slice(3):['360','390','480','760','1024']).map(Number);
const b=await chromium.launch();const out={};
for(const w of W){const pg=await b.newPage({viewport:{width:w,height:800},deviceScaleFactor:1,serviceWorkers:'block'});await pg.goto('file://'+f);await pg.waitForTimeout(300);
 out[w]=await pg.evaluate(()=>{const r={};const de=document.documentElement;r.pageOverflow=de.scrollWidth-innerWidth;
  const sec=e=>{let h=e;while(h&&!(h.matches&&h.matches('h3[id],section.ch'))){h=h.previousElementSibling||h.parentElement}return h?(h.id||''):''};
  r.tables=[...document.querySelectorAll('.tbl')].map((t,i)=>{const tb=t.querySelector('table');const rows=[...tb.tBodies[0].rows];const nc=tb.tHead?tb.tHead.rows[0].cells.length:0;
    const cw=[...(rows[0]||{cells:[]}).cells].map(c=>Math.round(c.getBoundingClientRect().width));
    let sq=0,maxLines=0;rows.forEach(tr=>[...tr.cells].forEach(c=>{const tx=c.textContent.trim();const cwid=c.getBoundingClientRect().width;const lh=parseFloat(getComputedStyle(c).lineHeight)||22;const lines=Math.round((c.getBoundingClientRect().height-16)/lh);
      if(tx.length>=10&&cwid<90)sq++; if(c===tr.cells[tr.cells.length-1]||true)maxLines=Math.max(maxLines,lines)}));
    return {i,sec:sec(t),nc,rows:rows.length,k1:!!t.closest('.k1'),scroll:tb.scrollWidth>t.clientWidth+1?tb.scrollWidth-t.clientWidth:0,cw,sq,maxLines,h:Math.round(t.getBoundingClientRect().height)}});
  r.eq=[...document.querySelectorAll('.eq')].filter(e=>e.scrollWidth>e.clientWidth+1).length+'/'+document.querySelectorAll('.eq').length;
  r.svg=[...document.querySelectorAll('.svgbox')].filter(e=>e.scrollWidth>e.clientWidth+1).length+'/'+document.querySelectorAll('.svgbox').length;
  r.other=[...document.querySelectorAll('main *')].filter(e=>{const b=e.getBoundingClientRect();return b.right>innerWidth+1&&!e.closest('.tbl,.eq,.svgbox')}).slice(0,5).map(e=>e.tagName+'.'+e.className);
  r.figs=[...document.querySelectorAll('figure.shot')].map(g=>Math.round(g.getBoundingClientRect().width));
  r.pinMin=Math.min(...[...document.querySelectorAll('.pin')].map(p=>p.getBoundingClientRect().width));
  r.tri=[...document.querySelectorAll('.tri')].map(g=>getComputedStyle(g).gridTemplateColumns);
  r.height=de.scrollHeight;return r});await pg.close()}
console.log(JSON.stringify(out));await b.close()})();
