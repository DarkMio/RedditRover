# coding=utf-8
from logging import getLogger
from time import time, sleep
from requests import Session
from threading import Lock


class RoverHandler:
    """
    Main handler for RedditRover, keeps track of all requests sent by OAuth and non-Auth sessions to keep the API-Limit
    from Reddit in place. The general rule: All non-auth have 30 requests per minute per IP, all OAuth session have
    60 requests per minutes without an IP limitation.

    :ivar logger: Logger for the handler, mainly writes debug messages into the log-file.
    :type logger: logging.Logger
    :vartype logger: logging.Logger
    :ivar no_auth: A unix timestamp of the last planned requests. Stacks up and could be in the future (so further
                   requests get sent after that. First come, first serve.)
    :type no_auth: float
    :vartype no_auth: float
    :ivar oauth: A dictionary with ``{'unique request token': [last_sent, lifetime]}``
    :type oauth: dict
    :vartype oauth: dict
    :ivar http: the requesting http session
    :type http: requests.Session
    :vartype http: requests.Session
    :ivar rl_lock: Threading Lock to lock up a requesting thread to update the timestamps on all requests, makes it all
                   thread safe and threads stack each other up.
    :type rl_lock: threading.Lock
    :vartype rl_lock: threading.Lock
    """

    def __init__(self):
        self.logger = getLogger('hndl')
        self.no_auth = time() - 1                                   # simply the time since the last no_auth was sent
        self.oauth = {}                                             # {'unique request token': [last_sent, lifetime]}
        self.http = Session()
        self.rl_lock = Lock()

    # noinspection PyBroadException
    def __del__(self):
        """
        Cleans up the http session on object deletion
        """
        if self.http:
            try:
                self.http.close()
            except Exception:
                pass

    # noinspection PyUnusedLocal
    @classmethod
    def evict(cls, urls):
        """
        Method utilized to evict entries for the given urls. By default this method returns False as a cache need not
        be present.

        :param urls: An iterable containing normalized urls.
        :type urls: list
        :return: The number of items removed from the cache.
        """
        return 0

    def request(self, request, proxies, timeout, verify, **_):
        """
        Cleans up the ``oauth`` attribute, then looks up if its an OAuth requests and dispatched the request in the
        appropriate time. Sleeps the thread for exactly the time until the next request can be sent.

        :param request: A ``requests.PreparedRequest`` object containing all the data necessary to perform the request.
        :param proxies: A dictionary of proxy settings to be utilized for the request.
        :param timeout: Specifies the maximum time that the actual HTTP request can take.
        :param verify: Specifies if SSL certificates should be validated.
        """
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
        """
        Responsible for dispatching the request and returning the result.
        Network level exceptions should be raised and only ``requests.Response`` should be returned.

        ``**_`` should be added to the method call to ignore the extra arguments intended for the cache handler.

        :param request: A ``requests.PreparedRequest`` object containing all the data necessary to perform the request.
        :param proxies: A dictionary of proxy settings to be utilized for the request.
        :param timeout: Specifies the maximum time that the actual HTTP request can take.
        :param verify: Specifies if SSL certificates should be validated.
        """
        self.logger.debug('{:4} {}'.format(request.method, request.url))
        return self.http.send(request, proxies=proxies, timeout=timeout, allow_redirects=False, verify=verify)

    @staticmethod
    def dispatch_timer(next_possible_dispatch):
        """
        Method to determine when the next request can be dispatched.
        :param next_possible_dispatch: Timestamp of the next possible dispatch.
        :type next_possible_dispatch: int | float
        :return: int | float
        """
        time_until_dispatch = next_possible_dispatch - time()
        if time_until_dispatch > 0:  # Make sure that we have given it enough time.
            return time_until_dispatch
        return 0
