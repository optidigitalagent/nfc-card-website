import aboutContent from './about-content.json' with {type:'json'};
import aboutMedia from './about-media.json' with {type:'json'};

export {aboutContent};

/** All biography and approved derivatives come from the v13 pinned source. */
export function aboutPage({locale,esc,url,finalCTA}) {
  if (!['uk','en'].includes(locale)) throw new Error('Unsupported About locale');
  const c=aboutContent[locale],f=c.founder,l=c.labels;
  const paragraphs=items=>items.map(p=>`<p>${esc(p)}</p>`).join('');
  const section=(id,title,body,cls='')=>`<section class="section about-chapter ${cls}" id="${id}" aria-labelledby="${id}-title"><h2 id="${id}-title">${esc(title)}</h2>${body}</section>`;
  const photo=(id,cls='',sizes='(max-width:767px) calc(100vw - 40px), (max-width:1440px) 45vw, 620px')=>{
    const m=aboutMedia[id];
    const desktop=m.variants.find(v=>v.role==='desktop'&&v.format==='webp');
    const sources=['mobile','desktop'].map(role=>m.variants.filter(v=>v.role===role).map(v=>`<source type="image/${v.format}" media="(${role==='mobile'?'max':'min'}-width:${role==='mobile'?767:768}px)" srcset="${esc(v.file)} ${v.width}w" sizes="${esc(sizes)}" width="${v.width}" height="${v.height}">`).join('')).join('');
    return `<figure class="about-photo ${cls}" data-founder-photo="${id}"><picture>${sources}<img src="${esc(desktop.file)}" width="${desktop.width}" height="${desktop.height}" alt="${esc(m.alt[locale])}" loading="lazy" decoding="async" sizes="${esc(sizes)}" data-media-provenance="verified_official_business_asset" data-media-claim-role="founder_personal_history"></picture></figure>`;
  };
  const editorialList=items=>`<ol class="about-editorial-list">${items.map((item,i)=>`<li><span class="about-index" aria-hidden="true">${String(i+1).padStart(2,'0')}</span><h3>${esc(item.title)}</h3><p>${esc(item.body)}</p></li>`).join('')}</ol>`;
  const ending={heading:l.ctaTitle,body:l.ctaBody,primaryLabel:l.cta,primaryHref:url('/solutions'),secondaryLabel:l.contact,secondaryHref:url('/contact'),primaryEvent:null,secondaryEvent:null};
  const fallbackCTA=`<section class="section final-conversion" aria-labelledby="about-cta-title"><div><h2 id="about-cta-title">${esc(ending.heading)}</h2><p>${esc(ending.body)}</p></div><div class="about-actions"><a class="button" href="${esc(ending.primaryHref)}">${esc(ending.primaryLabel)}</a><a class="text-action" href="${esc(ending.secondaryHref)}">${esc(ending.secondaryLabel)}</a></div></section>`;
  return `<div class="about-page">
    <section class="about-intro" aria-labelledby="about-title"><div class="section">
      <nav class="breadcrumbs" aria-label="${locale==='uk'?'Навігаційний шлях':'Breadcrumb'}"><a href="${esc(url('/'))}">${esc(l.home)}</a><span aria-hidden="true">/</span><span aria-current="page">${esc(l.about)}</span></nav>
      <p class="eyebrow">${esc(c.behind.eyebrow)}</p><h1 id="about-title">${esc(c.behind.title)}</h1>
      <div class="about-intro-copy">${paragraphs(c.behind.paragraphs)}</div>
      <a class="about-story-link" href="#about-founder-story">${esc(c.behind.link)} <span aria-hidden="true">↓</span></a>
    </div></section>
    <section class="section about-founder about-chapter" id="about-founder-story" aria-labelledby="about-founder-story-title">
      ${photo('portrait','about-portrait','(max-width:767px) min(100vw - 40px, 360px), (max-width:1440px) 33vw, 440px')}
      <div class="about-copy"><p class="eyebrow">${esc(l.founder)}</p><h2 id="about-founder-story-title">${esc(f.title)}</h2>${paragraphs(f.paragraphs)}<p class="about-education">${esc(f.education)}</p></div>
    </section>
    ${section('founder-timeline',f.timelineTitle,`<ol class="about-timeline">${f.timeline.map((step,i)=>`<li><span class="about-index" aria-hidden="true">${String(i+1).padStart(2,'0')}</span><h3>${esc(step.title)}</h3><p>${esc(step.body)}</p></li>`).join('')}</ol>`)}
    ${section('founder-hockey',f.hockey.title,`<div class="about-chapter-copy">${paragraphs(f.hockey.paragraphs)}</div><div class="about-photo-pair about-hockey-photos">${photo('hockey-team')}${photo('hockey-puck')}</div>`)}
    ${section('founder-water',f.water.title,`<div class="about-chapter-copy">${paragraphs(f.water.paragraphs)}</div><div class="about-photo-pair about-water-photos">${photo('gopro')}${photo('jetski')}</div>${photo('boat','about-boat','(max-width:767px) calc(100vw - 40px), (max-width:1060px) 90vw, 960px')}`)}
    ${section('founder-competencies',f.competenciesTitle,editorialList(f.competencies))}
    ${section('company-principles',f.principlesTitle,editorialList(f.principles))}
    ${section('founder-philosophy',f.philosophyTitle,`<div class="about-philosophy-grid">${photo('urban','about-urban','(max-width:767px) 240px, 300px')}<div class="about-copy"><blockquote>${paragraphs(f.philosophy)}</blockquote><h3>${esc(f.responsibilityTitle)}</h3><p>${esc(f.responsibility)}</p></div></div>`)}
    ${section('ecosystem',c.company.title,`<div class="about-company-copy"><div>${paragraphs(c.company.paragraphs)}</div><div>${paragraphs(c.company.productParagraphs)}<p class="about-formula">${esc(c.formula)}</p></div></div><ul class="about-ecosystem">${c.company.items.map((item,i)=>`<li${i===0?' class="about-current-product"':''}>${i<2?`<span class="eyebrow">${esc(i===0?l.current:l.sibling)}</span>`:''}<h3>${esc(item.title)}</h3><p>${esc(item.body)}</p></li>`).join('')}</ul>`,'about-company')}
    <section class="section about-chapter about-mission" id="why-nfc-card" aria-labelledby="why-nfc-card-title"><p class="eyebrow">${esc(c.why.eyebrow)}</p><h2 id="why-nfc-card-title">${esc(c.why.title)}</h2><div class="about-chapter-copy">${paragraphs(c.why.paragraphs)}</div><dl><div><dt>${esc(c.why.missionLabel)}</dt><dd>${esc(c.why.mission)}</dd></div><div><dt>${esc(c.why.visionLabel)}</dt><dd>${esc(c.why.vision)}</dd></div></dl></section>
    ${finalCTA?finalCTA(ending):fallbackCTA}
  </div>`;
}
