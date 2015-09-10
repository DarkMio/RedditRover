# coding=utf-8
from logging import getLogger
from time import time, sleep
from requests import Session
from threading import Lock


class RoverHandler:
    # @TODO : Currently freezes all threads, not nice (up to 2s possible) :
    # @TODO : - Locking thread when sending or calculating the exact dispatch time, all other threads should
    # @TODO :   queue up after that. Needs minor changes.
    # @TODO : Add unique request token lifetime to the list, so it gets deleted after 70 minutes. Definitly
    # @TODO : helps with memory filling up when running on dedis.

    def __init__(self):
        self.logger = getLogger('hndl')
        self.no_auth = time() - 1                                   # simply the time since the last no_auth was sent
        self.oauth = {}                                             # {'unique request token': time_last_sent}
        self.http = Session()
        self.rl_lock = Lock()

    def __del__(self):
        if self.http:
            try:
                self.http.close()
            except Exception:
                pass

    @classmethod
    def evict(cls, urls):
        return 0

    def request(self, request, proxies, timeout, verify, **_):
        self.rl_lock.acquire()
        bearer = ''
        if '_cache_key' in _:
            cache_key = _.get('_cache_key')
            token_group = cache_key[1]
            if len(token_group) >= 5:
                bearer = token_group[4]
        if bearer:
            if bearer in self.oauth:
                time_dispatched = self.dispatch_timer(self.oauth[bearer] + 1)
                self.oauth[bearer] = time_dispatched  # @TODO: Can be in one line, pls update
                self.rl_lock.release()
                return self.send_request(request, proxies, timeout, verify)
            else:
                self.oauth[bearer] = time()
                self.rl_lock.release()
                return self.send_request(request, proxies, timeout, verify)
        else:
            time_dispatched = self.dispatch_timer(self.no_auth + 2)
            self.no_auth = time_dispatched  # @TODO: Can also be inline, pls update
            self.rl_lock.release()
            return self.send_request(request, proxies, timeout, verify)

    def send_request(self, request, proxies, timeout, verify):
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        return self.http.send(request, proxies=proxies, timeout=timeout, allow_redirects=False, verify=verify)

    def dispatch_timer(self, next_possible_dispatch):
        time_until_dispatch = next_possible_dispatch - time()
        if time_until_dispatch > 0:  # Make sure that we have given it enough time.
            sleep(time_until_dispatch)
        return time()
