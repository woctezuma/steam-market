# Objective: retrieve all the listings of 'Booster Packs' on the Steam Market,
#            along with the sell price, and the volume available at this price.

import time
from pathlib import Path

import requests
from requests.exceptions import ConnectionError

from src.json_utils import load_json, save_json
from src.personal_info import (
    get_cookie_dict,
    update_and_save_cookie_to_disk_if_values_changed,
)
from src.utils import (
    TIMEOUT_IN_SECONDS,
    get_cushioned_cooldown_in_seconds,
    get_listing_output_file_name,
)


def get_steam_market_search_url() -> str:
    return "https://steamcommunity.com/market/search/render/"


def get_tag_item_class_no_for_trading_cards() -> int:
    return 2


def get_tag_item_class_no_for_profile_backgrounds() -> int:
    return 3


def get_tag_item_class_no_for_emoticons() -> int:
    return 4


def get_tag_item_class_no_for_booster_packs() -> int:
    return 5


def get_tag_drop_rate_str(rarity: str | None = None) -> str:
    if rarity is None:
        rarity = "common"

    if rarity == "extraordinary":
        tag_drop_rate_no = 3
    elif rarity == "rare":
        tag_drop_rate_no = 2
    elif rarity == "uncommon":
        tag_drop_rate_no = 1
    else:
        # Rarity: Common
        tag_drop_rate_no = 0

    return f"tag_droprate_{tag_drop_rate_no}"


def get_search_parameters(
    start_index: int = 0,
    delta_index: int = 100,
    tag_item_class_no: int | None = None,
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
    is_foil_trading_card: bool = True,
) -> dict[str, str]:
    if tag_drop_rate_str is None:
        tag_drop_rate_str = get_tag_drop_rate_str(rarity=rarity)

    if tag_item_class_no is None:
        # Typically, one of the following numbers:
        # 2: Trading Card
        # 3: Profile Background
        # 4: Emoticon
        # 5: Booster Pack
        tag_item_class_no = get_tag_item_class_no_for_booster_packs()

    # Sort by name to ensure that the download of listings is not affected by people buying/selling during the process.
    # Otherwise, it would be possible to sort columns by 'price' instead of by 'name',
    #                                 and in 'desc'-ending order rather than in 'asc'-ending order.
    column_to_sort_by = "name"
    sort_direction = "asc"

    params = {}

    params["norender"] = "1"
    params["category_753_Game[]"] = "any"
    params["category_753_droprate[]"] = tag_drop_rate_str
    params["category_753_item_class[]"] = f"tag_item_class_{tag_item_class_no}"
    params["appid"] = "753"
    params["sort_column"] = column_to_sort_by
    params["sort_dir"] = sort_direction
    params["start"] = str(start_index)
    params["count"] = str(delta_index)

    if tag_item_class_no == get_tag_item_class_no_for_trading_cards():
        if is_foil_trading_card:
            params["category_753_cardborder[]"] = "tag_cardborder_1"
        else:
            params["category_753_cardborder[]"] = "tag_cardborder_0"

    return params


def get_steam_api_rate_limits_for_market_search(
    has_secured_cookie: bool = False,
) -> dict[str, int]:
    # Objective: return the rate limits of Steam API for the market.

    if has_secured_cookie:
        rate_limits = {
            "max_num_queries": 50,
            "cooldown": get_cushioned_cooldown_in_seconds(num_minutes=1),
        }

    else:
        rate_limits = {
            "max_num_queries": 25,
            "cooldown": get_cushioned_cooldown_in_seconds(num_minutes=5),
        }

    return rate_limits


