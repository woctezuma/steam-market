# aiosteampy Integration Plan for steam-market

> **Generated:** 2026-07-13
> **Reviewed:** 2026-11-25
> **Status:** Draft (revised after review — see "Relevance Review" below)
> **Owner:** Project Maintainer

---

## Relevance Review (2026-11-25)

The original draft (2026-07-13) was reviewed against the current repository state and the current
aiosteampy release landscape. Verdict: **the strategy is still relevant, but the draft's code
examples are not runnable as written and must be fixed before implementation starts.**

**What is still valid:**

- No integration work has started yet: `requirements.txt` still only contains `beautifulsoup4`,
  `requests`, `steamspypi`; there is no `src/aiosteampy_client.py` or test script. The plan is the
  HEAD commit (`d3daa33`) and the codebase is unchanged since.
- The line numbers and file sizes quoted in the draft still match the current code exactly
  (`market_search.py` 274, `market_order.py` 409, `market_listing.py` 532, `inventory_utils.py`
  488, `cookie_utils.py` 36, `personal_info.py` 115 lines).
- The hybrid sync/async strategy and the phased roadmap remain sound.
- The priority order (market search/orders/listing first) is still correct.

**What changed or was wrong in the draft:**

1. **Version mismatch (critical).** The draft says "latest release: v0.7.21, March 2026" and
   recommends plain `pip install aiosteampy`, which installs stable **0.7.21** — but every code
   example in the draft (`client.market.search(...)`, `client.market.get_orders_histogram(...)`,
   `SteamSession.serialize()/deserialize()`, `client.transport.close()`) only exists in the
   **1.0.0 prerelease line**, not in 0.7.21. As of 2026-11-25 the latest stable on PyPI is still
   v0.7.21 (2026-03-12), but there is an active beta line: v1.0.0b1 (2026-05-24) through
   **v1.0.0b16 (2026-09-10)**. The two APIs differ completely (see the version decision below and
   the dual mapping in the Appendix). All examples in this revision are written against
   **v1.0.0b16**, with 0.7.21 equivalents in the Appendix.
2. **Per-call `asyncio.run()` is an anti-pattern.** The draft's wrapper creates a new event loop
   and a new client per call. That defeats connection pooling and cookie persistence, is slow
   over hundreds of items, and raises `RuntimeError` if called from a running loop. This revision
   uses one client and one `asyncio.run()` per batch.
3. **Several method names/fields were wrong even for the 1.0 line** (e.g. `client.market.search()`
   is not an async iterator — `search_results()` is; `listing.hash_name` is
   `item.description.market_hash_name`; `client.market.get_listing()` does not return
   `item_nameid` — use `get_item_name_id()`; `client.market.sell_item()` is
   `place_sell_listing()`; inventory for app 753/context 6 is `AppContext.STEAM_COMMUNITY`,
   not `AppContext.CS2`). All corrected below against the actual v1.0.0b16 wheel.
4. **Scope gaps.** The draft omits `market_buzz_detector.py` and `market_gamble_detector.py` as
   entry points, and `src/market_foil_utils.py` (goo-value endpoint). It also did not state that
   booster-pack **creation** (`ajaxcreatebooster`) and the goo-value endpoint
   (`ajaxgetgoovalueforitemtype`) are **not covered by aiosteampy in any version** — those must
   stay on `requests`. Non-Steam endpoints (steamcardexchange.net, steamspypi) also stay on
   `requests`.
5. **Code-reduction estimates were optimistic.** They count only Steam-API lines, but disk
   caching, cooldown timestamps, rate-limit bookkeeping and batch orchestration remain
   regardless of the HTTP library. Treat the table as an upper bound.

---

## Overview

