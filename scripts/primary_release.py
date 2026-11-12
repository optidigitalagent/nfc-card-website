"""Fail-closed publisher checks. This proposal grants no publication authority."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE_REPOSITORY='zaffirax55/nfc-card-website'
ORIGIN='https://optidigitalagent.github.io'
BASE='/nfc-card-website'
def full(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{40}',value) is not None
def read(path):return json.loads(path.read_text())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def lock_check(lock):
 if lock.get('source_repository')!=SOURCE_REPOSITORY or lock.get('origin')!=ORIGIN or lock.get('base')!=BASE:raise ValueError('Fixed release destination/source mismatch')
 if lock.get('status')!='ACCEPTED_FOR_PUBLIC_RELEASE':raise ValueError('Pending integration/content/provenance approval: release lock is not accepted')
 for k in ['source_main_commit','source_main_tree','storefront_commit','storefront_tree']:
  if not full(lock.get(k)):raise ValueError('Full accepted commit/tree required: '+k)
 if not lock.get('approval_reference'):raise ValueError('Real independent release acceptance required')
 return lock
def checkout_check(root,sha,tree):
 if git(root,'rev-parse','HEAD')!=sha or git(root,'rev-parse','HEAD^{tree}')!=tree:raise ValueError('Resolved source identity mismatch')
 if git(root,'status','--porcelain','--untracked-files=normal'):raise ValueError('Uncommitted source is not a deployable commit')
 if git(root,'rev-parse','--is-shallow-repository')!='false':raise ValueError('Complete source history required')
def content_gate(root):
 code="""import fs from 'node:fs';import {reviewedContentSha256,resolvePublication} from './src/publication.mjs';import {loadReleasePolicy} from './scripts/release-policy-input.mjs';
 const root=process.cwd();loadReleasePolicy(root);resolvePublication({env:{NFC_ENV:'production',NFC_DEPLOYMENT_TARGET:'github-pages',NFC_PUBLIC_ORIGIN:'https://optidigitalagent.github.io',NFC_PUBLIC_BASE_PATH:'/nfc-card-website',NFC_PUBLICATION_MODE:'PUBLIC'},config:{},flags:{},approval:JSON.parse(fs.readFileSync('src/publication-approval.json')),contentHash:reviewedContentSha256(root)});"""
 subprocess.run(['node','--input-type=module','-e',code],cwd=root,check=True)
def validate(root,lock):
 checkout_check(root,lock['storefront_commit'],lock['storefront_tree'])
 for branch in ['main','optidigital-3d-preview']:
  subprocess.run(['git','-C',str(root),'fetch','--no-tags','origin','refs/heads/'+branch+':refs/remotes/origin/'+branch],check=True)
 for commit in [lock['source_main_commit'],lock['storefront_commit']]:
  # Fixed source main and storefront must actually have been integrated.
  target='refs/remotes/origin/main' if commit==lock['source_main_commit'] else 'refs/remotes/origin/optidigital-3d-preview'
  subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',commit,target],check=True)
 if git(root,'rev-parse',lock['source_main_commit']+'^{tree}')!=lock['source_main_tree']:raise ValueError('Source main tree mismatch')
 # Reuse the unchanged lineage verifier against the actual source repository.
 import importlib.util
 spec=importlib.util.spec_from_file_location('lineage',ROOT/'scripts/verify_storefront_lineage.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 proof=module.verify(root,lock['storefront_commit'],git(root,'rev-parse','refs/remotes/origin/optidigital-3d-preview'))
 out=ROOT/'work/publication-evidence';out.mkdir(parents=True,exist_ok=True);(out/'lineage.json').write_text(json.dumps(proof,indent=2)+'\n')
 content_gate(root)
def artifact(root,lock):
 site=root/'site';version=read(site/'DEPLOYED_VERSION.json');manifest=read(site/'BUILD_MANIFEST.json')
 for key,expected in [('commit',lock['storefront_commit']),('publisherWorkflowCommit',os.environ['GITHUB_SHA']),('mode','production'),('origin',ORIGIN),('base',BASE)]:
  if version.get(key)!=expected:raise ValueError('Artifact identity mismatch: '+key)
 if manifest.get('mode')!='production' or manifest.get('fixtureOnly') is not False or not all(manifest.get('intakeEnabled',{}).get(k) for k in ['v1','v2']):raise ValueError('PUBLIC artifact required; rehearsal forbidden')
 if (site/'nfc-card-website').exists() or (site/'optidigital-3d').exists():raise ValueError('Incorrect Pages artifact mount')
 if 'Disallow: /\n' in (site/'robots.txt').read_text():raise ValueError('Noindex rehearsal must never replace primary')
 if not manifest.get('sitemapRoutes'):raise ValueError('Indexable sitemap required')
 rows=[]
 for p in sorted(site.rglob('*')):
  if p.is_symlink():raise ValueError('Artifact symlink')
  if p.is_file():rows.append({'path':p.relative_to(site).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 encoded=json.dumps(rows,sort_keys=True,separators=(',',':')).encode();out=ROOT/'work/publication-evidence';out.mkdir(parents=True,exist_ok=True)
 (out/'artifact.json').write_text(json.dumps({'source_repository':SOURCE_REPOSITORY,'storefront_commit':lock['storefront_commit'],'storefront_tree':lock['storefront_tree'],'publisher_workflow_commit':os.environ['GITHUB_SHA'],'manifest_sha256':hashlib.sha256(encoded).hexdigest(),'files':rows},indent=2)+'\n')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['lock','validate','artifact']);parser.add_argument('--source',type=Path);args=parser.parse_args()
 lock=lock_check(read(ROOT/'release/PRIMARY_RELEASE_LOCK.json'))
 if args.phase=='lock':
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:
   for key in ['source_main_commit','source_main_tree','storefront_commit','storefront_tree']:f.write(key+'='+lock[key]+'\n')
 elif args.phase=='validate':validate(args.source.resolve(),lock)
 else:artifact(args.source.resolve(),lock)
if __name__=='__main__':main()
