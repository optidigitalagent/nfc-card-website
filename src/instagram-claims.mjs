// Editorial regression guard for this product only. This is deliberately not a
// general natural-language fact checker; new copy still needs source review.
const rules = [
  ['automatic-follow', /\bautomatic(?:ally)?\s+follow(?:s|ing)?\b|\bfollow(?:s|ing)?\b[^.!?;]{0,28}\bautomatically\b|автоматичн[\p{L}]*\s+підпис[\p{L}]*|підпис[\p{L}]*[^.!?;]{0,28}автоматичн[\p{L}]*/giu],
  ['guaranteed-result', /\bguarantee(?:d|s)?\s+(?:(?:more|new|repeat)\s+)?(?:followers|sales|visits)\b|\b(?:followers|sales|repeat visits)\s+(?:are\s+)?guaranteed\b|гарант[\p{L}]*\s+(?:(?:нових|більше|повторні)\s+)?(?:підпис[\p{L}]*|продаж[\p{L}]*|візит[\p{L}]*)/giu],
  ['official-partnership', /\bofficial\s+(?:(?:Instagram|Meta)\s+)?(?:product|partner(?:ship)?)\b|\b(?:Instagram|Meta)\s+(?:official\s+)?partner\b|офіційн[\p{L}]*\s+(?:(?:Instagram|Meta)\s+)?(?:партнер[\p{L}]*|продукт[\p{L}]*)/giu],
  ['every-phone', /\b(?:works?|compatible)\s+(?:(?:on|with)\s+)?(?:every|all)\s+(?:phones?|smartphones?|devices?)\b|працю[\p{L}]*\s+(?:на|з)\s+(?:кожн[\p{L}]*|усіх|всіх)\s+(?:телефон[\p{L}]*|смартфон[\p{L}]*|пристро[\p{L}]*)/giu],
  ['qr-included', /\bQR(?:[ -](?:code|код)[\p{L}]*)?\s+(?:(?:is|код)\s+)?(?:included|available|включен[\p{L}]*|входить|доступн[\p{L}]*)|\b(?:includes?|with)\s+(?:a\s+)?QR\b|(?:містить|включає)\s+QR/giu],
  ['custom-design', /\b(?:custom|branded|personalised|personalized)\s+(?:Instagram\s+)?design\b|(?:індивідуальн[\p{L}]*|персональн[\p{L}]*|брендован[\p{L}]*)\s+дизайн[\p{L}]*/giu],
];

// Remove only a negated claim itself, not its sentence or surrounding claims.
// Thus "No guaranteed followers; guaranteed sales" still fails for sales.
const denied = [
  /\b(?:no|not|without)\s+(?:an?\s+)?(?:automatic following|automatic follow|guaranteed (?:followers|sales|repeat visits)|official (?:Instagram |Meta )?(?:product|partner)|custom (?:Instagram )?design)\b/giu,
  /\b(?:follower numbers and sales|followers|sales|repeat visits)\s+are not guaranteed\b/giu,
  /\b(?:does not|doesn't|cannot)\s+(?:follow automatically|automatically follow|work on every phone|guarantee (?:followers|sales))\b/giu,
  /\bQR(?: code)?\s+is not included\b|\b(?:no|without)\s+(?:a\s+)?QR(?: code)?\b/giu,
  /(?:не є)\s+офіційн[\p{L}]*\s+продукт[\p{L}]*\s+або\s+партнер[\p{L}]*\s+Instagram\s+чи\s+Meta/giu,
  /(?:не є|не|без)\s+(?:офіційн[\p{L}]*\s+(?:Instagram\s+)?партнер[\p{L}]*|автоматичн[\p{L}]*\s+підпис[\p{L}]*|гарант[\p{L}]*\s+(?:підпис[\p{L}]*|продаж[\p{L}]*)|персональн[\p{L}]*\s+дизайн[\p{L}]*|індивідуальн[\p{L}]*\s+дизайн[\p{L}]*)/giu,
  /не\s+(?:містить|включає)\s+QR(?:[ -]код[\p{L}]*)?|QR(?:[ -]код[\p{L}]*)?\s+не\s+включен[\p{L}]*/giu,
  /не\s+працю[\p{L}]*\s+на\s+(?:кожн[\p{L}]*|усіх|всіх)\s+телефон[\p{L}]*/giu,
  /не\s+підпис[\p{L}]*[^.!?;]{0,28}автоматичн[\p{L}]*/giu,
  /\bdoes not\s+follow[^.!?;]{0,28}automatically\b/giu,
  /персональн[\p{L}]*\s+дизайн[\p{L}]*\s*:\s*немає/giu,
  /\bcustom design\s*:\s*unavailable\b/giu,
];

export function assertInstagramClaims(text, path = 'instagram') {
  let claims = String(text).normalize('NFKC').replace(/[’‘]/g, "'");
  for (const pattern of denied) claims = claims.replace(pattern, ' ');
  for (const [rule, pattern] of rules) {
    pattern.lastIndex = 0;
    if (pattern.test(claims)) throw new Error(`Unverified Instagram claim (${rule}): ${path}`);
  }
  return true;
}

export function validateInstagramContent(content) {
  function walk(value, path) {
    if (typeof value === 'string') {
      // FAQ questions are not assertions. Answers and all metadata are checked.
      if (!path.includes('.question.')) assertInstagramClaims(value, path);
    } else if (value && typeof value === 'object') {
      if ('uk' in value || 'en' in value) {
        if (!value.uk || !value.en) throw new Error('Missing Instagram translation: ' + path);
        if (/[\u0400-\u04ff]/u.test(JSON.stringify(value.en))) throw new Error('Cyrillic in Instagram English: ' + path);
      }
      for (const [key, child] of Object.entries(value)) walk(child, path + '.' + key);
    }
  }
  walk(content, 'instagram');
  return true;
}
