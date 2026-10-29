// Shared anatomy for every external catalog product card.
export function catalogCard({className='',attributes='',media,eyebrow,title,href,titleAttributes='',description,proof,prices,primary,secondary,model,artworkModel='',mediaAccessory='',galleryPhotos=[]}){
 const plainTitle=title.replace(/<[^>]*>/g,'').replaceAll('&','&amp;').replaceAll('"','&quot;');
 const safeAttr=value=>String(value).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;');
 const artwork=artworkModel?`<img class="catalog-product-image catalog-artwork-poster" src="/assets/model-posters/${artworkModel}.webp?v=20261022-ribbons" alt="${plainTitle}" width="512" height="512" loading="lazy" decoding="async">`:media;
 const modelButton=model?`<button type="button" class="catalog-model-button" data-card-model="${model}" aria-label="3D: ${title.replace(/<[^>]*>/g,'').replaceAll('&','&amp;').replaceAll('"','&quot;')}"><span aria-hidden="true">◈</span> 3D</button>`:'';
 const photoStrip=galleryPhotos.length>1?`<div class="catalog-photo-choices" aria-label="${plainTitle}">${galleryPhotos.map((photo,i)=>`<a href="${href}" data-catalog-photo data-photo-src="${safeAttr(photo.src)}" data-photo-alt="${safeAttr(photo.alt)}" aria-label="${safeAttr(photo.label)}" ${i===0?'aria-current="true"':''}><img src="${safeAttr(photo.thumb||photo.src)}" alt="" width="72" height="72" loading="lazy" decoding="async"></a>`).join('')}</div>`:'';
 return `<article class="commerce-card catalog-card ${className}" ${attributes}><div class="commerce-card-media catalog-card-media ${photoStrip?'catalog-card-with-photos':''}">${artwork}${mediaAccessory}${modelButton}${photoStrip}</div><div class="commerce-card-copy catalog-card-copy"><p class="eyebrow catalog-card-eyebrow">${eyebrow}</p><h2><a class="commerce-card-link" href="${href}" ${titleAttributes}>${title}</a></h2><p class="catalog-card-description">${description}</p><div class="catalog-card-proof">${proof}</div><dl class="commerce-card-prices catalog-card-prices">${prices}</dl><div class="catalog-card-actions"><a class="button" href="${primary.href}" ${primary.attributes||''}>${primary.label}</a><a class="text-action" href="${secondary.href}" ${secondary.attributes||''}>${secondary.label}</a></div></div></article>`;
}

export function catalogPhotos(names,asset,locale){
 const lang={uk:'ua',en:'en',pl:'pl'}[locale];
 return names.map(name=>{const m=asset(name);const alt=m[`alt_${lang}`]||m.alt_ua||name;return {src:m.url,thumb:m.thumbnail_url||m.url,alt,label:alt};});
}
