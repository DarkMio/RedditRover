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
        self._table_rows()
        self._plugin_activity()
        self._subreddit_activity()
        self._post_histogram()

    def _table_rows(self):
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

    def _plugin_activity(self):
        dataset = db.get_all_stats()
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

    def _subreddit_activity(self):
        dataset = db.get_all_stats()
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

    def _post_histogram(self):
        dataset = db.get_all_stats()
        carelist = []
        date_change_dataset = [[line[1], datetime.datetime.strptime(line[2], "%Y-%m-%d %H:%M:%S")] for line in dataset]
        post_history = {}
        for line in date_change_dataset:
            timestamp = int(line[1].timestamp()) // 3600
            if line[0] in post_history:
                if timestamp in post_history[line[0]]:
                    post_history[line[0]][timestamp] += 1
                else:
                    post_history[line[0]][timestamp] = 1
            else:
                post_history[line[0]] = {timestamp: 1}
        for key, value in post_history.items():
            all_values = sorted(value.items())
            start, end = all_values[0][0], all_values[-1][0]
            for x in range(start, end+1):
                if x not in value:
                    value[x] = 0
        for k, v in post_history.items():
            some_list = []
            for key, value in sorted(v.items()):
                some_list.append([key*3600*1000, value])
            carelist.append({'name': k, 'data': some_list})
        with open('./out/post_history.json', 'w') as f:
            f.write(json.dumps(carelist))

sf = StatisticsFeeder(db, None)
sf.render_json()
