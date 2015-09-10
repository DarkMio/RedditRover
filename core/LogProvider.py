# coding=utf-8
import logging
import sys
import os
import time
from pkg_resources import resource_filename
from time import mktime
from calendar import timegm
from logging.handlers import BaseRotatingHandler

FORMAT = '%(asctime)s [%(levelname)s] -- [%(name)s:%(module)s/%(funcName)s]-- %(message)s'
CHAT_FORMAT = '[%(asctime)] %(message)'
LOGGING_LEVELS = {"NOTSET": logging.NOTSET, "DEBUG": logging.DEBUG,
                  "INFO": logging.INFO, "WARNING": logging.WARNING,
                  "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}
TIME_FORMAT = '%H:%M:%S'
DAY = 60 * 60 * 24  # Seconds in a day


# noinspection PyMissingConstructor
class SingleLevelFilter(logging.Filter):
    """Filters a certain logging-level out - used to split error messages to stderr instead of writing into stdout."""
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return record.levelno != self.passlevel
        else:
            return record.levelno == self.passlevel


def setup_logging(log_level="INFO", console_log_level=None, log_path_format="%Y/%m/%Y-%m-%d.log"):
    """Thanks to Renol: https://github.com/RenolY2/Renol-IRC-rv2
       This logging handler is quite powerful and nicely formatted."""
    null_handler = logging.NullHandler()
    logging.basicConfig(level=log_level, handlers=[null_handler])

    if console_log_level is None:
        console_log_level = log_level

    # log_level = LOGGING_LEVELS[log_level]
    console_log_level = LOGGING_LEVELS[console_log_level]

    logging_format = logging.Formatter(FORMAT, datefmt=TIME_FORMAT)

    # Set up the handler for logging to console
    filter_info = SingleLevelFilter(logging.INFO, True)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(logging_format)
    console_handler.addFilter(filter_info)

    # Separating error and regular output
    not_filter_info = SingleLevelFilter(logging.INFO, False)
    standard_handler = logging.StreamHandler(sys.__stdout__)
    standard_handler.setLevel(console_log_level)
    standard_handler.setFormatter(logging_format)
    standard_handler.addFilter(not_filter_info)

    # Adding a log handler
    file_handler = DailyRotationHandler(log_path_format, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging_format)

    # this logger writes completely into the console.
    bot_logger = logging.getLogger("bot")
    bot_logger.propagate = False
    bot_logger.addHandler(console_handler)
    bot_logger.addHandler(standard_handler)
    bot_logger.addHandler(file_handler)

    plugin_logger = logging.getLogger("plugin")
    plugin_logger.propagate = False
    plugin_logger.addHandler(console_handler)
    plugin_logger.addHandler(standard_handler)
    plugin_logger.addHandler(file_handler)

    database_logger = logging.getLogger("database")
    database_logger.propagate = False
    database_logger.addHandler(console_handler)
    database_logger.addHandler(standard_handler)
    database_logger.addHandler(file_handler)

    handler_logger = logging.getLogger('hndl')
    handler_logger.propagate = False
    handler_logger.addHandler(file_handler)

    bot_logger.info("RedditRover Logger initialized.")
    logging.getLogger("requests").setLevel(logging.WARNING)

    offset, tzname = local_time_offset()
    if offset >= 0:
        offset = "+" + str(offset)
    else:
        offset = str(offset)

    bot_logger.info("All time stamps are in UTC{0} ({1})".format(offset, tzname))
    return bot_logger


def local_time_offset():
    """Returns UTC offset and name of time zone at current time
       Based on http://stackoverflow.com/a/13406277"""
    t = time.time()

    if time.localtime(t).tm_isdst and time.daylight:
        return -time.altzone / 3600, time.tzname[1]
    else:
        return -time.timezone / 3600, time.tzname[0]


class DailyRotationHandler(BaseRotatingHandler):
    def __init__(self, pathformat="%Y/%m/%Y-%m-%d.log", utc=False, encoding=None, delay=False):
        self.path_format = pathformat
        self.utc = utc

        # Placeholder function for the info function of the
        # logging module.
        self.logging_writeinfo = lambda *args: None
        current_time = self._get_time()
        current_file = self._format_time(current_time)
        self._current_day = self._get_days_since_epoch(current_time)
        self._create_dirs(resource_filename('logs', current_file))
        BaseRotatingHandler.__init__(self, filename=resource_filename('logs', current_file), mode="a",
                                     encoding=encoding, delay=delay)

    # This function will be used to write information
    # about the rollover, e.g. the new file name that will be
    # written to.
    def set_logging_info_func(self, func):
        self.logging_writeinfo = func

    def shouldRollover(self, record):
        now = self._get_time()
        day = self._get_days_since_epoch(now)

        # The no_rollover attribute can be set when writing a log entry
        # so that no rollover happens. This can be used to keep
        # a set of log entries in the same file.
        if hasattr(record, "no_rollover") and record.no_rollover:
            return False
        elif self._current_day != day:
            self._current_day = day

            return True
        else:
            return False

    def do_rollover(self):
        new_filename = os.path.abspath(self._format_time())

        # To prevent the function from going into an infinite recursive
        # loop, the rollover will be disabled using the extra argument.
        self.logging_writeinfo("Rollover is happening! New filename is {}".format(new_filename),
                               extra={"no_rollover": True})

        if self.stream:
            self.stream.close()
            delattr(self, 'stream')

        self._create_dirs(new_filename)
        time_offset, timezone = local_time_offset()
        old_name = self.baseFilename
        self.baseFilename = new_filename
        self.stream = self._open()

        self.logging_writeinfo("Rollover happened! Old filename was {}".format(old_name), extra={"no_rollover": True})
        self.logging_writeinfo("New filename is {}".format(new_filename), extra={"no_rollover": True})

        # We want to have a time_offset string formatted as
        # "+<num>" or "-<num>". If the time offset is 0 or bigger,
        # we need to add the + sign to the string.
        time_offset_str = str(time_offset)
        if time_offset >= 0:
            time_offset_str = "+" + time_offset_str

        self.logging_writeinfo("Current time offset: %s (%s)", time_offset_str, timezone,
                               extra={"no_rollover": True})

    @staticmethod
    def _create_dirs(file_path):
        directories, filename = os.path.split(file_path)
        os.makedirs(directories, exist_ok=True)

    def _get_time(self):
        if self.utc:
            return time.gmtime()
        else:
            return time.localtime()

    def _format_time(self, struct_time=None):
        if struct_time is None:
            struct_time = self._get_time()
        return time.strftime(self.path_format, struct_time)

    def _get_days_since_epoch(self, struct_time):
        if self.utc:
            return timegm(struct_time) // DAY
        else:
            return mktime(struct_time) // DAY

if __name__ == "__main__":
    setup_logging()
