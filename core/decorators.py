# coding=utf-8
from functools import wraps
from time import sleep


def retry(exception_to_check, tries=4, delay=3, backoff=2):
    """
    Retry calling the decorated function using an exponential backoff.

    :param exception_to_check: the exception to check. may be a tuple of
        exceptions to check
    :type exception_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            logger, obj = None, None
            if args:
                obj = args[0]
            if obj and hasattr(obj, 'logger'):
                logger = obj.logger
            mdelay = delay
            for x in range(tries):
                try:
                    return f(*args, **kwargs)
                except exception_to_check as e:
                    obj_msg = ('', '{}.'.format(obj.__class__.__name__))[obj is not None]
                    msg = "{}{} encountered: {}: {}  -  retrying in {} seconds.".format(obj_msg, f.__name__,
                                                                                        e.__class__.__name__, e, mdelay)
                    if logger: logger.warning(msg)
                    else: print(msg)
                    sleep(mdelay)
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry
