// 매뉴얼 A4 PDF — usage: node pdf_law.js <manual 폴더> <파일명.pdf> "<푸터 제목>"
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');const {server,setup}=require('./common');
(async()=>{const M=path.resolve(process.argv[2]),name=process.argv[3],foot=process.argv[4];
 const repo=path.resolve(M,'..');const s=await server(repo,8933);const b=await chromium.launch();
 const ctx=await b.newContext({serviceWorkers:'block'});await setup(ctx);const p=await ctx.newPage();
 await p.goto('http://127.0.0.1:8933/manual/index.html');
 await p.addStyleTag({content:'@media print{.pfoot{display:none!important}}'});
 await p.evaluate(async()=>{for(const i of document.images)i.loading='eager';await document.fonts.ready;});await p.waitForTimeout(2500);
 const nkr='data:font/woff2;base64,'+fs.readFileSync(path.join(M,'assets/fonts/NotoSansKR-var.woff2')).toString('base64');
 await p.pdf({path:path.join(M,name),format:'A4',printBackground:true,displayHeaderFooter:true,headerTemplate:'<span></span>',
  footerTemplate:'<style>@font-face{font-family:NKR;src:url('+nkr+') format("woff2")}</style><div style="width:100%;font-size:8px;color:#666;padding:0 12mm;display:flex;justify-content:space-between;font-family:NKR,sans-serif"><span>'+foot+'</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
  margin:{top:'14mm',bottom:'16mm',left:'12mm',right:'12mm'}});
 await b.close();s.close();console.log('pdf ok');})();
