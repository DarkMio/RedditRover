# coding=utf-8
import jinja2
from core.database import Database
import json
import time
import datetime
from praw import Reddit

db = Database()

class StatisticsFeeder:
    """
    :type db: Database
    :type session: Reddit
    """
    def __init__(self, database, handler):
        self.db = database
        self.session = Reddit(user_agent='Statistics poller for RedditRover', handler=handler)

    def get_old_comment_karma(self):
        threads = self.db.get_karma_loads()
        for thread in threads:  # tuple of tuple
            thing_id = thread[0]
            thing = self.session.get_info(thing_id=thing_id)
            author_votes = thing.upvotes
            for comment in thing.comments:
                if comment.author in self.db.get_all_modules():
                    self.db.update_karma_count(thing_id, author_votes, comment.votes)

    def render_json(self):
        dataset = db.get_all_stats()
        carelist = []
        title = '<a href="{url}" target="_blank" class="text-primary"> {text} </a>'
        subreddit = '<a href="http://reddit.com/r/{sub}" target="_blank" class="text-warning"> {sub} </a>'
        author = '<a href="http://reddit.com/u/{usr}" target="_blank"> {usr} </a>'
        for line in dataset:
            carelist.append({'id': line[0], 'plugin': line[1], 'time': line[2],
                             'title': title.format(url=line[6], text=line[3]), 'username': author.format(usr=line[4]),
                             'subreddit': subreddit.format(sub=line[5]), 'permalink': line[6]})
        with open('./out/rows.json', 'w') as f:
            f.write(json.dumps(carelist))

        chart_data = {}
        for line in dataset:
            if line[1] in chart_data:
                chart_data[line[1]] += 1
            else:
                chart_data[line[1]] = 1
        carelist = []
        for k, v in chart_data.items():
            carelist.append({'name': k, 'data': v})

        with open('./out/post_list.json', 'w') as f:
            f.write(json.dumps(carelist))

        carelist = []
        subreddit_data = {}
        for line in dataset:
            if line[5] in subreddit_data:
                subreddit_data[line[5]] += 1
            else:
                subreddit_data[line[5]] = 1
        for k, v in subreddit_data.items():
            carelist.append({'name': k, 'data': v})
        carelist = sorted(carelist, key=lambda x: x['data'])
        carelist = [dict for dict in carelist if dict['data'] > 2]
        with open('./out/subreddit_data.json', 'w') as f:
            f.write(json.dumps(carelist))

        carelist = []
        date_change_dataset = [[line[1], datetime.datetime.strptime(line[2], "%Y-%m-%d %H:%M:%S")] for line in dataset]
        post_history = {}
        for line in date_change_dataset:
            timestamp = 1000 * int(line[1].timestamp())
            if line[0] in post_history:
                post_history[line[0]].append(timestamp)
            else:
                post_history[line[0]] = [timestamp]
        for k, v in post_history.items():
            carelist.append({'name': k, 'data': v})
        with open('./out/post_history.json', 'w') as f:
            f.write(json.dumps(carelist))

sf = StatisticsFeeder(db, None)
sf.get_old_comment_karma()