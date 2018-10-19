import json
import string
import pandas as pd
import logging
from time import sleep
from difflib import SequenceMatcher
from .soup_utils import find_html_in_comment
from .player import Player, getSoupFromURL
from .coach import Coach
from .team import Team


__all__ = ['getSoupFromURL', 'getCurrentPlayerNamesAndURLS',
           'buildPlayerDictionary', 'searchForName',
           'savePlayerDictionary', 'loadPlayerDictionary',
           'allGameLogs', 'seasonGameLogs']

BASKETBALL_LOG = 'basketball.log'

logging.basicConfig(filename=BASKETBALL_LOG,
                    level=logging.DEBUG,
                    )


def getCurrentPlayerNamesAndURLS(suppressOutput=True):

    names = []

    for letter in string.ascii_lowercase:
        letter_page = getSoupFromURL('https://www.basketball-reference.com/players/%s/' % (letter), suppressOutput)
        if letter_page is None:
            continue
        # we know that all the currently active players have <strong> tags, so we'll limit our names to those
        current_names = letter_page.findAll('strong')
        for n in current_names:
            name_data = n.children.__next__()
            try:
                names.append((name_data.contents[0], 'https://www.basketball-reference.com' + name_data.attrs['href']))
            except Exception as e:
                pass
        sleep(1) # sleeping to be kind for requests

    return dict(names)


def buildPlayerDictionary(suppressOutput=True):
    """
    Builds a dictionary for all current players in the league-- this takes about 10 minutes to run!
    """

    logging.debug("Begin grabbing name list")
    playerNamesAndURLS = getCurrentPlayerNamesAndURLS(suppressOutput)
    logging.debug("Name list grabbing complete")

    players={}
    for name, url in playerNamesAndURLS.items():
        players[name] = Player(name,url,scrape_data=True)
        sleep(1) # sleep to be kind.

    logging.debug("buildPlayerDictionary complete")

    return players


def buildSpecificPlayerDictionary(playerNamesURLs, suppressOutput=True):
    """
    Builds a dictionary for all specified players in the history of the league
    """

    logging.debug("Begin grabbing name list")
    logging.debug("Name list grabbing complete")

    logging.debug("Iterating over {} player names passed".format(len(playerNamesURLs)))
    players={}
    for name, url in playerNamesURLs.items():
        if url is not None:
            players[name] = Player(name, url, scrape_data=True)
            sleep(1) # sleep to be kind.
        else:
            logging.error("Player " + name + " not found!")

    logging.debug("buildSpecificPlayerDictionary complete")
    if len(playerNamesURLs) == len(players):
        logging.info("Successfully retrieved all players passed")
    else:
        logging.error("Missing {} players".format(len(playerNamesURLs) - len(players)))

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
    player_json = {name: player_data.to_json() for name, player_data in playerDictionary.items()}
    json.dump(player_json, open(pathToFile, 'w'), indent=0)


def loadPlayerDictionary(pathToFile):
    """
    Loads previously saved player dictionary from a JSON file
    """
    result = {}
    with open(pathToFile) as f:
        json_dict = json.loads(f.read())
        for player_name in json_dict:
            parsed_player = Player(None, None, False)
            parsed_player.__dict__ = json.loads(json_dict[player_name])
            result[player_name] = parsed_player
    return result


def dfFromGameLogURLList(gamelogs, dataframes=None):
    """
    Functions to parse the gamelogs
    Takes a list of game log urls and returns a concatenated DataFrame
    # fix issue with missing columns (+/-) between older seasons and recent
    """
    if dataframes is None:
        dataframes = [dfFromGameLogURL(g) for g in gamelogs]
    final_dataframes = list()
    final_columns = dataframes[-1].columns.values.tolist()
    for df in dataframes:
        missing_columns = set(final_columns) - set(df.columns.values.tolist())
        if len(missing_columns) > 0:
            final_df = df.reindex(final_columns, axis='columns')
            final_dataframes.append(final_df)
        else:
            final_dataframes.append(df)
    try:
        return pd.concat(final_dataframes)
    except Exception as e:
        print("ERROR - Couldn't merge dataframes:", e)
        print(final_dataframes)
        return None


def dfFromGameLogURL(url):
    """
    Takes a url of a player's game log for a given year, returns a DataFrame
    """
    sleep(1)
    glsoup = getSoupFromURL(url)

    reg_season_table = glsoup.find_all('table', id="pgl_basic")  # id for reg season table
    playoff_table = find_playoff_table(glsoup)

    # parse the table header.  we'll use this for the creation of the DataFrame
    header = []
    if len(reg_season_table) > 0 and reg_season_table[0] is not None:
        table_header = reg_season_table[0].find("thead")
    else:
        print("Error retrieving game log from:")
        print(url)
        exit(1)
    for th in table_header.find_all('th'):
        # if not th.getText() in header:
        header.append(th.getText())

    # add in headers for home/away and w/l columns. a must to get the DataFrame to parse correctly

    header.insert(5, 'HomeAway')
    header.insert(8, 'WinLoss')
    header.pop(0)
    header.remove('\xa0')
    header.remove('\xa0')

    reg = soupTableToDF(reg_season_table, header)
    playoff = soupTableToDF(playoff_table, header)

    if reg is None:
        return playoff
    elif playoff is None:
        return reg
    else:
        try:
            return pd.concat([reg, playoff])
        except Exception as e:
            print("ERROR - Couldn't merge dataframes:", e)
            print(reg)
            print(playoff)
            return None


