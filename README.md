# Steam Market


[![Build status][build-image]][build]
[![Updates][dependency-image]][pyup]
[![Python 3][python3-image]][pyup]
[![Code coverage][codecov-image]][codecov]
[![Code Quality][codacy-image]][codacy]

This repository contains Python code to find arbitrages on the Steam Market.

![Cover: ranking of market arbitrages](https://github.com/woctezuma/steam-market/wiki/img/rBxZxHX.png)

Arbitrages could consist in:
-   purchasing gems to craft booster packs, which are then immediately sold for more than their crafting cost,
-   purchasing items, typically foil cards, which are then immediately turned into more gems than they are worth,
-   purchasing games in order to produce the corresponding booster packs, with total profit greater than the game price,
-   turning normal cards into badges, if the expected value is positive, to create items worth more than the badge cost.

## Requirements

-   Install the latest version of [Python 3.X](https://www.python.org/downloads/).
-   Install the required packages:

```bash
pip install -r requirements.txt
```

## Data acquisition

### Cookie

To relax the rate limits enforced by Steam API, fill-in your cookie information in a file called `personal_info.json`:

1. To do so, make sure you are connected to your Steam account on a Steam Community page, e.g. [Steam Market](https://steamcommunity.com/market/).<br/> 
  ![steam community](https://github.com/woctezuma/steam-market/wiki/img/K0P9Uxu.png)

2. Press `<Shift-F9>` in your web browser to access the storage section of the developer tools.<br/>
  ![storage section](https://github.com/woctezuma/steam-market/wiki/img/xGfyU7r.png)
    
3. Use the filtering option (in the top right of the storage section) to find the cookie value for `steamLoginSecure`.<br/>
  ![filter for steamLoginSecure](https://github.com/woctezuma/steam-market/wiki/img/YhlPlUy.png)    
    
4. Copy-paste this cookie value into a new file called `personal_info.json`, which will be read by [`personal_info.py`](personal_info.py).<br/>
    ```json
    {
      "steamLoginSecure": "PASTE_YOUR_COOKIE_VALUE_HERE"
    }  
    ```

> **NB**: In the future, if you notice that the program bugs out due to seemingly very strict rate limits, then it may
be a sign that the cookie value tied to your session has changed.
In this case, try to fill-in your cookie information with its new value.

> **NB²**: If you want to automate the creation and sale of booster packs, you may need:
> 1. to have a [mobile authenticator app](https://github.com/Jessecar96/SteamDesktopAuthenticator) running in the background and auto-confirming market transactions,
> 2. to fill-in more cookie information.
I have been using the following entries, but you might not need to use all of them. Except for `steamLoginSecure` and `sessionid`, the values of the other entries are set in stone and do not need to be updated afterwards.
>    ```json
>    {
>      "browserid": "PASTE_YOUR_COOKIE_VALUE_HERE",
>      "steamMachineAuth_PASTE_YOUR_STEAM_ID_HERE": "PASTE_YOUR_COOKIE_VALUE_HERE",
>      "steamRememberLogin": "PASTE_YOUR_COOKIE_VALUE_HERE",
>      "sessionid": "PASTE_YOUR_COOKIE_VALUE_HERE",
>      "steamLoginSecure": "PASTE_YOUR_COOKIE_VALUE_HERE"
>    }
>    ```

### Gem cost for crafting Booster Packs

To have access to the gem cost for crafting Booster Packs, you will need to manually copy information available [here](https://steamcommunity.com/tradingcards/boostercreator/).

There are two solutions:
-   solution A is my original solution, but it requires a browser extension called *Augmented Steam*,
-   solution B is a more recent solution, and does not require any third-party browser extension.

#### Solution A
 
1. Install the browser extension called [*Augmented Steam*](https://es.isthereanydeal.com/), so that the number of gems required to craft a Booster Pack appears in the drop-down menu:<br/>
![browser extension](https://github.com/woctezuma/steam-market/wiki/img/0eovMPR.png)    

2. Then, right-click the drop-down menu and "inspect" the corresponding HTML code in your browser:<br/>
![drop-down menu](https://github.com/woctezuma/steam-market/wiki/img/jU6iI8n.png)

3. Copy the following line and paste it to `data/booster_game_creator.txt`:<br/>
![inspection](https://github.com/woctezuma/steam-market/wiki/img/y1QSzS7.png)

4. Add line-breaks, so that the file is formatted in the following way:<br/>
![formatting](https://github.com/woctezuma/steam-market/wiki/img/YAtWJ5O.png)

   For instance, with [Visual Studio Code](https://code.visualstudio.com/), press `<Ctrl-H>` and run:<br/>
![Visual Studio Code: replace](https://github.com/woctezuma/steam-market/wiki/img/aPKEI7W.png)

5. Strip the following unnecessary lines:

   - three lines (including an empty line) at the beginning:
   ```html
   <select id="booster_game_selector">
                           <option value="">Select a game...</option>
    
   ```

   - one line at the end:
   ```html
   </select>
   ```

#### Solution B

Alternatively, if you wish not to install any browser extension:

1. Press `<Ctrl-U>` to display the HTML code of [the Booser Creation webpage](https://steamcommunity.com/tradingcards/boostercreator/). 

2. At the end of the HTML code, find and copy the line below `CBoosterCreatorPage.Init`:<br/>
![javascript list of games](https://github.com/woctezuma/steam-market/wiki/img/JBxJue8.png)
    
3. Paste the line to `data/booster_game_creator_from_javascript.txt`.

4. Strip mentions of packs unavailable because they were crafted less than 24 hours ago. For instance:
   ```json
   {"appid":996580,"name":"Spyro\u2122 Reignited Trilogy","series":1,"price":"400",
   "unavailable":true,"available_at_time":"4 Sep @ 7:06pm"}
    ```
    should be replaced with:
   ```json
   {"appid":996580,"name":"Spyro\u2122 Reignited Trilogy","series":1,"price":"400"}
    ```    

   To do so, with [Visual Studio Code](https://code.visualstudio.com/), press `<Ctrl-H>` and remove occurences of :<br/>
![Visual Studio Code: remove mentions of unavailability](https://github.com/woctezuma/steam-market/wiki/img/sw2fFnT.png)
   ```regexp
   ,"unavailable":true,"available_at_time":"[\w ]*@[\w :]*"
   ```

## Usage

-   To parse all the options to craft 'Booster Packs', for the games you own, run:

```bash
python parsing_utils.py
```

-   To retrieve all the listings of 'Booster Packs' on the Steam Market, along with the sell price and volume, run:

```bash
python market_search.py
```

-   To retrieve the price which sellers ask for a ['Sack of Gems'](https://steamcommunity.com/market/listings/753/753-Sack%20of%20Gems), run:

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

-   To look for **free** games which i) feature trading cards (and thus crafting of booster packs), and ii) which I do not own, run:

```bash
python free_games_with_trading_cards.py
```

-   To create packs for a **manual** selection of games, e.g. if you want to create these specific packs every day, run:

```bash
python batch_create_packs.py
```

-   To list appIDs of interest for which we can under-cut the lowest sell order and still hope to make a profit:

```bash
python list_possible_lures.py
```

-   To look for games which i) are likely to have high bid orders for their booster packs, and ii) which I may not own yet, run:

```bash
python market_buzz_detector.py
```

-   To look for potentially profitable gambles on profile backgrounds and emoticons of "Common" rarity, run:

```bash
python market_gamble_detector.py
```

-   To find market arbitrages, e.g. sell a pack for more (fee excluded) than the cost to craft it (fee included), run:

```bash
python market_arbitrage.py
```

-   To find market arbitrages with foil cards, e.g. buy a foil card to turn it into more gems than its cost, run:

```bash
python market_arbitrage_with_foil_cards.py
```

**Caveat**: make sure to manually check the goo value of cards with a tool such as [this bookmarklet](https://gaming.stackexchange.com/a/351941).
Indeed, if an arbitrage with foil cards looks too good to be true, it is likely that the goo value was bugged,
because of a wrong item type.
It can happen for instance if the goo value actually corresponds to emoticon or a profile background, and was then
multiplied by 10 to get the value of the non-existent "foil" version of this emoticon or profile background.

**Caveat²**: the bookmarklet linked above does not account for foil versions, so you should multiply by 10 the goo value
if you are interested in foil cards. You can check by yourself that the bookmarklet returns the same goo values for 
normal cards and for foil cards.

## Drop-rate estimates

For the gamble detector, we are interested in drop-rate estimates, when crafting badges, for items of Common rarity.

Based on the data so far (239 crafed badges):
-   the drop-rates for Profile Backgrounds and for Emoticons are different (reject null hypothesis with 95% confidence),
-   conditionally to C/UC/R patterns, the drop-rates may be similar (fail to reject null hypothesis with 95% confidence).

where:
-   C/UC/R patterns are the numbers of Common/Uncommon/Rare items associated with each appID.

Therefore, we choose to estimate the drop-rates for Common rarity, conditionally to C/UC/R patterns.  
The values hard-coded in `drop_rate_estimates.py` are the centers of the [Wilson score intervals](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval) with 95% confidence.

## Results

The [Wiki](https://github.com/woctezuma/steam-market/wiki) shows a ranking of packs with high buy orders.

Rankings are also available for gambles with items of "Common" rarity, obtained after crafting a badge:
-   [profile backgrounds](https://github.com/woctezuma/steam-market/wiki/Profile_backgrounds),
-   [emoticons](https://github.com/woctezuma/steam-market/wiki/Emoticons).

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

