"""Explicit operator commands. No automatic schema changes or external notifications."""
import argparse,os
from .review_repository import ReviewRepository
def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['migrate','reconcile','outbox','retention']);parser.add_argument('--apply',action='store_true',help='Explicitly apply the configured retention policy. Without this, counts only.');args=parser.parse_args()
    if args.action=='migrate':ReviewRepository(os.environ['NFC_DATABASE_URL']).migrate();print('Migrations applied and checksums verified.');return
    from .review_config import configure
    runtime=configure()
    if args.action=='retention':print(runtime.service.retention(rejected_days=runtime.rejected_days,unused_asset_days=runtime.unused_asset_days,apply=args.apply))
    elif args.action=='reconcile':print('Reconciled jobs:',runtime.service.reconcile())
    else:
        from .commerce_repository import PostgresLeadService
        runtime.service.dispatch_outbox();PostgresLeadService(runtime.service.repo,secret=runtime.service.secret,mode=runtime.mode).dispatch()
        print('Production delivery is disabled; queued notifications remain pending.' if runtime.mode=='production' else 'Local/test outbox pass complete; no live messages sent.')
if __name__=='__main__':main()
