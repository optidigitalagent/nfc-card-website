(()=>{'use strict';

const finePointer=matchMedia('(hover: hover) and (pointer: fine)');
const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)');
const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));

function resting(host){
  host.style.setProperty('--nfc-card-rx','4deg');
  host.style.setProperty('--nfc-card-ry','-7deg');
  host.style.setProperty('--nfc-card-scale','.94');
  host.style.setProperty('--nfc-card-lift','18px');
  delete host.dataset.nfcCard3d;
}

function initNfcCard3D(host){
  if(!host||host.dataset.nfcCard3dReady==='true')return;

  const image=host.querySelector(':scope > .catalog-product-image, :scope > picture > .catalog-product-image, :scope .catalog-product-image');
  if(!image)return;
  if(image.closest('.branded-concept,.instagram-placeholder'))return;

  host.dataset.nfcCard3dReady='true';
  resting(host);

  let frame=0;
  let clientX=0;
  let clientY=0;

  const paint=()=>{
    frame=0;
    if(!finePointer.matches||reduceMotion.matches)return resting(host);

    const rect=host.getBoundingClientRect();
    if(!rect.width||!rect.height)return;

    const x=clamp((clientX-rect.left)/rect.width,0,1);
    const y=clamp((clientY-rect.top)/rect.height,0,1);

    const ry=(x-.5)*18;
    const rx=(.5-y)*14;

    host.style.setProperty('--nfc-card-rx',rx.toFixed(2)+'deg');
    host.style.setProperty('--nfc-card-ry',ry.toFixed(2)+'deg');
    host.style.setProperty('--nfc-card-scale','.97');
    host.style.setProperty('--nfc-card-lift','26px');
  };

  const move=event=>{
    if(!finePointer.matches||reduceMotion.matches)return;
    clientX=event.clientX;
    clientY=event.clientY;
    if(!frame)frame=requestAnimationFrame(paint);
  };

  const enter=event=>{
    if(!finePointer.matches||reduceMotion.matches)return;
    host.dataset.nfcCard3d='active';
    move(event);
  };

  const leave=()=>{
    if(frame){cancelAnimationFrame(frame);frame=0;}
    resting(host);
  };

  host.addEventListener('pointerenter',enter,{passive:true});
  host.addEventListener('pointermove',move,{passive:true});
  host.addEventListener('pointerleave',leave,{passive:true});
  host.addEventListener('pointercancel',leave,{passive:true});
}

function mount(){
  document.querySelectorAll('.catalog-card-media').forEach(initNfcCard3D);
}

window.initNfcCard3D=initNfcCard3D;

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',mount,{once:true});
}else{
  mount();
}
})();