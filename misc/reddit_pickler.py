"""Looks like PRAW doesn't want to get pickle'd.
    Both single submissions and generators are indeed broken."""

from praw import Reddit
import pickle
from sys import setrecursionlimit
from time import time
from os import listdir


def get_session():
    return Reddit(user_agent="Data Pickler for data training.")


def get_submissions(r, subreddit):
    return r.get_subreddit(subreddit).get_hot(limit=1)


def get_single_submission(generator):
    for sub in generator:
        return sub


def write_reddit(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_reddit(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def single_submission(r):
    return r.get_submission(url='http://www.reddit.com/r/thebutton/comments/36salf/')


if __name__ == "__main__":
    r = get_session()
    # Get hot:
    submissions = get_submissions(r, "dota2")
    # Return first of hot:
    submission = get_single_submission(submissions)
    # Get a singular submission via URL:
    single_submission = single_submission(r)
    carelist = [submissions, submission, single_submission]
    for pls_pickle in carelist:
        try:
            write_reddit(pls_pickle, "../t_data/{}.pi".format(int(time())))
        except Exception as e:
            print("Writing error: {}".format(e))
    # setrecursionlimit(10000)
    for file in listdir("../t_data/"):
        try:
            print(load_reddit("../t_data/{}".format(file)))
        except Exception as e:
            print("Loading error: {}".format(e))
