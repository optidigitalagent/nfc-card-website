/* Scoped, dependency-free carousel; order/review state is owned by existing clients. */
window.NFCGallery={mount(gallery,event){
  const slides=[...gallery.querySelectorAll('[data-slide]')],frame=gallery.querySelector('[data-gallery-frame]'),dialog=gallery.querySelector('dialog'),zoomImage=dialog.querySelector('.lightbox-scroll img'),opener=gallery.querySelector('[data-zoom]');
  const controls=[...gallery.querySelectorAll('[data-thumb-to],[data-lightbox-to]')];
  let index=0,restore=null,locked=null,swipeUntil=0;
  const source=i=>slides[i].querySelector('img');
  const loaded=new Set();
  function preload(){for(const i of [(index+1)%slides.length,(index+slides.length-1)%slides.length]){const src=source(i).src;if(!loaded.has(src)){loaded.add(src);const img=new Image();img.src=src;}}}
  function modalImage(){const img=source(index);zoomImage.src=img.src;zoomImage.alt=img.alt;zoomImage.width=Number(img.getAttribute('width'))||img.naturalWidth;zoomImage.height=Number(img.getAttribute('height'))||img.naturalHeight;dialog.querySelector('[data-lightbox-count]').textContent=`${index+1} / ${slides.length}`;}
  function select(n,announce=true){
    index=(n+slides.length)%slides.length;
    slides.forEach((slide,i)=>slide.hidden=i!==index);
    controls.forEach(button=>{const active=Number(button.dataset.thumbTo??button.dataset.lightboxTo)===index;button.setAttribute('aria-pressed',String(active));if(active){const rail=button.parentElement,left=button.offsetLeft-rail.offsetLeft;if(left<rail.scrollLeft||left+button.offsetWidth>rail.scrollLeft+rail.clientWidth)rail.scrollTo({left:left-(rail.clientWidth-button.offsetWidth)/2,behavior:'instant'});}});
    gallery.querySelector('.gallery-caption').textContent=slides[index].dataset.caption;
    gallery.querySelector('[data-gallery-count]').textContent=`${index+1} / ${slides.length}`;
    if(dialog.open)modalImage();preload();
    if(announce){event('product_gallery_slide',{asset_index:index});event('product_gallery_view',{asset_index:index});}
  }
  function lock(){const body=document.body;locked={y:scrollY,position:body.style.position,top:body.style.top,width:body.style.width,paddingRight:body.style.paddingRight};const gutter=innerWidth-document.documentElement.clientWidth;body.style.position='fixed';body.style.top=`-${locked.y}px`;body.style.width='100%';if(gutter)body.style.paddingRight=`${gutter}px`;}
  function unlock(){if(!locked)return;const body=document.body,old=locked;locked=null;for(const key of ['position','top','width','paddingRight'])body.style[key]=old[key];window.scrollTo({top:old.y,behavior:'instant'});}
  function finishClose(){if(dialog.open||!locked)return;dialog.dataset.zoomed='false';dialog.querySelector('[data-lightbox-zoom]').setAttribute('aria-pressed','false');const target=restore;restore=null;unlock();(target?.isConnected?target:opener).focus({preventScroll:true});}
  // Native close events are queued. Restore synchronously so a rapid reopen
  // cannot save a stale fixed-body state; a delayed event must not unlock it.
  function close(){dialog.close();finishClose();}
  function open(){if(dialog.open||performance.now()<swipeUntil)return;finishClose();restore=document.activeElement;lock();modalImage();dialog.showModal();dialog.querySelector('[data-lightbox-close]').focus();event('product_gallery_view',{asset_index:index});}
  controls.forEach(button=>button.addEventListener('click',()=>select(Number(button.dataset.thumbTo??button.dataset.lightboxTo))));
  for(const mode of ['gallery','lightbox'])for(const [direction,delta] of [['prev',-1],['next',1]])gallery.querySelector(`[data-${mode}-${direction}]`).onclick=()=>select(index+delta);
  opener.onclick=open;
  gallery.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();select(e.key==='Home'?0:e.key==='End'?slides.length-1:index+(e.key==='ArrowRight'?1:-1));}else if(e.key==='Enter'&&e.target===frame){e.preventDefault();open();}});
  function swipe(surface){let start=null;const end=(x,y)=>{if(start&&Math.abs(x-start.x)>45&&Math.abs(x-start.x)>Math.abs(y-start.y)*1.2){select(index+(x<start.x?1:-1));swipeUntil=performance.now()+400;}start=null;};
    surface.addEventListener('pointerdown',e=>{if(e.pointerType!=='touch'&&dialog.dataset.zoomed!=='true')start={x:e.clientX,y:e.clientY};});
    surface.addEventListener('pointerup',e=>{if(e.pointerType!=='touch')end(e.clientX,e.clientY);});surface.addEventListener('pointercancel',()=>start=null);
    surface.addEventListener('touchstart',e=>{if(e.touches.length===1&&dialog.dataset.zoomed!=='true')start={x:e.touches[0].clientX,y:e.touches[0].clientY};},{passive:true});
    surface.addEventListener('touchend',e=>{if(e.changedTouches.length)end(e.changedTouches[0].clientX,e.changedTouches[0].clientY);},{passive:true});surface.addEventListener('touchcancel',()=>start=null);
  }
  swipe(frame);swipe(dialog.querySelector('.lightbox-scroll'));
  dialog.querySelector('[data-lightbox-close]').onclick=close;
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});dialog.addEventListener('click',e=>{if(e.target===dialog)close();});
  dialog.addEventListener('close',finishClose);
  dialog.querySelector('[data-lightbox-zoom]').onclick=e=>{const zoom=dialog.dataset.zoomed!=='true';dialog.dataset.zoomed=String(zoom);dialog.querySelector('.lightbox-scroll').scrollTo({left:0,top:0,behavior:'instant'});e.currentTarget.setAttribute('aria-pressed',String(zoom));};
  dialog.addEventListener('keydown',e=>{if(e.key==='Tab'){const buttons=[...dialog.querySelectorAll('button')].filter(b=>!b.disabled&&b.getClientRects().length),first=buttons[0],last=buttons.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
  select(0,false);
}};
