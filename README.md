basketballcrawler
==================

This is a python module to scrape basketball-reference.com and convert various stats into usable data structures for analysis.


Requirements
------------

Beautiful Soup (version 4 or above)

Pandas (0.11 or above)

Usage
-----

Still developing the API.  Right now you can get a list of all player overview urls, generate a list of game log urls for a given player, and convert that list into pandas dataframe.

I'll be putting up a IPython notebook here, too.

Notes
-----
players.json was generated on 03/09/2013 by buildPlayerDictionary() and savePlayerDictionary().  It is a good way to jumpstart your analysis and can be loaded with ... loadPlayerDictoinary().  Note that it's a pretty large (13M) file.  I'd recommend building your own, fresh copy.  Note that it takes about 10 minutes to build due to spacing out the web requests.
