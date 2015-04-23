from abc import ABCMeta, abstractmethod
import logging


class Base(metaclass=ABCMeta):
    DESCRIPTION = None      # user_agent: describes the bot / function / author
    USERNAME = None         # reddit username
    PASSWORD = None         # password of reddit username
    REGEX = None            # most basic regex string - pre-filters incoming threads
    session = None          # a full session with login into reddit.
    logger = None           # logger for specific module

    def __init__(self):
        self.factory_logger()

    def integrity_check(self):
        assert self.USERNAME and self.PASSWORD and self.REGEX and self.DESCRIPTION, \
               "Failed constant variable integrity check. Check your object and its initialization."
        return True

    def factory_logger(self):
        self.logger = logging.getLogger("plugin")
        self.logger.info("Logging set up for sub module {}. Module is up and ready.".format(__name__))

    def factory_reddit(self):
        import praw
        self.session = praw.Reddit(user_agent = self.DESCRIPTION)
        self.session.login(self.USERNAME, self.PASSWORD)

    @abstractmethod
    def information_of_interest(self, string):
        pass

    @abstractmethod
    def logical_features(self):
        pass

    @abstractmethod
    def update_procedure(self, thing_id):
        pass