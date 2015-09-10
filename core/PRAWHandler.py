# coding=utf-8
from praw.handlers import *
from logging import getLogger
from time import time
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


class Dispatcher:
    def __init__(self):
        self.tick = 1
        self.no_auth = {'last_request': time(), 'requests': []}     # A dict with requests and last dispatch time
        self.oauth = []                                             # A list of RegisteredApp

    def dispatch(self):
        for app in self.oauth:
            app.get_request()
            # send
            pass
        if len(self.no_auth) > 0 and self.no_auth['last_request'] < time() - 1:
            request = self.no_auth['requests'].pop(0)
            # handle send event
            pass

    def add_request(self, request, _cache_key=None):
        if _cache_key:
            for app in self.oauth:
                if app.key == _cache_key:
                    app += request
        else:
            self.no_auth['request'].append(request)


class RoverHandler:

    def __init__(self):
        self.logger = getLogger('hndl')
        self.tick = 1                                               # 1 second = 1 tick
        self.no_auth = {'last_request': time(), 'requests': []}     # A dict with requests and last dispatch time
        self.oauth = []                                             # A list of RegisteredApp
        self.http = Session()

    def __del__(self):
        if self.http:
            try:
                self.http.close()
            except Exception:
                pass

    @staticmethod
    def dispatcher(function):
        @wraps(function)
        def wrapped(cls):
            if cls.no_auth['last_request'] < time() - 2 and len(cls.no_auth['requests']) > 0: # A call every 2 seconds
                cls.send_request(*cls.no_auth['requests'].pop(0))

    def send_request(self, request, proxies, timeout, verify):
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        return self.http.send(request, proxies=proxies, timeout=timeout, allow_redirects=False, verify=verify)

class RegisteredApp:

    def __init__(self, unique_key):
        self.key = unique_key           # A simple string, originally request_token from OAuth
        self.created = time()           # Time created, so we can delete itself if needed.
        self.last_request = time() - 1  # Time of the last request, on creation simply default value
        self.requests = []              # All upcoming requests from oldest -> newest

    def __add__(self, other):
        self.requests.append(other)

    def get_request(self):
        if len(self.requests) > 0 and self.last_request > time() - 1:
            self.last_request = time()
            return self.requests.pop(0)

    def delete_object(self, lifetime):
        if lifetime < time() and len(self.requests):
            del self

