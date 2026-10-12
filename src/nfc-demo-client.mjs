// Everything in this demo stays in memory. No NFC permission or form submission.
for (const demo of document.querySelectorAll('[data-nfc-demo]')) {
 const tap=demo.querySelector('[data-demo-tap]');
 const reset=demo.querySelector('[data-demo-reset]');
 const card=demo.querySelector('[data-demo-card-tap]');
 const open=demo.querySelector('[data-demo-open]');
 const home=demo.querySelector('[data-demo-home]');
 const review=demo.querySelector('[data-demo-review]');
 const complete=demo.querySelector('[data-demo-complete]');
 const status=demo.querySelector('[data-demo-status]');
 const finish=demo.querySelector('[data-demo-finish]');
 const ratingNote=demo.querySelector('[data-demo-rating-note]');
 const connection=demo.querySelector('[data-demo-connection]');
 const stars=[...demo.querySelectorAll('[data-demo-star]')];
 const situations=[...demo.querySelectorAll('[data-demo-situation]')];
 const comment=demo.querySelector('#nfc-demo-comment');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 let timer;
 let rating=0;

 function setState(state) {
  demo.dataset.state=state;
  status.textContent=status.dataset[state];
  tap.replaceChildren(document.createTextNode(state==='review'&&rating?finish.textContent:tap.dataset[state]));
  const arrow=document.createElement('span');arrow.setAttribute('aria-hidden','true');arrow.textContent='↗';tap.append(arrow);
  tap.disabled=state==='approaching';
  reset.disabled=state==='idle';
  card.disabled=state!=='idle';
  home.hidden=state==='review'||state==='done';
  open.hidden=state!=='notified';
  review.hidden=state!=='review';
  complete.hidden=state!=='done';
  const current=state==='review'||state==='done'?2:state==='notified'?1:0;
  for (const step of demo.querySelectorAll('[data-demo-step]')) {
   const index=Number(step.dataset.demoStep);
   step.classList.toggle('is-complete',index<current||state==='done');
   if(index===current)step.setAttribute('aria-current','step');else step.removeAttribute('aria-current');
  }
  connection.querySelector('span').textContent=state==='idle'||state==='approaching'?connection.dataset.idle:connection.dataset.connected;
 }
 function showReview() {
  if(demo.dataset.state!=='notified')return;
  setState('review');review.scrollTop=0;stars[0].focus({preventScroll:true});
 }
 function start() {
  if(demo.dataset.state!=='idle')return;
  setState('approaching');
  if(matchMedia('(max-width: 900px)').matches)demo.querySelector('.nfc-demo-phone').scrollIntoView({block:'center',behavior:reduced.matches?'instant':'smooth'});
  timer=setTimeout(()=>{setState('notified');open.focus({preventScroll:true});},reduced.matches?0:1050);
 }
 function restart() {
  clearTimeout(timer);rating=0;finish.disabled=true;
  for(const star of stars){star.classList.remove('is-filled');star.setAttribute('aria-pressed','false');}
  ratingNote.textContent=ratingNote.dataset.empty;comment.value='';
  review.scrollTop=0;complete.scrollTop=0;setState('idle');tap.focus({preventScroll:true});
 }
 function selectRating(value) {
  rating=value;
  for(const star of stars){star.classList.toggle('is-filled',Number(star.dataset.demoStar)<=value);star.setAttribute('aria-pressed',String(Number(star.dataset.demoStar)===value));}
  ratingNote.textContent=ratingNote.dataset.selected.replace('{n}',String(value));finish.disabled=false;
  setState('review');
 }
 function finishDemo() {
  if(demo.dataset.state!=='review'||!rating)return;
  comment.value='';setState('done');complete.querySelector('a').focus({preventScroll:true});
 }
 tap.addEventListener('click',()=>{
  const state=demo.dataset.state;
  if(state==='idle')start();else if(state==='notified')showReview();else if(state==='review'){
   if(rating)finishDemo();else stars[0].focus();
  }else if(state==='done')restart();
 });
 card.addEventListener('click',start);open.addEventListener('click',showReview);
 finish.addEventListener('click',finishDemo);reset.addEventListener('click',restart);
 for(const star of stars){
  star.addEventListener('click',()=>selectRating(Number(star.dataset.demoStar)));
  star.addEventListener('keydown',event=>{
   const value=Number(star.dataset.demoStar);
   const next={ArrowRight:Math.min(5,value+1),ArrowUp:Math.min(5,value+1),ArrowLeft:Math.max(1,value-1),ArrowDown:Math.max(1,value-1),Home:1,End:5}[event.key];
   if(next===undefined)return;event.preventDefault();selectRating(next);stars[next-1].focus({preventScroll:true});
  });
 }
 for(const option of situations)option.addEventListener('click',()=>{
  demo.dataset.situation=option.dataset.demoSituation;
  for(const item of situations)item.setAttribute('aria-pressed',String(item===option));
  demo.querySelector('[data-demo-business]').textContent=option.dataset.business;
  demo.querySelector('[data-demo-symbol]').textContent=option.dataset.symbol;
 });
}
