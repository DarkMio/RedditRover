# coding=utf-8
import jinja2
from core.database import Database
import json
import time
import datetime

db = Database()
env = jinja2.Environment(loader=jinja2.FileSystemLoader('./html/'), autoescape=True)

template = env.get_template('index.html')
with open('./out/index.html', 'w') as f:
    f.write(template.render())

css = env.get_template('style.css')
with open('./out/style.css', 'w') as f:
    f.write(css.render(plugins=db.get_all_modules(), colors=['#FFCC99', '#66CCFF', '#66FF66', '#9966FF', '#CCCC00'], ))

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

print(dataset)
