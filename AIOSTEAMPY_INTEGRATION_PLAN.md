# aiosteampy Integration Plan for steam-market

> **Generated:** 2026-07-13  
> **Status:** Draft  
> **Owner:** Project Maintainer

---

## Overview

This document outlines how to integrate [aiosteampy](https://github.com/somespecialone/aiosteampy) into the existing `steam-market` codebase. The library provides a comprehensive, typed, async Python interface to Steam's API, which can replace the current manual `requests`-based HTTP calls and BeautifulSoup parsing.

**Key Benefits of Integration:**
- Typed responses (no more manual JSON parsing)
- Built-in rate limiting and session management
- Comprehensive Steam API coverage (Market, Inventory, Trade Offers, etc.)
- Active maintenance (latest release: v0.7.21, March 2026)
- Better error handling and retry logic

---

## Critical Consideration: Async vs Sync

**The entire current codebase is synchronous** (uses `requests` library) **while aiosteampy is async-only** (uses `asyncio` + `aiohttp`).

### Integration Strategy Options

| Strategy | Effort | Complexity | Recommendation |
|----------|--------|------------|----------------|
| **Hybrid Approach** | Low-Medium | Medium | ✅ **RECOMMENDED START** |
| **Full Async Migration** | High | High | Future goal |
| **Sync Wrapper Layer** | Medium | Medium | Alternative |

**Recommended Hybrid Approach:**
- Run aiosteampy calls in separate async contexts using `asyncio.run()`
- Keep existing sync code intact initially
- Gradually migrate high-value components

---

## Integration Points by Priority

### 🏆 HIGH PRIORITY (Direct Market Data Replacements)

These files contain the most complex manual HTTP calls and parsing logic. Replacing them with aiosteampy will provide the biggest reduction in code complexity and maintenance burden.

#### 1. `src/market_search.py`

| Current Function | Lines | aiosteampy Replacement | Complexity Reduction |
|-----------------|-------|------------------------|---------------------|
| `get_all_listings()` | 86-196 | `client.market.search()` | High |
| `get_search_parameters()` | 40-83 | Built into aiosteampy | Eliminates ~44 lines |

**Current Implementation:**
- Manual URL construction
- Query parameter building
- Rate limiting logic
- Response parsing
- Cookie management

**aiosteampy Equivalent:**
```python
async def get_all_listings_aiosteampy(client):
    results = {}
    async for listing in client.market.search(
        app_id=753,
        category_753_game=["any"],
        category_753_droprate=["any"],
        category_753_item_class=["tag_item_class_5"],  # Booster packs
        sort_column="name",
        sort_dir="asc",
        count=100
    ):
        results[listing.hash_name] = {
            "sell_listings": listing.sell_listings,
            "sell_price": listing.sell_price,
            "sell_price_text": listing.sell_price_text,
        }
    return results
```

**Benefits:**
- Eliminates ~110 lines of manual request/parsing logic
- Built-in typing for all response fields
- Automatic rate limiting
- Better error handling

---

#### 2. `src/market_order.py`

| Current Function | Lines | aiosteampy Replacement | Complexity Reduction |
|-----------------|-------|------------------------|---------------------|
| `download_market_order_data()` | 60-168 | `client.market.get_orders_histogram()` | High |
| `get_market_order_parameters()` | 33-40 | Built into aiosteampy | Eliminates ~8 lines |
| `get_market_order_headers()` | 43-57 | Not needed | Eliminates ~15 lines |

**Current Implementation:**
- Manual HTTP headers construction
- Query parameter building
- Response JSON parsing
- Error handling for various status codes

**aiosteampy Equivalent:**
```python
async def download_market_order_data_aiosteampy(client, item_nameid):
    try:
        histogram = await client.market.get_orders_histogram(item_nameid)
        
        # Extract bid (buy order)
        bid_price = histogram.buy_order_graph[0][0] if histogram.buy_order_graph else -1
        bid_volume = histogram.buy_order_graph[0][1] if histogram.buy_order_graph else -1
        
        # Extract ask (sell order)
        ask_price = histogram.sell_order_graph[0][0] if histogram.sell_order_graph else -1
        ask_volume = histogram.sell_order_graph[0][1] if histogram.sell_order_graph else -1
        
        return bid_price, ask_price, bid_volume, ask_volume
    except Exception as e:
        print(f"Error fetching orders for item {item_nameid}: {e}")
        return -1, -1, -1, -1
```

**Benefits:**
- Eliminates ~110 lines of manual HTTP handling
- Typed response structure
- Automatic retry logic
- Cleaner error handling

---

#### 3. `src/market_listing.py`

| Current Function | Lines | aiosteampy Replacement | Complexity Reduction |
|-----------------|-------|------------------------|---------------------|
| `get_listing_details()` | 247-305 | `client.market.get_listing()` | High |
| `parse_item_name_id()` | 233-244 | Direct field access | Eliminates parsing |

**Current Implementation:**
- BeautifulSoup HTML parsing
- Complex regex/string manipulation to extract item data
- Multiple parsing functions for different data types

**aiosteampy Equivalent:**
```python
async def get_listing_details_aiosteampy(client, listing_hash):
    listing = await client.market.get_listing(listing_hash)
    
    return {
        listing_hash: {
            "item_nameid": listing.item_nameid,
            "is_marketable": listing.marketable,
            "item_type_no": listing.type,
        }
    }, 200
```

**Benefits:**
- Eliminates BeautifulSoup dependency for this use case
- No more HTML parsing or regex extraction
- Typed fields (no more string parsing)
- ~60 lines reduced to ~10

---

### 🥈 MEDIUM PRIORITY (Inventory Operations)

#### `src/inventory_utils.py`

| Current Function | Lines | aiosteampy Replacement | Notes |
|-----------------|-------|------------------------|-------|
| `download_steam_inventory()` | 79-117 | `client.inventory.get()` | Direct replacement |
| `get_my_steam_profile_id()` | 25-26 | `session.steam_id` | Built into session |
| `create_booster_pack()` | 149-202 | Not supported | Steam API limitation |
| `sell_booster_pack()` | 238-298 | `client.market.sell_item()` | Direct replacement |
| `retrieve_asset_id()` | 301-365 | Inventory filtering | Use aiosteampy models |

**aiosteampy Equivalent for Inventory:**
```python
async def download_steam_inventory_aiosteampy(client):
    inventory = await client.inventory.get(AppContext.CS2)
    return {
        "rgDescriptions": inventory.descriptions,
        "rgInventory": inventory.items,
    }

async def sell_booster_pack_aiosteampy(client, asset_id, price_in_cents):
    result = await client.market.sell_item(
        asset_id=asset_id,
        app_id=753,
        context_id=6,
        price=price_in_cents,
    )
    return result
```

**Benefits:**
- Cleaner inventory data access
- Built-in typing for items and descriptions
- Automatic cookie/session handling

---

### 🥉 LOW PRIORITY (Session & Authentication)

#### `src/personal_info.py` + `src/cookie_utils.py`

| Current Function | Lines | aiosteampy Replacement | Notes |
|-----------------|-------|------------------------|-------|
| Cookie management | 1-107 | `SteamSession.serialize()` / `deserialize()` | Full replacement |
| `force_update_sessionid()` | 21-36 | Built into session | Automatic handling |

**Current Implementation:**
- Manual cookie dictionary management
- JSON file I/O
- Session ID updates

**aiosteampy Equivalent:**
```python
# Loading session
session = SteamSession.deserialize(load_json("personal_info.json"))

# Saving session
session_dump = session.serialize()
save_json(session_dump, "personal_info.json")

# Session is automatically managed by aiosteampy
# No need for manual sessionid updates
```

**Benefits:**
- Automatic session persistence
- Built-in cookie jar management
- Secure credential handling

---

## Main Script Integration

### `market_arbitrage.py`

**Current workflow (lines 54-58):**
```python
market_order_dict = load_market_order_data(
    filtered_badge_data,
    retrieve_market_orders_online=retrieve_market_orders_online,
    verbose=verbose,
)
```

**With aiosteampy:**
```python
async def load_market_order_data_async(client, badge_data):
    market_order_dict = {}
    
    for app_id in badge_data:
        listing_hash = badge_data[app_id]["listing_hash"]
        item_nameid = get_item_nameid(listing_hash)  # Keep existing
        
        bid, ask, bid_vol, ask_vol = await download_market_order_data_aiosteampy(
            client, item_nameid
        )
        
        market_order_dict[listing_hash] = {
            "bid": bid,
            "ask": ask,
            "bid_volume": bid_vol,
            "ask_volume": ask_vol,
        }
    
    return market_order_dict

# In apply_workflow():
market_order_dict = asyncio.run(load_market_order_data_async(client, filtered_badge_data))
```

### `market_arbitrage_with_foil_cards.py`

Similar pattern - replace market data fetching with aiosteampy calls wrapped in `asyncio.run()`.

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal:** Set up aiosteampy and validate it works with your existing data.

1. **Add dependency**
   ```bash
   pip install aiosteampy
   # or
   poetry add aiosteampy
   ```

2. **Create integration module** `src/aiosteampy_client.py`
   ```python
   """
   aiosteampy integration module for steam-market.
   Provides sync-compatible wrappers for async aiosteampy operations.
   """
   
   import asyncio
   from typing import Any
   from aiosteampy import SteamSession, SteamClient, SteamPublicClient
   from aiosteampy.client import AppContext
   
   
   class SteamMarketClient:
       """Wrapper for aiosteampy that provides sync-compatible interface."""
       
       def __init__(self, cookie_file: str = "personal_info.json"):
           self.cookie_file = cookie_file
           self._session = None
           self._client = None
           
       def _load_session(self):
           """Load session from cookie file."""
           from src.personal_info import load_steam_cookie_from_disk
           cookie = load_steam_cookie_from_disk(self.cookie_file)
           if cookie and "steamLoginSecure" in cookie:
               self._session = SteamSession.deserialize(cookie)
               self._client = SteamClient(self._session)
           else:
               self._client = SteamPublicClient()
           return self._client
       
       async def _close(self):
           """Close the client transport."""
           if self._client:
               await self._client.transport.close()
       
       # --- Public sync-compatible methods ---
       
       def get_market_histogram_sync(self, item_nameid: str) -> dict[str, Any]:
           """Get market order histogram (sync wrapper)."""
           async def _async_get():
               client = self._load_session()
               try:
                   histogram = await client.market.get_orders_histogram(item_nameid)
                   return self._histogram_to_dict(histogram)
               finally:
                   await self._close()
           return asyncio.run(_async_get())
       
       def search_market_sync(self, **kwargs) -> dict[str, dict]:
           """Search market listings (sync wrapper)."""
           async def _async_search():
               client = self._load_session()
               try:
                   results = {}
                   async for listing in client.market.search(**kwargs):
                       results[listing.hash_name] = {
                           "sell_listings": listing.sell_listings,
                           "sell_price": listing.sell_price,
                           "sell_price_text": listing.sell_price_text,
                       }
                   return results
               finally:
                   await self._close()
           return asyncio.run(_async_search())
       
       @staticmethod
       def _histogram_to_dict(histogram) -> dict[str, Any]:
           """Convert aiosteampy histogram to dict format."""
           bid_price = histogram.buy_order_graph[0][0] if histogram.buy_order_graph else -1
           bid_volume = histogram.buy_order_graph[0][1] if histogram.buy_order_graph else -1
           ask_price = histogram.sell_order_graph[0][0] if histogram.sell_order_graph else -1
           ask_volume = histogram.sell_order_graph[0][1] if histogram.sell_order_graph else -1
           
           return {
               "bid": bid_price,
               "ask": ask_price,
               "bid_volume": bid_volume,
               "ask_volume": ask_volume,
           }
   ```

3. **Create test script** `test_aiosteampy_integration.py`
   ```python
   from src.aiosteampy_client import SteamMarketClient
   
   def test_public_api():
       """Test aiosteampy with public (no auth) API."""
       client = SteamMarketClient()
       
       # Test histogram
       histogram = client.get_market_histogram_sync("176611887")  # Glock-18
       print(f"Histogram: {histogram}")
       
       # Test search
       results = client.search_market_sync(
           app_id=753,
           category_753_item_class=["tag_item_class_5"],
           count=10
       )
       print(f"Found {len(results)} listings")
   
   if __name__ == "__main__":
       test_public_api()
   ```

4. **Run and validate**
   ```bash
   python test_aiosteampy_integration.py
   ```

---

### Phase 2: Gradual Migration (Week 3-4)

**Goal:** Replace one module at a time, starting with highest value.

#### Step 1: Replace `market_order.py`

Create `market_order_aiosteampy.py` with async implementation, then update `market_arbitrage.py` to use it optionally.

**Migration approach:**
```python
# In market_arbitrage.py, add parameter:
def apply_workflow(
    *,
    ...,
    use_aiosteampy: bool = False,  # New parameter
    ...
):
    if use_aiosteampy:
        from src.market_order_aiosteampy import load_market_order_data as load_market_order_data_aiosteampy
        market_order_dict = load_market_order_data_aiosteampy(badge_data, verbose=verbose)
    else:
        market_order_dict = load_market_order_data(badge_data, retrieve_market_orders_online=retrieve_market_orders_online, verbose=verbose)
```

#### Step 2: Replace `market_search.py`

Follow same pattern - create new file, add toggle parameter.

#### Step 3: Update main entry points

Update CLI scripts to accept `--use-aiosteampy` flag.

---

### Phase 3: Full Migration (Week 5+)

**Goal:** Convert entire codebase to async and remove `requests` dependency.

1. Convert main scripts to async:
   - `market_arbitrage.py` → `market_arbitrage_async.py`
   - `market_arbitrage_with_foil_cards.py` → async version
   - Update all utility functions

2. Remove `requests` and `beautifulsoup4` dependencies (if all Steam API calls use aiosteampy)

3. Add proper async entry points:
   ```python
   async def main():
       # ... async code
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

4. Update rate limiting to use aiosteampy's built-in mechanisms

---

## Code Reduction Estimates

| File | Current Lines | After Migration | Reduction |
|------|---------------|-----------------|-----------|
| `market_search.py` | 274 | ~80 | ~70% |
| `market_order.py` | 409 | ~120 | ~70% |
| `market_listing.py` | 532 | ~150 | ~72% |
| `inventory_utils.py` | 488 | ~200 | ~59% |
| `cookie_utils.py` | 36 | ~0 | 100% |
| `personal_info.py` | 115 | ~20 | ~83% |
| **Total** | **1,854** | **~570** | **~69%** |

**Estimated total reduction: ~1,284 lines of code** (69% reduction in Steam API interaction code).

---

## Quick Start: Immediate Usage

You can start using aiosteampy **today** for public market data without modifying any existing code:

```python
# test_public_api.py
import asyncio
from aiosteampy.client import SteamPublicClient

async def main():
    client = SteamPublicClient()
    
    # Get market histogram for an item (public data, no auth)
    # Item nameid 176611887 = Glock-18 | Fully Tuned (Field-Tested)
    histogram = await client.market.get_orders_histogram(176611887)
    
    print(f"Buy order graph: {histogram.buy_order_graph}")
    print(f"Sell order graph: {histogram.sell_order_graph}")
    
    # Search for booster packs
    search_results = []
    async for listing in client.market.search(
        app_id=753,
        category_753_item_class=["tag_item_class_5"],  # 5 = Booster Pack
        count=10
    ):
        search_results.append(listing)
        print(f"Found: {listing.hash_name} at {listing.sell_price} cents")
    
    await client.transport.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Run with:
```bash
python test_public_api.py
```

---

## Testing Strategy

1. **Unit tests for new async functions**
2. **Comparison tests**: Run both old and new implementations, compare results
3. **Rate limit validation**: Verify aiosteampy handles rate limits correctly
4. **Error handling**: Test with invalid inputs, network issues

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **API differences** | Medium | High | Test thoroughly, compare outputs |
| **Rate limiting changes** | Low | Medium | Monitor API usage, adjust if needed |
| **Async complexity** | Medium | Medium | Use hybrid approach initially |
| **Breaking changes in aiosteampy** | Low | Medium | Pin version, monitor releases |
| **Session migration issues** | Medium | High | Test auth flow early, have fallback |

---

## Success Criteria

- [ ] Phase 1: aiosteampy installed and basic public API calls working
- [ ] Phase 1: Integration module created and tested
- [ ] Phase 2: `market_order.py` replaced with aiosteampy version
- [ ] Phase 2: All existing tests pass with new implementation
- [ ] Phase 2: Rate limiting behavior validated
- [ ] Phase 3: All market-related modules migrated
- [ ] Phase 3: Full async conversion complete
- [ ] Performance benchmark shows improvement or parity
- [ ] Code reduction targets met (60-70% in API interaction code)

---

## References

- [aiosteampy GitHub](https://github.com/somespecialone/aiosteampy)
- [aiosteampy Documentation](https://aiosteampy.somespecial.one)
- [aiosteampy DeepWiki](https://deepwiki.com/somespecialone/aiosteampy)
- [PyPI: aiosteampy](https://pypi.org/project/aiosteampy/)

---

## Appendix: Current vs aiosteampy API Mapping

| Your Current Function | aiosteampy Equivalent | Notes |
|----------------------|----------------------|-------|
| `get_all_listings()` | `client.market.search()` | Async iterator |
| `download_market_order_data()` | `client.market.get_orders_histogram()` | Direct mapping |
| `get_listing_details()` | `client.market.get_listing()` | Returns typed Listing model |
| `download_steam_inventory()` | `client.inventory.get()` | Returns Inventory model |
| `create_booster_pack()` | Not supported | Steam API limitation |
| `sell_booster_pack()` | `client.market.sell_item()` | Direct mapping |
| Cookie management | `SteamSession.serialize()` / `deserialize()` | Full replacement |
| Rate limiting | Built into client | Per-endpoint configuration |

---

## File Changes Summary

| Action | File | Description |
|--------|------|-------------|
| **Create** | `src/aiosteampy_client.py` | Integration wrapper module |
| **Create** | `test_aiosteampy_integration.py` | Initial test script |
| **Create** | `AIOSTEAMPY_INTEGRATION_PLAN.md` | This document |
| **Modify** | `requirements.txt` | Add `aiosteampy` dependency |
| **Modify** | `market_order.py` | Add aiosteampy alternative (Phase 2) |
| **Modify** | `market_search.py` | Add aiosteampy alternative (Phase 2) |
| **Modify** | `market_listing.py` | Add aiosteampy alternative (Phase 2) |
| **Modify** | `inventory_utils.py` | Add aiosteampy alternative (Phase 2) |
| **Modify** | `market_arbitrage.py` | Add toggle for aiosteampy (Phase 2) |
| **Delete** | `cookie_utils.py` | Obsoleted by SteamSession (Phase 3) |
| **Delete** | `personal_info.py` | Obsoleted by SteamSession (Phase 3) |
