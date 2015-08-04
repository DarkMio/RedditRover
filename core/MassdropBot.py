from configparser import ConfigParser
from os import path
import praw
import core.filtering as filtering
import pkgutil
import warnings

from core import LogProvider
from core.MultiThreader import MultiThreader
from core.DatabaseProvider import DatabaseProvider
from misc import warning_filter


class MassdropBot:
    logger = None  # Logging Session with full console setup.
    config = None  # Holds later a full set of configs from ConfigParser.
    users = None  # Holds usernames
    passwords = None  # Holds passwords within
    responders = None  # Keeps track of all responder objects
    multi_thread = None  # Reference to MultiThreader, which ... does the threading.
    database = None  # Reference to the DatabaseProvider

    reddit = None  # Anonymous reddit session
    submissions = None  # Kinda list of submissions which the threads work through
    comments = None  # Same applies here, the comments are like a list, another thread runs through them

    def __init__(self):
        warning_filter.ignore()
        self.logger = LogProvider.setup_logging(log_level="DEBUG")
        self.read_config()
        self.load_responders()
        self.multi_thread = MultiThreader()
        self.database = DatabaseProvider()
        self.reddit = praw.Reddit(user_agent='Data-Poller for several logins by /u/DarkMio')
        global database
        database = self.database
        global config
        config = self.config
        self.submission_stream()
        self.comment_stream()
        self.multi_thread.go([self.print_submissions])
        self.multi_thread.join_threads()

    def load_responders(self):
        """Main method to load sub-modules, which are designed as a framework for multiple bots.
           This allows to abstract bots even more than what PRAW does and it's nicely handled in
           a threaded environment to do multiple tasks pretty efficient without writing a full new bot."""
        # cleaning of the list
        self.responders = list()
        # preparing the right sub path.
        package = filtering
        prefix = package.__name__ + "."

        # we're running through all
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            module = __import__(modname, fromlist="dummy")
            # every sub module has to have an object provider,
            # this makes importing the object itself easy and predictable.
            module_object = module.init()
            try:
                # could / should fail due to variable validation
                # (aka: is everything properly set to even function remotely.)
                module_object.integrity_check()
                self.logger.info('Module "{}" is initialized and ready.'.format(module_object.__class__.__name__))
            except AssertionError as e:
                # Catches the error and skips the module. The import will now be reversed.
                self.logger.error("{}: {}".format(module_object.__class__.__name__, e))
                del module, module_object
                continue
            # If nothing failed, it's fine to import.
            self.responders.append(module_object)
        self.logger.info("Imported a total of {} object(s).".format(len(self.responders)))

    def print_submissions(self):
        """Prints one recent submission and one recent comment object."""
        from pprint import pprint

        for sub in self.submissions:
            pprint(vars(sub))
            break
        for cmt in self.comments:
            pprint(vars(cmt))
            break

    def submission_thread(self):
        for submission in self.submissions:
            for responder in self.responders:
                if not self.database.get_thing_from_storage(submission.id, responder.BOT_NAME):
                    try:
                        if submission.is_self and submission.selftext:
                            responded = responder.execute_submission(submission)
                        elif submission.is_self:
                            responded = responder.execute_titlepost(submission)
                        else:
                            responded = responder.execute_link(submission)

                        # a responder should return with true of false, so we can manage the database for it here.
                        # reminder: writing on multiple threads is bad, reading is always fine.
                        if responded:
                            self.database.insert_into_storage(submission.id, responder.BOT_NAME)
                    except Exception as e:
                        self.logger.error("{} error: {}".format(responder.__class__.__name__, e.__cause__))

    def comment_thread(self):
        for comment in self.comments:
            for responder in self.responders:
                if not self.database.get_thing_from_storage(comment.id, responder.BOT_NAME):
                    try:
                        responder.execute_comment(comment)
                    except Exception as e:
                        self.logger.error("{} error: {}".format(responder.__class__.__name__, e.__cause__))

    def submission_stream(self):
        """Opens a new thread, which reads submissions from a specified subreddit."""
        self.submissions = praw.helpers.submission_stream(self.reddit, 'massdropbot', limit=None, verbosity=0)
        self.logger.info("Opened submission stream successfully.")

    def comment_stream(self):
        """Opens a new thread, which reads comments from a specified subreddit."""
        self.comments = praw.helpers.comment_stream(self.reddit, 'massdropbot', limit=None, verbosity=0)
        self.logger.info("Opened comment stream successfully.")

    def read_config(self):
        """Reads the config."""
        self.config = ConfigParser()
        self.config.read(path.dirname(__file__) + "/config/config.ini")
        self.logger.info("Configuration read and set up properly.")


if __name__ == "__main__":
    mb = MassdropBot()
