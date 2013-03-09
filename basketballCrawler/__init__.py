import pandas

from bs4 import BeautifulSoup
import requests

import time
import json
import sys

import os

__all__ = ['buildPlayerDictionary', 'searchForName', 'savePlayerDictionary', 'loadPlayerDictionary']

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
    letters = list('abcdefghijklmnopqrstuvwxyz')
    names = []
    for letter in letters:
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
    print "Grabbing name list..."
    sys.stdout.flush()
    playerNamesAndURLS = getCurrentPlayerNamesAndURLS(supressOutput)
    print "done."
    sys.stdout.flush()

    players={}
    for name, url in playerNamesAndURLS.items():
        players[name] = {'overview_url':url}
        players[name]['overview_url_content'] = None
        players[name]['gamelog_url_list'] = []
        players[name]['gamelog_data'] = None
    
    print "Grabbing player overview URLs..."
    sys.stdout.flush()
    for i, (name, player_dict) in enumerate(players.items()):
        if players[name]['overview_url_content'] is None:
            if not supressOutput:
                print i, 
        
            overview_soup = getSoupFromURL(players[name]['overview_url'], supressOutput)
            players[name]['overview_url_content'] = overview_soup.text

        
            # the links to each year's game logs are in <li> tags, and the text contains 'Game Logs'
            # so we can use those to pull out our urls.
            for li in overview_soup.find_all('li'):
                if 'Game Logs' in li.getText():
                    game_log_links =  li.findAll('a')
                
            for game_log_link in game_log_links:
                players[name]['gamelog_url_list'].append('http://www.basketball-reference.com' + game_log_link.get('href'))
        
            time.sleep(1) # sleep to be kind.
    print "done."
    sys.stdout.flush()
    return players

def searchForName(playerDictionary, search_string):
    """Case insensitive partial search for player names, returns a list of strings,
    names that contained the search string.  Uses difflib for fuzzy matching.
    """
    search_string = search_string.lower()
    return [name for name in playerDictionary.keys() if search_string in name.lower()]


def savePlayerDictionary(playerDictionary, pathToFile):
    """Saves player dictionary to a JSON file"""
#    for name, k in players.items():
#        player_archive[name] = {'gamelog_url_list':k['gamelog_url_list'], 
#                                'overview_url':k['overview_url'], 
#                                'overview_url_content':k['overview_url_content']}
    
    json.dump(playerDictionary, open(pathToFile, 'wb'), indent=0)

def loadPlayerDictionary(pathToFile):
    """Loads previously saved player dictionary from a JSON file"""
    f = open(pathToFile)
    json_string = f.read()
    return json.loads(json_string)

### Functions to parse the gamelogs

def dfFromGameLogURLList(gamelogs):
    """Takes a list of game log urls and returns a concatenated DataFrame"""
    return pandas.concat([dfFromGameLogURL(g) for g in gamelogs])

def dfFromGameLogURL(url):
    """Takes a url of a player's game log for a given year, returns a DataFrame"""
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
        return pandas.concat([reg, playoff])
    
def soupTableToDF(table_soup, header):
    """Parses the HTML/Soup table for the gamelog stats.
    
    Returns a pandas DataFrame
    """
    if not table_soup:
        return None
    else:
        rows = table_soup[0].findAll('tr')[1:]  # all rows but the header
        
        # remove blank rows
        rows = [r for r in rows if len(r.findAll('td')) > 0]
        
        parsed_table = [[col.getText() for col in row.findAll('td')] for row in rows] # build 2d list of table values
        return pandas.io.parsers.TextParser(parsed_table, names=header, index_col=2, parse_dates=True).get_chunk()


def gameLogs(playerDictionary, name):

    ### would be nice to put some caching logic here...
    return dfFromGameLogURLList(playerDictionary[name]['gamelog_url_list'])

