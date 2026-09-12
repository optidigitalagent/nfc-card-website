// Shared Pages build/client boundary. Only explicit public configuration belongs here.
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

export function pagesFormHTML(html, {endpoint = '', locale, esc}) {
  const notice = endpoint ? (locale === 'uk'
    ? 'Надсилаємо лише ім’я, контакт, картку та кількість. Коментар і додаткові деталі погодимо в месенджері.'
    : 'We send only your name, contact, card and quantity. Please share comments and additional details in a messenger.') : unavailable(locale);
  // Native submission is inert even if either client script fails to load. Only
  // the mounted JSON client may enable the submit control after initialization.
  return html.replace(/action="\/api\/leads" method="post"/g, 'data-pages-form action="" method="dialog"')
    .replace(/<div class="preview-notice">[\s\S]*?<\/div>/g, `<div class="preview-notice" role="status">${esc(notice)}</div>`)
    .replace(/(<button class="button submit-button" type="submit")/g, '$1 disabled');
}

const products = ['standard', 'branded', 'bulk', 'consultation'];
const quantities = ['1', '2', 'more'];
const channels = ['telegram', 'whatsapp', 'viber'];
const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
const idempotencyKey = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
export function leadPayload(input, {basePath = '', pathname, utm = {}}) {
  basePath = publicBasePath(basePath);
  const name = String(input.name || '').trim(), phone = String(input.phone || '').trim();
  if (!['uk', 'en'].includes(input.locale) || !products.includes(input.variant) || !quantities.includes(input.quantity) ||
      (input.variant === 'bulk' && input.quantity !== 'more') || !name || name.length > 120 ||
      !/^\+?[\d ()-]+$/.test(phone) || phone.replace(/\D/g, '').length < 7 || phone.replace(/\D/g, '').length > 15 ||
      !channels.includes(input.messenger) || input.consent !== true || input.website) throw Error('invalid_fields');
  // Use the actual page, never a browser-provided source, price, ID or timestamp.
  const sourcePage = String(pathname || '').split(/[?#]/)[0].replace(/\/$/, '') || '/';
  if (!/^\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_-]*$/.test(sourcePage) ||
      (basePath && sourcePage !== basePath && !sourcePage.startsWith(basePath + '/'))) throw Error('invalid_source_page');
  const payload = {language: input.locale, product: input.variant, quantity: input.quantity === 'more' ? 'more' : Number(input.quantity),
    customer_name: name, contact: {phone: phone.replace(/[ ()-]/g, ''), messenger: input.messenger}, source_page: sourcePage};
  const attribution = Object.fromEntries(utmKeys.filter(key => typeof utm[key] === 'string' && utm[key].trim()).map(key => [key, utm[key].trim().slice(0, 200)]));
  if (Object.keys(attribution).length) payload.utm = attribution;
  if (new TextEncoder().encode(JSON.stringify(payload)).length > 8192) throw Error('body_too_large');
  return payload;
}

export async function submitLead(endpoint, pending, fetcher = globalThis.fetch) {
  endpoint = leadEndpoint(endpoint);
  if (!endpoint) throw Error('unavailable');
  if (!idempotencyKey.test(pending.key)) throw Error('invalid_idempotency_key');
  const response = await fetcher(endpoint, {method: 'POST', mode: 'cors', credentials: 'omit', redirect: 'error',
    cache: 'no-store', referrerPolicy: 'no-referrer', headers: {'Content-Type': 'application/json', 'Idempotency-Key': pending.key},
    body: JSON.stringify(pending.payload), signal: AbortSignal.timeout(20000)});
  if (!response.ok || response.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') throw Error('request_unconfirmed');
  const value = await response.json();
  // Telegram status (including failure) cannot decide whether a lead was saved.
  if (value?.durable_saved !== true || typeof value.lead_id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value.lead_id)) throw Error('request_unconfirmed');
  return {lead_id: value.lead_id, durable_saved: true};
}

export function mountPagesForm(form, {endpoint, basePath, locale, pathname, attribution, selection, select, lockSelection, event}) {
  const P = (uk, en) => locale === 'uk' ? uk : en, q = name => form.elements.namedItem(name);
  const submit = form.querySelector('[type=submit]'), result = form.querySelector('.form-result'), note = form.querySelector('.pending-notice');
  const label = submit.textContent;
  try { endpoint = leadEndpoint(endpoint); } catch { endpoint = ''; }
  if (!endpoint) {
    // Preview never reads or writes personal-data drafts, registers a transport,
    // or emits form analytics. Keep only the visual product/quantity controls.
    submit.disabled = true;
    form.querySelector('.preview-notice').textContent = unavailable(locale);
    form.onsubmit = e => { e.preventDefault(); };
    form.addEventListener('change', e => {
      if (['variant', 'quantity'].includes(e.target.name)) select({variant: q('variant').value, quantity: q('quantity').value});
    });
    form.dataset.enhanced = 'true';
    return;
  }
  let busy = false, pending = null;
  // Language switches share the same pending attempt, but other project sites
  // and differently configured endpoints cannot reuse it.
  const route = pathname.slice(basePath.length).replace(/^\/en(?=\/|$)/, '').replace(/\/$/, '') || '/';
  const storageKey = `nfc-pages-v17:${basePath}:${endpoint}:${route}`;
  const draftKey = storageKey + ':draft';
  const snapshot = () => ({name: q('name').value, phone: q('phone').value, messenger: q('messenger').value,
    comment: q('comment').value, consent: q('consent').checked, ...selection()});
  function restore(values) {
    if (!values || !products.includes(values.variant) || !quantities.includes(values.quantity)) return;
    for (const key of ['name', 'phone', 'messenger', 'comment']) if (typeof values[key] === 'string') q(key).value = values[key];
    q('consent').checked = values.consent === true;
    select({variant: values.variant, quantity: values.quantity});
  }
  function lock() {
    for (const el of form.elements) if (!['hidden', 'submit', 'button'].includes(el.type)) el.disabled = true;
    lockSelection(true);
    note.hidden = false;
    note.textContent = P('Результат спроби ще не підтверджено. Повторимо ту саму заявку з тими самими даними, щоб не створити дублікат.',
      'The attempt is not confirmed yet. We will retry the same request with the same details to avoid a duplicate.');
  }
  function status(message, state) {
    result.textContent = message;
    result.dataset.status = state;
    result.hidden = false;
    result.focus();
  }
  try { restore(JSON.parse(sessionStorage.getItem(draftKey) || 'null')); } catch {}
  form.addEventListener('input', () => { if (!pending) try { sessionStorage.setItem(draftKey, JSON.stringify(snapshot())); } catch {} });
  form.addEventListener('change', e => {
    if (pending) return;
    if (['variant', 'quantity'].includes(e.target.name)) {
      select({variant: q('variant').value, quantity: q('quantity').value});
      event(e.target.name === 'variant' ? 'product_variant_select' : 'quantity_select', selection());
    }
    try { sessionStorage.setItem(draftKey, JSON.stringify(snapshot())); } catch {}
  });
  form.onsubmit = async e => {
    e.preventDefault();
    if (!endpoint || busy || form.dataset.complete) return;
    if (!pending && !form.reportValidity()) return;
    busy = true;
    submit.disabled = true;
    submit.textContent = P('Надсилаємо…', 'Sending…');
    form.setAttribute('aria-busy', 'true');
    try {
      if (!pending) {
        const fields = snapshot();
        const payload = leadPayload({...fields, locale, website: q('website').value}, {basePath, pathname, utm: attribution});
        const next = {key: crypto.randomUUID(), payload, fields};
        // Persist before sending. If storage is unavailable, there is no request
        // whose idempotency key could be lost on reload.
        localStorage.setItem(storageKey, JSON.stringify(next));
        pending = next;
      }
      lock();
      const receipt = await submitLead(endpoint, pending);
      form.dataset.complete = 'true';
      submit.hidden = true;
      note.hidden = true;
      // Keep a committed marker if cleanup fails; never turn durable success
      // into an apparent failure because browser storage could not be cleared.
      try { localStorage.setItem(storageKey, JSON.stringify({committed: receipt})); } catch {}
      try { sessionStorage.removeItem(draftKey); } catch {}
      status(P('Заявку прийнято. Номер: ', 'Request accepted. Reference: ') + receipt.lead_id, 'success');
      event('order_submit_success', selection());
    } catch (error) {
      status(error.message === 'invalid_fields' ? P('Перевірте ім’я, телефон, месенджер, картку, кількість і згоду.', 'Check your name, phone, messenger, card, quantity and consent.') :
        P('Прийняття заявки не підтверджено. Дані та вибір залишаються у формі. Спробуйте ще раз або зв’яжіться з нами в месенджері.',
          'Request acceptance is not confirmed. Your details and selection remain in the form. Retry or contact us in a messenger.'), 'error');
      event('order_submit_error');
    } finally {
      busy = false;
      submit.disabled = !endpoint || !!form.dataset.complete;
      submit.textContent = label;
      form.removeAttribute('aria-busy');
    }
  };
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) || 'null');
    if (stored?.committed) {
      // A completed attempt is not a new form submission and is never replayed.
      localStorage.removeItem(storageKey);
    } else if (stored) {
      const expected = leadPayload({...stored.fields, locale: stored.payload?.language, website: ''},
        {basePath, pathname: stored.payload?.source_page, utm: stored.payload?.utm});
      if (JSON.stringify(expected) !== JSON.stringify(stored.payload) || !idempotencyKey.test(stored.key || '')) throw Error('invalid_pending');
      pending = stored;
      restore(stored.fields);
      lock();
    }
    submit.disabled = false;
  } catch {
    endpoint = '';
    submit.disabled = true;
    form.querySelector('.preview-notice').textContent = unavailable(locale);
  }
  form.dataset.enhanced = 'true';
}
