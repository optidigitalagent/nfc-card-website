"""Owner-operated local credential setup. Never prints or stores the plaintext password."""
from getpass import getpass
from pathlib import Path
import argparse
from argon2 import PasswordHasher

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    target=args.output.resolve();root=Path(__file__).resolve().parents[1]
    if target.is_relative_to(root/'site'):raise ValueError('Credential hashes cannot be stored in public output.')
    password=getpass('New NFC moderation password (at least 14 characters): ')
    if len(password)<14:raise ValueError('Use at least 14 characters.')
    if password!=getpass('Repeat password: '):raise ValueError('Passwords do not match.')
    target.parent.mkdir(parents=True,exist_ok=True)
    # Refuse accidental overwrite; credential rotation is an explicit owner operation.
    with target.open('x',encoding='utf-8') as file:file.write(PasswordHasher().hash(password))
    print('Argon2 hash saved to the specified private file. No plaintext password was saved.')

if __name__=='__main__':main()
