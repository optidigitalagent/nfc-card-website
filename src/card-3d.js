(()=>{'use strict';

const finePointer=matchMedia('(hover: hover) and (pointer: fine)');
const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)');
const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));

function reset(host){
  host.style.setProperty('--nfc-card-rx','0deg');
  host.style.setProperty('--nfc-card-ry','0deg');
  host.style.setProperty('--nfc-card-scale','1');
  delete host.dataset.nfcCard3d;
}

function initCatalogCard3D(host){
  if(!host||host.dataset.nfcCard3dReady==='true')return;

  const image=host.querySelector('.catalog-product-image');
  if(!image)return;

  /* Only real existing catalog images get the effect. */
  if(image.closest('.branded-concept,.instagram-placeholder'))return;

  host.dataset.nfcCard3dReady='true';
  let raf=0;
  let clientX=0;
  let clientY=0;

  const paint=()=>{
    raf=0;
    if(!finePointer.matches||reduceMotion.matches)return reset(host);

    const rect=host.getBoundingClientRect();
    if(!rect.width||!rect.height)return;

    const x=clamp((clientX-rect.left)/rect.width,0,1);
    const y=clamp((clientY-rect.top)/rect.height,0,1);

    const ry=(x-.5)*12;
    const rx=(.5-y)*9;

    host.style.setProperty('--nfc-card-rx',rx.toFixed(2)+'deg');
    host.style.setProperty('--nfc-card-ry',ry.toFixed(2)+'deg');
    host.style.setProperty('--nfc-card-scale','1.018');
  };

  const move=event=>{
    if(!finePointer.matches||reduceMotion.matches)return;
    clientX=event.clientX;
    clientY=event.clientY;
    if(!raf)raf=requestAnimationFrame(paint);
  };

  const enter=event=>{
    if(!finePointer.matches||reduceMotion.matches)return;
    host.dataset.nfcCard3d='active';
    move(event);
  };

  const leave=()=>{
    if(raf){cancelAnimationFrame(raf);raf=0;}
    reset(host);
  };

  host.addEventListener('pointerenter',enter,{passive:true});
  host.addEventListener('pointermove',move,{passive:true});
  host.addEventListener('pointerleave',leave,{passive:true});
  host.addEventListener('pointercancel',leave,{passive:true});
}

function mount(){
  document.querySelectorAll('.catalog-card-media').forEach(initCatalogCard3D);
}

window.initNfcCard3D=initCatalogCard3D;

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',mount,{once:true});
}else{
  mount();
}
})();