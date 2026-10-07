// The Mini selector is an enquiry UI. The gateway recalculates every quote.
const form=document.querySelector('[data-niche-form]');
if(form){
 const basePath=document.documentElement.dataset.publicBasePath||'';
 const locale=document.documentElement.lang;
 const select=form.elements.namedItem('quantity'),custom=form.elements.namedItem('customQuantity');
 const price=form.querySelector('[data-niche-price]');
 const figures=[...document.querySelectorAll('.niche-pricing .price-rows dd')].map(node=>node.textContent);
 const labels={uk:'Індивідуальний розрахунок — без ціни й передоплати на цьому етапі.',en:'Individual quote — no price or deposit at this stage.',pl:'Wycena indywidualna — bez ceny i zaliczki na tym etapie.'};
 const concept={uk:'3–4 початкові концепції безкоштовно — без ціни й передоплати.',en:'3–4 initial concepts free of charge — no price or deposit.',pl:'3–4 wstępne projekty bezpłatnie — bez ceny i zaliczki.'};
 const draftKey=`nfc-mini-selection:${location.pathname.replace(/\/$/,'')}`;
 const saveChoice=()=>{try{sessionStorage.setItem(draftKey,select.value)}catch{}};
 const current=()=>({variant:form.elements.namedItem('variant').value,quantity:select.value});
 function update(){
  const other=select.value==='other',customBox=form.querySelector('[data-custom-quantity]');
  customBox.hidden=!other;custom.disabled=!other;custom.required=other;
  price.textContent=select.value==='concepts'?concept[locale]:['1','2','4','10'].includes(select.value)&&locale!=='pl'?figures[['1','2','4','10'].indexOf(select.value)]:labels[locale];
  if(!form.dataset.complete && form.dataset.attemptState!=='uncertain')form.querySelector('.submit-button').textContent=select.value==='concepts'?form.dataset.conceptsSubmit:form.dataset.physicalSubmit;
 }
 select.addEventListener('change',()=>{update();saveChoice()});custom.addEventListener('input',update);update();
 const {mountPagesForm}=await import(basePath+'/assets/pages.mjs');
 mountPagesForm(form,{endpoint:document.documentElement.dataset.leadEndpoint||'',basePath,locale,pathname:location.pathname,attribution:{},selection:current,
  select:value=>{select.value=value.quantity;update();},lockSelection:()=>{},
  event:(name,value)=>{if(!['quantity_select','order_submit_success','order_submit_error'].includes(name))return;const detail={event:name,product_family:'nfc-review-card-mini',solution_id:form.dataset.solution,niche:form.dataset.solution.includes('beauty')?'beauty':'restaurant',design_mode:form.dataset.designMode,quantity_mode:value?.quantity,locale,route:document.body.dataset.route};window.dispatchEvent(new CustomEvent('nfc:analytics',{detail}));},
  quoteForSelection:()=>({currency:locale==='pl'?'PLN':'UAH',amount:null,deposit:null})});
 const allowed=new Set(['1','2','4','10','other','advice',...(form.dataset.designMode==='branded'?['concepts']:[])]);
 const applyChoice=value=>{
  if(!allowed.has(value))return false;
  if(form.applyNicheIntent)return form.applyNicheIntent(value);
  select.value=value;update();return true;
 };
 const query=new URLSearchParams(location.search);
 const intent=query.get('intent');
 const initial=intent==='concepts'&&form.dataset.designMode==='branded'?'concepts':intent==='advice'?'advice':intent==='order'&&['1','2','4','10'].includes(query.get('quantity'))?query.get('quantity'):null;
 let remembered=null;try{remembered=sessionStorage.getItem(draftKey)}catch{}
 const initialApplied=initial?applyChoice(initial):false;
 if(!initial&&allowed.has(remembered))applyChoice(remembered);
 update();
 if(initial){if(initialApplied)saveChoice();const clean=new URL(location.href);clean.searchParams.delete('intent');clean.searchParams.delete('quantity');history.replaceState(history.state,'',clean);}
 document.addEventListener('click',event=>{
  const a=event.target.closest?.('a[data-niche-intent]');if(!a)return;
  const target=new URL(a.href,location.href);
  if(target.origin!==location.origin||target.pathname.replace(/\/$/,'')!==location.pathname.replace(/\/$/,''))return;
  event.preventDefault();
  const requested=a.dataset.nicheIntent==='concepts'&&form.dataset.designMode==='branded'?'concepts':a.dataset.nicheIntent==='advice'?'advice':null;
  if(requested&&applyChoice(requested)){saveChoice();update();}
  document.getElementById('request')?.scrollIntoView({behavior:'smooth'});
 });
 document.querySelectorAll('.locale-switch').forEach(a=>a.addEventListener('click',()=>{
  if(form.dataset.attemptState!=='draft')return;
  const target=new URL(a.href,location.href);
  if(!target.pathname.endsWith('/'))target.pathname+='/';
  if(select.value==='concepts')target.searchParams.set('intent','concepts');
  else if(select.value==='advice')target.searchParams.set('intent','advice');
  else if(['1','2','4','10'].includes(select.value)){target.searchParams.set('intent','order');target.searchParams.set('quantity',select.value);}
  a.href=target.href;
 }));
}
