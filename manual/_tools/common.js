// 법규 사이트 캡처 공용 — 저장소를 로컬 서버로 띄우고 Pretendard 를 로컬 woff2 로 주입, 외부 요청 차단
const http=require('http'),fs=require('fs'),path=require('path');
const PD='/home/claude/vendor/pretendard-1.3.9/dist/web/static/woff2/';
const W={300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'};
const FONT=Object.entries(W).map(([w,n])=>`@font-face{font-family:'Pretendard';src:url(data:font/woff2;base64,${fs.readFileSync(PD+'Pretendard-'+n+'.woff2').toString('base64')}) format('woff2');font-weight:${w}}`).join('\n');
function server(root,port){return new Promise(res=>{const s=http.createServer((q,w)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p.endsWith('/'))p+='index.html';
 fs.readFile(path.join(root,p),(e,d)=>{if(e){w.writeHead(404);w.end();return;}const ct={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.woff2':'font/woff2','.pdf':'application/pdf'}[path.extname(p)]||'application/octet-stream';w.writeHead(200,{'Content-Type':ct});w.end(d);});});s.listen(port,()=>res(s));});}
async function setup(ctx){await ctx.route(/^https?:\/\/(?!127\.0\.0\.1)/,r=>r.abort());await ctx.addInitScript(css=>{document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=css;document.head.appendChild(s);});},FONT);}
module.exports={server,setup,FONT};