def get_all_listings(
    all_listings: dict[str, dict] | None = None,
    url: str | None = None,
    tag_item_class_no: int | None = None,
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
    start_index: int = 0,
    listing_output_file_name: str | None = None,
) -> dict[str, dict]:
    if url is None:
        url = get_steam_market_search_url()

    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    rate_limits = get_steam_api_rate_limits_for_market_search(has_secured_cookie)

    if all_listings is None:
        all_listings = {}

    num_listings = None

    query_count = 0
    delta_index = 100

    while (num_listings is None) or (start_index < num_listings):
        if num_listings is not None:
            print(f"[{start_index}/{num_listings}]")

        req_data = get_search_parameters(
            start_index=start_index,
            delta_index=delta_index,
            tag_item_class_no=tag_item_class_no,
            tag_drop_rate_str=tag_drop_rate_str,
            rarity=rarity,
        )

        if query_count >= rate_limits["max_num_queries"]:
            if listing_output_file_name:
                print(f"Saving temporary data to {listing_output_file_name}.")
                save_json(all_listings, listing_output_file_name)

            cooldown_duration = rate_limits["cooldown"]
            print(
                f"Number of queries {query_count} reached. Cooldown: {cooldown_duration} seconds",
            )
            time.sleep(cooldown_duration)
            query_count = 0

        try:
            if has_secured_cookie:
                resp_data = requests.get(
                    url,
                    params=req_data,
                    cookies=cookie,
                    timeout=TIMEOUT_IN_SECONDS,
                )
            else:
                resp_data = requests.get(
                    url,
                    params=req_data,
                    timeout=TIMEOUT_IN_SECONDS,
                )
        except ConnectionError:
            resp_data = None

        start_index += delta_index
        query_count += 1

        if resp_data and resp_data.ok:
            result = resp_data.json()

            if has_secured_cookie:
                jar = dict(resp_data.cookies)
                cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

            num_listings_based_on_latest_query = result["total_count"]

            if num_listings_based_on_latest_query is None:
                num_listings_based_on_latest_query = num_listings

            if num_listings is not None:
                num_listings = max(num_listings, num_listings_based_on_latest_query)
            else:
                num_listings = num_listings_based_on_latest_query

            listings: dict[str, dict] = {}
            for listing in result["results"]:
                listing_hash = listing["hash_name"]

                listings[listing_hash] = {}
                listings[listing_hash]["sell_listings"] = listing["sell_listings"]
                listings[listing_hash]["sell_price"] = listing["sell_price"]
                listings[listing_hash]["sell_price_text"] = listing["sell_price_text"]

        else:
            status_code = resp_data.status_code if resp_data else None
            print(
                f"Wrong status code ({status_code}) for start_index = {start_index} after {query_count} queries.",
            )
            if status_code is None:
                continue

            break

        all_listings.update(listings)

    return all_listings


def download_all_listings(
    listing_output_file_name: str | None = None,
    url: str | None = None,
    tag_item_class_no: int | None = None,
    start_index: int = 0,
) -> bool:
    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name()

    if not Path(listing_output_file_name).exists():
        all_listings = get_all_listings(
            url=url,
            tag_item_class_no=tag_item_class_no,
            start_index=start_index,
        )

        save_json(all_listings, listing_output_file_name)

    return True


def update_all_listings(
    listing_output_file_name: str | None = None,
    url: str | None = None,
    tag_item_class_no: int | None = None,
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
    start_index: int = 0,
) -> bool:
    # Caveat: this is mostly useful if download_all_listings() failed in the middle of the process, and you want to
    # restart the process without risking losing anything, in case the process fails again.

    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name()

    try:
        all_listings = load_all_listings(
            listing_output_file_name=listing_output_file_name,
        )
        print(f"Loading {len(all_listings)} listings from disk.")
    except FileNotFoundError:
        print("Downloading listings from scratch.")
        all_listings = None

    all_listings = get_all_listings(
        all_listings,
        url=url,
        tag_item_class_no=tag_item_class_no,
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity,
        start_index=start_index,
        listing_output_file_name=listing_output_file_name,
    )

    save_json(all_listings, listing_output_file_name)

    return True


def load_all_listings(listing_output_file_name: str | None = None) -> dict[str, dict]:
    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name()

    try:
        all_listings = load_json(listing_output_file_name)
    except FileNotFoundError:
        print(
            f"File {listing_output_file_name} not found. Initializing listings with an empty dictionary.",
        )
        all_listings = {}

    return all_listings


if __name__ == "__main__":
    update_all_listings()
