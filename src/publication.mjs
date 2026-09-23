import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {isIP} from 'node:net';
import {publicBasePath, publicURL} from './pages.mjs';

export const PREVIEW = 'PUBLIC_PREVIEW';
export const PUBLIC = 'PUBLIC';
export const INDEXABLE = 'PUBLIC_INDEXABLE';
const PUBLIC_ROUTES = ['/', '/about', '/solutions', '/solutions/review-card',
  '/solutions/branded-review-card', '/solutions/instagram-card', '/instagram-card', '/solutions/menu-card', '/menu-card', '/delivery-and-payment', '/warranty-and-returns'];
const LEGAL_ROUTES = ['/privacy', '/terms'];
const localized = routes => routes.flatMap(route => [route, '/en' + (route === '/' ? '' : route)]);

export function reviewedContentSha256(root) {
  const hash = createHash('sha256');
  const files = fs.readdirSync(path.join(root, 'src'), {recursive: true, withFileTypes: true})
    .filter(entry => entry.isFile()).map(entry => path.relative(root, path.join(entry.parentPath, entry.name)).split(path.sep).join('/'))
    .filter(file => file !== 'src/publication-approval.json').sort();
  for (const file of files) hash.update(file + '\0').update(fs.readFileSync(path.join(root, file))).update('\0');
  return hash.digest('hex');
}

export function publicOrigin(value, localAllowed = false) {
  if (typeof value !== 'string' || /[\s<>"'\\]/.test(value)) throw Error('Invalid public origin');
  let parsed;
  try { parsed = new URL(value); } catch { throw Error('Invalid public origin'); }
  if (parsed.username || parsed.password || parsed.search || parsed.hash || parsed.pathname !== '/') throw Error('Origin must not contain credentials, path, query or fragment');
  if (localAllowed && parsed.protocol === 'http:' && parsed.hostname === '127.0.0.1') return parsed.origin;
  const host = parsed.hostname.toLowerCase();
  if (parsed.protocol !== 'https:' || host.endsWith('.') || isIP(host.replace(/^\[|\]$/g, '')) ||
      !host.includes('.') || /(^|\.)(localhost|local|internal)$/.test(host)) throw Error('Public origin must be a non-loopback HTTPS hostname');
  return parsed.origin;
}

export function resolvePublication({env = process.env, config, flags, approval, contentHash}) {
  const deploymentTarget = env.NFC_DEPLOYMENT_TARGET || 'fullstack';
  if (!['fullstack', 'github-pages'].includes(deploymentTarget)) throw Error('Invalid NFC_DEPLOYMENT_TARGET');
  const basePath = publicBasePath(env.NFC_PUBLIC_BASE_PATH);
  const mode = env.NFC_PUBLICATION_MODE || PREVIEW;
  if (![PREVIEW, INDEXABLE, PUBLIC].includes(mode)) throw Error('Invalid NFC_PUBLICATION_MODE');
  const runtime = env.NFC_ENV || 'local';
  if (!['local', 'test', 'production'].includes(runtime)) throw Error('Invalid NFC_ENV');
  if (runtime === 'production' && !env.NFC_PUBLIC_ORIGIN) throw Error('Production build requires NFC_PUBLIC_ORIGIN');
  const origin = publicOrigin(env.NFC_PUBLIC_ORIGIN || config.origin, runtime !== 'production' && mode === PREVIEW);
  if (deploymentTarget === 'github-pages') {
    if (!env.NFC_PUBLIC_ORIGIN) throw Error('GitHub Pages requires explicit NFC_PUBLIC_ORIGIN');
    publicOrigin(origin);
  }
  if (mode === INDEXABLE) {
    publicOrigin(origin);
    const legal = config.legal || {};
    const hasIdentity = ['identity', 'address', 'registration'].every(key => typeof legal[key] === 'string' && legal[key].trim());
    if (config.publicationReady !== true || !hasIdentity || legal.privacyApproved !== true || legal.termsApproved !== true ||
        !['legal_identity_confirmed', 'warranty_policy_confirmed', 'personalized_returns_policy_confirmed'].every(key => flags[key] === true) ||
        approval.schemaVersion !== 1 || approval.ownerAuthorizedIndexing !== true || approval.publicationInputsConfirmed !== true ||
        typeof approval.approvalReference !== 'string' || !approval.approvalReference.trim() ||
        !/^[a-f0-9]{64}$/.test(contentHash || '') || approval.reviewedContentSha256 !== contentHash) {
      throw Error('Indexing blocked: confirmed legal content, publication inputs and content-bound owner authorization required');
    }
  }
  if (mode === PUBLIC) {
    // The owner confirmed the named seller and defect refunds for this Pages
    // launch. This is a distinct, content-bound authorization; it does not assert
    // nonexistent registration/address facts or weaken the old fullstack gate.
    const launch = approval.publicLaunch;
    if (deploymentTarget !== 'github-pages' || runtime !== 'production' ||
        launch?.ownerAuthorizedPublication !== true || launch?.sellerName !== 'Артем Антонов' ||
        launch?.defectReturnAndRefundConfirmed !== true || !launch?.approvalReference ||
        launch?.reviewedContentSha256 !== contentHash) throw Error('Indexing blocked: content-bound PUBLIC authorization required');
  }
  const indexed = mode === INDEXABLE || mode === PUBLIC;
  const sitemapRoutes = localized(indexed ? [...PUBLIC_ROUTES, ...LEGAL_ROUTES] : PUBLIC_ROUTES);
  return Object.freeze({schemaVersion: 1, mode, origin, sitemapRoutes,
    indexableRoutes: indexed ? sitemapRoutes : [], contentHash,
    ...(basePath || deploymentTarget === 'github-pages' ? {basePath, deploymentTarget} : {})});
}

export function robotsMeta(publication, route) {
  return publication.indexableRoutes.includes(route) ? 'index,follow' : 'noindex,nofollow';
}

export function assertFinalLegalContent(publication, route, body) {
  if ([INDEXABLE, PUBLIC].includes(publication.mode) && [...LEGAL_ROUTES, '/warranty-and-returns'].includes(route) &&
      /\bdraft\b|чернетк|awaiting owner approval|до погодження власником/iu.test(body)) {
    throw Error('Indexing blocked: legal or policy page is still a draft');
  }
}

export function robotsFile(publication) {
  if (publication.mode === PREVIEW) return 'User-agent: *\nDisallow: /\n';
  const excluded = ['/admin', '/en/admin', '/api', '/order', '/en/order', '/contact', '/en/contact',
    '/reviews/new', '/en/reviews/new', '/thank-you', '/en/thank-you', '/healthz'];
  return 'User-agent: *\nAllow: ' + publicURL('/', publication) + '\n' + excluded.map(route => 'Disallow: ' + publicURL(route, publication) + '\n').join('') +
    'Sitemap: ' + publication.origin + publicURL('/sitemap.xml', publication) + '\n';
}
