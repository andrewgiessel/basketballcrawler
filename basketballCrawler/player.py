from soup_utils import getSoupFromURL
import re
import logging
import json

class Player(object):
    # Regex patterns for player info
    POSN_PATTERN = u'^Position: (.*?)\u25aa'
    HEIGHT_PATTERN = u'Height: ([0-9]-[0-9]{1,2})'
    WEIGHT_PATTERN = u'Weight: ([0-9]{2,3}) lbs'

    name = None

    positions = []
    height = None
    weight = None

    overview_url = None
    overview_url_content = None
    gamelog_data = None
    gamelog_url_list = []

    def __init__(self, _name, _overview_url, scrape_data=True):
        self.name = _name
        self.overview_url = _overview_url

        # Explicitly declaring all fields in the constructor will ensure that
        # they're included in JSON serialization
        self.positions = []
        self.height = None
        self.weight = None
        self.overview_url_content = None
        self.gamelog_data = None
        self.gamelog_url_list = []

        if scrape_data:
            self.scrape_data()

    def scrape_data(self):
        print self.name, self.overview_url
        if self.overview_url_content is not None:
            raise Exception("Can't populate this!")

        overview_soup = getSoupFromURL(self.overview_url)
        self.overview_url_content = overview_soup.text

        try:
            pos = filter(lambda x: 'Position:' in x, [p.text for p in overview_soup.findAll('p')])[0].strip().replace('\n','')
            self.positions = re.findall(self.POSN_PATTERN, pos)[0].strip().encode("utf8").split(" and ")
            self.height = overview_soup.find('span', {'itemprop':'height'}).text
            self.weight = overview_soup.find('span', {'itemprop':'weight'}).text[:-2]

        except Exception as ex:
            logging.error(ex.message)
            self.positions = []
            self.height = None
            self.weight = None

        # the links to each year's game logs are in <li> tags, and the text contains 'Game Logs'
        # so we can use those to pull out our urls.
        for li in overview_soup.find_all('li'):
            game_log_links = []
            if 'Game Logs' in li.getText():
                game_log_links =  li.findAll('a')

            for game_log_link in game_log_links:
                if 'gamelog' in game_log_link.get('href'):
                    self.gamelog_url_list.append('http://www.basketball-reference.com' + game_log_link.get('href'))

    def to_json(self):
        return json.dumps(self.__dict__)
