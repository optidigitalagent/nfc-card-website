/* Generated Polish dictionary is inserted at build time. */
(() => {
  'use strict';
  const polish = /*POLISH_UI_DICTIONARY*/ {};
  const has = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
  window.nfcTranslate = (locale, uk, en) => {
    if (locale === 'uk') return uk;
    if (locale === 'en') return en;
    if (locale === 'pl' && typeof uk === 'string' && has(polish, uk)) return polish[uk];
    throw Error('Missing ' + locale + ' UI translation: ' + String(uk));
  };
  const safe = {
    variant: value => ['standard', 'branded', 'bulk', 'consultation', 'instagram', 'review_3d'].includes(value),
    quantity: value => value === 'more' || /^[1-9]\d{0,3}$/.test(value) && Number(value) <= 10000,
    product: value => ['nfc-review-card', 'branded-review-card', 'nfc-instagram-card', 'nfc-menu-card', 'nfc-review-card-3d'].includes(value),
    intent: value => ['card_order', 'menu_consultation'].includes(value),
    menu_status: value => ['existing', 'needs_development'].includes(value)
  };
  window.nfcSwitchLocaleURL = (href, values = {}) => {
    const target = new URL(href, location.href);
    if (target.origin !== location.origin) throw Error('Cross-origin language switch');
    target.search = '';
    const current = new URL(location.href);
    for (const [key, valid] of Object.entries(safe)) {
      const value = values[key] ?? current.searchParams.get(key);
      if (typeof value === 'string' && valid(value)) target.searchParams.set(key, value);
    }
    let id = '';
    try { id = decodeURIComponent(current.hash.slice(1)); } catch {}
    target.hash = /^[A-Za-z][A-Za-z0-9_:-]{0,79}$/.test(id) && document.getElementById(id) ? '#' + encodeURIComponent(id) : '';
    return target.pathname + target.search + target.hash;
  };
})();
