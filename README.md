# Steam Market


[![Build status][build-image]][build]
[![Updates][dependency-image]][pyup]
[![Python 3][python3-image]][pyup]
[![Code coverage][codecov-image]][codecov]
[![Code Quality][codacy-image]][codacy]

This repository contains Python code to find arbitrages on the Steam Market.

## Requirements

-   Install the latest version of [Python 3.X](https://www.python.org/downloads/).
-   Install the required packages:

```bash
pip install -r requirements.txt
```

## Data acquisition

-   To have access to the cost of Booster Packs in gems, copy info from [here](https://steamcommunity.com/tradingcards/boostercreator/) to `data/booster_game_creator.txt`:

    1. To do so, right-click the drop-down menu and "inspect" the corresponding HTML code in your browser:   
![drop-down menu](https://github.com/woctezuma/steam-market/wiki/img/jU6iI8n.png)

    2. You will be able to copy-paste this line:    
![inspection](https://github.com/woctezuma/steam-market/wiki/img/y1QSzS7.png)

    3. Format it this way:
![formatting](https://github.com/woctezuma/steam-market/wiki/img/YAtWJ5O.png)

    4. For instance, with Visual Studio Code, this requires adding line-breaks with `<Ctrl-H>`
![Visual Studio Code: replace](https://github.com/woctezuma/steam-market/wiki/img/aPKEI7W.png)

-   To relax the rate limits enforced by Steam API, fill-in your cookie information in a file called `personal_info.txt`:

    1. To do so, make sure you are connected to your Steam account on a Steam Community page, e.g. [Steam Market](https://steamcommunity.com/market/). 
![steam community](https://github.com/woctezuma/steam-market/wiki/img/K0P9Uxu.png)

    2. Press `<Shift-F9>` in your web browser to access the storage section of the developer tools.
![storage section](https://github.com/woctezuma/steam-market/wiki/img/xGfyU7r.png)
    
    3. Use the filtering option (in the top right of the storage section) to find the cookie value for `steamLoginSecure`.
![select any cookie](https://github.com/woctezuma/steam-market/wiki/img/YhlPlUy.png)    
    
    4. Copy-paste this cookie value into a new file called `personal_info.txt`, which will be read by [`personal_info.py`](personal_info.py).
![get_steam_cookie()](https://github.com/woctezuma/steam-market/wiki/img/cUjUara.png)    
        
## Usage

-   To retrieve all the listings of 'Booster Packs' on the Steam Market, along with the sell price and volume, run:

```bash
python market_search.py
```

-   To parse all the options to craft 'Booster Packs', for the games you own, run:

```bash
python market_utils.py
```

## References

-   [An example](https://www.resetera.com/threads/pc-gaming-era-april-2019-goodbye-uzzy-is-your-new-king.108742/page-123#post-20167882) of market arbitrage.
-   [A blog post about scraping Steam Market](https://www.blakeporterneuro.com/learning-python-project-3-scrapping-data-from-steams-community-market/)

<!-- Definitions -->

[build]: <https://travis-ci.org/woctezuma/steam-market>
[build-image]: <https://travis-ci.org/woctezuma/steam-market.svg?branch=master>

[pyup]: <https://pyup.io/repos/github/woctezuma/steam-market/>
[dependency-image]: <https://pyup.io/repos/github/woctezuma/steam-market/shield.svg>
[python3-image]: <https://pyup.io/repos/github/woctezuma/steam-market/python-3-shield.svg>

[codecov]: <https://codecov.io/gh/woctezuma/steam-market>
[codecov-image]: <https://codecov.io/gh/woctezuma/steam-market/branch/master/graph/badge.svg>

[codacy]: <https://www.codacy.com/app/woctezuma/steam-market>
[codacy-image]: <https://api.codacy.com/project/badge/Grade/c1b2f9f7a02a47a4baa22f6439be9c8a>

