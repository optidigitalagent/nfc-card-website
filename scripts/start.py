import os
from wsgiref.simple_server import make_server
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.wsgi import application
if __name__=='__main__':
    with make_server('127.0.0.1',int(os.environ.get('PORT','8765')),application) as server:server.serve_forever()
