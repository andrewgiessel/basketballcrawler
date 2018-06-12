from .soup_utils import getSoupFromURL
import re
import logging
import json


class Player(object):
    # Regex patterns for player info
    POSN_PATTERN = re.compile('(Point Guard|Center|Power Forward|Shooting Guard|Small Forward)')
    HEIGHT_PATTERN = re.compile('(^[0-9]-[0-9]{1,2})')
    WEIGHT_PATTERN = re.compile('([0-9]{2,3})lb')
    NICKNAMES_PATTERN = re.compile("[(]([A-Za-z, 0-9-.]+)[)]")

    def __init__(self, _name, _overview_url, scrape_data=True):
        self.name = _name
        self.overview_url = _overview_url

        # Explicitly declaring all fields in the constructor will ensure that
        # they're included in JSON serialization
        self.nicknames = []
        self.positions = []
        self.height = None
        self.weight = None
        self.teams_dict = {}
        self.overview_url_content = None
        self.gamelog_data = None
        self.gamelog_url_list = []
        self.gamelog_url_dict = {}

        if scrape_data:
            self.scrape_data()

    def scrape_data(self):
        print(self.name, self.overview_url)
        if self.overview_url_content is not None:
            raise Exception("Can't populate this!")

        overview_soup = getSoupFromURL(self.overview_url)
        self.overview_url_content = overview_soup.text

        try:
            player_position_text = overview_soup.find_all(text=self.POSN_PATTERN)[0]
            player_height_text = overview_soup.find_all(text=self.HEIGHT_PATTERN)[0]
            player_weight_text = overview_soup.find_all(text=self.WEIGHT_PATTERN)[0]
            self.height = self.HEIGHT_PATTERN.findall(player_height_text)[0].strip()
            self.weight = self.WEIGHT_PATTERN.findall(player_weight_text)[0].strip()
            tempPositions = self.POSN_PATTERN.findall(player_position_text)
            self.positions = [position.strip() for position in tempPositions]
            self.scrape_player_nicknames(overview_soup)
            self.scrape_teams(overview_soup)

        except Exception as ex:
            logging.error(ex)
            self.positions = []
            self.nicknames = []
            self.height = None
            self.weight = None

        # the links to each year's game logs are in <li> tags, and the text contains 'Game Logs'
        # so we can use those to pull out our urls.
        link_prefix = "https://www.basketball-reference.com"
        for li in overview_soup.find_all('li'):
            if 'Game Logs' in li.getText():
                all_links = li.findAll('a')
                for link in all_links:
                    link_suffix = link.get('href')
                    if "/gamelog/" in link_suffix:
                        full_link = link_prefix + link_suffix
                        season = link.get_text().strip()
                        self.gamelog_url_list.append(full_link)
                        self.gamelog_url_dict[season] = full_link
                if len(self.gamelog_url_list) > 0:
                    break

    def scrape_player_nicknames(self, soup):
        bio_soup = soup.find('div', id="meta")
        bio_lines = bio_soup.find_all('p')
        for line in bio_lines:
            line_text = re.sub("\n", "", line.get_text())
            nicknames_text = self.NICKNAMES_PATTERN.match(line_text)
            if nicknames_text is not None:
                nicknames_text = nicknames_text.group(1)
                self.nicknames = nicknames_text.split(", ")
                return

    def scrape_teams(self, soup):
        all_rows = soup.find("table", id="per_game").find("tbody").find_all("tr")
        for row in all_rows:
            season = row.find("th", attrs={"data-stat": "season"})
            if season is None:
                continue
            season = season.find("a").get_text()
            team = row.find("td", attrs={"data-stat": "team_id"}).find("a")
            if team is None:
                continue
            self.teams_dict[season] = team.get_text()

    def to_json(self):
        self.overview_url_content = None
        return json.dumps(self.__dict__)