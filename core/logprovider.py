# coding=utf-8
import logging
import sys
import os
import time
from pkg_resources import resource_filename
from time import mktime
from calendar import timegm
from logging.handlers import BaseRotatingHandler

FORMAT = '%(asctime)s [%(levelname)s] -- [%(name)s:%(module)s/%(funcName)s] -- %(message)s'
CHAT_FORMAT = '[%(asctime)] %(message)'
LOGGING_LEVELS = {"NOTSET": logging.NOTSET, "DEBUG": logging.DEBUG,
                  "INFO": logging.INFO, "WARNING": logging.WARNING,
                  "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}
TIME_FORMAT = '%H:%M:%S'
DAY = 60 * 60 * 24  # Seconds in a day


# noinspection PyMissingConstructor
class _SingleLevelFilter(logging.Filter):
    """
    Filters a certain logging-level out - used to split error messages to stderr instead of writing into stdout.

    :ivar passlevel: The logging level from where the split should occur.
    :type passlevel: str | int
    :vartype passlevel: str | int
    :ivar reject: Sets if these messages should be displayed in that handler.
    :type reject: bool
    :vartype reject: bool
    """
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        """
        Checks if it has to be filtered or not.

        :param record: a logger message
        :return: **True** if filtered, else **False**.
        :rtype: bool
        """
        if self.reject:
            return record.levelno != self.passlevel
        else:
            return record.levelno == self.passlevel


def setup_logging(log_level="INFO", console_log_level=None, log_path_format="logs/%Y/%m/%Y-%m-%d.log",
                  web_log_path='../logs/log.txt'):
    """
    Thanks to Renol: https://github.com/RenolY2/Renol-IRC-rv2 - This logging handler is quite powerful and
    nicely formatted. This sets up the main Logger and needed to receive bot and plugin messages. If you're testing
    a single plugin it is recommended to execute this.

    :param log_level: Level on which the logger operates
    :type log_level: str
    :param console_log_level: Determines the console log level, which is usually the same as `log_level`
    :type console_log_level: str
    :param log_path_format: Path-Format for `/logs/`, supports sub folders
    :type log_path_format: str
    """
    null_handler = logging.NullHandler()
    logging.basicConfig(level=log_level, handlers=[null_handler])

    if console_log_level is None:
        console_log_level = log_level

    # log_level = LOGGING_LEVELS[log_level]
    console_log_level = LOGGING_LEVELS[console_log_level]

    logging_format = logging.Formatter(FORMAT, datefmt=TIME_FORMAT)

    # Set up the handler for logging to console
    filter_info = _SingleLevelFilter(logging.INFO, True)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(logging_format)
    console_handler.addFilter(filter_info)

    # Separating error and regular output
    not_filter_info = _SingleLevelFilter(logging.INFO, False)
    standard_handler = logging.StreamHandler(sys.__stdout__)
    standard_handler.setLevel(console_log_level)
    standard_handler.setFormatter(logging_format)
    standard_handler.addFilter(not_filter_info)

    # Adding a log handler
    file_handler = DailyRotationHandler(log_path_format, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging_format)

    # Adding a 1.5k lines web handler
    web_handler = MaxFileHandler(web_log_path, encoding='utf-8')
    web_handler.setLevel(logging.DEBUG)
    web_handler.setFormatter(logging_format)

    # this logger writes completely into the console.
    bot_logger = logging.getLogger("bot")
    bot_logger.propagate = False
    bot_logger.addHandler(console_handler)
    bot_logger.addHandler(standard_handler)
    bot_logger.addHandler(file_handler)
    bot_logger.addHandler(web_handler)

    plugin_logger = logging.getLogger("plugin")
    plugin_logger.propagate = False
    plugin_logger.addHandler(console_handler)
    plugin_logger.addHandler(standard_handler)
    plugin_logger.addHandler(file_handler)
    plugin_logger.addHandler(web_handler)

    database_logger = logging.getLogger("database")
    database_logger.propagate = False
    database_logger.addHandler(console_handler)
    database_logger.addHandler(standard_handler)
    database_logger.addHandler(file_handler)
    database_logger.addHandler(web_handler)

    handler_logger = logging.getLogger('hndl')
    handler_logger.propagate = False
    handler_logger.addHandler(file_handler)
    handler_logger.addHandler(web_handler)

    bot_logger.info("RedditRover Logger initialized.")
    logging.getLogger("requests").setLevel(logging.WARNING)

    offset, tzname = _local_time_offset()
    if offset >= 0:
        offset = "+" + str(offset)
    else:
        offset = str(offset)
    bot_logger.info("All time stamps are in UTC{0} ({1})".format(offset, tzname))
    return bot_logger


def _local_time_offset():
    """
    Returns UTC offset and name of time zone at current time
    Based on http://stackoverflow.com/a/13406277
    """
    t = time.time()
    if time.localtime(t).tm_isdst and time.daylight:
        return -time.altzone / 3600, time.tzname[1]
    else:
        return -time.timezone / 3600, time.tzname[0]


# noinspection PyPep8Naming
class DailyRotationHandler(BaseRotatingHandler):
    """
    This handler swaps over logs after a day. Quirky method names result from inheriting.

    :ivar path_format: Path-Format for `/logs/`, supports sub folders
    :type path_format: str
    :vartype path_format: str
    :ivar utc: Timestamp in utc
    :type utc: bool
    :vartype utc: bool
    """
    def __init__(self, pathformat="logs/%Y/%m/%Y-%m-%d.log", utc=False, encoding=None, delay=False):
        self.path_format = pathformat
        self.utc = utc
        current_time = self._get_time()
        current_file = self._format_time(current_time)
        self._current_day = self._get_days_since_epoch(current_time)
        self._create_dirs(resource_filename('logs', current_file))
        BaseRotatingHandler.__init__(self, filename=resource_filename('logs', current_file), mode="a",
                                     encoding=encoding, delay=delay)

    def shouldRollover(self, record):
        """
        Checks if a rollover has to be done

        :param record: Logger message
        :return: Boolean to determine if or if not.
        :rtype: bool
        """
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

    def doRollover(self):
        """
        Does the rollover.
        """
        new_filename = os.path.abspath(self._format_time())
        if self.stream:
            self.stream.close()
            delattr(self, 'stream')
        self._create_dirs(new_filename)
        self.baseFilename = new_filename
        self.stream = self._open()

    @staticmethod
    def _create_dirs(file_path):
        """
        Creates the dirs if needed.
        """
        directories, filename = os.path.split(file_path)
        os.makedirs(directories, exist_ok=True)

    def _get_time(self):
        """
        Gets timezone time or utc time, based on the utc flag on attribute `utc`.
        """
        if self.utc:
            return time.gmtime()
        else:
            return time.localtime()

    def _format_time(self, struct_time=None):
        """
        Formats the time

        :param struct_time: time formatter
        :return: Formatted time
        :rtype: time.strftime
        """
        if struct_time is None:
            struct_time = self._get_time()
        return time.strftime(self.path_format, struct_time)

    def _get_days_since_epoch(self, struct_time):
        """
        More time functions

        :param struct_time: the struct_time used to calculate epoch.
        :return: formatted time
        """
        if self.utc:
            return timegm(struct_time) // DAY
        else:
            return mktime(struct_time) // DAY


class MaxFileHandler(logging.FileHandler):
    def __init__(self, filename, max_len=1500, buffer_len=1400, mode='a+', encoding=None, delay=False):
        assert max_len > buffer_len, "buffer_len has to be smaller than max_len"
        super().__init__(filename, mode, encoding, delay)
        self.max_len = max_len
        self.filename, self.mode, self.encoding = filename, mode, encoding
        self.f_len = len(self.stream.read().splitlines())
        self.buffer_len = buffer_len

    def emit(self, record):
        if self.stream is None:
            self.stream = self._open()
        length = self.f_len - self.max_len
        if length > 0:
            from time import sleep
            self.acquire()
            with open(self.filename, 'r+', encoding='utf-8') as f:
                f_lines = f.read().splitlines()
                f_lines = f_lines[self.max_len - self.buffer_len:]
                f.seek(0)
                f.truncate(0)
                f.write('\n'.join(f_lines) + self.terminator)
                self.f_len = len(f_lines)
            self.release()

            # f_list = self.f_list[length:]
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg)
            self.f_len += 1
            stream.write(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


if __name__ == "__main__":
    from time import sleep
    logger = setup_logging()
    for i in range(16000):
        if i % 1500 == 0:
            print(">> HALTED")
            sleep(5)
        logger.info(i)
