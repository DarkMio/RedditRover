# coding=utf-8
from praw.handlers import DefaultHandler
from logging import getLogger


class PRAWHandler(DefaultHandler):
    """It's like the default handler, but hacked open."""

    def __init__(self):
        super().__init__()
        self.logger = getLogger('hndl')

    def request(self, request, proxies, timeout, verify, **_):
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        return self.http.send(request, proxies=proxies, timeout=timeout, allow_redirects=False, verify=verify)

# for a test commit