"""Bounded Pages builds and public form boundary; no live requests or backend writes."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = '/nfc-card-website'
ORIGIN = 'https://optidigitalagent.github.io'
# Syntactically public test fixture only: every transport call is stubbed.
ENDPOINT = 'https://bridge.nfc-card-fixture.com/api/nfc-card/leads'
NODE = shutil.which('node')


@pytest.fixture
def source(tmp_path):
    shutil.copytree(ROOT / 'src', tmp_path / 'src')
    dest = tmp_path / 'refinements/visual-about-v13'
    dest.mkdir(parents=True)
    shutil.copyfile(ROOT / 'refinements/visual-about-v13/routes.json', dest / 'routes.json')
    return tmp_path


def build(source, pages=True, **values):
    env = {k: v for k, v in os.environ.items() if not k.startswith('NFC_')}
    env.update(NFC_ENV='production', NFC_PUBLIC_ORIGIN=ORIGIN)
    if pages:
        env.update(NFC_DEPLOYMENT_TARGET='github-pages', NFC_PUBLIC_BASE_PATH=BASE)
    env.update(values)
    result = subprocess.run([NODE, 'src/build.mjs'], cwd=source, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return source / 'site'


def node(script):
    module = (ROOT / 'src/pages.mjs').as_uri()
    result = subprocess.run([NODE, '--input-type=module'], input=f"import * as pages from {json.dumps(module)};\n"
                            + "import assert from 'node:assert/strict';\n" + script,
                            text=True, capture_output=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def assert_project_url(value, site, base=BASE):
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        if f'{parsed.scheme}://{parsed.netloc}' != ORIGIN:
            return
    elif not value.startswith('/'):
        return
    assert parsed.path == base or parsed.path.startswith(base + '/'), value
    relative = parsed.path[len(base):].lstrip('/')
    target = site / relative
    assert target.is_file() or (target / 'index.html').is_file(), value


@pytest.mark.parametrize('base', [BASE, BASE + '/', '', '/'])
def test_all_static_urls_metadata_css_and_content_use_base_path(source, base):
    site = build(source, NFC_PUBLIC_BASE_PATH=base)
    normalized = base.rstrip('/')
    for file in site.rglob('*.html'):
        soup = BeautifulSoup(file.read_text(), 'html.parser')
        assert soup.select_one('meta[name=robots]')['content'] == 'noindex,nofollow'
        for el in soup.select('[href],[src],[poster],[data-source],[srcset]'):
            for attr in ('href', 'src', 'poster', 'data-source'):
                if el.get(attr):
                    assert_project_url(el[attr], site, normalized)
            for item in el.get('srcset', '').split(','):
                if item.strip():
                    assert_project_url(item.strip().split()[0], site, normalized)
        og = soup.select_one('meta[property="og:url"]')
        if og:
            assert_project_url(og['content'], site, normalized)
        for script in soup.select('script[type="application/ld+json"]'):
            for value in strings(json.loads(script.string)):
                assert_project_url(value, site, normalized)
        assert 'localhost' not in str(soup) and '127.0.0.1' not in str(soup)
    for url in re.findall(r'url\([\'"]?([^\)\'"\s]+)', (site / 'assets/style.css').read_text()):
        assert_project_url(url, site, normalized)
    for value in strings(json.loads((site / 'assets/content.json').read_text())):
        assert_project_url(value, site, normalized)
    sitemap = BeautifulSoup((site / 'sitemap.xml').read_text(), 'xml')
    assert len(sitemap.select('loc')) == 14
    for loc in sitemap.select('loc'):
        assert_project_url(loc.text, site, normalized)
    assert (site / '.nojekyll').exists()
    assert not (source / 'server').exists()


def test_pages_cleans_server_artifacts_and_default_build_remains_fullstack(source):
    site = build(source, pages=False)
    baseline = {p.relative_to(site): p.read_bytes() for p in site.rglob('*') if p.is_file()}
    server = {p.relative_to(source): p.read_bytes() for p in (source / 'server').rglob('*') if p.is_file()}
    assert len(list(site.rglob('*.html'))) == 26
    admin = site / 'admin/reviews/index.html'
    admin.parent.mkdir(parents=True)
    admin.write_text('stale admin')
    build(source)
    assert not (site / 'admin').exists()
    assert not (site / 'reviews/new').exists() and not (site / 'en/reviews/new').exists()
    assert not (site / '_redirects').exists()
    for filename in ['reviews.js', 'reviews-renderer.js', 'admin-reviews.js', 'reviews.css']:
        assert not (site / 'assets' / filename).exists()
    assert server == {p.relative_to(source): p.read_bytes() for p in (source / 'server').rglob('*') if p.is_file()}
    for file in site.rglob('*.html'):
        soup = BeautifulSoup(file.read_text(), 'html.parser')
        assert not soup.select('a[href*="/reviews/new"],a[href*="/admin"],script[src*="reviews"]')
    for file in ['app.js', 'commerce.js']:
        text = (site / 'assets' / file).read_text()
        assert '/api/leads' not in text and 'NFC_FULLSTACK_START' not in text
        result = subprocess.run([NODE, '--check', str(site / 'assets' / file)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    # Switching back cannot inherit a static 404, redirected pages or Pages client.
    build(source, pages=False)
    restored = {p.relative_to(site): p.read_bytes() for p in site.rglob('*') if p.is_file()}
    assert restored == baseline
    soup = BeautifulSoup((site / 'order/index.html').read_text(), 'html.parser')
    assert soup.form['action'] == '/api/leads' and soup.form['method'] == 'post'
    assert 'disabled' not in soup.select_one('[type=submit]').attrs


@pytest.mark.parametrize('endpoint', ['', ENDPOINT])
def test_forms_are_inert_before_client_and_expose_only_public_config(source, endpoint):
    secret = 'synthetic-must-never-be-in-public-artifact'
    site = build(source, NFC_LEAD_ENDPOINT=endpoint, LEAD_GATEWAY_SECRET=secret,
                 LEAD_SOURCE_NFC_CARD_SECRET=secret, TELEGRAM_BOT_TOKEN=secret)
    forms = 0
    for file in site.rglob('*.html'):
        soup = BeautifulSoup(file.read_text(), 'html.parser')
        for form in soup.select('.lead-form'):
            forms += 1
            assert form['method'] == 'dialog' and form['action'] == ''
            assert form.has_attr('data-pages-form')
            assert form.select_one('[type=submit]').has_attr('disabled')
            assert soup.html['data-lead-endpoint'] == ''
            assert soup.html['data-publication-mode'] == 'PUBLIC_PREVIEW'
            assert soup.select_one('.header .preview-badge').text == 'PUBLIC PREVIEW'
            assert soup.html['data-public-base-path'] == BASE
            notice = form.select_one('.preview-notice')
            assert notice['role'] == 'status'
            expected_notice = ('Онлайн-заявки тимчасово недоступні у preview-версії. Функцію буде активовано після підключення захищеного збереження заявок.'
                               if soup.html['lang'] == 'uk' else
                               'Online enquiries are temporarily unavailable in the preview version. The feature will be enabled after secure lead storage is connected.')
            assert notice.text == expected_notice
            if endpoint:
                assert endpoint not in str(soup)
            assert form.select_one('[name=name]') and form.select_one('[name=phone]')
            assert form.select_one('[name=quantity]') and form.select_one('[name=variant]')
            assert_project_url(form.select_one('[name=source]')['value'], site)
    assert forms == 8
    for file in site.rglob('*'):
        if file.is_file():
            assert secret.encode() not in file.read_bytes()


def test_built_clients_fetch_and_navigate_under_project_path(source):
    site = build(source)
    scripts = {name: (site / 'assets' / name).read_text() for name in ['app.js', 'commerce.js']}
    content = json.loads((site / 'assets/content.json').read_text())
    node('const scripts=' + json.dumps(scripts) + ';\nconst content=' + json.dumps(content) + ';\n' + r"""
      const {default:vm}=await import('node:vm');
      for(const name of ['app.js','commerce.js']){
        const fetched=[],historyChanges=[],links=[
          {href:'https://optidigitalagent.github.io/nfc-card-website/en/solutions/review-card/'},
          {href:'https://optidigitalagent.github.io/nfc-card-website/en/order/'}];
        const localeLink={href:'https://optidigitalagent.github.io/nfc-card-website/en/solutions/review-card',
          addEventListener(kind,fn){this[kind]=fn;}};
        const doc={documentElement:{lang:'uk',dataset:{publicBasePath:'/nfc-card-website',deploymentTarget:'github-pages',publicationMode:'PUBLIC_PREVIEW'}},
          body:{dataset:{route:'/solutions/review-card'}},referrer:'',getElementById:()=>null,
          querySelector:selector=>name==='commerce.js'&&selector==='[data-product]'?{dataset:{product:'standard'}}:null,
          querySelectorAll:selector=>selector==='.locale-switch'?[localeLink]:selector==='a[href]'?links:[],addEventListener(){}};
        const location={origin:'https://optidigitalagent.github.io',pathname:'/nfc-card-website/solutions/review-card/',
          search:'?quantity=2&utm_source=fixture',hash:'#request',href:'https://optidigitalagent.github.io/nfc-card-website/solutions/review-card/?quantity=2&utm_source=fixture#request'};
        const state={document:doc,location,history:{replaceState:(a,b,url)=>historyChanges.push(url)},
          sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},URL,URLSearchParams,Intl,Set,Map,
          CustomEvent:class{},window:{addEventListener(){},dispatchEvent(){}},fetch:async url=>{fetched.push(url);return {ok:true,json:async()=>content};}};
        vm.runInNewContext(scripts[name],state);
        await new Promise(resolve=>setImmediate(resolve));
        assert.deepEqual(fetched,['/nfc-card-website/assets/content.json']);
        assert.equal(state.window.nfcAnalyticsEvents?.length||0,0);
        localeLink.click();assert.ok(new URL(localeLink.href,location.origin).pathname.startsWith('/nfc-card-website/'));
        assert.equal(new URL(localeLink.href,location.origin).searchParams.get('quantity'),'2');
        if(name==='commerce.js'){
          for(const link of links){assert.ok(link.href.startsWith('/nfc-card-website/'));assert.equal(new URL(link.href,location.origin).searchParams.get('utm_source'),'fixture');}
          assert.equal(new URL(links[1].href,location.origin).searchParams.get('source'),location.pathname);
          assert.ok(historyChanges.every(url=>url.startsWith('/nfc-card-website/')));
        }
      }
    """)


def test_base_origin_target_and_endpoint_validation():
    node(r"""
      for (const value of ['nfc-card-website', '//other', '/a//b', '/a/../b', '/a/./b', '/a?x', '/a#b', '/%2e', '/a\\b', '/a b'])
        assert.throws(() => pages.publicBasePath(value));
      assert.equal(pages.publicBasePath('/nfc-card-website/'), '/nfc-card-website');
      assert.equal(pages.publicURL('/en/order?quantity=2#request', {basePath:'/nfc-card-website'}), '/nfc-card-website/en/order?quantity=2#request');
      assert.equal(pages.publicURL('/nfc-card-website/en', {basePath:'/nfc-card-website'}), '/nfc-card-website/en');
      assert.equal(pages.publicURL('https://elsewhere.com/p', {basePath:'/nfc-card-website'}), 'https://elsewhere.com/p');
      for (const value of ['/api/leads','http://bridge.company.com/leads','https://127.0.0.1/leads','https://[::1]/leads',
        'https://localhost/leads','https://service.internal/leads','https://service.railway.internal/leads','https://private.local/leads',
        'https://user:password@bridge.company.com/leads','https://bridge.company.com/leads?secret=x','https://bridge.company.com/leads#x',
        'https://bridge.company.com/leads?','https://bridge.company.com/leads#','https://bridge.company.com/',
        'https://bridge.company.com:444/leads','https://bridge.company.com/a/../leads','https://bridge.company.com/a//leads',
        'https://bridge.company.com/%2e/leads','https://bridge.company.com./leads','https://api.telegram.org/bot123/sendMessage',
        'https://bridge.company.com/leads\n','https://bridge.company.com/\\evil']) assert.throws(() => pages.leadEndpoint(value), value);
      assert.equal(pages.leadEndpoint(''), '');
      assert.equal(pages.leadEndpoint('https://bridge.company.com/api/nfc-card/leads'), 'https://bridge.company.com/api/nfc-card/leads');
    """)
    module = (ROOT / 'src/publication.mjs').as_uri()
    node(f"""
      const {{resolvePublication, robotsFile}} = await import({json.dumps(module)});
      const config={{origin:'http://127.0.0.1:8765'}};
      for(const env of [{{NFC_DEPLOYMENT_TARGET:'unknown'}}, {{NFC_DEPLOYMENT_TARGET:'github-pages'}},
        {{NFC_DEPLOYMENT_TARGET:'github-pages',NFC_PUBLIC_ORIGIN:'https://optidigitalagent.github.io/nfc-card-website'}}])
        assert.throws(()=>resolvePublication({{env,config,flags:{{}},approval:{{}}}}));
      const robots=robotsFile({{mode:'PUBLIC_INDEXABLE',origin:'{ORIGIN}',basePath:'{BASE}'}});
      assert.ok(robots.includes('Disallow: {BASE}/admin\\n'));
      assert.ok(robots.includes('Sitemap: {ORIGIN}{BASE}/sitemap.xml\\n'));
    """)


PAYLOAD_FIXTURE = r"""
const fields={locale:'uk',variant:'branded',quantity:'2',name:'  Test Customer  ',phone:'+380 (98) 000-00-00',messenger:'telegram',consent:true};
const context={basePath:'/nfc-card-website',pathname:'/nfc-card-website/order/?source=spoof#request',utm:{utm_source:'test',utm_campaign:'x'.repeat(400),referrer:'private',arbitrary:'ignored'}};
"""


def test_minimal_payload_allowlists_source_normalization_and_utm_limits():
    node(PAYLOAD_FIXTURE + r"""
      const payload=pages.leadPayload({...fields,source:'IADDS',lead_id:'fake',timestamp:'fake',displayed_price:'1',comment:'private'},context);
      assert.deepEqual(Object.keys(payload), ['language','product','quantity','customer_name','contact','source_page','utm']);
      assert.equal(payload.customer_name,'Test Customer'); assert.equal(payload.quantity,2);
      assert.deepEqual(payload.contact,{phone:'+380980000000',messenger:'telegram'});
      assert.equal(payload.source_page,'/nfc-card-website/order');
      assert.deepEqual(Object.keys(payload.utm),['utm_source','utm_campaign']); assert.equal(payload.utm.utm_campaign.length,200);
      for(const changed of [{locale:'ru'},{variant:'invented'},{quantity:'0'},{quantity:'3'},{quantity:'1.5'},{quantity:'-1'},
        {variant:'bulk',quantity:'2'},{name:''},{name:'x'.repeat(121)},{phone:''},{phone:'abc1234567'},{phone:'1'.repeat(16)},
        {messenger:'email'},{consent:false},{website:'bot'}]) assert.throws(()=>pages.leadPayload({...fields,...changed},context));
      for(const pathname of ['/order','//evil.com','/nfc-card-website-evil/order','/nfc-card-website/../order','/nfc-card-website/%2fsecret'])
        assert.throws(()=>pages.leadPayload(fields,{...context,pathname}));
      const custom=pages.leadPayload({...fields,variant:'bulk',quantity:'more'},context); assert.equal(custom.quantity,'more');
      assert.equal(pages.leadPayload({...fields,locale:'en'},{...context,pathname:'/nfc-card-website/en/contact'}).language,'en');
    """)


def test_transport_requires_durable_ack_and_never_falls_back():
    node(PAYLOAD_FIXTURE + f"const endpoint={json.dumps(ENDPOINT)};\n" + r"""
      const pending={key:crypto.randomUUID(),payload:pages.leadPayload(fields,context)};
      let calls=[];
      const send=value=>async (url,options)=>{calls.push({url,options}); return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});};
      await assert.rejects(pages.submitLead('',pending,send({}))); assert.equal(calls.length,0);
      for(const value of [{ok:true},{ok:true,saved:true,lead_id:'NFC-1'},{durable_saved:false,lead_id:'NFC-1'},
        {durable_saved:'true',lead_id:'NFC-1'},{durable_saved:true},{durable_saved:true,lead_id:'<script>'},
        {ok:true,receipt:{id:'NFC-123',mode:'live'}},{telegram:'sent'}])
        await assert.rejects(pages.submitLead(endpoint,pending,send(value)));
      await assert.rejects(pages.submitLead(endpoint,pending,async()=>new Response('<html>ok</html>',{status:200})));
      await assert.rejects(pages.submitLead(endpoint,pending,async()=>new Response(JSON.stringify({durable_saved:true,lead_id:'NFC-1'}),{status:503,headers:{'Content-Type':'application/json'}})));
      const result=await pages.submitLead(endpoint,pending,send({durable_saved:true,lead_id:'NFC-test-123',telegram:'failed'}));
      assert.deepEqual(result,{lead_id:'NFC-test-123',durable_saved:true});
      for(const {url,options} of calls){
        assert.equal(url,endpoint); assert.equal(options.headers['Idempotency-Key'],pending.key);
        assert.deepEqual(JSON.parse(options.body),pending.payload); assert.equal(options.redirect,'error');
        assert.equal(options.credentials,'omit'); assert.equal(options.referrerPolicy,'no-referrer');
        assert.deepEqual(Object.keys(options.headers),['Content-Type','Idempotency-Key']);
      }
    """)


# Minimal DOM seam exercises the real mounted handler without a browser, network,
# third-party DOM package or production storage. Browser QA belongs to the main task.
FORM_FIXTURE = r"""
const storage=()=>{const data=new Map();return {getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};};
globalThis.localStorage=storage(); globalThis.sessionStorage=storage();
function fixture(endpoint,locale='en'){
 const control=(value,type='text')=>({value,type,checked:false,disabled:false});
 const values={name:control('Test Customer'),phone:control('+380980000000'),messenger:control('telegram'),comment:control('Retained comment'),consent:control('yes','checkbox'),variant:control('branded','hidden'),quantity:control('2','select-one'),website:control('','hidden')};
 values.consent.checked=true;
 const submit={type:'submit',textContent:'Send request',disabled:true,hidden:false};
 const elements=[...Object.values(values),submit];elements.namedItem=n=>values[n];
 const result={dataset:{},focus(){},hidden:true},notice={},pendingNote={hidden:true};
 const nodes={'[type=submit]':submit,'.form-result':result,'.pending-notice':pendingNote,'.preview-notice':notice};
 let selected={variant:'branded',quantity:'2'},locked=false,events=[];
 const handlers={};
 const form={elements,dataset:{},querySelector:s=>nodes[s],reportValidity:()=>true,addEventListener:(n,fn)=>handlers[n]=fn,setAttribute(){},removeAttribute(){}};
 pages.mountPagesForm(form,{endpoint,basePath:'/nfc-card-website',locale,pathname:'/nfc-card-website/'+(locale==='uk'?'':'en/')+'order',attribution:{utm_source:'test'},selection:()=>selected,select:v=>{selected=v;values.variant.value=v.variant;values.quantity.value=v.quantity;},lockSelection:v=>locked=v,event:(name,data)=>events.push({name,data})});
 return {form,values,submit,result,notice,events,handlers,get selected(){return selected},get locked(){return locked},send:()=>form.onsubmit({preventDefault(){}})};
}
"""


def test_mounted_unavailable_form_preserves_fields_and_never_submits():
    node(FORM_FIXTURE + r"""
      let calls=0;globalThis.fetch=async()=>{calls++;throw Error('network forbidden');};
      let storageCalls=0;
      for(const store of [localStorage,sessionStorage])for(const op of ['getItem','setItem','removeItem'])
        store[op]=()=>{storageCalls++;throw Error('preview storage forbidden');};
      for(const locale of ['uk','en']){
        const f=fixture('',locale);await f.send();
        assert.equal(f.submit.disabled,true);assert.equal(f.values.name.disabled,false);
        assert.equal(f.values.name.value,'Test Customer');assert.equal(f.values.comment.value,'Retained comment');
        assert.deepEqual(f.selected,{variant:'branded',quantity:'2'});
        assert.ok(f.notice.textContent.includes(locale==='uk'?'тимчасово недоступні':'temporarily unavailable'));
        f.values.quantity.value='more';f.handlers.change({target:{name:'quantity'}});assert.equal(f.selected.quantity,'more');
        assert.equal(f.handlers.input,undefined);
        assert.equal(f.events.length,0);
        f.submit.disabled=false;await f.send();assert.equal(f.form.dataset.complete,undefined);
      }
      assert.equal(calls,0);assert.equal(storageCalls,0);
    """)


def test_mounted_retry_reload_duplicate_guard_and_durable_success():
    node(FORM_FIXTURE + f"const endpoint={json.dumps(ENDPOINT)};\n" + r"""
      const requests=[];let finish;
      globalThis.fetch=(url,options)=>{requests.push({url,options});return new Promise(resolve=>finish=resolve);};
      const f=fixture(endpoint);assert.equal(f.submit.disabled,false);
      const first=f.send();await f.send();assert.equal(requests.length,1);assert.equal(f.submit.disabled,true);
      finish(new Response(JSON.stringify({ok:true,telegram:'sent'}),{headers:{'Content-Type':'application/json'}}));await first;
      assert.equal(f.result.dataset.status,'error');assert.equal(f.form.dataset.complete,undefined);
      assert.equal(f.values.name.value,'Test Customer');assert.equal(f.values.comment.value,'Retained comment');assert.equal(f.locked,true);
      const reload=fixture(endpoint,'uk');assert.equal(reload.locked,true);assert.deepEqual(reload.selected,{variant:'branded',quantity:'2'});
      const retry=reload.send();assert.equal(requests.length,2);
      assert.equal(requests[0].options.body,requests[1].options.body);
      assert.equal(requests[0].options.headers['Idempotency-Key'],requests[1].options.headers['Idempotency-Key']);
      finish(new Response(JSON.stringify({durable_saved:true,lead_id:'NFC-committed-123',telegram:'failed'}),{headers:{'Content-Type':'application/json'}}));await retry;
      assert.equal(reload.result.dataset.status,'success');assert.equal(reload.form.dataset.complete,'true');
      assert.ok(reload.result.textContent.includes('NFC-committed-123'));
      assert.equal(reload.submit.disabled,true);await reload.send();assert.equal(requests.length,2);
      assert.deepEqual(reload.events.filter(e=>e.name==='order_submit_success'),[{name:'order_submit_success',data:{variant:'branded',quantity:'2'}}]);
      assert.ok(!JSON.stringify(reload.events).includes('Test Customer'));
    """)


def test_storage_failure_blocks_network_and_build_validation_precedes_output_cleanup(source):
    node(FORM_FIXTURE + f"const endpoint={json.dumps(ENDPOINT)};\n" + r"""
      let calls=0;globalThis.fetch=async()=>{calls++;throw Error();};
      const f=fixture(endpoint);localStorage.setItem=()=>{throw Error('storage unavailable');};
      await f.send();assert.equal(calls,0);assert.equal(f.result.dataset.status,'error');
      assert.equal(f.values.name.value,'Test Customer');assert.equal(f.values.name.disabled,false);
    """)
    site = build(source)
    original = hashlib.sha256((site / 'index.html').read_bytes()).hexdigest()
    env = {k: v for k, v in os.environ.items() if not k.startswith('NFC_')}
    env.update(NFC_PUBLIC_ORIGIN=ORIGIN, NFC_PUBLIC_BASE_PATH=BASE, NFC_DEPLOYMENT_TARGET='github-pages',
               NFC_LEAD_ENDPOINT='https://user:secret@bridge.company.com/leads')
    result = subprocess.run([NODE, 'src/build.mjs'], cwd=source, env=env, capture_output=True, text=True)
    assert result.returncode != 0 and 'Invalid NFC_LEAD_ENDPOINT' in result.stderr
    assert 'user:secret' not in result.stderr
    assert hashlib.sha256((site / 'index.html').read_bytes()).hexdigest() == original
