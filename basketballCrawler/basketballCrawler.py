import time
import json
import string
import pandas as pd
import logging
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import re

__all__ = ['getSoupFromURL', 'getCurrentPlayerNamesAndURLS',
           'buildPlayerDictionary', 'searchForName',
           'savePlayerDictionary', 'loadPlayerDictionary',
           'gameLogs']

BASKETBALL_LOG = 'basketball.log'

logging.basicConfig(filename=BASKETBALL_LOG,
                    level=logging.DEBUG,
                   )


def getSoupFromURL(url, supressOutput=True):
    """
    This function grabs the url and returns and returns the BeautifulSoup object
    """
    if not supressOutput:
        print url

    try:
        r = requests.get(url)
    except:
        return None

    return BeautifulSoup(r.text)


def getCurrentPlayerNamesAndURLS(supressOutput=True):

    names = []

    for letter in string.ascii_lowercase:
        letter_page = getSoupFromURL('http://www.basketball-reference.com/players/%s/' % (letter), supressOutput)

        # we know that all the currently active players have <strong> tags, so we'll limit our names to those
        current_names = letter_page.findAll('strong')
        for n in current_names:
            name_data = n.children.next()
            names.append((name_data.contents[0], 'http://www.basketball-reference.com' + name_data.attrs['href']))
        time.sleep(1) # sleeping to be kind for requests

    return dict(names)


def buildPlayerDictionary(supressOutput=True):
    """
    Builds a dictionary for all current players in the league-- this takes about 10 minutes to run!
    """

    # Regex patterns for player info
    POSN_PATTERN = u'^Position: (.*?)\u25aa'
    HEIGHT_PATTERN = u'Height: ([0-9]-[0-9]{1,2})'
    WEIGHT_PATTERN = u'Weight: ([0-9]{2,3}) lbs'

    logging.debug("Begin grabbing name list")
    playerNamesAndURLS = getCurrentPlayerNamesAndURLS(supressOutput)
    logging.debug("Name list grabbing complete")

    players={}
    for name, url in playerNamesAndURLS.items():
        players[name] = {'overview_url':url}
        players[name]['overview_url_content'] = None
        players[name]['gamelog_url_list'] = []
        players[name]['gamelog_data'] = None

    logging.debug("Grabbing player overview URLs")

    for i, (name, player_dict) in enumerate(players.items()):
        if players[name]['overview_url_content'] is None:
            if not supressOutput:
                print i,

            overview_soup = getSoupFromURL(players[name]['overview_url'], supressOutput)
            players[name]['overview_url_content'] = overview_soup.text

            try:
                player_infotext = overview_soup.findAll('p',attrs={'class':'padding_bottom_half'})[0].text.split('\n')[0]

                positions = re.findall(POSN_PATTERN,player_infotext)[0].strip().encode("utf8").split(" and ")
                height = re.findall(HEIGHT_PATTERN,player_infotext)[0].strip().encode("utf8")
                weight = re.findall(WEIGHT_PATTERN,player_infotext)[0].strip().encode("utf8")

                players[name]["positions"] = positions
                players[name]["height"] = height
                players[name]["weight"] = weight
            except Exception as ex:
                logging.error(ex.message)
                players[name]['positions'] = []

            # the links to each year's game logs are in <li> tags, and the text contains 'Game Logs'
            # so we can use those to pull out our urls.
            for li in overview_soup.find_all('li'):
                if 'Game Logs' in li.getText():
                    game_log_links =  li.findAll('a')

            for game_log_link in game_log_links:
                players[name]['gamelog_url_list'].append('http://www.basketball-reference.com' + game_log_link.get('href'))

            time.sleep(1) # sleep to be kind.

    logging.debug("buildPlayerDictionary complete")

    return players


def fuzzy_ratio(name, search_string):
    """
    Calculate difflib fuzzy ratio
    """
    return SequenceMatcher(None, search_string.lower(), name.lower()).ratio()


def searchForName(playerDictionary, search_string, threshold=0.5):
    """
    Case insensitive partial search for player names, returns a list of strings,
    names that contained the search string.  Uses difflib for fuzzy matching.
    threshold:
    """
    players_name = playerDictionary.keys()
    search_string = search_string.lower()
    players_ratio = map(lambda name: [name, fuzzy_ratio(name, search_string)], players_name)
    searched_player_dict = [name for name in players_name if search_string in name.lower()]
    searched_player_fuzzy = [player for (player, ratio) in players_ratio if ratio > threshold]
    return list(set(searched_player_dict + searched_player_fuzzy))


def savePlayerDictionary(playerDictionary, pathToFile):
    """
    Saves player dictionary to a JSON file
    """
#    for name, k in players.items():
#        player_archive[name] = {'gamelog_url_list':k['gamelog_url_list'],
#                                'overview_url':k['overview_url'],
#                                'overview_url_content':k['overview_url_content']}

    json.dump(playerDictionary, open(pathToFile, 'wb'), indent=0)


def loadPlayerDictionary(pathToFile):
    """
    Loads previously saved player dictionary from a JSON file
    """
    f = open(pathToFile)
    json_string = f.read()
    return json.loads(json_string)


def dfFromGameLogURLList(gamelogs):
    """
    Functions to parse the gamelogs
    Takes a list of game log urls and returns a concatenated DataFrame
    """
    return pd.concat([dfFromGameLogURL(g) for g in gamelogs])


def dfFromGameLogURL(url):
    """
    Takes a url of a player's game log for a given year, returns a DataFrame
    """
    glsoup = getSoupFromURL(url)

    reg_season_table = glsoup.findAll('table', attrs={'id': 'pgl_basic'})  # id for reg season table
    playoff_table = glsoup.findAll('table', attrs={'id': 'pgl_basic_playoffs'}) # id for playoff table

    # parse the table header.  we'll use this for the creation of the DataFrame
    header = []
    for th in reg_season_table[0].findAll('th'):
        if not th.getText() in header:
            header.append(th.getText())

    # add in headers for home/away and w/l columns. a must to get the DataFrame to parse correctly

    header[5] = u'HomeAway'
    header.insert(7, u'WinLoss')

    reg = soupTableToDF(reg_season_table, header)
    playoff = soupTableToDF(playoff_table, header)

    if reg is None:
        return playoff
    elif playoff is None:
        return reg
    else:
        return pd.concat([reg, playoff])


def soupTableToDF(table_soup, header):
    """
    Parses the HTML/Soup table for the gamelog stats.
    Returns a pandas DataFrame
    """
    if not table_soup:
        return None
    else:
        rows = table_soup[0].findAll('tr')[1:]  # all rows but the header

        # remove blank rows
        rows = [r for r in rows if len(r.findAll('td')) > 0]

        parsed_table = [[col.getText() for col in row.findAll('td')] for row in rows] # build 2d list of table values
        return pd.io.parsers.TextParser(parsed_table, names=header, index_col=2, parse_dates=True).get_chunk()


def gameLogs(playerDictionary, name):
    ### would be nice to put some caching logic here...
    return dfFromGameLogURLList(playerDictionary[name]['gamelog_url_list'])
