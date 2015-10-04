# coding=utf-8
from core.database import Database
import json
import datetime
from praw import Reddit
from praw.objects import Submission, Comment, MoreComments
from configparser import ConfigParser
from pkg_resources import resource_filename
from time import time
import atexit


class StatisticsFeeder:
    """
    :type db: Database
    :type session: Reddit
    """
    def __init__(self, database, handler, path='../html/'):
        self.db = database
        self.path = path
        self.session = Reddit(user_agent='Statistics poller for RedditRover', handler=handler)
        self.config = ConfigParser()
        self.config.read(resource_filename('config', 'bot_config.ini'))
        self.authors = self.get_authors()
        self.status_online()
        atexit.register(self.status_offline)

    def _set_status(self, state, message):
        template_info = '''<span class="label label-{type}">Status: {title}</span>'''
        if state == 'online':
            info = template_info.format(type='success', title='Online', content=message)
        elif state == 'offline':
            info = template_info.format(type='danger', title='Offline', content=message)
        elif state == 'warning':
            info = template_info.format(type='warn', title='Warning', content=message)
        else:
            info = ''
        self._write_meta(info=info)

    def _write_meta(self, info):
        meta_stats = self.db.select_day_from_meta(time())
        if meta_stats:
            date, subm, comments, cycles = meta_stats
            reacted = self.db.get_total_responses_per_day(time())[0]
            rate = reacted * 100 / (comments + subm)
        else:
            subm, comments, cycles, rate = 0, 0, 0, 0
        with open(self.path + '_data/_meta.json', 'w') as f:
            f.write(json.dumps(
                {'status': info, 'submissions': subm, 'comments': comments, 'cycles': cycles,
                 'rate': '{:.5f}'.format(rate)}
            ))

    def status_online(self):
        self._set_status('online', 'The bot is currently running, last update was {}'.format(time()))

    def status_offline(self):
        self._set_status('offline', 'The bot is currently offline.')

    def status_warning(self, traceback=None):
        if traceback:
            self._set_status('warning', 'Here is the latest traceback: <br /><pre>{}</pre>'.format(traceback))
        else:
            self._set_status('warning', 'Check the console, there is maybe an error. (no traceback given)')

    def get_authors(self):
        carelist = []
        for section in self.config.sections():
            for option in self.config.options(section):
                if option == 'username':
                    carelist.append(self.config.get(section, option).lower())
        return carelist

    def get_old_comment_karma(self):
        threads = self.db.get_karma_loads()
        for thread in threads:  # tuple of tuple
            thing_id = thread[0]
            thing = self.session.get_info(thing_id=thing_id)
            author_votes = thing.score
            if type(thing) is Comment:
                replies = thing.replies
            elif type(thing) is Submission:
                thing.replace_more_comments(limit=None, threshold=1)
                replies = thing.comments
            elif type(thing) is MoreComments:
                replies = thing.comments(update=True)
            for comment in replies:
                if comment.author and comment.author.name.lower() in self.authors:
                    self.db.update_karma_count(thing_id, author_votes, comment.score)
                    break
            else:
                self.db.update_karma_count_with_null(thing_id, author_votes)

    def _write_filler_karma(self):
        from random import randint
        threads = self.db.get_karma_loads()
        for thread in threads:
            thread_id = thread[0]
            self.db.update_karma_count(thread_id, randint(-50, 350), randint(-50, 350))

    def render_overview(self):
        self.status_online()
        self._table_rows()
        self._plugin_activity()
        self._subreddit_activity()
        self._post_histogram()

    def _table_rows(self):
        dataset = self.db.get_all_stats()
        carelist = []
        title = '<a href="{url}" target="_blank" class="text-primary"> {text} </a>'
        subreddit = '<a href="http://reddit.com/r/{sub}" target="_blank" class="text-warning"> {sub} </a>'
        author = '<a href="http://reddit.com/u/{usr}" target="_blank"> {usr} </a>'
        for line in dataset:
            if line[8] and line[7]:
                result = line[8] - line[7]
                line_7 = line[7]
                line_8 = line[8]  # @TODO: Better variable assignment
            else:
                line_7 = '-'
                line_8 = '-'
                result = '-'
            carelist.append({'id': line[0], 'plugin': line[1], 'time': line[2],
                             'title': title.format(url=line[6], text=line[3]), 'username': author.format(usr=line[4]),
                             'subreddit': subreddit.format(sub=line[5]), 'permalink': line[6],
                             'upvotes_author': line_7, 'upvotes_plugin': line_8, 'upvotes_difference': result})

        with open(self.path + '_data/overview_rows.json', 'w') as f:
            f.write(json.dumps(carelist))

    def _plugin_activity(self):
        dataset = self.db.get_all_stats()
        chart_data = {}
        for line in dataset:
            if line[1] in chart_data:
                chart_data[line[1]] += 1
            else:
                chart_data[line[1]] = 1
        carelist = []
        for k, v in chart_data.items():
            carelist.append({'name': k, 'data': v})
        with open(self.path + '_data/post_list.json', 'w') as f:
            f.write(json.dumps(carelist))

    def _subreddit_activity(self):
        def tighten_filter(list, min_submissions):
            return [dict for dict in list if dict['data'] > min_submissions]
        dataset = self.db.get_all_stats()
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
        i = 0
        while(len(carelist) > 16):
            carelist = tighten_filter(carelist, i)
            i += 1
        with open(self.path + '_data/subreddit_data.json', 'w') as f:
            f.write(json.dumps(carelist))

    def _post_histogram(self):
        dataset = self.db.get_all_stats()
        carelist = []
        date_change_dataset = [[line[1], datetime.datetime.strptime(line[2], "%Y-%m-%d %H:%M:%S")] for line in dataset]
        post_history = {}
        # Insert all data in hourly ticks
        for line in date_change_dataset:
            # Yay, <= py3.2 doesn't have datetime.timestamp()
            timestamp = int((line[1] - datetime.datetime.utcfromtimestamp(0)).total_seconds()) // 3600
            if line[0] in post_history:
                if timestamp in post_history[line[0]]:
                    post_history[line[0]][timestamp] += 1
                else:
                    post_history[line[0]][timestamp] = 1
            else:
                post_history[line[0]] = {timestamp: 1}
        # Sort values and insert nil-values so the graphs are accurate per tick
        for key, value in post_history.items():
            all_values = sorted(value.items())
            start, end = all_values[0][0], all_values[-1][0]
            for x in range(start, end + 1):
                if x not in value:
                    value[x] = 0
        # transform the data again to get simple json for js - also transform timestamp to js readable
        for k, v in post_history.items():
            some_list = []
            for key, value in sorted(v.items()):
                some_list.append([key * 3600 * 1000, value])
            carelist.append({'name': k, 'data': some_list})
        # write out
        with open(self.path + '_data/post_history.json', 'w') as f:
            f.write(json.dumps(carelist))

    def render_karma(self):
        self._total_karma()
        self._average_karma()

    def _total_karma(self):
        dataset = self.db.get_all_stats()
        caredict = {}
        carelist = []
        for line in dataset:
            if not line[8]:
                karma = 0
            else:
                karma = line[8]
            if line[1] in caredict:
                caredict[line[1]] += karma
            else:
                caredict[line[1]] = karma
        for key, value in caredict.items():
            carelist.append({'name': key, 'data': value})
        with open(self.path + '_data/total_karma.json', 'w+') as f:
            f.write(json.dumps(carelist))

    def _average_karma(self):
        dataset = self.db.get_all_stats()
        caredict = {}
        carelist = []
        for line in dataset:
            if not line[8]:
                karma = 0
            else:
                karma = line[8]
            if line[1] in caredict:
                caredict[line[1]] = [caredict[line[1]][0] + karma, caredict[line[1]][1] + 1]
            else:
                caredict[line[1]] = [karma, 1]
        for key, value in caredict.items():
            carelist.append({'name': key, 'data': value[0] / value[1]})
        with open(self.path + '_data/average_karma.json', 'w+') as f:
            f.write(json.dumps(carelist))

    def render_messages(self):
        self._message_rows()

    def _message_rows(self):
        carelist = []
        messages = self.db.get_all_messages()
        message_template = 'You\'ve mailed my bot here: http://reddit.com/message/messages/{msg_id}%0A%0A---%0A%0A'
        url_template = 'http://reddit.com/message/compose/?to={author}&subject={subject}&message={msg_template}'
        reply_template = '<a href="{answer_url}" target="_blank"> {body} </a>'
        for line in messages:
            msg = message_template.format(msg_id=line[0])
            url = url_template.format(author=line[4], subject=line[3], msg_template=msg)
            reply = reply_template.format(answer_url=url, body=line[5])
            carelist.append({'id': line[0], 'plugin': line[1], 'time': line[2], 'title': line[3],
                             'username': line[4], 'body': reply})
        with open(self.path + '_data/message_rows.json', 'w') as f:
            f.write(json.dumps(carelist))

if __name__ == "__main__":
    db = Database()
    sf = StatisticsFeeder(db, None)
    sf.get_old_comment_karma()
    # sf._write_filler_karma()
    sf.render_overview()
    sf.render_karma()
    from time import sleep
    sleep(60)
