// Shared Pages build/client boundary. Only explicit public configuration belongs here.
import {instagramProfileURL} from './commerce-contract.mjs';
export function publicBasePath(value = '') {
  if (value === '' || value === '/') return '';
  if (typeof value !== 'string' || !/^\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_-]+\/?$/.test(value)) {
    throw Error('Invalid NFC_PUBLIC_BASE_PATH');
  }
  return value.replace(/\/$/, '');
}

export function publicURL(value, {basePath = '', origin = ''} = {}) {
  if (!basePath || typeof value !== 'string') return value;
  if (origin && value === origin) return origin + basePath + '/';
  if (origin && value.startsWith(origin + '/')) return origin + publicURL(value.slice(origin.length), {basePath});
  if (!value.startsWith('/') || value.startsWith('//')) return value;
  if (value === basePath || value.startsWith(basePath + '/') || value.startsWith(basePath + '?') || value.startsWith(basePath + '#')) return value;
  return basePath + value;
}

export function publicData(value, publication) {
  if (typeof value === 'string') return publicURL(value, publication);
  if (Array.isArray(value)) return value.map(item => publicData(item, publication));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, publicData(item, publication)]));
  return value;
}

export function publicHTML(html, publication) {
  return html.replace(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g, (_, json) =>
    '<script type="application/ld+json">' + JSON.stringify(publicData(JSON.parse(json), publication)).replaceAll('<', '\\u003c') + '</script>')
    .replace(/\b(href|src|poster|action|data-source)="([^"]*)"/g, (_, attr, value) => `${attr}="${publicURL(value, publication)}"`)
    .replace(/\bsrcset="([^"]*)"/g, (_, value) => 'srcset="' + value.split(',').map(item => item.trim().split(/\s+/).map((part, i) => i ? part : publicURL(part, publication)).join(' ')).join(', ') + '"')
    .replace(/(<meta property="og:url" content=")([^"]*)/g, (_, start, value) => start + publicURL(value, publication))
    .replace(/(name="source" value=")([^"]*)/g, (_, start, value) => start + publicURL(value, publication));
}

