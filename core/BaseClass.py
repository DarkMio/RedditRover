from abc import ABCMeta, abstractmethod
import logging


class Base(metaclass=ABCMeta):
    DESCRIPTION = None      # user_agent: describes the bot / function / author
    USERNAME = None         # reddit username
    PASSWORD = None         # password of reddit username
    REGEX = None            # most basic regex string - pre-filters incoming threads
    session = None          # a full session with login into reddit.
    logger = None           # logger for specific module
    config = None           # Could be used for ConfigParser - there is a method for that.

    def __init__(self):
        self.factory_logger()

    def integrity_check(self):
        assert self.USERNAME and self.PASSWORD and self.REGEX and self.DESCRIPTION, \
               "Failed constant variable integrity check. Check your object and its initialization."
        return True

    def factory_logger(self):
        self.logger = logging.getLogger("plugin")

    def factory_reddit(self):
        import praw
        self.session = praw.Reddit(user_agent = self.DESCRIPTION)
        self.session.login(self.USERNAME, self.PASSWORD)

    def factory_config(self):
        from os import path
        from configparser import ConfigParser
        self.config = ConfigParser()
        self.config.read(path.dirname(__file__) + "/config/bot_config.ini")

    @abstractmethod
    def execute_submission(self, submission):
        pass

    @abstractmethod
    def execute_comment(self, comment):
        pass

    @abstractmethod
    def update_procedure(self, thing_id):
        pass