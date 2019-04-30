# Steam Market


[![Build status][build-image]][build]
[![Updates][dependency-image]][pyup]
[![Python 3][python3-image]][pyup]
[![Code coverage][codecov-image]][codecov]
[![Code Quality][codacy-image]][codacy]

This repository contains Python code to find arbitrages on the Steam Market.

![Cover: ranking of market arbitrages](https://github.com/woctezuma/steam-market/wiki/img/rBxZxHX.png)

## Requirements

-   Install the latest version of [Python 3.X](https://www.python.org/downloads/).
-   Install the required packages:

```bash
pip install -r requirements.txt
```

## Data acquisition

-   To relax the rate limits enforced by Steam API, fill-in your cookie information in a file called `personal_info.txt`:

    1. To do so, make sure you are connected to your Steam account on a Steam Community page, e.g. [Steam Market](https://steamcommunity.com/market/).<br/> 
  ![steam community](https://github.com/woctezuma/steam-market/wiki/img/K0P9Uxu.png)

    2. Press `<Shift-F9>` in your web browser to access the storage section of the developer tools.<br/>
  ![storage section](https://github.com/woctezuma/steam-market/wiki/img/xGfyU7r.png)
    
    3. Use the filtering option (in the top right of the storage section) to find the cookie value for `steamLoginSecure`.<br/>
  ![filter for steamLoginSecure](https://github.com/woctezuma/steam-market/wiki/img/YhlPlUy.png)    
    
    4. Copy-paste this cookie value into a new file called `personal_info.txt`, which will be read by [`personal_info.py`](personal_info.py).<br/>
  ![paste into personal_info.txt](https://github.com/woctezuma/steam-market/wiki/img/hMiqZJH.png)    

> **NB**: In the future, if you notice that the program bugs out due to seemingly very strict rate limits, then it may
be a sign that the cookie value tied to your session has changed.
In this case, try to fill-in your cookie information with its new value.

-   To have access to the cost of Booster Packs in gems, copy info from [here](https://steamcommunity.com/tradingcards/boostercreator/) to `data/booster_game_creator.txt`:

    1. To do so, install the browser extension called [*Augmented Steam*](https://es.isthereanydeal.com/), so that the number of gems required to craft a Booster Pack appears in the drop-down menu:<br/>
  ![browser extension](https://github.com/woctezuma/steam-market/wiki/img/0eovMPR.png)    

    2. Then, right-click the drop-down menu and "inspect" the corresponding HTML code in your browser:<br/>
  ![drop-down menu](https://github.com/woctezuma/steam-market/wiki/img/jU6iI8n.png)

    3. You will be able to copy-paste this line:<br/>
  ![inspection](https://github.com/woctezuma/steam-market/wiki/img/y1QSzS7.png)

    4. Format it this way:<br/>
  ![formatting](https://github.com/woctezuma/steam-market/wiki/img/YAtWJ5O.png)

    5. For instance, with [Visual Studio Code](https://code.visualstudio.com/), this requires adding line-breaks with `<Ctrl-H>`:<br/>
  ![Visual Studio Code: replace](https://github.com/woctezuma/steam-market/wiki/img/aPKEI7W.png)

## Usage

-   To parse all the options to craft 'Booster Packs', for the games you own, run:

```bash
python parsing_utils.py
```

-   To retrieve all the listings of 'Booster Packs' on the Steam Market, along with the sell price and volume, run:

```bash
python market_search.py
```

-   To retrieve the price which sellers ask for a 'Sack of Gems', run:

```bash
python sack_of_gems.py
```

-   To retrieve i) the "item name id" of a listing, and ii) whether a *crafted* item would really be marketable, run:

```bash
python market_listing.py
```

-   To match listing hashes with badge creation details, run:

```bash
python market_utils.py
```


-   To retrieve the ask and bid for 'Booster Packs', run:

```bash
python market_order.py
```

-   To find market arbitrages, e.g. sell a pack for more (fee excluded) than the cost to craft it (fee included), run:

```bash
python market_arbitrage.py
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