export function publicCSS(css, publication) {
  return css.replace(/url\((['"]?)(\/[^)'"\s]+)\1\)/g, (_, quote, value) => `url(${quote}${publicURL(value, publication)}${quote})`);
}

// This is a public browser-facing bridge URL, never a private gateway URL or a
// credential-bearing URL. Supplying it is an operator's explicit configuration;
// URL validation alone does not establish that a service stores leads durably.
export function leadEndpoint(value = '') {
  if (value === '') return '';
  const invalid = () => { throw Error('Invalid NFC_LEAD_ENDPOINT: public HTTPS URL without credentials, query or fragment required'); };
  if (typeof value !== 'string' || value.length > 2048 || /[\s<>"'\\%?#]/.test(value) || !value.startsWith('https://')) return invalid();
  let url;
  try { url = new URL(value); } catch { return invalid(); }
  const host = url.hostname;
  if (url.protocol !== 'https:' || url.username || url.password || url.port || url.search || url.hash ||
      host.length > 253 || host.split('.').some(label => label.length > 63) ||
      !/^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,63}$/.test(host) ||
      /(^|\.)(localhost|local|internal|invalid|test|example)$/.test(host) ||
      ['api.telegram.org', 't.me', 'telegram.me'].includes(host) ||
      url.pathname === '/' || !/^\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_-]+\/?$/.test(url.pathname) ||
      value !== url.href) return invalid();
  return url.href;
}

export const unavailable = locale => locale === 'uk'
  ? 'Онлайн-заявки тимчасово недоступні у preview-версії. Функцію буде активовано після підключення захищеного збереження заявок.'
  : 'Online enquiries are temporarily unavailable in the preview version. The feature will be enabled after secure lead storage is connected.';

export const previewCSS = '.header .preview-brand{display:flex;flex-direction:column;justify-content:center;gap:2px;flex-shrink:0}.preview-badge{display:block;width:max-content;font-size:9px;line-height:1.1;letter-spacing:.08em;font-weight:600;color:var(--nfc-steel-700)}';

export function submissionNotice(locale,selection){
 const uk=locale==='uk';
 return selection==='instagram'?(uk?'Надсилаємо ім’я, контакт, кількість, Instagram-посилання, коментар і згоду для опрацювання заявки.':'We send your name, contact, quantity, Instagram profile URL, comment and consent to process the enquiry.'):(uk?'Надсилаємо лише ім’я, контакт, картку та кількість. Коментар і додаткові деталі погодимо в месенджері.':'We send only your name, contact, card and quantity. Please share comments and additional details in a messenger.');
}
export function pagesFormHTML(html, {endpoint = '', locale, esc}) {
  const notice = endpoint ? submissionNotice(locale,html.includes('data-commerce-form data-variant="instagram"')?'instagram':'') : unavailable(locale);
  // Native submission is inert even if either client script fails to load. Only
  // the mounted JSON client may enable the submit control after initialization.
  return html.replace(/action="\/api\/leads" method="post"/g, 'data-pages-form action="" method="dialog"')
    .replace(/<div class="preview-notice">[\s\S]*?<\/div>/g, `<div class="preview-notice" role="status">${esc(notice)}</div>`)
    .replace(/(<button class="button submit-button" type="submit")/g, '$1 disabled')
    .replace(/(<div class="form-result"[^>]*><\/div>)/g, '$1<button class="button secondary" type="button" data-new-request hidden>' + (locale === 'uk' ? 'Створити іншу заявку' : 'Start another enquiry') + '</button>');
}

const products = ['standard', 'branded', 'bulk', 'consultation', 'instagram'];
const quantities = ['1', '2', 'more'];
const channels = ['telegram', 'whatsapp', 'viber'];
const idempotencyKey = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/;
export function leadPayload(input, {basePath = '', pathname, utm = {}}) {
  basePath = publicBasePath(basePath);
  if(input.variant==='instagram'&&!instagramProfileURL(input.instagramUrl))throw Error('invalid_instagram_url');
  const name = String(input.name || '').trim().normalize('NFC'), phone = String(input.phone || '').trim();
  if (!['uk', 'en'].includes(input.locale) || !products.includes(input.variant) || !quantities.includes(input.quantity) ||
      (input.variant === 'instagram' && (!['1','2'].includes(input.quantity)||!instagramProfileURL(input.instagramUrl)||typeof input.comment!=='string'||input.comment.length>2000)) ||
      (input.variant === 'bulk' && input.quantity !== 'more') || !name || name.length > 100 || /[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]/u.test(name) ||
      !/^\+?[\d ()-]+$/.test(phone) || phone.replace(/\D/g, '').length < 7 || phone.replace(/\D/g, '').length > 15 ||
      !channels.includes(input.messenger) || input.consent !== true || input.website) throw Error('invalid_fields');
  const route = String(pathname || '').split(/[?#]/)[0].replace(/\/$/, '') || '/';
  const sourcePage = route === basePath ? basePath + '/' : route;
  const relative = sourcePage.slice(basePath.length);
  if (!sourcePage.startsWith(basePath + '/') || !['/', '/en', ...['order','contact','about','solutions/review-card','solutions/branded-review-card','solutions/instagram-card','instagram-card'].flatMap(r=>['/'+r,'/en/'+r])].includes(relative)) throw Error('invalid_source_page');
  const payload = {language: input.locale, product: input.variant === 'instagram' ? 'nfc-instagram-card' : input.variant === 'branded' ? 'branded-review-card' : 'review-card',
    quantity: input.quantity === 'more' ? 3 : Number(input.quantity), customerName: name,
    contact: {phone: phone.replace(/[ ()-]/g, ''), preferredMethod: input.messenger}, sourcePage,
    selection: {variant: input.variant, quantity: input.quantity}};
  if(input.variant==='instagram')Object.assign(payload,{productSchemaVersion:1,product_id:'nfc-instagram-card',sku:'NFC-IG-READY',offer:'ready',instagramUrl:instagramProfileURL(input.instagramUrl),comment:input.comment.trim(),consent:true});
  const attribution = {};
  for (const key of ['source', 'medium', 'campaign', 'term', 'content']) {
    const value = utm['utm_' + key];
    if (typeof value === 'string' && value.trim() && !/[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]/u.test(value)) attribution[key] = value.trim().normalize('NFC').slice(0, 100);
  }
  if (Object.keys(attribution).length) payload.utm = attribution;
  return payload;
}

const requestOptions = {mode: 'cors', credentials: 'omit', redirect: 'error', cache: 'no-store', referrerPolicy: 'no-referrer'};
export async function submitLead(endpoint, pending, fetcher = globalThis.fetch, wait = ms => new Promise(resolve => setTimeout(resolve, ms))) {
  endpoint = leadEndpoint(endpoint);
  if (!endpoint) throw Error('unavailable');
  if (!idempotencyKey.test(pending.key)) throw Error('invalid_idempotency_key');
  // A fresh signed challenge is independent of the stable lead body/key. Renewing
  // it on retry cannot create another lead and never needs a browser secret.
  const url = endpoint + '/challenge?sourcePage=' + encodeURIComponent(pending.payload.sourcePage);
  const check = await fetcher(url, {...requestOptions, signal: AbortSignal.timeout(20000)});
  if (!check.ok) throw Error('challenge_unavailable');
  const challenge = await check.json();
  if (typeof challenge.challenge !== 'string' || challenge.challenge.length > 800 ||
      !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}$/.test(challenge.challenge) || challenge.minimumDelayMs !== 2000) throw Error('invalid_challenge');
  await wait(challenge.minimumDelayMs + 100);
  const wasUncertain = pending.uncertain === true;
  pending.uncertain = true;
  const response = await fetcher(endpoint, {method: 'POST', mode: 'cors', credentials: 'omit', redirect: 'error',
    cache: 'no-store', referrerPolicy: 'no-referrer',
    headers: {'Content-Type': 'application/json', 'Idempotency-Key': pending.key},
    body: JSON.stringify({...pending.payload, website: '', challenge: challenge.challenge}), signal: AbortSignal.timeout(20000)});
  if (response.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') throw Error('request_unconfirmed');
  const value = await response.json();
  if (!response.ok) {
    if (response.status === 409 && value?.code === 'idempotency_conflict' && idempotencyKey.test(value.existingLeadId || ''))
      throw Object.assign(Error('existing_request'), {leadId: value.existingLeadId});
    if (!wasUncertain && response.status === 422 && ['invalid_payload', 'invalid_selection'].includes(value?.code)) {
      pending.uncertain = false;
      throw Error('invalid_fields');
    }
    throw Error('request_unconfirmed');
  }
  // Only the PostgreSQL COMMIT receipt establishes success; delivery is separate.
  if (response.status !== 202 || value?.ok !== true || value.source !== 'NFC_CARD' || value.durableSaved !== true ||
      typeof value.leadId !== 'string' || !idempotencyKey.test(value.leadId)) throw Error('request_unconfirmed');
  return {leadId: value.leadId, durableSaved: true};
}

export function mountPagesForm(form, {endpoint, basePath, locale, pathname, attribution, selection, select, lockSelection, event}) {
  const P = (uk, en) => locale === 'uk' ? uk : en, q = name => form.elements.namedItem(name);
  const submit = form.querySelector('[type=submit]'), result = form.querySelector('.form-result'), note = form.querySelector('.pending-notice');
  const label = submit.textContent;
  try { endpoint = leadEndpoint(endpoint); } catch { endpoint = ''; }
  if (!endpoint) {
    submit.disabled = true;
    form.querySelector('.preview-notice').textContent = unavailable(locale);
    form.onsubmit = e => { e.preventDefault(); };
    form.addEventListener('change', e => {
      if (['variant', 'quantity'].includes(e.target.name)) select({variant: q('variant').value, quantity: q('quantity').value});
    });
    form.dataset.enhanced = 'true';
    return;
  }
  const updateNotice=()=>{form.querySelector('.preview-notice').textContent=submissionNotice(locale,selection().variant);};
  updateNotice();
  let busy = false, pending = null;
  const storageKey = `nfc-public-attempt:${basePath}:${endpoint}:${pathname.replace(/\/$/, '')}`;
  // Only opaque IDs and lifecycle state survive reload. No personal fields,
  // request body or personal-data hash ever enters browser storage.
  let stored;
  try { stored = JSON.parse(sessionStorage.getItem(storageKey) || 'null'); } catch {}
  const recovered = idempotencyKey.test(stored?.key || '') && ['uncertain', 'complete'].includes(stored?.state);
  let key = recovered ? stored.key : crypto.randomUUID(), inheritedUncertainty = recovered && stored.state === 'uncertain';
  const newRequest = form.querySelector('[data-new-request]');
  function remember(state, leadId) {
    try { sessionStorage.setItem(storageKey, JSON.stringify({key, state, ...(leadId ? {leadId} : {})})); } catch {}
  }
  function clearProfileError(){const input=q('instagramUrl'),error=form.querySelector('#e-instagramUrl');if(input){input.removeAttribute('aria-invalid');input.setAttribute('aria-describedby','instagram-help');}if(error){error.hidden=true;error.textContent='';}}
  q('instagramUrl')?.addEventListener('input',clearProfileError);
  const snapshot = () => ({name: q('name').value, phone: q('phone').value, messenger: q('messenger').value,
    consent: q('consent').checked, instagramUrl:q('instagramUrl')?.value.trim(),comment:q('comment')?.value||'', ...selection()});
  function lock(locked) {
    for (const el of form.elements) if (!['hidden', 'submit', 'button'].includes(el.type)) el.disabled = locked;
    lockSelection(locked);
    if(!locked)select(selection());
    note.hidden = !locked;
    if (locked) note.textContent = P('Результат спроби ще не підтверджено. Повторимо ту саму заявку з тими самими даними, щоб не створити дублікат.',
      'The attempt is not confirmed yet. We will retry the same request with the same details to avoid a duplicate.');
  }
  function status(message, state) {
    result.textContent = message; result.dataset.status = state; result.hidden = false; result.focus();
  }
  function completed(leadId, previous = false) {
    form.dataset.complete = 'true'; submit.hidden = true; submit.disabled = true; note.hidden = true;
    status((previous ? P('Попередню заявку вже збережено. Нові дані не надсилалися. Номер: ', 'Your previous enquiry is already saved. The new details were not submitted. Reference: ') :
      selection().variant==='instagram'?P('Дякуємо! Заявку отримано. Я зв’яжуся з вами, перевірю Instagram-посилання та уточню деталі замовлення. Номер: ','Thank you! Your enquiry has been received. I will contact you, check the Instagram link and confirm your order details. Reference: '):P('Дякуємо! Заявку збережено. Деталі погодимо у вибраному месенджері. Номер: ', 'Thank you! Your request is saved. We will agree the details in your selected messenger. Reference: ')) + leadId, previous ? 'existing' : 'success');
    remember('complete', leadId);
    if (newRequest) newRequest.hidden = false;
  }
  if (newRequest) newRequest.onclick = () => {
    if (busy || !form.dataset.complete) return;
    delete form.dataset.complete; pending = null; inheritedUncertainty = false; key = crypto.randomUUID();
    try { sessionStorage.removeItem(storageKey); } catch {}
    lock(false); submit.hidden = false; submit.disabled = false; newRequest.hidden = true; result.hidden = true;
    q('name').focus?.();
  };
  form.addEventListener('change', e => {
    if (pending) return;
    if (['variant', 'quantity'].includes(e.target.name)) {
      select({variant: q('variant').value, quantity: q('quantity').value});
      updateNotice();
      event(e.target.name === 'variant' ? 'product_variant_select' : 'quantity_select', selection());
    }
  });
  form.onsubmit = async e => {
    e.preventDefault();
    if (busy || form.dataset.complete) return;
    if (!pending && !form.reportValidity()) return;
    busy = true; submit.disabled = true; submit.textContent = P('Надсилаємо…', 'Sending…');
    form.setAttribute('aria-busy', 'true'); result.hidden = true;
    try {
      if (!pending) {
        clearProfileError();
        const payload = leadPayload({...snapshot(), locale, website: q('website').value}, {basePath, pathname, utm: attribution});
        pending = {key, payload, uncertain: inheritedUncertainty};
        // Conservative before transport: a page close at any point may hide a COMMIT.
        remember('uncertain');
      }
      lock(true);
      const receipt = await submitLead(endpoint, pending);
      completed(receipt.leadId);
      event('order_submit_success', selection());
    } catch (error) {
      if (error.message === 'existing_request') { completed(error.leadId, true); return; }
      if (!pending?.uncertain && !inheritedUncertainty) {
        pending = null; lock(false); key = crypto.randomUUID();
        try { sessionStorage.removeItem(storageKey); } catch {}
      }
      if(error.message==='invalid_instagram_url'){
        const message=P('Вкажіть повне HTTPS-посилання саме на Instagram-профіль, без дописів, Reels або параметрів посилання.','Enter the full HTTPS Instagram profile URL, without posts, Reels or link parameters.');
        status(message,'error');const input=q('instagramUrl'),fieldError=form.querySelector('#e-instagramUrl');
        if(fieldError){fieldError.textContent=message;fieldError.hidden=false;}
        if(input){input.setAttribute('aria-invalid','true');input.setAttribute('aria-describedby','instagram-help e-instagramUrl');input.focus();}
        event('order_submit_error');return;
      }
      status(error.message === 'invalid_fields' ? P('Перевірте ім’я (до 100 символів), телефон, месенджер, картку, кількість, Instagram-посилання (для Instagram Card) і згоду.', 'Check your name (up to 100 characters), phone, messenger, card, quantity, Instagram profile URL (for Instagram Card) and consent.') :
        P('Прийняття заявки не підтверджено. Дані та вибір залишаються у формі. Спробуйте ще раз або зв’яжіться з нами в месенджері.',
          'Request acceptance is not confirmed. Your details and selection remain in the form. Retry or contact us in a messenger.'), 'error');
      event('order_submit_error');
    } finally {
      busy = false; submit.disabled = !!form.dataset.complete; submit.textContent = label; form.removeAttribute('aria-busy');
    }
  };
  submit.disabled = false; form.dataset.enhanced = 'true';
  if (recovered && stored.state === 'complete' && idempotencyKey.test(stored.leadId || '')) completed(stored.leadId, true);
}
