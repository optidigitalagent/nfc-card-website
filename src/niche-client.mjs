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
 const current=()=>({variant:form.elements.namedItem('variant').value,quantity:select.value});
 function update(){
  const other=select.value==='other',customBox=form.querySelector('[data-custom-quantity]');
  customBox.hidden=!other;custom.disabled=!other;custom.required=other;
  price.textContent=select.value==='concepts'?concept[locale]:['1','2','4','10'].includes(select.value)&&locale!=='pl'?figures[['1','2','4','10'].indexOf(select.value)]:labels[locale];
 }
 select.addEventListener('change',update);custom.addEventListener('input',update);update();
 const {mountPagesForm}=await import(basePath+'/assets/pages.mjs');
 mountPagesForm(form,{endpoint:document.documentElement.dataset.leadEndpoint||'',basePath,locale,pathname:location.pathname,attribution:{},selection:current,
  select:value=>{select.value=value.quantity;update();},lockSelection:()=>{},
  event:(name,value)=>{if(!['quantity_select','order_submit_success','order_submit_error'].includes(name))return;const detail={event:name,product_family:'nfc-review-card-mini',solution_id:form.dataset.solution,niche:form.dataset.solution.includes('beauty')?'beauty':'restaurant',design_mode:form.dataset.designMode,quantity_mode:value?.quantity,locale,route:document.body.dataset.route};window.dispatchEvent(new CustomEvent('nfc:analytics',{detail}));},
  quoteForSelection:()=>({currency:locale==='pl'?'PLN':'UAH',amount:null,deposit:null})});
}
