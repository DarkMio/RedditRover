from configparser import ConfigParser
from os import path
import praw
import core.filtering as filtering
import pkgutil

from core import LogProvider
from core.MultiThreader import MultiThreader

class MassdropBot(object):
    logger = None           # Logging Session with full console setup.
    config = None           # Holds later a full set of configs from ConfigParser.
    users = None            # Holds usernames
    passwords = None        # Holds passwords within
    responders = None       # Keeps track of all responder objects
    multi_thread = None     # Reference to MultiThreader, which ... does the threading.

    reddit = None           # Anonymous reddit session
    submissions = None      # Kinda list of submissions which the threads work through
    comments = None         # Same applies here, the comments are a list, another thread runs through them

    def __init__(self):
        self.logger = LogProvider.setup_logging(log_level="DEBUG")
        self.read_config()
        self.load_responders()
        self.multi_thread = MultiThreader()
        self.reddit = praw.Reddit(user_agent='Data-Poller for several bot-logins by /u/DarkMio')
        self.submission_stream()
        self.comment_stream()
        self.multi_thread.go([self.print_submissions])
        self.multi_thread.join_threads()

    def load_responders(self):
        # cleaning of the list
        self.responders = list()
        # preparing the right sub path.
        package = filtering
        prefix = package.__name__ + "."

        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            module = __import__(modname, fromlist="dummy")
            module = module.init()
            try:
                module.integrity_check()
                self.logger.info('Module "{}" is initialized and ready.'.format(module.__class__.__name__))
            except AssertionError as e:
                self.logger.error("{}: {}".format(module.__class__.__name__, e))
                continue
            self.responders.append(module)
        self.logger.info("Imported a total of {} object(s).".format(len(self.responders)))

    def print_submissions(self):
        from pprint import pprint
        for sub in self.submissions:
            pprint(vars(sub))
            break
        for cmt in self.comments:
            pprint(vars(cmt))
            break

    def submission_stream(self):
        self.submissions = praw.helpers.submission_stream(self.reddit, 'all', limit=None, verbosity=0)
        self.logger.info("Opened submission stream successfully.")

    def comment_stream(self):
        self.comments = praw.helpers.comment_stream(self.reddit, 'all', limit=None, verbosity=0)
        self.logger.info("Opened comment stream successfully.")


    def read_config(self):
        self.config = ConfigParser()
        self.config.read(path.dirname(__file__) + "/config/config.ini")
        self.logger.info("Configuration read and set up properly.")


if __name__ == "__main__":
    mb = MassdropBot()