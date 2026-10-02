// Dedicated public-solution form controller. The base physical offer remains Branded.
const form=document.querySelector('[data-niche-form]');
if(form){
 const basePath=document.documentElement.dataset.publicBasePath||'';
 const locale=document.documentElement.lang;
 const select=form.elements.namedItem('quantity');
 const price=form.querySelector('[data-niche-price]');
 const figures=[...document.querySelectorAll('.niche-pricing .price-rows dd')].map(node=>node.textContent);
 const labels={uk:'Індивідуальний розрахунок',en:'Individual quote',pl:'Wycena indywidualna'};
 const advice={uk:'Кількість визначимо разом — без ціни й передоплати.',en:'We will choose the quantity together — no price or deposit yet.',pl:'Liczbę kart dobierzemy razem — bez ceny i zaliczki na tym etapie.'};
 const current=()=>({variant:'branded',quantity:select.value});
 function update(){price.textContent=select.value==='1'?figures[0]:select.value==='2'?figures[1]:select.value==='advice'?advice[locale]:labels[locale];}
 select.addEventListener('change',update);update();
 const {mountPagesForm}=await import(basePath+'/assets/pages.mjs');
 let commerce;
 try{const response=await fetch(basePath+'/assets/content.json');if(response.ok)commerce=(await response.json()).commerce;}catch{}
 const {selectionQuote}=await import(basePath+'/assets/commerce-contract.mjs');
 mountPagesForm(form,{endpoint:document.documentElement.dataset.leadEndpoint||'',basePath,locale,pathname:location.pathname,attribution:{},selection:current,
  select:value=>{select.value=value.quantity;update();},lockSelection:()=>{},
  event:(name,value)=>{if(!['quantity_select','order_submit_success','order_submit_error'].includes(name))return;const detail={event:name,solution_id:form.dataset.solution,base_product:'branded-review-card',quantity_mode:value?.quantity==='advice'?'advice':value?.quantity,locale,route:document.body.dataset.route};window.dispatchEvent(new CustomEvent('nfc:analytics',{detail}));},
  quoteForSelection:(_variant,quantity)=>quantity==='advice'?{currency:locale==='pl'?'PLN':'UAH',amount:null,deposit:null}:commerce?selectionQuote(commerce,'branded',quantity,locale):null});
}
