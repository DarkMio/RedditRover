from core.BaseClass import Base
from configparser import ConfigParser
from os import path
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
# maybe: import scrapy
import re

class Massdrop(Base):

    def __init__(self):
        super().__init__()
        super().factory_config()
        self.BOT_NAME = 'MassdropBot'
        self.DESCRIPTION = self.config.get(self.BOT_NAME, 'description')
        self.USERNAME = self.config.get('MassdropBot', 'username')
        self.PASSWORD = self.config.get('MassdropBot', 'password')
        self.REGEX = r"(?P<url>https?:\/\/(?:www\.)?massdrop\.com\/buy\/[^\s;,.\])]*)"
        self.factory_reddit()
        self.load_responses()

    def load_responses(self):
        self.response_header = ConfigParser()
        self.response_header.read(path.dirname(__file__) + "/config/MassdropResponses")


    def execute_comment(self, comment):
        pass

    def execute_submission(self, submission):
        # submission.body? - - may need an instance check beforehand.
        search_text = (submission.url, submission.selftext)[submission.url=='self']
        url = re.findall(self.REGEX, search_text)
        if url:
            # Do a response.
            # fix the url > here
            response = self.generate_response(url)
            self.session._add_comment(submission.thing_id, "Some response")
            return True
        else:
            return False

        pass

    def update_procedure(self, thing_id):

        pass

    def generate_response(self, massdrop_links):
        """Takes multiple links at once, iterates, generates a response appropiately.
           Idea is to take into account: Title, Price, Running Drop, Time left"""
        drop_field = []
        textbody = ""
        for url in massdrop_links:
            fix_url = url + ('&', '?')['?' in url] + 'mode=guest_open'
            try:
                pass
                bs = BeautifulSoup(urlopen(fix_url))
                title = bs.title.string
                # price = bs - needs scraping first
                # running = bs.something != ''
                # time_left = bs.something
                # drop_field.append({"title": title, "price": price, "running": running,
                #                    "us_only": ("", "US only")[us_only], "time_left": time_left})
            except HTTPError as e:
                self.logger.error("HTTPError:", e.msg)
                pass
            except Exception as e:
                self.logger.error("Oh noes, an unexpected error happened:", e.__cause__)

        # item is a dictionary that fits on the right binding - saves time, is short
        for item in drop_field:
            # shrug, reformat that in load_response_header
            textbody += self.response_header.get('Massdrop', 'product_binding').format(item)

        return self.response_header.get('Massdrop', 'intro_drop') + textbody + \
            self.response_header.get('Massdrop', 'outro_drop')


class MassdropText:

    response_header = None
    intro = ""
    product_binding = ""
    outro_drop = ""
    update_binding = ""

    def __init__(self, filepath):
        ch = self.response_header = ConfigParser()
        self.response_header = ch.read(filepath)

        self.intro = ch.get('MASSDROP', 'intro')
        self.intro_drop = ch.get('MASSDROP', 'intro_drop')
        self.product_binding = ch.get('MASSDROP', 'product_binding')
        self.update_binding = ch.get('MASSDROP', 'update_binding')
        self.outro_drop = ch.get('MASSDROP', 'outro_drop')

    def __repr__(self):
        p = "\n\t"
        return "Fields:" + p + self.intro + p + self.intro_drop + p + self. product_binding +p\
            + self.outro_drop







def init():
    """Init Call from module importer to return only the object itself, rather than the module."""
    return Massdrop()

if __name__ == "__main__":
    mt = MassdropText("D:\Projects\python\MassdropBot\core\config\MassdropResponses")
    print(mt)