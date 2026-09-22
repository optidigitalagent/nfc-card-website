// Product schema v1 is additive to the accepted v6 lead/Review Card contract.
export const IG = 'instagram';
export function validateCommerce(c) {
  const fail = () => { throw Error('invalid_commerce_configuration'); };
  if(typeof c.revision!=='string'||!c.revision.length||c.revision.length>120||c.physicalProduct?.id!=='nfc-review-card')fail();
  if(c.schemaVersion!==6||c.productSchemaVersion!==1||c.currency!=='UAH'||c.market!=='UA'||c.deposit!==200||c.depositIncluded!==true)fail();
  if(JSON.stringify(Object.keys(c.variants))!==JSON.stringify(['standard','branded'])||JSON.stringify(c.interests)!==JSON.stringify(['standard','branded','bulk','consultation',IG]))fail();
  if(JSON.stringify(c.quantities)!==JSON.stringify(['1','2','more'])||JSON.stringify(c.customQuoteInterests)!==JSON.stringify(['bulk','consultation'])||c.bulkQuantity!=='more')fail();
  const p=c.products, ig=p?.['nfc-instagram-card'];
  if(ig?.pricingRevision!=='NFC-INSTAGRAM-UA-2026-09-v18'||typeof ig?.evidence!=='string'||!ig.evidence)fail();
  if(Object.keys(p||{}).sort().join()!=='nfc-instagram-card,nfc-review-card'||ig.sku!=='NFC-IG-READY'||ig.category!=='INSTAGRAM'||Object.keys(ig.offers).join()!=='ready')fail();
  const ready=ig.offers.ready;
  if(ready.customDesign!==false||ready.qr!=='not_included'||JSON.stringify(ready.quantities)!=='["1","2"]')fail();
  const expected={standard:['nfc-review-card','standard'],branded:['nfc-review-card','branded'],bulk:['nfc-review-card','custom'],consultation:['nfc-review-card','consultation'],instagram:['nfc-instagram-card','ready']};
  if(Object.keys(c.selections||{}).sort().join()!==Object.keys(expected).sort().join())fail();
  for(const [key,[product,offer]] of Object.entries(expected))if(c.selections[key]?.product_id!==product||c.selections[key]?.offer!==offer)fail();
  if(Object.keys(p['nfc-review-card'].offers).sort().join()!=='branded,standard')fail();
  for(const key of ['standard','branded'])if(p['nfc-review-card'].offers[key]?.legacyPriceKey!==key)fail();
  for(const prices of [c.variants.standard.prices,c.variants.branded.prices,ready.prices])if(Object.keys(prices).join()!=='1,2'||!Object.values(prices).every(n=>Number.isInteger(n)&&n>=c.deposit&&n<100000000))fail();
  if(ready.prices['1']!==1500||ready.prices['2']!==2600)fail();
  return c;
}
export function selectionQuote(c, selection, quantity='1') {
  const q=String(quantity), spec=c.selections[selection];
  const valid=!!spec&&c.quantities.includes(q)&&(selection!==IG||['1','2'].includes(q));
  const offer=spec&&c.products[spec.product_id].offers[spec.offer];
  const prices=offer?.legacyPriceKey?c.variants[offer.legacyPriceKey].prices:offer?.prices;
  return {valid,pricingRevision:spec?(c.products[spec.product_id].pricingRevision||c.revision):c.revision,evidence:spec?(c.products[spec.product_id].evidence||c.evidence):c.evidence,amount:valid&&q!=='more'?(prices?.[q]??null):null,...(spec||{})};
}

// Accept exact HTTPS profile URLs only, never redirects, credentials or content URLs.
export function instagramProfileURL(value) {
  if(typeof value!=='string'||value.length>250||!/^https:\/\/(?:www\.)?instagram\.com\/[A-Za-z0-9._]{1,30}\/?$/i.test(value))return null;
  const name=value.split('/')[3].toLowerCase();
  if(name.startsWith('.')||name.endsWith('.')||name.includes('..')||new Set(['p','reel','reels','stories','explore','accounts','direct','about','legal','developer','developers','web','api','challenge','oauth','tv']).has(name))return null;
  return 'https://www.instagram.com/'+name+'/';
}
