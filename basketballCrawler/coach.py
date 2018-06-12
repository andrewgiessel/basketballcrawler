from .soup_utils import getSoupFromURL
import logging


class Coach(object):

    def __init__(self, name, _overview_url, scrape_data=True):
        self.name = name
        self.overview_url = _overview_url
        self.overview_url_content = None
        self.teams = {}

        if scrape_data:
            self.scrape_data()

    def scrape_data(self):
        print(self.name, self.overview_url)
        if self.overview_url_content is not None:
            raise Exception("Can't populate this!")

        overview_soup = getSoupFromURL(self.overview_url)
        self.overview_url_content = overview_soup.text

        try:
            self.scrape_teams(overview_soup)

        except Exception as ex:
            logging.error(ex.message)
            self.teams = {}

    def scrape_teams(self, soup):
        table_soup = soup.find("table", id="coach-stats").find("tbody")
        rows = table_soup.find_all("tr")
        for row in rows:
            season = row.find("th", attrs={"data-stat": "season"}).get_text()
            team = row.find("td", attrs={"data-stat": "team_id"}).find("a").get("title")
            self.teams[season] = team
