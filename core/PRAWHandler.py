# coding=utf-8
from praw.handlers import *
from logging import getLogger
from time import time, sleep
from requests import Session


class PRAWHandler(RateLimitHandler):
    """It's like the default handler, but hacked open."""
    # @TODO: Remove monkey patching (the fuck.) and keep track of sessions to limit rates.
    # @TODO: Even better idea: Rewrite the handler.

    def __init__(self):
        super().__init__()
        self.logger = getLogger('hndl')

    def request(self, request, proxies, timeout, verify, **_):
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        return self.http.send(request, proxies=proxies, timeout=timeout, allow_redirects=False, verify=verify)
PRAWHandler.request = PRAWHandler.rate_limit(PRAWHandler.request)


class RoverHandler:

    def __init__(self):
        self.logger = getLogger('hndl')
        self.no_auth = time() - 1                                   # simply the time since the last no_auth was sent
        self.oauth = {}                                             #
        self.http = Session()

    def __del__(self):
        if self.http:
            try:
                self.http.close()
            except Exception:
                pass

    def request(self, request, proxies, timeout, verify, **_):
        bearer = ''
        if '_cache_key' in _:
            cache_key = _.get('_cache_key')
            token_group = cache_key[1]
            if len(token_group) >= 5:
                bearer = token_group[4]
        if bearer:
            if bearer in self.oauth:
                time_dispatched = self.dispatch_timer(self.oauth[bearer] + 1)
                return self.send_request(request, proxies, timeout, verify)
        else:
            time_dispatched = self.dispatch_timer(self.no_auth + 2)
            return self.send_request(request, proxies, timeout, verify)

    def send_request(self, request, proxies, timeout, verify):
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        return self.http.send(request, proxies=proxies, timeout=timeout, allow_redirects=False, verify=verify)

    @staticmethod
    def dispatch_timer(next_possible_dispatch):
        time_until_dispatch = (next_possible_dispatch) - time()
        if time_until_dispatch > 0:  # Make sure that we have given it enough time.
            sleep(time_until_dispatch)
        return time()