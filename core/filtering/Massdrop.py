from core.BaseClass import Base
from configparser import ConfigParser
from os import path
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
import re
from json import loads
from praw.objects import Comment

class Massdrop(Base):

    def __init__(self):
        super().__init__()
        super().factory_config(True)
        self.BOT_NAME = 'MassdropBot'
        self.DESCRIPTION = self.config.get(self.BOT_NAME, 'description')
        self.USERNAME = self.config.get('MassdropBot', 'username')
        self.PASSWORD = self.config.get('MassdropBot', 'password')
        self.REGEX = re.compile(r"(?P<url>https?:\/\/(?:www\.)?massdrop\.com\/buy\/[^\s;,.\])]*)", re.UNICODE)
        # self.session = self.factory_reddit()
        # self.responses = MassdropText(path.dirname(__file__) + "../config/MassdropResponses.ini")
        self.responses = MassdropText("../config/MassdropResponses.ini")
        self.get_database()

    def execute_comment(self, comment):
        url = self.REGEX.findall(comment.body)
        if url:
            response = self.generate_response(url)
            self.session._add_comment(comment.fullname, response)
            return True
        return False

    def execute_submission(self, submission):
        url = self.REGEX.findall(submission.selftext)
        if url:
            response = self.generate_response(url)
            self.session._add_comment(submission.thing_id, response)
            return True
        return False

    def execute_link(self, link_submission):
        link = self.REGEX.search(link_submission.url).groups()
        if link:
            response = self.generate_response([link])
            self.session._add_comment(link_submission.thing_id, response)
            return True
        return False

    def execute_titlepost(self, title_only):
        pass

    def update_procedure(self, thing_id):
        comment = self.session.get_info(thing_id=thing_id)
        if isinstance(comment, Comment):
            url = self.REGEX.findall(comment.body)
            if url:
                response = self.generate_response(url)

    def execute_textbody(self, string):
        url = self.REGEX.findall(string)
        if url:
            response = self.generate_response(url)
            print(response)

    def generate_response(self, massdrop_links, time_left=None):
        """Takes multiple links at once, iterates, generates a response appropiately.
           Idea is to take into account: Title, Price, Running Drop, Time left"""
        drop_field = []
        textbody = ""
        for url in massdrop_links:
            fix_url = url + ('?', '&')['?' in url] + 'mode=guest_open'
            try:
                pass
                bs = BeautifulSoup(urlopen(fix_url))
                # There is only one H1 - the product name - which is handy.
                product_name = bs.find('h1').string
                # BS4 returns a type error on a find.strings when there is nothing. So we select first, check if there
                # is something and if so, we join that (since they're split like that: $ | 49 | .99 )
                current_price = ""
                current_price_selector = bs.find('strong', attrs={'class': 'current-price'})
                if current_price_selector:
                    current_price = ''.join(current_price_selector.strings)
                # Here is a story: Massdrop serves their old drops with full pricing on their webpage - even
                # if the drop isn't running. Otherwise this is deep selection of data they store in a div. -shrug-
                prices = ""
                pricedrops = bs.find('div', attrs={'class': 'threshold-bars'})
                if current_price:
                    prices = loads(pricedrops.attrs['data-drop-info'])['prices']
                    prices = massdrop_pricer(current_price, prices)
                    # time represented as string like: 4 DAYS LEFT, hence the lower().
                    time_left = " / " + bs.find('span', attrs={'class': 'med0text item-time'}).string.lower()
                else:
                    time_left = "drop has ended"
                drop_field.append({"title": product_name, 'current_price': current_price, 'prices': prices,
                                   "time_left": time_left, 'fix_url': fix_url})

            except HTTPError as e:
                self.logger.error("HTTPError:", e.msg)
                pass
            except Exception as e:
                self.logger.error("Oh noes, an unexpected error happened:", e.__cause__)

        # item is a dictionary that fits on the right binding - saves time, is short
        for item in drop_field:
            textbody += self.responses.product_binding.format(**item)

        textbody = self.responses.intro_drop + textbody + self.responses.outro_drop
        return textbody.replace('\\n', '\n')


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
        return "Fields:" + p + self.intro + p + self.intro_drop + p + self. product_binding + p + self.update_binding \
               + p + self.outro_drop


def massdrop_pricer(price, pricelist):
    if isinstance(price, str) and price.startswith("$"):
        price = price[1:]
    pricelist = [float(x) for x in pricelist if float(x) < float(price)]
    if len(pricelist) > 1:
        pricestring = "${:.2f}".format(pricelist[0])
        for item in pricelist[1:]:
            pricestring += "/${:.2f}".format(item)
        return ': drops to ' + pricestring
    elif len(pricelist) == 1:
        return ': drops to ' + "${:.2f}".format(pricelist[0])
    else:
        return ""


def init():
    """Init Call from module importer to return only the object itself, rather than the module."""
    return Massdrop()

if __name__ == "__main__":
    mt = MassdropText("..\config\MassdropResponses.ini")
    print(mt)
    md = Massdrop()

    print(md.execute_textbody("""
                        1:    https://www.massdrop.com/buy/vortex-poker-iii-compact-keyboard
                        2:    https://www.massdrop.com/buy/vortex-pbt-keycaps?mode=guest_open,
                        3:    https://www.massdrop.com/buy/spyderco-manix-2-lightweight-black-blade
                              """))
