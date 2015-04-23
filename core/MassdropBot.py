from configparser import ConfigParser
from os import path
import core.filtering as filtering
import pkgutil
import json

from core import LogProvider


class MassdropBot(object):
    logger = None           # Logging Session with full console setup.
    config = None           # Holds later a full set of configs from ConfigParser.
    users = None            # Holds usernames
    passwords = None        # Holds passwords within
    responders = None       # Keeps track of all responder objects

    def __init__(self):
        self.logger = LogProvider.setup_logging(log_level="DEBUG")
        self.read_config()
        self.load_responders()

    def load_responders(self):
        # cleaning of the list
        self.responders = list()
        # preparing the right sub path.
        package = filtering
        prefix = package.__name__ + "."

        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            self.logger.info("Found sub-module {0} (is a package: {1})".format(modname, ispkg))
            module = __import__(modname, fromlist="dummy")
            module = module.init()
            self.responders.append(module)
        self.logger.info("Imported a total of {} object(s).".format(len(self.responders)))

    def read_config(self):
        self.config = ConfigParser()
        self.config.read(path.dirname(__file__) + "/config/config.ini")
        self.logger.info("Configuration read and set up properly.")


if __name__ == "__main__":
    mb = MassdropBot()