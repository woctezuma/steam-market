# Steam Market


[![Build status][build-image]][build]
[![Code coverage][codecov-image]][codecov]
[![Code Quality][codacy-image]][codacy]

This repository contains Python code to find arbitrages on the Steam Market.

![Cover: ranking of market arbitrages](https://github.com/woctezuma/steam-market/wiki/img/rBxZxHX.png)

Arbitrages could consist in:
-   [purchasing gems][sack-of-gems] to craft booster packs, which are then immediately sold for more than their crafting cost,
-   purchasing items, typically foil cards, which are then immediately turned into more gems than they are worth,
-   purchasing games in order to produce the corresponding booster packs, with profit greater than the game price,
-   turning normal cards into badges, based on the expected value, to create items worth more than the badge cost.

## Requirements

-   Install the latest version of [Python 3.X](https://www.python.org/downloads/) (at least version 3.12).
-   Install the required packages:

```bash
pip install -r requirements.txt
```

## Data acquisition

### Cookie

To relax the rate limits enforced by Steam API, fill in your cookie information in a file called `personal_info.json`:

<details><summary>How to fill in your cookie information</summary>
<p>

1. To do so, make sure you are connected to your Steam account on a Steam Community page, e.g. [Steam Market](https://steamcommunity.com/market/).<br/> 
  ![steam community](https://github.com/woctezuma/steam-market/wiki/img/K0P9Uxu.png)

2. Press `<Shift-F9>` in your web browser to access the storage section of the developer tools.<br/>
  ![storage section](https://github.com/woctezuma/steam-market/wiki/img/xGfyU7r.png)
    
3. Use the filtering option (in the top right of the storage section) to find the cookie value for `steamLoginSecure`.<br/>
  ![filter for steamLoginSecure](https://github.com/woctezuma/steam-market/wiki/img/YhlPlUy.png)    
    
4. Copy-paste this cookie value into a new file called `personal_info.json`, which will be read by [`src/personal_info.py`](src/personal_info.py).<br/>
    ```json
    {
      "steamLoginSecure": "PASTE_YOUR_COOKIE_VALUE_HERE"
    }  
    ```

</p>
</details>

> **NB**: In the future, if you notice that the program bugs out due to seemingly very strict rate limits, then it may
be a sign that the cookie value tied to your session has changed.
In this case, try to fill in your cookie information with its new value.

> **NB²**: If you want to automate the creation and sale of booster packs, you may need:
> 1. to have a [mobile authenticator app](https://github.com/Jessecar96/SteamDesktopAuthenticator) running in the background and auto-confirming market transactions,
> 2. to fill in more cookie information.
I have been using the following entries, but you might not need to use all of them. Except for `browserid`, values need to be updated from time to time.
>    ```json
>    {
>      "browserid": "PASTE_YOUR_COOKIE_VALUE_HERE",
>      "steamDidLoginRefresh": "PASTE_YOUR_COOKIE_VALUE_HERE",
>      "sessionid": "PASTE_YOUR_COOKIE_VALUE_HERE",
>      "steamLoginSecure": "PASTE_YOUR_COOKIE_VALUE_HERE"
>    }
>    ```

### Gem cost for crafting Booster Packs

To have access to the gem cost for crafting Booster Packs, you will need to manually copy information available [here](https://steamcommunity.com/tradingcards/boostercreator/).

<details><summary>How to list craftable packs with the Booster Creation webpage</summary>
<p>

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
</p>
</details>

   To do so, with [Visual Studio Code](https://code.visualstudio.com/), press `<Ctrl-H>` and remove occurrences of :<br/>
![Visual Studio Code: remove mentions of unavailability](https://github.com/woctezuma/steam-market/wiki/img/sw2fFnT.png)
   ```regexp
   ,"unavailable":true,"available_at_time":"[\w ]*@[\w :]*"
   ```

## Usage

-   To look for games which i) are may have high bids for their booster packs, and ii) which I may not own yet, run:

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

```javascript
javascript:var a=g_rgAssets[Object.keys(g_rgAssets)[0]],b=a[Object.keys(a)[0]],c=b[Object.keys(b)[0]],gem_action=c.owner_actions&&c.owner_actions.filter(function(d){return/javascript:GetGooValue/.test(d.link)})[0];if(gem_action){var matches=gem_action.link.match(/javascript:GetGooValue\( '%contextid%', '%assetid%', (\d+), (\d+), \d+ \)/);fetch("https://steamcommunity.com/auction/ajaxgetgoovalueforitemtype/?appid="+matches[1]+"&item_type="+matches[2]+"&border_color=0").then(function(d){return d.json()}).then(function(d){alert("This is worth "+d.goo_value+" gems")})["catch"](function(d){return console.error(d)})}else alert("This is worth 0 gems");
```

**Caveat²**: the bookmarklet linked above does not account for foil versions, so you should multiply by 10 the goo value
if you are interested in foil cards. You can check by yourself that the bookmarklet returns the same goo values for 
normal cards and for foil cards.

## Drop-rate estimates

For the gamble detector, we are interested in drop-rate estimates, when crafting badges, for items of Common rarity.

Based on the data so far (1127 crafted badges):
-   the drop-rates for Profile Backgrounds and for Emoticons are different (reject null hypothesis with 95% confidence),
-   conditionally to C/UC/R patterns, the drop-rates may be similar (fail to reject null hypothesis with 95% confidence).

where:
-   C/UC/R patterns are the numbers of Common/Uncommon/Rare items associated with each appID.

Therefore, we choose to estimate the drop-rates for Common rarity, conditionally to C/UC/R patterns.  
The values hard-coded in [`src/drop_rate_estimates.py`](src/drop_rate_estimates.py) are the centers of the [Wilson score intervals](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval) with 95% confidence.

## Results

The [Wiki](https://github.com/woctezuma/steam-market/wiki) shows a ranking of packs with high buy orders.

Rankings are also available for gambles with items of "Common" rarity, obtained after crafting a badge:
-   [profile backgrounds](https://github.com/woctezuma/steam-market/wiki/Profile_backgrounds),
-   [emoticons](https://github.com/woctezuma/steam-market/wiki/Emoticons).

## References

-   [An example](https://www.resetera.com/threads/pc-gaming-era-april-2019-goodbye-uzzy-is-your-new-king.108742/page-123#post-20167882) of market arbitrage.
-   [A blog post about scraping Steam Market](https://www.blakeporterneuro.com/learning-python-project-3-scrapping-data-from-steams-community-market/)

<!-- Definitions -->

[sack-of-gems]: <https://steamcommunity.com/market/listings/753/753-Sack%20of%20Gems>

[build]: <https://github.com/woctezuma/steam-market/actions>
[build-image]: <https://github.com/woctezuma/steam-market/workflows/Python application/badge.svg?branch=master>

[pyup]: <https://pyup.io/repos/github/woctezuma/steam-market/>
[dependency-image]: <https://pyup.io/repos/github/woctezuma/steam-market/shield.svg>
[python3-image]: <https://pyup.io/repos/github/woctezuma/steam-market/python-3-shield.svg>

[codecov]: <https://codecov.io/gh/woctezuma/steam-market>
[codecov-image]: <https://codecov.io/gh/woctezuma/steam-market/branch/master/graph/badge.svg>

[codacy]: <https://app.codacy.com/gh/woctezuma/steam-market>
[codacy-image]: <https://api.codacy.com/project/badge/Grade/c1b2f9f7a02a47a4baa22f6439be9c8a>

