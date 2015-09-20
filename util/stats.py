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
title = '<a href="{url}" target="_blank"> {text} </a>'
for line in dataset:
    carelist.append({'id': line[0], 'plugin': line[1], 'time': line[2], 'title': title.format(url=line[5], text=line[3]),
                     'username': line[4], 'permalink': line[5]})
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


print(dataset)