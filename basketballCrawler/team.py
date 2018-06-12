from .soup_utils import getSoupFromURL
import re
import logging


class Team(object):
    ID_PATTERN = "[A-Z]{3}"

    def __init__(self, name, _overview_url, scrape_data=True):
        self.name = name
        self.id = self.get_id_from_url(_overview_url)
        self.overview_url = _overview_url
        self.overview_url_content = None
        self.location = None
        self.former_names = None
        self.coach = None

        if scrape_data:
            self.scrape_data()

    def get_id_from_url(self, url):
        team_id_regex = re.compile(self.ID_PATTERN)
        return team_id_regex.search(url).group(0)

    def scrape_data(self):
        print(self.name, self.overview_url)
        if self.overview_url_content is not None:
            raise Exception("Can't populate this!")

        overview_soup = getSoupFromURL(self.overview_url)
        self.overview_url_content = overview_soup.text

        try:
            bio_soup = overview_soup.find('div', attrs={"id": "meta"})
            bio_lines = bio_soup.find_all('p')
            bio_text_lines = [line for line in bio_lines if line.find("strong") is not None]
            self.scrape_location(bio_text_lines)
            self.scrape_former_names(bio_text_lines)

        except Exception as ex:
            logging.error(ex.message)
            self.location = {}
            self.former_names = []

    def scrape_location(self, soup):
        location_line_text = soup[0].get_text()
        location_text = re.sub("\n ?", "", location_line_text)
        location_text = re.sub(" ?Location: ", "", location_text).split(", ")
        self.location = {"city": location_text[0], "state": location_text[1]}

    def scrape_former_names(self, soup):
        former_names_line_text = soup[1].get_text()
        former_names_text = re.sub("\n ?", "", former_names_line_text)
        self.former_names = re.sub(" ?Team Names: ", "", former_names_text).split(", ")

    def get_location(self):
        return f"{self.location.get('city')}, {self.location.get('state')}"

    def get_city(self):
        return self.location.get('city')

    def get_state(self):
        return self.location.get('state')

    def get_name(self):
        return self.name
