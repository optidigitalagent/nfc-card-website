// A local simulation: no NFC permission, network requests, or persistent storage.
for (const demo of document.querySelectorAll('[data-nfc-demo]')) {
 const tap=demo.querySelector('[data-demo-tap]');
 const reset=demo.querySelector('[data-demo-reset]');
 const open=demo.querySelector('[data-demo-open]');
 const home=demo.querySelector('[data-demo-home]');
 const review=demo.querySelector('[data-demo-review]');
 const complete=demo.querySelector('[data-demo-complete]');
 const status=demo.querySelector('[data-demo-status]');
 const finish=demo.querySelector('[data-demo-finish]');
 const stars=[...demo.querySelectorAll('[data-demo-star]')];
 let timer;

 function setState(state) {
  demo.dataset.state=state;
  status.textContent=status.dataset[state];
  tap.hidden=state!=='idle' && state!=='approaching';
  tap.disabled=state==='approaching';
  reset.hidden=state==='idle';
  home.hidden=state==='review' || state==='done';
  open.hidden=state!=='notified';
  review.hidden=state!=='review';
  complete.hidden=state!=='done';
  const current=state==='review' || state==='done'?2:state==='notified'?1:0;
  for (const step of demo.querySelectorAll('[data-demo-step]')) {
   if (Number(step.dataset.demoStep)===current) step.setAttribute('aria-current','step');
   else step.removeAttribute('aria-current');
  }
 }
 tap.addEventListener('click',()=>{
  if (demo.dataset.state!=='idle') return;
  setState('approaching');
  timer=setTimeout(()=>{
   setState('notified');
   open.focus({preventScroll:true});
  },matchMedia('(prefers-reduced-motion: reduce)').matches?0:850);
 });
 open.addEventListener('click',()=>{
  setState('review');
  stars[0].focus({preventScroll:true});
 });
 for (const star of stars) star.addEventListener('click',()=>{
  const rating=Number(star.dataset.demoStar);
  for (const item of stars) {
   item.classList.toggle('is-filled',Number(item.dataset.demoStar)<=rating);
   item.setAttribute('aria-pressed',String(item===star));
  }
  finish.disabled=false;
 });
 finish.addEventListener('click',()=>{
  if (finish.disabled) return;
  setState('done');
  demo.querySelector('#nfc-demo-comment').value='';
  complete.querySelector('a').focus({preventScroll:true});
 });
 reset.addEventListener('click',()=>{
  clearTimeout(timer);
  finish.disabled=true;
  for (const star of stars) {star.classList.remove('is-filled');star.setAttribute('aria-pressed','false');}
  demo.querySelector('#nfc-demo-comment').value='';
  setState('idle');
  tap.focus({preventScroll:true});
 });
}
