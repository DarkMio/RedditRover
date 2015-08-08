from abc import ABCMeta, abstractmethod
import logging
import praw
from OAuth2Util import OAuth2Util


class Base(metaclass=ABCMeta):
    DESCRIPTION = None  # user_agent: describes the bot / function / author
    USERNAME = None  # reddit username
    PASSWORD = None  # password of reddit username
    REGEX = None  # most basic regex string - pre-filters incoming threads
    BOT_NAME = None  # Give the bot a nice name.
    session = None  # a full session with login into reddit.
    logger = None  # logger for specific module
    config = None  # Could be used for ConfigParser - there is a method for that.
    database = None  # Session to database.

    def __init__(self, database):
        self.factory_logger()
        self.database = database

    def integrity_check(self):
        assert self.USERNAME and self.PASSWORD and self.REGEX and self.DESCRIPTION, \
            "Failed constant variable integrity check. Check your object and its initialization."
        return True

    def factory_logger(self):
        self.logger = logging.getLogger("plugin")

    def factory_reddit(self, config_file=None):
        session = praw.Reddit(user_agent=self.DESCRIPTION)
        if not config_file:
            # @TODO: Needs replacement with Bot Name
            oauth = OAuth2Util(session, configfile="../config/Massdrop_OAuth.ini")
        else:
            oauth = OAuth2Util(session, configfile=config_file)
        return session, oauth

    def factory_config(self, auto_config):
        from os import path
        from configparser import ConfigParser

        self.config = ConfigParser()
        self.config.read(path.dirname(__file__) + "/config/bot_config.ini")

        if auto_config:
            pass

    @abstractmethod
    def execute_submission(self, submission):
        pass

    @abstractmethod
    def execute_link(self, link_submission):
        pass

    @abstractmethod
    def execute_titlepost(self, title_only):
        pass

    @abstractmethod
    def execute_comment(self, comment):
        pass

    @abstractmethod
    def update_procedure(self, thing_id, created, lifetime, last_updated, interval):
        pass
