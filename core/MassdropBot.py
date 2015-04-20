from configparser import ConfigParser
from os import path
import json

from core import LogProvider


class MassdropBot(object):
    logger = None           # Logging Session with full console setup.
    config = None           # Holds later a full set of configs from ConfigParser.
    users = None            # Holds usernames
    passwords = None        # Holds passwords within

    def __init__(self):
        self.logger = LogProvider.setup_logging(log_level="DEBUG")
        self.read_config()
        self.logger.error("I am raising an error.")

    def load_responders(self):
        return

    def read_config(self):
        self.config = ConfigParser()
        self.config.read(path.dirname(__file__) + "/config/config.ini")
        self.users = json.loads(self.config.get('REDDIT', 'usernames'))
        self.passwords = json.loads(self.config.get('REDDIT', 'passwords'))
        assert len(self.users) == len(self.passwords), "Mismatch in username and password length."
        self.logger.info("Configuration read and set up properly.")


if __name__ == "__main__":
    mb = MassdropBot()