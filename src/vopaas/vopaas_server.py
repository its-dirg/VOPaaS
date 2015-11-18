"""
The VOPaaS proxy main module
"""
import argparse
from logging.handlers import SysLogHandler
import os
import logging
import sys

import cherrypy
from beaker.middleware import SessionMiddleware
from werkzeug.debug import DebuggedApplication
from saml2.httputil import Unauthorized

from satosa.satosa_config import SATOSAConfig
from satosa.base import SATOSABase
from satosa.context import Context
from satosa.util import unpack_either

LOGFILE_NAME = 'vopaas.log'
base_formatter = logging.Formatter("[%(asctime)-19.19s] [%(levelname)-5.5s]: %(message)s")


#https://docs.python.org/2/library/logging.handlers.html
#http://stackoverflow.com/questions/3968669/how-to-configure-logging-to-syslog-in-python
#Can be logged with import syslog as well.
#satosa_stats = logging.getLogger("satosa_stats")
#Linux#hdlr = SysLogHandler("/dev/log")
#OS X#
#hdlr = SysLogHandler("/var/run/syslog")
#hdlr.setFormatter(base_formatter)
#satosa_stats.addHandler(hdlr)
#satosa_stats.setLevel(logging.INFO)

satosa_logger = logging.getLogger("satosa")
hdlr = logging.FileHandler(LOGFILE_NAME)
hdlr.setFormatter(base_formatter)
satosa_logger.addHandler(hdlr)
satosa_logger.setLevel(logging.INFO)

cherrypy_logger = logging.getLogger("cherrypy")
hdlr = logging.FileHandler("cherrypy.log")
hdlr.setFormatter(base_formatter)
cherrypy_logger.addHandler(hdlr)
cherrypy_logger.setLevel(logging.INFO)


class WsgiApplication(SATOSABase):
    """
    The WSGI application
    """

    def __init__(self, config):
        """
        :type config: satosa.satosa_config.SATOSAConfig
        :param config: The vopaas proxy config
        """
        super(WsgiApplication, self).__init__(config)

    def run_server(self, environ, start_response):
        """
        Main proxy function
        :param environ: The WSGI environ
        :param start_response: The WSGI start_response
        :return: response
        """
        path = environ.get('PATH_INFO', '').lstrip('/')
        if ".." in path:
            resp = Unauthorized()
            return resp(environ, start_response)

        context = Context()
        context.path = path
        context.request = unpack_either(environ)
        context.cookie = environ.get("HTTP_COOKIE", "")

        resp = self.run(context)
        return resp(environ, start_response)


def main():
    """
    The main function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true', dest="debug",
                        help="Enable debug mode.")
    parser.add_argument('-e', dest="entityid",
                        help="Entity id for the underlying IdP. If not "
                             "specified, a discovery server will be used "
                             "instead.")
    parser.add_argument(dest="proxy_config",
                        help="Configuration file for the SATOSA proxy.")
    args = parser.parse_args()

    sys.path.insert(0, os.getcwd())

    server_config = SATOSAConfig(args.proxy_config)
    wsgi_app = WsgiApplication(server_config, args.debug).run_server
    if args.debug:
        wsgi_app = DebuggedApplication(wsgi_app)
        satosa_logger.setLevel(logging.DEBUG)
        cherrypy_logger.setLevel(logging.DEBUG)

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': server_config.PORT
    })
    if server_config.HTTPS:
        cherrypy.config.update({
            'server.ssl_certificate': server_config.SERVER_CERT,
            'server.ssl_private_key': server_config.SERVER_KEY,
            'server.ssl_certificate_chain': server_config.CERT_CHAIN,
        })

    cherrypy.tree.mount(None, '/static', {
        '/': {
            'tools.staticdir.dir': server_config.STATIC_DIR,
            'tools.staticdir.on': True,
        }
    })
    cherrypy.tree.mount(None, '/robots.txt', {
        '/': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(server_config.STATIC_DIR,
                                                      "robots.txt")

        }
    })

    cherrypy.tree.graft(SessionMiddleware(wsgi_app, server_config.SESSION_OPTS),
                        '/')

    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == '__main__':
    main()
