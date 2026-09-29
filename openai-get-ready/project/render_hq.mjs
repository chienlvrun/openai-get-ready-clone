// Final renderer: node render_hq.mjs outdir RS FPS startFrame endFrame segName -> outdir/segName.mp4
import { chromium } from 'playwright-core';
import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process';
const [out,RSs,FPSs,as,bs,seg]=process.argv.slice(2); const RS=+RSs,FPS=+FPSs,a=+as,b=+bs;
fs.mkdirSync(out,{recursive:true});
const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--allow-file-access-from-files']});
const pg=await br.newPage({viewport:{width:800,height:600}});
pg.on('pageerror',e=>console.log('[err]',e.message));
await pg.goto('file://'+path.resolve('index.html')+'?rs='+RS);
await pg.waitForFunction('window.ready===true',null,{timeout:120000});
const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate',String(FPS),'-c:v','png','-i','-',
 '-vf','scale=out_color_matrix=bt709:out_range=tv','-c:v','libx264','-preset','medium','-crf','12','-pix_fmt','yuv420p',
 '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-r',String(FPS),path.join(out,seg+'.mp4')],{stdio:['pipe','inherit','inherit']});
for(let f=a;f<b;f+=1){
  const url=await pg.evaluate(t=>{window.renderAt(t);return document.getElementById('c').toDataURL('image/png');},f/FPS);
  if(!ff.stdin.write(Buffer.from(url.split(',')[1],'base64'))) await new Promise(r=>ff.stdin.once('drain',r));
  if(f%30==0) console.log(seg,f);
}
ff.stdin.end(); await new Promise(r=>ff.on('close',r)); await br.close();
