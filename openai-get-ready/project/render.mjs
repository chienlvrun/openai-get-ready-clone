// QA renderer: node render.mjs outdir --range a b step   (env FPS, RS)
import { chromium } from 'playwright-core';
import fs from 'fs'; import path from 'path';
const out=process.argv[2]; const ri=process.argv.indexOf('--range');
const FPS=+(process.env.FPS||60), RS=+(process.env.RS||1);
const [a,b,step]=ri>0?process.argv.slice(ri+1,ri+4).map(Number):[0,726,1];
fs.mkdirSync(out,{recursive:true});
const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--allow-file-access-from-files']});
const pg=await br.newPage({viewport:{width:800,height:600}});
pg.on('console',m=>console.log('[page]',m.text())); pg.on('pageerror',e=>console.log('[err]',e.message));
if(process.env.PARAM) await pg.addInitScript(`window.PARAM=${process.env.PARAM}`);
await pg.goto('file://'+path.resolve('index.html')+'?rs='+RS);
await pg.waitForFunction('window.ready===true',null,{timeout:120000});
for(let f=a;f<b;f+=step){
  const url=await pg.evaluate(t=>{window.renderAt(t);return document.getElementById('c').toDataURL('image/png');},f/FPS);
  fs.writeFileSync(path.join(out,String(f).padStart(5,'0')+'.png'),Buffer.from(url.split(',')[1],'base64'));
}
await br.close();
