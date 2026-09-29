// Scene: every element is a vector layer driven by measured per-frame tables (ref fps = output fps = 60).
const FPS_REF=60, NFR=726;
const DISC_RGB={white:'rgb(223,223,223)',purple:'rgb(140,58,239)',orange:'rgb(242,106,32)',green:'rgb(17,208,78)',dark:'rgb(38,38,38)',blue:'rgb(9,107,247)'};
const DOT_RGB=['rgb(242,106,32)','rgb(9,107,247)','rgb(17,208,78)','rgb(140,58,239)','rgb(255,255,255)'];
const TXT_RGB={white:'rgb(255,255,255)',green:'rgb(12,194,70)',purple:'rgb(140,58,239)'};
const P=window.PARAM||{};
let EYEP={}, GLY={};
function init(){
  for(const k in EYE_TPL){ const p=new Path2D(); for(const poly of EYE_TPL[k]){ poly.forEach((q,i)=>i?p.lineTo(q[0],q[1]):p.moveTo(q[0],q[1])); p.closePath(); } EYEP[k]=p; }
  for(const k of ['big','t1','t2']) GLY[k]=TRACE[k].map(g=>new Path2D(g.d));
  GLY.bigline=TRACE.big.map(g=>g.dline?new Path2D(g.dline):null);
}
function drawDiscs(c,f){
  const L=DISCS[f]; if(!L) return;
  for(const [col,x,y,r] of L){
    c.save(); c.beginPath(); c.arc(x,y,Math.max(r,0),0,Math.PI*2); c.fillStyle=DISC_RGB[col]; c.fill();
    const E=(EYES[f]||{})[col];
    if(E&&E.length){ c.clip(); c.fillStyle=col==='dark'?'#fff':'#000';
      for(const [g,a,b,cc,d,e,ff] of E){ c.save(); c.transform(a,b,cc,d,e,ff); c.fill(EYEP[g],'evenodd'); c.restore(); } }
    c.restore();
  }
}
function drawDots(c,f){
  const L=DOTS[f]; if(!L) return;
  const dr=P.dotdr||0;
  for(const [ci,x,y,r] of L){ c.beginPath(); c.arc(x,y,Math.max(0.1,r+dr),0,Math.PI*2); c.fillStyle=DOT_RGB[ci]; c.fill(); }
}
function drawText(c,f){
  for(const key of ['big','t1','t2']){
    const S=TSTATE[key]; if(!S||f<S.a||f>S.b) continue;
    const fr=S.frames[f-S.a]; if(!fr) continue;
    const [s,tx,ty]=fr.T; const st=fr.st;
    c.save(); c.transform(s,0,0,s,tx,ty);
    TRACE[key].forEach((g,i)=>{
      const v=st[i]; if(!v) return;
      const col=TXT_RGB[g.color]; const off=fr.off&&fr.off[i]; if(off){ c.save(); c.translate(off[0]/s,off[1]/s); }
      if(v===2){ c.fillStyle=col; c.fill(GLY[key][i],'evenodd'); }
      else if(v>0&&v<=1&&key==='big'&&GLY.bigline[i]){ const L=g.lineT; c.save(); c.fillStyle=col; c.globalAlpha=v; c.scale(1/L[0],1/L[0]); c.translate(-L[1],-L[2]); c.fill(GLY.bigline[i]); c.restore(); }
      else if(v>0&&v<=1){ c.strokeStyle=col; c.globalAlpha=v; c.lineWidth=((S.lineW&&S.lineW[g.color])||P['sw_'+key]||S.sw)/s; c.lineJoin='miter'; c.stroke(GLY[key][i]); c.globalAlpha=1; }
      if(off) c.restore();
    });
    c.restore();
  }
}
function renderAt(t){
  const c=ctx; const f=Math.min(NFR-1,Math.max(0,Math.round(t*FPS_REF)));
  c.setTransform(1,0,0,1,0,0); c.fillStyle='#000'; c.fillRect(0,0,c.canvas.width,c.canvas.height);
  c.setTransform(RS,0,0,RS,0,0);
  drawDiscs(c,f); drawText(c,f); drawDots(c,f);
}
