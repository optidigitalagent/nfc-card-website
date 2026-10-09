// Shared gallery: approved image treatment plus manual video playback.
export function galleryView({variant,names,title,locale,P,esc,picture,asset,temporaryNote,captionMode}) {
  const suffix={uk:'ua',en:'en',pl:'pl'}[locale];
  if(!suffix)throw Error('Unsupported gallery locale: '+locale);
  const mediaText=(entry,field)=>{
    const key=field+'_'+suffix;
    if(!Object.hasOwn(entry,key)||typeof entry[key]!=='string')throw Error('Missing gallery '+key);
    return entry[key];
  };
  const placeholder=name=>asset(name).media_type==='placeholder';
  const placeholderOnly=names.every(placeholder);
  const video=name=>asset(name).media_type==='video';
  const hasVideo=names.some(video);
  const caption=name=>{
    const m=asset(name);
    if(captionMode==='physical-mini-example'){
      const kind=m.product_id==='beauty-review-card'?'beauty':m.product_id==='restaurant-review-card'?'restaurant':null;
      if(!kind)throw Error('Physical Mini example requires a niche photo: '+name);
      return {
        uk:kind==='beauty'?'Приклад фізичного формату Beauty Review Card Mini: на фото готовий рожевий дизайн. Ваш персональний дизайн підготуємо окремо.':'Приклад фізичного формату Restaurant Review Card Mini: на фото готовий зелено-бежевий дизайн. Ваш персональний дизайн підготуємо окремо.',
        en:kind==='beauty'?'Beauty Review Card Mini physical-format example: the photo shows the ready-made pink design. Your custom design is prepared separately.':'Restaurant Review Card Mini physical-format example: the photo shows the ready-made green and beige design. Your custom design is prepared separately.',
        pl:kind==='beauty'?'Przykład fizycznego formatu Beauty Review Card Mini: zdjęcie pokazuje gotowy różowy wzór. Indywidualny projekt przygotujemy osobno.':'Przykład fizycznego formatu Restaurant Review Card Mini: zdjęcie pokazuje gotowy zielono-beżowy wzór. Indywidualny projekt przygotujemy osobno.'
      }[locale];
    }
    if(m.caption_ua&&m.caption_en)return mediaText(m,'caption');
    if(variant==='menu')return P('Візуалізація NFC Menu Card; форма та колір показані для вибору виконання.','NFC Menu Card visualization showing a format and colour option.');
    return variant==='branded'?temporaryNote:name.startsWith('05')?P('Промоілюстрація переходу до форми. Оцінку, текст і публікацію обирає клієнт.','An illustration of the path to the form. The customer chooses the rating, text and publication.'):name.startsWith('01')?P('Візуалізація готового дизайну Google Review Card.','A render of the ready-made Google Review Card design.'):P('Реальне фото поточної Google Review Card: формат, масштаб і поверхня.','An actual photo of the current Google Review Card: format, scale and finish.');
  };
  const label=name=>placeholder(name)?P('місце для майбутнього фото','future photo placeholder'):video(name)?P('відео','video'):P('зображення','image');
  const rail=()=>`<div class="commerce-thumbnails" aria-label="${hasVideo?P('Мініатюри фото та відео','Photo and video thumbnails'):P('Мініатюри фото','Photo thumbnails')}">${names.map((name,i)=>`<button type="button" data-thumb-to="${i}" aria-label="${P('Показати','Show')} ${label(name)} ${i+1} ${P('із','of')} ${names.length}" aria-pressed="${i===0}">${placeholder(name)?`<span class="placeholder-thumb" aria-hidden="true">${esc(mediaText(asset(name),'alt'))}</span>`:`<img src="${asset(name).thumbnail_url||asset(name).url}" alt="" width="160" height="160" loading="lazy">`}${video(name)?'<span class="thumb-video" aria-hidden="true">▶</span>':''}</button>`).join('')}</div>`;
  const arrow=(direction,modal=false)=>`<button type="button" class="icon-button" data-${modal?'lightbox':'gallery'}-${direction} aria-label="${direction==='prev'?P('Попередній матеріал','Previous item'):P('Наступний матеріал','Next item')}">${direction==='prev'?'←':'→'}</button>`;
  const slides=names.map((name,i)=>{
    const m=asset(name);
    const content=video(name)?`<video class="commerce-gallery-image gallery-video" controls playsinline preload="none" poster="${m.poster_url}" data-source="${m.url}" width="${m.width}" height="${m.height}" aria-label="${esc(mediaText(m,'alt'))}" data-media-provenance="${m.provenance}" data-media-claim-role="${m.claim_role}">${(m.tracks||[]).map(track=>`<track kind="subtitles" src="${track.url}" srclang="${track.language}" label="${track.label}" ${locale===track.language?'default':''}>`).join('')}</video>`:picture(name,'commerce-gallery-image',i===0);
    return `<figure data-slide="${i}" data-kind="${placeholder(name)?'placeholder':video(name)?'video':'image'}" data-caption="${esc(caption(name))}" ${i?'hidden':''}>${content}</figure>`;
  }).join('');
  const frameLabel=placeholderOnly?P('Майбутні фото. Стрілки — попередній або наступний матеріал.','Planned photos. Arrow keys change items.'):hasVideo?P('Фото та відео. Стрілки — попередній або наступний матеріал; Enter — відкрити.','Photos and videos. Arrow keys change items; Enter opens the viewer.'):P('Фото. Стрілки — попереднє або наступне фото; Enter — відкрити.','Photos. Arrow keys change the photo; Enter opens the viewer.');
  const opener=placeholderOnly?'':`<button type="button" class="gallery-open" aria-label="${P('Збільшити зображення','Enlarge image')}" data-image-label="${P('Збільшити зображення','Enlarge image')}" data-video-label="${P('Відкрити відео у переглядачі','Open video in viewer')}" data-zoom><span aria-hidden="true" class="gallery-enlarge">⤢</span></button>`;
  return `<div class="commerce-gallery" data-commerce-gallery aria-label="${P('Галерея','Gallery')} ${title}"><div class="gallery-frame" tabindex="0" role="group" aria-label="${frameLabel}" data-gallery-frame>${slides}${opener}</div><div class="gallery-controls">${arrow('prev')}<span class="gallery-hint">${placeholderOnly?P('Майбутні фото','Planned photos'):hasVideo?P('Гортайте фото та відео','Browse photos and videos'):P('Гортайте фото','Browse photos')}</span><output data-gallery-count aria-live="polite">1 / ${names.length}</output>${arrow('next')}</div>${rail()}<p class="gallery-caption">${esc(caption(names[0]))}</p><dialog class="image-lightbox" aria-describedby="gallery-viewer-caption" aria-label="${hasVideo?P('Перегляд фото та відео картки','Card photo and video viewer'):P('Перегляд фото картки','Card photo viewer')}"><div class="lightbox-toolbar">${arrow('prev',true)}<output data-lightbox-count aria-live="polite">1 / ${names.length}</output>${arrow('next',true)}<button type="button" class="icon-button" data-lightbox-close aria-label="${P('Закрити переглядач','Close viewer')}">×</button></div><div class="lightbox-scroll" aria-label="${P('Зведіть або розведіть пальці, щоб змінити масштаб; перетягніть збільшене фото','Pinch to zoom; drag the enlarged image to pan')}"><img alt="" width="1600" height="1000" draggable="false"><video hidden controls playsinline preload="none" aria-label="${P('Відео','Video')} ${title}"></video></div><p class="lightbox-caption" id="gallery-viewer-caption">${esc(caption(names[0]))}</p></dialog></div>`;
}
