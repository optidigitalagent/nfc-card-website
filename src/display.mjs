import commerce from './commerce.json' with { type: 'json' };
import {selectionQuote} from './commerce-contract.mjs';
import { config } from './model.mjs';
import {assertLocale, localizedValue, translate, uah} from './locale.mjs';

const localeKey = assertLocale;

/** Canonical offer, shared with the server. Never uses a client price. */
export function canonicalQuote(variant, quantity = '1') {
  const key = String(quantity);
  const {valid,amount,product_id,offer,pricingRevision,evidence}=selectionQuote(commerce,variant,key);
  return {
    variant,
    product: variant,
    quantity: key,
    status: Number.isFinite(amount) ? 'confirmed' : 'custom',
    type: Number.isFinite(amount) ? 'confirmed' : 'custom',
    amount,
    value: amount,
    price: amount,
    currency: commerce.currency,
    deposit: commerce.deposit,
    depositIncluded: commerce.depositIncluded,
    valid, product_id, offer, pricingRevision,
    evidence
  };
}

export function money(amount, locale = 'uk') {
  if (!Number.isFinite(amount) || amount < 0) throw new TypeError('Invalid canonical amount');
  return uah(localeKey(locale), amount);
}

export function priceText(quote, locale = 'uk') {
  if (quote?.status !== 'confirmed' || !Number.isFinite(quote.amount ?? quote.value)) {
    return translate(localeKey(locale), 'Індивідуальний прорахунок', 'Custom quote');
  }
  return money(quote.amount ?? quote.value, locale);
}

/** Channel-specific links use the confirmed contacts, with a visible phone fallback. */
export function contactItems(contacts = config.contacts, locale = 'uk') {
  if (typeof contacts === 'string') {
    locale = contacts;
    contacts = config.contacts;
  }
  const lang = localeKey(locale);
  return Object.entries(contacts)
    .filter(([, contact]) => contact?.status === 'confirmed' && contact.href && contact.evidence)
    .map(([kind, contact]) => ({
      kind,
      href: contact.href,
      label: typeof contact.label === 'object' ? localizedValue(contact.label,lang,'contact '+kind) : contact.label,
      display: contact.display || contact.value,
      value: contact.value,
      fallback: ['viber', 'whatsapp'].includes(kind) ? config.contacts.phone.href : null,
      event: kind + '_click'
    }));
}

export function factText(fact, locale, fallback = '') {
  if (fact?.status !== 'confirmed') return fallback;
  return fact.value && typeof fact.value === 'object' ? localizedValue(fact.value,localeKey(locale),'fact') : String(fact.value);
}
