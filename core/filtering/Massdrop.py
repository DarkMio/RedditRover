from core.BaseClass import Base
from configparser import ConfigParser
from os.path import dirname
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
import re
from json import loads
from praw.objects import Comment


class Massdrop(Base):

    def __init__(self, database):
        super().__init__(database)
        super().factory_config()
        self.BOT_NAME = 'MassdropBot'
        self.DESCRIPTION = self.config.get(self.BOT_NAME, 'description')
        self.USERNAME = self.config.get(self.BOT_NAME, 'username')
        self.OAUTH_FILENAME = self.config.get(self.BOT_NAME, 'oauth')
        self.REGEX = re.compile(r"(?P<url>https?:\/\/(?:www\.)?massdrop\.com\/buy\/[^\s;,.\])]*)", re.UNICODE)
        self.session, self.oauth = self.factory_reddit(config_file=dirname(__file__)+"/../config/"+self.OAUTH_FILENAME)
        self.responses = MassdropText(dirname(__file__) + "/../config/bot_config.ini")

    def execute_comment(self, comment):
        url = self.REGEX.findall(comment.body)
        if url:
            response = self.generate_response(url)
            if response:
                self.oauth.refresh()
                generated = self.session._add_comment(comment.fullname, response)
                self.database.insert_into_update(generated.name, self.BOT_NAME, 1209600, 43200)
                return True
        return False

    def execute_submission(self, submission):
        url = self.REGEX.findall(submission.selftext)
        if url:
            response = self.generate_response(url)
            if response:
                self.oauth.refresh()
                generated = self.session._add_comment(submission.name, response)
                self.database.insert_into_update(generated.name, self.BOT_NAME, 1209600, 43200)
                return True
        return False

    def execute_link(self, link_submission):
        link = self.REGEX.findall(link_submission.url)
        if link:
            response = self.generate_response(link)
            if response:
                self.oauth.refresh()
                generated = self.session._add_comment(link_submission.name, response)
                self.database.insert_into_update(generated.name, self.BOT_NAME, 1209600, 43200)
                return True
        return False

    def execute_titlepost(self, title_only):
        pass

    def update_procedure(self, thing_id, created, lifetime, last_updated, interval):
        self.oauth.refresh()
        comment = self.session.get_info(thing_id=thing_id)
        if comment.score < -2:
            comment.delete()
            self.database.delete_from_update(thing_id, self.BOT_NAME)
            return

        if isinstance(comment, Comment):
            url = self.REGEX.findall(comment.body)
            if url:
                response = self.generate_response(url, from_update=True)
                comment.edit(response)
                return

    def execute_textbody(self, string):
        url = self.REGEX.findall(string)
        if url:
            response = self.generate_response(url)
            print(response)

    def generate_response(self, massdrop_links, time_left=None, from_update=False):
        """Takes multiple links at once, iterates, generates a response appropiately.
           Idea is to take into account: Title, Price, Running Drop, Time left"""
        drop_field = []
        textbody = ""
        fixed_urls = 0
        for url in massdrop_links:
            # if that is already a fixed url, we may ignore it.
            fix_url = url
            if 'mode=guest_open' in url and not from_update:
                continue
            if not from_update:
                fix_url = fix_url + ('?', '&')['?' in url] + 'mode=guest_open'
            try:
                pass
                bs = BeautifulSoup(urlopen(fix_url), "html.parser")
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
                fixed_urls += 1
            except HTTPError as e:
                self.logger.error("HTTPError:", e.msg)
                pass
            except Exception as e:
                self.logger.error("Oh noes, an unexpected error happened:", e)

        if len(drop_field) == 0:
            return

        # item is a dictionary that fits on the right binding - saves time, is short
        for item in drop_field:
            textbody += self.responses.product_binding.format(**item)

        textbody = self.responses.intro_drop.format(products=('product', 'products')[fixed_urls > 1]) + \
                   textbody + self.responses.outro_drop
        return textbody.replace('\\n', '\n')


class MassdropText:
    intro = ""
    product_binding = ""
    outro_drop = ""
    update_binding = ""

    def __init__(self, filepath):
        ch = ConfigParser()
        ch.read(filepath)
        self.intro = ch.get('MassdropBot', 'intro')
        self.intro_drop = ch.get('MassdropBot', 'intro_drop')
        self.product_binding = ch.get('MassdropBot', 'product_binding')
        self.update_binding = ch.get('MassdropBot', 'update_binding')
        self.outro_drop = ch.get('MassdropBot', 'outro_drop')

    def __repr__(self):
        p = "\n\t"
        return "Fields:" + p + self.intro + p + self.intro_drop + p + self. product_binding + p + self.update_binding \
               + p + self.outro_drop


def massdrop_pricer(price, pricelist):
    if isinstance(price, str) and price.startswith("$"):
        price = price[1:].replace(',', '')
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


def init(database):
    """Init Call from module importer to return only the object itself, rather than the module."""
    return Massdrop(database)

if __name__ == "__main__":
    mt = MassdropText("..\config\MassdropResponses.ini")
    print(mt)
    md = Massdrop()

    # print(md.execute_textbody('https://www.massdrop.com/buy/goboof-alfa'))

    print(md.update_procedure("t1_ctv1673", 0, 0, 0, 0))