This document outlines how to integrate [aiosteampy](https://github.com/somespecialone/aiosteampy)
into the existing `steam-market` codebase. The library provides a typed, async Python interface to
Steam's API, which can replace the current manual `requests`-based HTTP calls and BeautifulSoup
parsing for the Steam Community endpoints.

**Key Benefits of Integration:**

- Typed responses (no more manual JSON parsing / HTML scraping for `item_nameid`)
- Built-in rate-limit errors (`TooManyRequests` / `RateLimitExceeded`) and session management
- Comprehensive Steam API coverage (Market, Inventory, Trade Offers, etc.)
- Active maintenance: 16 prereleases of the 1.0 line between 2026-05-24 and 2026-09-10

**Scope limits (endpoints aiosteampy does NOT cover, keep `requests` for these):**

- Booster pack creation: `POST /tradingcards/ajaxcreatebooster/` (`src/inventory_utils.py`)
- Goo value: `GET /auction/ajaxgetgoovalueforitemtype/` (`src/market_foil_utils.py`)
- Third-party APIs: `steamcardexchange.net` (`src/download_steam_card_exchange.py`),
  `steamspypi` (`src/free_games_with_trading_cards.py`)

---

## Version Decision (must be made before Phase 1)

| | Option A: stable 0.7.21 | Option B: prerelease 1.0.0b16 (RECOMMENDED) |
|---|---|---|
| Install | `pip install aiosteampy==0.7.21` | `pip install aiosteampy==1.0.0b16` (exact prerelease pin works without `--pre`) |
| Latest release | 2026-03-12 (no newer stable as of 2026-11-25) | 2026-09-10 (v1.0.0b16) |
| Python requirement | >= 3.10 | >= 3.12 (repo venv is Python 3.14.5, OK) |
| API shape | Flat methods on the client (`client.get_item_orders_histogram(...)`), no `SteamSession` class; cookies via `aiosteampy.helpers.restore_from_cookies` / `aiosteampy.utils.get_jsonable_cookies`; close via `await client.session.close()` | Namespaced components (`client.market.*`, `client.inventory.*`), `aiosteampy.session.SteamSession` with `serialize()/deserialize()`, close via `await client.transport.close()` |
| Churn risk | Low (stable) | High between betas — mitigate by exact pinning |
| Matches examples below | No (see Appendix for 0.7.21 equivalents) | Yes |

**Recommendation:** Option B, pinned exactly to `aiosteampy==1.0.0b16` in `requirements.txt`.
Rationale: the 1.0 line is where active development happens, it has the cleaner namespaced API,
and all examples in this plan are written against it. If prereleases are unacceptable for the
create-then-sell workflow (real orders), fall back to Option A and use the 0.7.21 mapping in the
Appendix — the roadmap and priorities are identical either way.

**Currency/country/language matter:** the current code requests EUR (`currency=3`), `country=FR`,
`language=english`. Configure the client accordingly, otherwise prices come back in USD:

```python
from aiosteampy.client import SteamPublicClient
from aiosteampy.client.constants import Currency, Language

client = SteamPublicClient(currency=Currency.EUR, country="FR", language=Language.ENGLISH)
```

---

## Critical Consideration: Async vs Sync

**The entire current codebase is synchronous** (uses `requests`) **while aiosteampy is
async-only** (uses `asyncio` + `aiohttp`).

### Integration Strategy Options

| Strategy | Effort | Complexity | Recommendation |
|----------|--------|------------|----------------|
| **Hybrid Approach** | Low-Medium | Medium | **RECOMMENDED START** |
| **Full Async Migration** | High | High | Future goal |
| **Sync Wrapper Layer** | Medium | Medium | Alternative |

**Recommended Hybrid Approach (corrected):**

- Keep the existing sync code intact initially.
- Run **one** aiosteampy client inside **one** `asyncio.run()` call that processes a whole batch
  (e.g. all market orders), instead of one `asyncio.run()` per item. A new event loop + new client
  per item would lose connection pooling and the shared cookie jar, and is much slower.
- Create the client once per batch, close it once (`await client.transport.close()`).
- Do not call `asyncio.run()` from inside a running event loop; the entry scripts are sync, so this
  is fine as long as each public sync wrapper wraps a *batch*, not a single request.

---

## Integration Points by Priority

All examples below are written against **aiosteampy v1.0.0b16** (see Appendix for 0.7.21).

### HIGH PRIORITY (Direct Market Data Replacements)

These files contain the most complex manual HTTP calls and parsing logic. Replacing them with
aiosteampy gives the biggest reduction in code complexity and maintenance burden.

#### 1. `src/market_search.py`

| Current Function | Lines | aiosteampy Replacement (v1.0.0b16) | Complexity Reduction |
|-----------------|-------|-----------------------------------|---------------------|
| `get_all_listings()` | 87-196 | `client.market.search_results()` | High |
| `get_search_parameters()` | 40-83 | `filters={...}` argument | Eliminates ~44 lines |

**Current implementation:** manual URL construction, query-parameter building, rate limiting,
response parsing, cookie management.

**aiosteampy equivalent:**

```python
async def get_all_listings_aiosteampy(client, tag_item_class_no=5, tag_drop_rate_str=None):
    from aiosteampy.client import App

    filters = {
        "category_753_Game[]": "any",
        "category_753_droprate[]": tag_drop_rate_str or "any",
        "category_753_item_class[]": f"tag_item_class_{tag_item_class_no}",
    }
    if tag_item_class_no == 2:  # trading cards
        filters["category_753_cardborder[]"] = "tag_cardborder_1"  # foil

    results = {}
    async for items in client.market.search_results(
        app=App.STEAM,            # appid 753
        filters=filters,
        sort_column="name",       # keep: name/asc so downloads are stable while trading happens
        sort_dir="asc",
        count=100,
    ):
        for item in items:
            results[item.description.market_hash_name] = {
                "sell_listings": item.sell_listings,
                "sell_price": item.sell_price,          # int, cents
                "sell_price_text": item.sell_price_text,
            }
    return results
```

Notes:

- `search_results()` is the async paginator (yields `list[MarketSearchItem]` per page);
  `search()` returns a single `MarketSearchResult(items, total)` page.
- Filter keys must be the exact Steam query keys **including the `[]` suffix and casing**
  (`category_753_Game[]`, not `category_753_game`). They map 1:1 to what
  `get_search_parameters()` builds today.
- `MarketSearchItem` has no `hash_name` attribute; the hash name lives at
  `item.description.market_hash_name`.
- Sorting by `name`/`asc` is preserved on purpose (see the comment in the current code).

**Benefits:** eliminates ~110 lines of manual request/parsing logic, typed fields, and Steam
rate limits surface as `aiosteampy.exceptions.TooManyRequests`.

---

#### 2. `src/market_order.py`

| Current Function | Lines | aiosteampy Replacement (v1.0.0b16) | Complexity Reduction |
|-----------------|-------|-----------------------------------|---------------------|
| `download_market_order_data()` | 60-168 | `client.market.get_orders_histogram()` | High |
| `get_market_order_parameters()` | 33-40 | Client configured with currency/country/language | Eliminates ~8 lines |
| `get_market_order_headers()` | 43-57 | Not needed | Eliminates ~15 lines |

**Current implementation:** manual headers, query params, JSON parsing, status-code handling.

**aiosteampy equivalent:**

```python
async def download_market_order_data_aiosteampy(client, item_nameid: int):
    from aiosteampy.exceptions import TooManyRequests

    try:
        histogram = await client.market.get_orders_histogram(item_nameid)
    except TooManyRequests:
        raise  # keep the draft behavior: stop and let the caller re-check rate limits

    # prices are ints in cents; volumes come from the graph entries
    bid_price = histogram.highest_buy_order if histogram.highest_buy_order is not None else -1
    ask_price = histogram.lowest_sell_order if histogram.lowest_sell_order is not None else -1
    bid_volume = histogram.buy_order_graph[0].quantity if histogram.buy_order_graph else -1
    ask_volume = histogram.sell_order_graph[0].quantity if histogram.sell_order_graph else -1

    return bid_price, ask_price, bid_volume, ask_volume
```

Notes:

- In v1.0.0b16 `get_orders_histogram(item_name_id)` returns the `ItemOrdersHistogram` model
  directly (in 0.7.21 it is `get_item_orders_histogram(...)` and returns a
  `(histogram, last_modified)` tuple — see Appendix).
- `OrderGraphEntry` is a NamedTuple `(price, quantity, repr)`, so `graph[0][0]` / `graph[0][1]`
  also still work, but the named fields are clearer.
- The endpoint is rate-limited by Steam and supports `If-Modified-Since`; v1.0.0b16 exposes
  `if_modified_since=` on the call and raises `ResourceNotModified` on 304 — a natural fit for
  the existing 72-hour `UPDATE_COOLDOWN_IN_HOURS` logic.

**Benefits:** eliminates ~110 lines of manual HTTP handling; typed response; Steam 429 raises a
dedicated exception.

---

#### 3. `src/market_listing.py`

| Current Function | Lines | aiosteampy Replacement (v1.0.0b16) | Complexity Reduction |
|-----------------|-------|-----------------------------------|---------------------|
| `get_listing_details()` | 247-305 | `client.market.get_item_name_id()` | High |
| `parse_item_name_id()` + `parse_marketability_from_script()` | 218-244 | Direct field access on `ItemDescription` | Eliminates BeautifulSoup parsing |
| `parse_item_type_no_from_script()` | 80-215 | **Not covered** — keep or re-derive | Partial |

**Current implementation:** BeautifulSoup parsing of the listing page's last `<script>` tag to
extract `item_nameid`, `marketable`, and the goo `item_type_no`.

**aiosteampy equivalent:**

```python
async def get_listing_details_aiosteampy(client, listing_hash: str):
    from aiosteampy.client import App

    item_nameid = await client.market.get_item_name_id(listing_hash, App.STEAM)
    # marketability: from the item description attached to search results / inventory
    #   description.marketable  (bool)
    return {listing_hash: {"item_nameid": item_nameid}}
```

Notes:

- `get_item_name_id(market_hash_name, App.STEAM)` fetches the listing page and extracts the
  nameid for us — this removes the only BeautifulSoup usage in the repo, so `beautifulsoup4` can
  be dropped once this migration lands.
- `is_marketable` is available as `ItemDescription.marketable` (present on descriptions returned
  by market search and inventory), so `parse_marketability_from_script()` can go too.
- `item_type_no` (the "Turn into Gems..." type, used for foil goo values) is **not** exposed by
  aiosteampy — keep `parse_item_type_no_from_script()` (or read it from the goo endpoint in
  `market_foil_utils.py`).
- URL-encoding of special characters (`#`, `?`) in listing hashes is handled by the library's
  URL building; `fix_app_name_for_url_query()` becomes unnecessary for API calls (keep it only if
  it is used for display links).

**Benefits:** ~60 lines of parsing reduced to a few; `beautifulsoup4` dependency removable.

---

### MEDIUM PRIORITY (Inventory Operations)

#### `src/inventory_utils.py`

| Current Function | Lines | aiosteampy Replacement (v1.0.0b16) | Notes |
|-----------------|-------|-----------------------------------|-------|
| `download_steam_inventory()` | 79-117 | `client.inventory.get(AppContext.STEAM_COMMUNITY)` or `get_user_inventory()` | Direct replacement |
| `get_my_steam_profile_id()` | 25-26 | `session.steam_id` / `client.state` | Built into session |
| `create_booster_pack()` | 149-202 | **Not supported by aiosteampy** | Keep `requests` (`ajaxcreatebooster`) |
| `sell_booster_pack()` | 238-298 | `client.market.place_sell_listing()` | Direct replacement |
| `retrieve_asset_id()` | 301-365 | Filter `EconItem`s by `description.market_hash_name` | Use aiosteampy models |

**aiosteampy equivalent:**

```python
from aiosteampy.client import AppContext

async def download_steam_inventory_aiosteampy(client):
    inv = await client.inventory.get(AppContext.STEAM_COMMUNITY)  # app 753, context 6
    # inv.items: Sequence[EconItem]; each item has .asset_id and .description
    return inv

async def sell_booster_pack_aiosteampy(client, asset_id: int, price_in_cents: int):
    # current code's price is what the seller receives -> use to_receive=
    return await client.market.place_sell_listing(
        asset_id,
        AppContext.STEAM_COMMUNITY,
        to_receive=round(price_in_cents),
    )

def retrieve_asset_id_aiosteampy(inv, listing_hash: str, focus_on_marketable_items: bool = True):
    for item in inv.items:
        descr = item.description
        if descr.market_hash_name == listing_hash:
            if descr.marketable or not focus_on_marketable_items:
                return item.asset_id
    return None
```

Notes:

- App 753 / context 6 is `AppContext.STEAM_COMMUNITY` (NOT `AppContext.CS2` — that is app 730).
- `client.inventory.get(...)` fetches the *authenticated user's* inventory and returns an
  `Inventory(items, total, last_asset_id)`; pagination via `start_asset_id`.
  `client.inventory.get_user_inventory(steam_id, app_ctx)` is the public variant.
- `place_sell_listing` has overloads taking an `EconItem` or an `asset_id` + `AppContext`, with
  either `price=` (total buyer pays) or `to_receive=` (what the seller receives). The current
  `price_in_cents` is the seller's revenue, so use `to_receive=`.
- `create_booster_pack()` must keep using `requests` — aiosteampy has no booster/goo-creation
  endpoint in any released version.

---

### LOW PRIORITY (Session & Authentication)

#### `src/personal_info.py` + `src/cookie_utils.py`

| Current Function | Lines | aiosteampy Replacement (v1.0.0b16) | Notes |
|-----------------|-------|-----------------------------------|-------|
| Cookie management | `personal_info.py` 1-115, `cookie_utils.py` 1-36 | `SteamSession.serialize()` / `deserialize()` | Full replacement |
| `force_update_sessionid()` | `cookie_utils.py` 21-36 | Built into the client | Automatic handling |

**aiosteampy equivalent (v1.0.0b16):**

```python
from aiosteampy.session import SteamSession
from aiosteampy.client import SteamClient

# Loading session (adapt to how SteamSession accepts cookies/tokens in the pinned version)
session = SteamSession.deserialize(load_json("personal_info.json"))
client = SteamClient(session)

# Saving session
save_json(client.session.serialize(), "personal_info.json")
```

For **v0.7.21** there is no `SteamSession`; instead (see Appendix):

```python
from aiosteampy import SteamClient  # constructed with credentials, then:
from aiosteampy.helpers import restore_from_cookies
from aiosteampy.utils import get_jsonable_cookies

await restore_from_cookies(load_json("personal_info.json"), client)  # from cookie dict
save_json(get_jsonable_cookies(client.session), "personal_info.json")
```

**Benefits:** automatic session persistence, cookie-jar management, and `sessionid` refresh;
`force_update_sessionid()` can be deleted.

---

## Main Script Integration

Entry points to update: `market_arbitrage.py`, `market_arbitrage_with_foil_cards.py`,
`market_buzz_detector.py`, `market_gamble_detector.py`.

### `market_arbitrage.py`

**Current workflow:** `load_market_order_data(filtered_badge_data, ...)` (sync, `requests`).

**With aiosteampy (one event loop for the whole batch):**

```python
async def load_market_order_data_async(client, badge_data, verbose=False):
    from src.market_listing import get_item_nameid_batch  # keep disk cache layer

    market_order_dict = {}
    listing_hashes = [badge_data[app_id]["listing_hash"] for app_id in badge_data]
    item_nameids = get_item_nameid_batch(listing_hashes)  # may itself use aiosteampy

    for app_id in badge_data:
        listing_hash = badge_data[app_id]["listing_hash"]
        item_nameid = item_nameids[listing_hash]["item_nameid"]
        bid, ask, bid_vol, ask_vol = await download_market_order_data_aiosteampy(client, item_nameid)
        market_order_dict[listing_hash] = {
            "bid": bid, "ask": ask, "bid_volume": bid_vol, "ask_volume": ask_vol,
        }
    return market_order_dict

# In apply_workflow(), wrap the whole batch in a single asyncio.run():
if use_aiosteampy:
    from src.aiosteampy_client import run_batch_with_client
    market_order_dict = run_batch_with_client(
        load_market_order_data_async, filtered_badge_data, verbose=verbose
    )
else:
    market_order_dict = load_market_order_data(
        filtered_badge_data,
        retrieve_market_orders_online=retrieve_market_orders_online,
        verbose=verbose,
    )
```

The other three entry scripts follow the same pattern: replace the market data fetching calls
with aiosteampy calls wrapped in a single `asyncio.run()` per batch.

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal:** install aiosteampy, pin it, and validate it works with existing data.

1. **Add dependency** (Option B; exact pin — a prerelease pin does not need `--pre`):

   ```bash
   pip install aiosteampy==1.0.0b16
   ```

   Add to `requirements.txt`: `aiosteampy==1.0.0b16`. (Option A: `aiosteampy==0.7.21`.)
   Note: v1.0.0b16 requires Python >= 3.12 — the project venv is Python 3.14.5, OK.

2. **Create integration module** `src/aiosteampy_client.py` — one client per batch, one event
   loop per batch:

   ```python
   """aiosteampy integration module for steam-market.

   Provides a sync-compatible entry point that runs a whole batch of async
   aiosteampy operations inside a single asyncio.run() with a single client.
   """

   import asyncio
   from collections.abc import Awaitable, Callable
   from typing import Any, TypeVar

   from aiosteampy.client import AppContext, SteamClient, SteamPublicClient
   from aiosteampy.client.constants import Currency, Language
   from aiosteampy.session import SteamSession

   from src.json_utils import load_json, save_json

   T = TypeVar("T")

   COOKIE_FILE = "personal_info.json"


   def make_public_client() -> SteamPublicClient:
       return SteamPublicClient(currency=Currency.EUR, country="FR", language=Language.ENGLISH)


   def make_authenticated_client() -> SteamClient:
       session = SteamSession.deserialize(load_json(COOKIE_FILE))
       client = SteamClient(session, currency=Currency.EUR, country="FR", language=Language.ENGLISH)
       return client


   def run_batch_with_client(
       batch_fn: Callable[[Any, ...], Awaitable[T]],
       *args: Any,
       authenticated: bool = False,
       **kwargs: Any,
   ) -> T:
       """Run batch_fn(client, *args, **kwargs) in one event loop with one client."""

       async def _run() -> T:
           client = make_authenticated_client() if authenticated else make_public_client()
           try:
               return await batch_fn(client, *args, **kwargs)
           finally:
               await client.transport.close()

       return asyncio.run(_run())


   def save_session(client: SteamClient, file_name: str = COOKIE_FILE) -> None:
       save_json(client.session.serialize(), file_name)
   ```

   Note: `AppContext` is imported here only for convenience re-export; the pinned version's exact
   import locations are `aiosteampy.client` (App, AppContext, SteamClient, SteamPublicClient),
   `aiosteampy.client.constants` (Currency, Language), `aiosteampy.session` (SteamSession).
   Confirm against the pinned wheel before finalizing (see Appendix).

3. **Create test script** `test_aiosteampy_integration.py` (public API only, no auth):

   ```python
   from aiosteampy.client import App
   from src.aiosteampy_client import run_batch_with_client, make_public_client


   async def _smoke(client):
       # Histogram for a known item nameid (Glock-18 | Fully Tuned, Field-Tested)
       histogram = await client.market.get_orders_histogram(176611887)
       print("highest bid:", histogram.highest_buy_order, "lowest ask:", histogram.lowest_sell_order)

       # Search booster packs on app 753
       count = 0
       async for items in client.market.search_results(
           app=App.STEAM,
           filters={
               "category_753_Game[]": "any",
               "category_753_droprate[]": "any",
               "category_753_item_class[]": "tag_item_class_5",
           },
           sort_column="name",
           sort_dir="asc",
           count=10,
       ):
           for item in items:
               count += 1
               print(item.description.market_hash_name, item.sell_price, item.sell_price_text)
       return count


   if __name__ == "__main__":
       n = run_batch_with_client(_smoke)
       print(f"OK, {n} listings")
   ```

4. **Run and validate:** `python test_aiosteampy_integration.py` — compare a few histograms and
   search results against the existing JSON data in `data/`.

---

### Phase 2: Gradual Migration (Week 3-4)

**Goal:** replace one module at a time, starting with the highest value, keeping a toggle so the
old path remains available.

1. **`market_order.py`**: add `download_market_order_data_aiosteampy()` and make
   `download_market_order_data_batch()` accept `use_aiosteampy: bool = False`; batch through
   `run_batch_with_client`.
2. **`market_search.py`**: same pattern for `get_all_listings()`.
3. **`market_listing.py`**: replace the BeautifulSoup parsing with `get_item_name_id()` +
   `ItemDescription.marketable`; keep `parse_item_type_no_from_script()`.
4. **Entry points**: add a `--use-aiosteampy` flag to the four scripts.
5. **Comparison tests**: run old and new implementations over the same listing hashes and diff
   the resulting dicts (see Testing Strategy).

---

### Phase 3: Full Migration (Week 5+)

**Goal:** convert the codebase to async and drop dependencies that are no longer needed.

1. Convert main scripts to async entry points (`asyncio.run(main())` once at the top).
2. `inventory_utils.py`: inventory via `client.inventory.get(...)`, selling via
   `place_sell_listing(...)`; keep `requests` only for `create_booster_pack()` and the goo-value
   endpoint in `market_foil_utils.py`.
3. Delete `cookie_utils.py` and most of `personal_info.py` (session handled by `SteamSession`).
4. Remove `beautifulsoup4` from `requirements.txt` (only user was `market_listing.py`).
   Keep `requests` (booster creation, goo value, steamcardexchange, steamspypi).
5. Re-validate rate limiting: aiosteampy raises on Steam 429; keep the existing cooldown
   bookkeeping in `market_order.py` (the 72 h `UPDATE_COOLDOWN_IN_HOURS` cache) — the library
   does not replace your on-disk caching.

---

## Code Reduction Estimates (upper bounds)

The draft's table counted only Steam-API lines; disk caching, cooldown timestamps, rate-limit
bookkeeping and batch orchestration remain regardless of the HTTP library. Treat these as
optimistic upper bounds:

| File | Current Lines | After Migration | Reduction |
|------|---------------|-----------------|-----------|
| `market_search.py` | 274 | ~120 | ~56% |
| `market_order.py` | 409 | ~250 | ~39% |
| `market_listing.py` | 532 | ~330 | ~38% |
| `inventory_utils.py` | 488 | ~330 | ~32% (booster creation stays) |
| `cookie_utils.py` | 36 | 0 | 100% |
| `personal_info.py` | 115 | ~30 | ~74% |
| **Total** | **1,854** | **~1,060** | **~43%** |

(The original draft claimed ~69% / ~1,284 lines; that assumed the caching and orchestration logic
would disappear, which it does not.)

---

## Quick Start: Immediate Usage (public data, no code changes)

Works today against v1.0.0b16 with just `pip install aiosteampy==1.0.0b16`:

```python
# test_public_api.py
import asyncio

from aiosteampy.client import App, SteamPublicClient
from aiosteampy.client.constants import Currency, Language


async def main():
    client = SteamPublicClient(currency=Currency.EUR, country="FR", language=Language.ENGLISH)
    try:
        # Orders histogram for an item (item nameid 176611887 = Glock-18 | Fully Tuned, FT)
        histogram = await client.market.get_orders_histogram(176611887)
        print("highest bid:", histogram.highest_buy_order)
        print("lowest ask:", histogram.lowest_sell_order)
        print("bid graph[0]:", histogram.buy_order_graph[0])  # (price, quantity, repr)

        # Search booster packs on the Steam app (753)
        async for items in client.market.search_results(
            app=App.STEAM,
            filters={"category_753_item_class[]": "tag_item_class_5"},
            count=10,
        ):
            for item in items:
                print(item.description.market_hash_name, item.sell_price_text)
    finally:
        await client.transport.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Run with: `python test_public_api.py`

---

## Testing Strategy

- `tests.py` is `unittest`-based and hits the live network; keep it working for the old path.
- Add comparison tests: run old and new implementations over the same listing hashes, assert the
  resulting dicts are equal (prices may differ slightly over time — compare structure and
  allow small price drift, or compare against frozen fixtures).
- Validate rate-limit behavior: Steam 429 must surface as `TooManyRequests` (b16) /
  `RateLimitExceeded` (0.7.21) and trigger the existing cooldown logic.
- Test error handling with invalid item nameids / listing hashes.
- Test the authenticated flow (session restore from `personal_info.json`) before enabling
  create-then-sell with the new client.

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Wrong version installed** (stable 0.7.21 vs 1.0 beta have incompatible APIs) | High | High | Pin exactly (`aiosteampy==1.0.0b16`); Appendix maps both APIs; smoke-test script in Phase 1 |
| **Prerelease churn** in the 1.0 beta line | Medium | Medium | Exact pin; re-run smoke test after any bump; renovate.json already tracks requirements |
| **API differences vs the draft's examples** | Medium | High | All examples in this revision were verified against the actual v1.0.0b16 wheel; re-verify signatures when bumping |
| **Async complexity** (per-call `asyncio.run()` pitfalls) | Medium | Medium | One client + one `asyncio.run()` per batch (`run_batch_with_client`) |
| **Session migration issues** | Medium | High | Test auth flow early; keep the old cookie path as fallback until validated |
| **Uncovered endpoints** (booster creation, goo value) | Certain | Low | Keep `requests` for those; do not try to force them through aiosteampy |
| **Currency mismatch** (USD vs EUR prices) | Low | High | Always construct the client with `currency=Currency.EUR, country="FR"` |
| **Breaking changes in aiosteampy** | Low | Medium | Pin version, monitor releases |

---

## Success Criteria

- [ ] Phase 1: pinned aiosteampy installed; smoke-test script runs against the public API and
      returns sane EUR prices
- [ ] Phase 1: `src/aiosteampy_client.py` created; `run_batch_with_client` runs a batch in one
      event loop
- [ ] Phase 2: `market_order.py` and `market_search.py` have aiosteampy paths behind a toggle;
      comparison tests show identical structure to the old path
- [ ] Phase 2: `market_listing.py` parses via aiosteampy; `beautifulsoup4` removable
- [ ] Phase 2: all four entry scripts accept `--use-aiosteampy`; existing `tests.py` still passes
      on the old path
- [ ] Phase 2: rate-limit behavior validated (429 -> dedicated exception -> cooldown)
- [ ] Phase 3: inventory + sell via aiosteampy; booster creation still on `requests`
- [ ] Phase 3: session persistence via `SteamSession`; `cookie_utils.py` deleted
- [ ] Performance benchmark shows improvement or parity; code reduction in the 30-45% range on
      the touched files

---

## References

- [aiosteampy GitHub](https://github.com/somespecialone/aiosteampy)
- [aiosteampy Documentation](https://aiosteampy.somespecial.one)
- [aiosteampy DeepWiki](https://deepwiki.com/somespecialone/aiosteampy)
- [PyPI: aiosteampy](https://pypi.org/project/aiosteampy/) (latest stable 0.7.21; prereleases up to 1.0.0b16)
- Verified locally against the actual wheels `aiosteampy-0.7.21-py3-none-any.whl` and
  `aiosteampy-1.0.0b16-py3-none-any.whl` (2026-11-25)

---

## Appendix: API Mapping — current code vs aiosteampy v1.0.0b16 vs v0.7.21

| Current function (file) | aiosteampy v1.0.0b16 (recommended) | aiosteampy v0.7.21 (stable fallback) |
|------------------------|-----------------------------------|--------------------------------------|
| `get_all_listings()` (`market_search.py`) | `async for items in client.market.search_results(app=App.STEAM, filters={"category_753_Game[]": "any", ...}, sort_column="name", sort_dir="asc", count=100)`; hash name at `item.description.market_hash_name`; single page: `client.market.search(...)` -> `MarketSearchResult(items, total)` | `async for (items, total) in client.market_search_results(app=App.STEAM, filters={...}, sort_column="name", sort_dir="asc", count=100)`; single page: `client.get_market_search_results(...)` |
| `download_market_order_data()` (`market_order.py`) | `h = await client.market.get_orders_histogram(item_nameid)`; `h.highest_buy_order`, `h.lowest_sell_order`, `h.buy_order_graph[0].quantity` (returns the model directly) | `h, last_modified = await client.get_item_orders_histogram(item_nameid)`; `h.buy_order_graph[0]` is `OrderGraphEntry(price, quantity, repr)` |
| `get_listing_details()` / `parse_item_name_id()` (`market_listing.py`) | `nameid = await client.market.get_item_name_id(listing_hash, App.STEAM)`; marketable via `ItemDescription.marketable` from search/inventory descriptions | same names: `client.get_item_name_id(obj, app)` (flat, no `.market`) |
| `download_steam_inventory()` (`inventory_utils.py`) | own: `inv = await client.inventory.get(AppContext.STEAM_COMMUNITY)` -> `Inventory(items, total, last_asset_id)`; public: `client.inventory.get_user_inventory(steam_id, app_ctx)` | `items, total, last_assetid = await client.get_user_inventory(steam_id, AppContext.STEAM_COMMUNITY)` or async iterator `client.user_inventory(...)` |
| `sell_booster_pack()` (`inventory_utils.py`) | `await client.market.place_sell_listing(asset_id, AppContext.STEAM_COMMUNITY, to_receive=price_in_cents)` | `await client.place_sell_listing(asset_id, AppContext.STEAM_COMMUNITY, to_receive=...)` |
| `create_booster_pack()` | **not supported** — keep `requests` | **not supported** — keep `requests` |
| goo value (`market_foil_utils.py`) | **not supported** — keep `requests` | **not supported** — keep `requests` |
| cookie/session management (`personal_info.py`, `cookie_utils.py`) | `aiosteampy.session.SteamSession.deserialize(dict)` / `session.serialize()`; `SteamClient(session, ...)`; `session.steam_id` | no `SteamSession`: `await restore_from_cookies(cookies, client)` (`aiosteampy.helpers`), `get_jsonable_cookies(client.session)` (`aiosteampy.utils`) |
| client construction | `SteamPublicClient(currency=Currency.EUR, country="FR", language=Language.ENGLISH)`; `from aiosteampy.client import App, AppContext, SteamClient, SteamPublicClient`; `from aiosteampy.client.constants import Currency, Language` | `SteamPublicClient(currency=Currency.EUR, country="FR", language=Language.ENGLISH)`; `from aiosteampy import App, AppContext, Currency, Language, SteamClient, SteamPublicClient` |
| closing the client | `await client.transport.close()` | `await client.session.close()` (aiohttp session; there is no `transport`) |
| rate-limit error | `aiosteampy.exceptions.TooManyRequests` | `aiosteampy.exceptions.RateLimitExceeded` |
| imports of enums | `aiosteampy.client` (App, AppContext), `aiosteampy.client.constants` (Currency, Language) | top-level `aiosteampy` (App, AppContext, Currency, Language) |

App/context reference: `App.STEAM = 753`; `AppContext.STEAM_COMMUNITY = (App.STEAM, 6)` — this is
the app/context pair the current code hardcodes (`appid=753`, `contextid=6`). `AppContext.CS2`
is app 730/context 2 and is irrelevant for booster packs.

---

## File Changes Summary

| Action | File | Description |
|--------|------|-------------|
| **Create** | `src/aiosteampy_client.py` | Integration module (`run_batch_with_client`, client factories) |
| **Create** | `test_aiosteampy_integration.py` | Public-API smoke test |
| **Modify** | `AIOSTEAMPY_INTEGRATION_PLAN.md` | This document |
| **Modify** | `requirements.txt` | Add pinned `aiosteampy==1.0.0b16` (or `==0.7.21`) |
| **Modify** | `src/market_order.py` | aiosteampy path behind toggle (Phase 2) |
| **Modify** | `src/market_search.py` | aiosteampy path behind toggle (Phase 2) |
| **Modify** | `src/market_listing.py` | Replace BeautifulSoup parsing (Phase 2) |
| **Modify** | `src/inventory_utils.py` | Inventory + sell via aiosteampy (Phase 3); booster creation stays on `requests` |
| **Modify** | `market_arbitrage.py`, `market_arbitrage_with_foil_cards.py`, `market_buzz_detector.py`, `market_gamble_detector.py` | `--use-aiosteampy` flag (Phase 2) |
| **Delete** | `src/cookie_utils.py` | Obsoleted by session handling (Phase 3) |
| **Shrink** | `src/personal_info.py` | Keep only the cookie-file I/O shim for `SteamSession` (Phase 3) |
| **Modify** | `requirements.txt` | Remove `beautifulsoup4` once `market_listing.py` is migrated (Phase 3); keep `requests` |
