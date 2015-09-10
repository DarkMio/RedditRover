# coding=utf-8
from logging import getLogger
from time import time, sleep
from requests import Session
from threading import Lock


class RoverHandler:

    def __init__(self):
        self.logger = getLogger('hndl')
        self.no_auth = time() - 1                                   # simply the time since the last no_auth was sent
        self.oauth = {}                                             # {'unique request token': [last_sent, lifetime]}
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
        # cleans up the dictionary with access keys every time someone tries a request.
        self.oauth = {key: value for key, value in self.oauth.items() if value[1] > time()}
        bearer = ''
        if '_cache_key' in _:
            cache_key = _.get('_cache_key')
            token_group = cache_key[1]
            if len(token_group) >= 5:
                bearer = token_group[4]

        if bearer and bearer in self.oauth:
            if bearer in self.oauth:
                # lock the thread to update values
                self.rl_lock.acquire()
                last_dispatched = self.oauth[bearer][0]
                left_until_dispatch = self.dispatch_timer(last_dispatched + 1)
                self.oauth[bearer][0] = time() + left_until_dispatch
                self.rl_lock.release()
                # and now we can sleep the single thread in here - the timer should've updated, so the next
                # thread cannot possibly dispatch at the same time, instead gets slept later in.
                sleep(left_until_dispatch)
        elif bearer:
            self.oauth[bearer] = [time(), time() + 70 * 60]  # lifetime: 70 minutes
        else:
            self.rl_lock.acquire()
            last_dispatched = self.no_auth
            left_until_dispatch = self.dispatch_timer(last_dispatched + 2)
            self.no_auth = time() + left_until_dispatch
            self.rl_lock.release()
            sleep(left_until_dispatch)
        return self.send_request(request, proxies, timeout, verify)

    def send_request(self, request, proxies, timeout, verify):
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        return self.http.send(request, proxies=proxies, timeout=timeout, allow_redirects=False, verify=verify)

    def dispatch_timer(self, next_possible_dispatch):
        time_until_dispatch = next_possible_dispatch - time()
        if time_until_dispatch > 0:  # Make sure that we have given it enough time.
            return time_until_dispatch
        return 0