def find_playoff_table(glsoup):
    playoff_table = glsoup.find_all('table', id="pgl_basic_playoffs")  # id for playoff table
    if len(playoff_table) > 0:
        return playoff_table
    div_soup = glsoup.find("div", id="all_pgl_basic_playoffs")
    if div_soup is None:
        return []
    playoff_soup = find_html_in_comment(div_soup)
    if playoff_soup is None:
        return []
    playoff_table = playoff_soup.find_all('table', id="pgl_basic_playoffs")
    return playoff_table


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

        # build 2d list of table values
        parsed_rows = [[col.getText() for col in row.findAll('td')] for row in rows]
        parsed_table = [row for row in parsed_rows if row[0] != ""]
        try:
            return pd.DataFrame.from_records(parsed_table, columns=header).dropna(subset=["G"])
        except Exception as e:
            print("ERROR - Couldn't create dataframe:", e)
            print(parsed_table)
            return None


def allGameLogs(playerDictionary, name, dataframes=None):
    ### would be nice to put some caching logic here...
    return dfFromGameLogURLList(playerDictionary.get(name).gamelog_url_list, dataframes)


def seasonGameLogs(playerDictionary, name, season):
    return dfFromGameLogURL(playerDictionary.get(name).gamelog_url_dict.get(season))


def getAllPlayerNamesAndURLS(suppressOutput=True):

    names = []

    for letter in string.ascii_lowercase:
        letter_page = getSoupFromURL('https://www.basketball-reference.com/players/{}/'.format(letter), suppressOutput)
        if letter_page is None:
            continue
        all_rows = letter_page.find("table", id="players").find("tbody").find_all("tr")
        for row in all_rows:
            player = row.find("th", attrs={"data-stat": "player", "scope": "row"})
            if player is None:
                continue
            player = player.find("a")
            name = player.get_text()
            try:
                names.append((name, 'https://www.basketball-reference.com' + player.attrs['href']))
            except Exception as e:
                print("ERROR:", e)
        sleep(1) # sleeping to be kind for requests

    return dict(names)


def getAllPlayers(suppressOutput=True, min_year_active=2004):

    players = dict()

    for letter in string.ascii_lowercase:
        letter_page = getSoupFromURL('https://www.basketball-reference.com/players/{}/'.format(letter), suppressOutput)
        if letter_page is None:
            continue
        all_rows = letter_page.find("table", id="players").find("tbody").find_all("tr")
        for row in all_rows:
            player = row.find("th", attrs={"data-stat": "player", "scope": "row"})
            if player is None:
                continue
            player = player.find("a")
            name = player.get_text()
            last_year_active_soup = row.find("td", attrs={"data-stat": "year_max"})
            last_year_active = int(last_year_active_soup.get_text())
            try:
                if last_year_active >= min_year_active:
                    players[name] = Player(name, 'https://www.basketball-reference.com' + player.attrs['href'])
            except Exception as e:
                print("ERROR:", e)
        sleep(1) # sleeping to be kind for requests

    return players


def getAllCoaches(suppressOutput=True, min_year_active=2004):

    coaches = dict()
    glsoup = getSoupFromURL('https://www.basketball-reference.com/coaches/', suppressOutput)
    all_rows = glsoup.find("table", id="coaches").find("tbody").find_all("tr")
    for row in all_rows:
        coach = row.find("th", attrs={"data-stat": "coach", "scope": "row"})
        if coach is None:
            continue
        coach = coach.find("a")
        name = coach.get_text()
        last_year_active_soup = row.find("td", attrs={"data-stat": "year_max"})
        last_year_active = int(last_year_active_soup.get_text())
        try:
            if last_year_active >= min_year_active:
                coaches[name] = Coach(name, 'https://www.basketball-reference.com' + coach.attrs['href'])
        except Exception as e:
            print("ERROR:", e)
    sleep(1) # sleeping to be kind for requests
    return coaches


def getCurrentTeams(suppressOutput=True):

    teams = dict()
    glsoup = getSoupFromURL('https://www.basketball-reference.com/teams/', suppressOutput)

    active_teams_table = glsoup.find('table', id='teams_active')  # id for reg season table
    all_rows = active_teams_table.find_all("th", attrs={"data-stat": "franch_name"})
    active_teams = list()
    for row in all_rows:
        team = row.find("a")
        if team is None:
            continue
        active_teams.append(team)
    for team in active_teams:
        name = team.get_text()
        try:
            teams[name] = Team(name, 'https://www.basketball-reference.com' + team.attrs['href'])
        except Exception as e:
            print("ERROR:", e)
    sleep(1)  # sleeping to be kind for requests

    return teams
