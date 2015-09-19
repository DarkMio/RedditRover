# coding=utf-8
import jinja2
from core.database import Database


db = Database()
env = jinja2.Environment(loader=jinja2.FileSystemLoader('./html/'), autoescape=True)
template = env.get_template('index.html')
with open('./out/index.html', 'w') as f:
    f.write(template.render(entries=db.get_all_storage()))
css = env.get_template('style.css')
with open('./out/style.css', 'w') as f:
    f.write(css.render(plugins=db.get_all_modules(), colors=['#FFCC99', '#66CCFF', '#66FF66', '#9966FF', '#CCCC00'], ))
