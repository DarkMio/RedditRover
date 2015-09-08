from praw.handlers import DefaultHandler
from logging import getLogger


class PRAWHandler(DefaultHandler):
    """It's like the default handler, but hacked open."""

    def __init__(self):
        self.dh = super(PRAWHandler, self).__init__()
        self.logger = getLogger('handler')

    def request(self, request, proxies, timeout, verify, **_):
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        super()
        self.dh.request(request, proxies, timeout, verify, **_)
