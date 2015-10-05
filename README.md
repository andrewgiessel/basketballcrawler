basketballcrawler
==================

[![Join the chat at https://gitter.im/andrewgiessel/basketballcrawler](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/andrewgiessel/basketballcrawler?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

This is a python module to scrape [basketball-reference.com](http://www.basketball-reference.com/) and convert various
stats into usable data structures for analysis.

[Here](https://github.com/andrewgiessel/basketballcrawler/blob/master/basketball_scraper_notebook.ipynb) is a link to a
sample IPython Notebook file demonstrating the library.


Requirements
------------

- [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/bs4/doc/#) >= 4.0
- [pandas](http://pandas.pydata.org/) >= 0.11


Usage
-----

Still developing the API.  Right now you can get a list of all player overview urls, generate a list of game log urls for
a given player, and convert that list into pandas dataframe.


Notes
-----

`players.json` was generated on 03/09/2013 by `buildPlayerDictionary()` and `savePlayerDictionary()`.
I'd recommend building your own, fresh copy. It takes about 10 minutes to scrape from the site.
To create the most recent `players.json`, you can use as follows.

```python
import basketballCrawler as bc
players = bc.buildPlayerDictionary()
bc.savePlayerDictionary(players, '/path/to/file')
```

You can also download generated `players.json`. However, note that it's a pretty large (13M) file.

```python
players = bc.loadPlayerDictionary('/path/to/players.json')
```

In order to search player name, use `searchForName` function, for example,

```python
searched_player = bc.searchForName(players, 'Murphey') # players is player dictionary
```


TODO
----

- I'm considering turning this into a class, instead of using a dictionary, so one doesn't have to pass around this dictionary all the time.  Hesitant.
- Local Database construction.
- League-wide statistics.
- Extract other key information from the player overview page- position might be an especially useful variable to use for supervised learning and height/weight is a clearly important variable as well.
