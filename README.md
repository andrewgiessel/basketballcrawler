basketballcrawler
==================

This is a python module to scrape basketball-reference.com and convert various stats into usable data structures for analysis.

[Here](https://github.com/andrewgiessel/basketballcrawler/blob/master/basketball_scraper_notebook.ipynb) is a link to a sample IPython Notebook file demonstrating the library.


Requirements
------------

- [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/bs4/doc/#) >= 4.0
- [pandas](http://pandas.pydata.org/) >= 0.11


Usage
-----

Still developing the API.  Right now you can get a list of all player overview urls, generate a list of game log urls for a given player, and convert that list into pandas dataframe.


Notes
-----

`players.json` was generated on 03/09/2013 by `buildPlayerDictionary()` and `savePlayerDictionary()`.  It is a good way to jumpstart your analysis and can be loaded with ... `loadPlayerDictoinary()`.  Note that it's a pretty large (13M) file.  I'd recommend building your own, fresh copy.  Note that it takes about 10 minutes due to spacing out the web requests.


TODO
----

- I'm considering turning this into a class, instead of using a dictionary, so one doesn't have to pass around this dictionary all the time.  Hesitant.
- Local Database construction.
- League-wide statistics.
- Extract other key information from the player overview page- position might be an especially useful variable to use for supervised learning and height/weight is a clearly important variable as well.
