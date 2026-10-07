// v31 Mini pricing is a separate contract from the original Review Card range.
export const MINI_PRODUCTS = Object.freeze({
  'beauty-review-card': {niche:'beauty',designMode:'ready'},
  'branded-beauty-review-card': {niche:'beauty',designMode:'branded'},
  'restaurant-review-card': {niche:'restaurant',designMode:'ready'},
  'branded-restaurant-review-card': {niche:'restaurant',designMode:'branded'}
});
export const MINI_QUANTITIES = Object.freeze([1,2,4,10]);
const TIERS = Object.freeze({
  ready:{1:900,2:720,4:650,10:440},
  branded:{1:900,2:900,4:750,10:500}
});
export function miniQuote(solutionId, quantity, locale='uk', mode='physical_order') {
  const product=MINI_PRODUCTS[solutionId];
  if(!product || !['uk','en','pl'].includes(locale))throw Error('invalid_mini_selection');
  const active=['physical_order','free_design_concepts','quantity_advice'].includes(mode);
  if(!active || (mode==='free_design_concepts'&&product.designMode!=='branded'))throw Error('invalid_mini_request');
  const number=Number(quantity);
  if(mode==='physical_order'&&(!Number.isSafeInteger(number)||number<1||number>10000))throw Error('invalid_mini_quantity');
  const fixed=mode==='physical_order'&&locale!=='pl'&&MINI_QUANTITIES.includes(number);
  const unitPrice=fixed?TIERS[product.designMode][number]:null;
  return {productFamily:'nfc-review-card-mini',solutionId,niche:product.niche,designMode:product.designMode,
    quantity:mode==='physical_order'?number:null,quantityMode:mode==='physical_order'?(fixed?'fixed_bundle':'custom_quote'):mode,
    unitPrice,amount:fixed?unitPrice*number:null,currency:locale==='pl'?'PLN':'UAH',
    deposit:fixed?200:null,depositDueNow:false,pricingRevision:'NFC-CARD-BEAUTY-RESTAURANT-MINI-PRICE-v31'};
}
