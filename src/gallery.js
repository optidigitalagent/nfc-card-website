/* Scoped, dependency-free carousel; order/review state is owned by existing clients. */
window.NFCGallery={mount(gallery,event){
  const slides=[...gallery.querySelectorAll('[data-slide]')],frame=gallery.querySelector('[data-gallery-frame]'),dialog=gallery.querySelector('dialog'),viewport=dialog.querySelector('.lightbox-scroll'),zoomImage=viewport.querySelector('img'),opener=gallery.querySelector('[data-zoom]');
  const controls=[...gallery.querySelectorAll('[data-thumb-to]')];
  const zoomVideo=dialog.querySelector('video');
  const videos=[...gallery.querySelectorAll('video')];
  const pauseVideos=()=>videos.forEach(video=>video.pause());
  const prepareVideo=(video,src)=>{if(video.getAttribute('src')!==src){video.src=src;video.load();}};
  let index=0,restore=null,locked=null,swipeUntil=0;
  let scale=1,panX=0,panY=0,gesture=null;
  const pointers=new Map();
  const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
  function renderZoom(){
    const maxX=Math.max(0,(zoomImage.offsetWidth*scale-viewport.clientWidth)/2);
    const maxY=Math.max(0,(zoomImage.offsetHeight*scale-viewport.clientHeight)/2);
    panX=clamp(panX,-maxX,maxX);panY=clamp(panY,-maxY,maxY);
    zoomImage.style.setProperty('--zoom-scale',String(scale));
    zoomImage.style.setProperty('--pan-x',`${panX}px`);zoomImage.style.setProperty('--pan-y',`${panY}px`);
    dialog.dataset.zoomed=String(scale>1.01);
  }
  function resetZoom(){scale=1;panX=0;panY=0;pointers.clear();gesture=null;renderZoom();}
  function zoomTo(next,x=0,y=0){const old=scale;scale=clamp(next,1,4);
    if(scale===1){panX=0;panY=0;}
    else{panX=x-(x-panX)*scale/old;panY=y-(y-panY)*scale/old;}
    renderZoom();
  }
  const source=i=>slides[i].querySelector('img');
  const loaded=new Set();
  function preload(){for(const i of [(index+1)%slides.length,(index+slides.length-1)%slides.length]){const next=source(i);if(!next)continue;const src=next.src;if(!loaded.has(src)){loaded.add(src);const img=new Image();img.src=src;}}}
  function modalImage(){
    dialog.querySelector('.lightbox-caption').textContent=slides[index].dataset.caption;
    const video=slides[index].querySelector('video');
    const placeholder=slides[index].querySelector('[data-placeholder]');
    dialog.querySelector('.lightbox-scroll [data-placeholder]')?.remove();
    zoomImage.hidden=!!video||!!placeholder;zoomVideo.hidden=!video;
    dialog.dataset.mediaKind=video?'video':'image';
    if(video){zoomVideo.querySelectorAll('track').forEach(track=>track.remove());video.querySelectorAll('track').forEach(track=>zoomVideo.append(track.cloneNode(true)));zoomVideo.poster=video.poster;zoomVideo.setAttribute('aria-label',video.getAttribute('aria-label'));prepareVideo(zoomVideo,video.dataset.source);}
    else if(placeholder){zoomVideo.pause();zoomVideo.removeAttribute('src');zoomVideo.load();dialog.querySelector('.lightbox-scroll').append(placeholder.cloneNode(true));}
    else{zoomVideo.querySelectorAll('track').forEach(track=>track.remove());zoomVideo.pause();zoomVideo.removeAttribute('src');zoomVideo.load();const img=source(index);zoomImage.src=img.src;zoomImage.alt=img.alt;zoomImage.width=Number(img.getAttribute('width'))||img.naturalWidth;zoomImage.height=Number(img.getAttribute('height'))||img.naturalHeight;}
    dialog.querySelector('[data-lightbox-count]').textContent=`${index+1} / ${slides.length}`;
  }
  function select(n,announce=true){
    pauseVideos();resetZoom();
    index=(n+slides.length)%slides.length;
    slides.forEach((slide,i)=>slide.hidden=i!==index);
    const video=slides[index].querySelector('video');frame.dataset.activeKind=video?'video':'image';
    if(opener)opener.setAttribute('aria-label',video?opener.dataset.videoLabel:opener.dataset.imageLabel);
    if(video&&!dialog.open)prepareVideo(video,video.dataset.source);
    controls.forEach(button=>{const active=Number(button.dataset.thumbTo)===index;button.setAttribute('aria-pressed',String(active));if(active){const rail=button.parentElement,left=button.offsetLeft-rail.offsetLeft;if(left<rail.scrollLeft||left+button.offsetWidth>rail.scrollLeft+rail.clientWidth)rail.scrollTo({left:left-(rail.clientWidth-button.offsetWidth)/2,behavior:'instant'});}});
    gallery.querySelector('.gallery-caption').textContent=slides[index].dataset.caption;
    gallery.querySelector('[data-gallery-count]').textContent=`${index+1} / ${slides.length}`;
    if(dialog.open)modalImage();preload();
    if(announce){event('product_gallery_slide',{asset_index:index});event('product_gallery_view',{asset_index:index});}
  }
  function lock(){const body=document.body;locked={y:scrollY,position:body.style.position,top:body.style.top,width:body.style.width,paddingRight:body.style.paddingRight};const gutter=innerWidth-document.documentElement.clientWidth;body.style.position='fixed';body.style.top=`-${locked.y}px`;body.style.width='100%';if(gutter)body.style.paddingRight=`${gutter}px`;}
  function unlock(){if(!locked)return;const body=document.body,old=locked;locked=null;for(const key of ['position','top','width','paddingRight'])body.style[key]=old[key];window.scrollTo({top:old.y,behavior:'instant'});}
  function finishClose(){if(dialog.open||!locked)return;pauseVideos();resetZoom();const video=slides[index].querySelector('video');if(video)prepareVideo(video,video.dataset.source);const target=restore;restore=null;unlock();(target?.isConnected?target:opener||frame).focus({preventScroll:true});}
  // Native close events are queued. Restore synchronously so a rapid reopen
  // cannot save a stale fixed-body state; a delayed event must not unlock it.
  function close(){dialog.close();finishClose();}
  function open(){if(dialog.open||performance.now()<swipeUntil)return;finishClose();pauseVideos();restore=document.activeElement;lock();resetZoom();modalImage();dialog.showModal();dialog.querySelector('[data-lightbox-close]').focus();event('product_gallery_view',{asset_index:index});}
  controls.forEach(button=>button.addEventListener('click',()=>select(Number(button.dataset.thumbTo))));
  for(const mode of ['gallery','lightbox'])for(const [direction,delta] of [['prev',-1],['next',1]])gallery.querySelector(`[data-${mode}-${direction}]`).onclick=()=>select(index+delta);
  if(opener)opener.onclick=open;
  gallery.addEventListener('keydown',e=>{if(e.target.closest('video'))return;if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();select(e.key==='Home'?0:e.key==='End'?slides.length-1:index+(e.key==='ArrowRight'?1:-1));}else if(opener&&e.key==='Enter'&&e.target===frame){e.preventDefault();open();}});
  function swipe(surface){let start=null;const end=(x,y)=>{if(start&&Math.abs(x-start.x)>45&&Math.abs(x-start.x)>Math.abs(y-start.y)*1.2){select(index+(x<start.x?1:-1));swipeUntil=performance.now()+400;}start=null;};
    surface.addEventListener('pointerdown',e=>{if(!e.target.closest('video')&&e.pointerType!=='touch'&&dialog.dataset.zoomed!=='true')start={x:e.clientX,y:e.clientY};});
    surface.addEventListener('pointerup',e=>{if(e.pointerType!=='touch')end(e.clientX,e.clientY);});surface.addEventListener('pointercancel',()=>start=null);
    surface.addEventListener('touchstart',e=>{if(!e.target.closest('video')&&e.touches.length===1&&dialog.dataset.zoomed!=='true')start={x:e.touches[0].clientX,y:e.touches[0].clientY};},{passive:true});
    surface.addEventListener('touchend',e=>{if(e.changedTouches.length)end(e.changedTouches[0].clientX,e.changedTouches[0].clientY);},{passive:true});surface.addEventListener('touchcancel',()=>start=null);
  }
  swipe(frame);
  const midpoint=points=>({x:(points[0].x+points[1].x)/2,y:(points[0].y+points[1].y)/2});
  const distance=points=>Math.hypot(points[0].x-points[1].x,points[0].y-points[1].y);
  const centered=point=>{const rect=viewport.getBoundingClientRect();return {x:point.x-rect.left-rect.width/2,y:point.y-rect.top-rect.height/2};};
  viewport.addEventListener('pointerdown',e=>{
    if(!dialog.open||zoomImage.hidden||e.target.closest('video'))return;
    viewport.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(pointers.size===1)gesture={kind:'pan',x:e.clientX,y:e.clientY,panX,panY};
    else if(pointers.size===2){const points=[...pointers.values()];gesture={kind:'pinch',distance:distance(points),center:centered(midpoint(points)),scale,panX,panY};}
  });
  viewport.addEventListener('pointermove',e=>{
    if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(pointers.size===2&&gesture?.kind==='pinch'){
      const points=[...pointers.values()],center=centered(midpoint(points));
      scale=clamp(gesture.scale*distance(points)/Math.max(1,gesture.distance),1,4);
      const ratio=scale/gesture.scale;
      panX=center.x-(gesture.center.x-gesture.panX)*ratio;
      panY=center.y-(gesture.center.y-gesture.panY)*ratio;
      renderZoom();
    }else if(pointers.size===1&&scale>1&&gesture?.kind==='pan'){
      panX=gesture.panX+e.clientX-gesture.x;panY=gesture.panY+e.clientY-gesture.y;renderZoom();
    }
  });
  function finishPointer(e,cancelled=false){
    if(!pointers.has(e.pointerId))return;
    if(!cancelled&&pointers.size===1&&scale===1&&gesture?.kind==='pan'){
      const dx=e.clientX-gesture.x,dy=e.clientY-gesture.y;
      if(Math.abs(dx)>45&&Math.abs(dx)>Math.abs(dy)*1.2)select(index+(dx<0?1:-1));
    }
    pointers.delete(e.pointerId);
    if(pointers.size===1){const point=[...pointers.values()][0];gesture={kind:'pan',x:point.x,y:point.y,panX,panY};}
    else gesture=null;
  }
  viewport.addEventListener('pointerup',e=>finishPointer(e));
  viewport.addEventListener('pointercancel',e=>finishPointer(e,true));
  viewport.addEventListener('dblclick',e=>{if(zoomImage.hidden)return;const center=centered({x:e.clientX,y:e.clientY});zoomTo(scale>1?1:2,center.x,center.y);});
  viewport.addEventListener('wheel',e=>{if(!e.ctrlKey||zoomImage.hidden)return;e.preventDefault();const center=centered({x:e.clientX,y:e.clientY});zoomTo(scale*Math.exp(-e.deltaY*.01),center.x,center.y);},{passive:false});
  dialog.querySelector('[data-lightbox-close]').onclick=close;
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});dialog.addEventListener('click',e=>{if(e.target===dialog)close();});
  dialog.addEventListener('close',finishClose);
  dialog.addEventListener('keydown',e=>{if(e.key==='Tab'){const buttons=[...dialog.querySelectorAll('button')].filter(b=>!b.disabled&&b.getClientRects().length),first=buttons[0],last=buttons.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
  select(0,false);
  videos.forEach(video=>video.addEventListener('play',()=>{videos.forEach(other=>{if(other!==video)other.pause();});event('product_gallery_view',{asset_index:index});}));
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseVideos();});
  window.addEventListener('pagehide',pauseVideos);
  new IntersectionObserver(entries=>{if(!dialog.open&&!entries[0].isIntersecting)pauseVideos();}).observe(frame);
}};
