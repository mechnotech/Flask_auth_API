# flask_app/pywsgi.py
from gevent import monkey

from settings import config

monkey.patch_all()

from gevent.pywsgi import WSGIServer
from app import app

http_server = WSGIServer(('', config.auth_port), app)
http_server.serve_forever()
