# Objective: retrieve the ask and bid for Booster Packs.

import time
from contextlib import suppress
from datetime import timedelta
from http import HTTPStatus

import requests
from requests.exceptions import ConnectionError, ReadTimeout

from src.cookie_utils import force_update_sessionid
from src.creation_time_utils import get_current_time, to_timestamp
from src.json_utils import load_json, save_json
from src.market_listing import get_item_nameid, get_item_nameid_batch
from src.personal_info import (
    get_cookie_dict,
    update_and_save_cookie_to_disk_if_values_changed,
)
from src.utils import (
    TIMEOUT_IN_SECONDS,
    get_cushioned_cooldown_in_seconds,
    get_market_order_file_name,
)

INTER_REQUEST_COOLDOWN_FIELD = "cooldown_between_each_request"

UPDATE_COOLDOWN_FIELD = "update_timestamp"
UPDATE_COOLDOWN_IN_HOURS = 72


def get_steam_market_order_url() -> str:
    return "https://steamcommunity.com/market/itemordershistogram"


def get_market_order_parameters(item_nameid: str) -> dict[str, str]:
    params = {}

    params["country"] = "FR"
    params["language"] = "english"
    params["currency"] = "3"
    params["item_nameid"] = item_nameid
    params["two_factor"] = "0"

    return params


def get_steam_api_rate_limits_for_market_order(
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

    rate_limits[INTER_REQUEST_COOLDOWN_FIELD] = 0

    return rate_limits


def get_market_order_headers() -> dict[str, str]:
    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "Host": "steamcommunity.com",
        "If-Modified-Since": "Tue, 01 Nov 2022 00:00:00 GMT",
        "Referer": "https://steamcommunity.com/market/listings/753/753-Sack%20of%20Gems",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
        "X-Requested-With": "XMLHttpRequest",
    }


def download_market_order_data(
    listing_hash: str,
    item_nameid: str | None = None,
    verbose: bool = False,
    listing_details_output_file_name: str | None = None,
) -> tuple[float, float, int, int]:
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    if item_nameid is None:
        item_nameid = get_item_nameid(
            listing_hash,
            listing_details_output_file_name=listing_details_output_file_name,
        )

    if item_nameid is not None:
        url = get_steam_market_order_url()
        req_data = get_market_order_parameters(item_nameid=item_nameid)

        try:
            if has_secured_cookie:
                resp_data = requests.get(
                    url,
                    params=req_data,
                    cookies=cookie,
                    headers=get_market_order_headers(),
                    timeout=TIMEOUT_IN_SECONDS,
                )
            else:
                resp_data = requests.get(
                    url,
                    params=req_data,
                    headers=get_market_order_headers(),
                    timeout=TIMEOUT_IN_SECONDS,
                )
        except ReadTimeout:
            print(f"[WARNING] Request timeout for {listing_hash}.")
            resp_data = None
        except ConnectionError:
            resp_data = None

    else:
        print(
            f"No query to download market orders for {listing_hash}, because item name ID is unknown.",
        )

        resp_data = None

    if resp_data and resp_data.ok:
        result = resp_data.json()

        if has_secured_cookie:
            jar = dict(resp_data.cookies)
            cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

        try:
            buy_order_graph = result["buy_order_graph"]

            try:
                # highest_buy_order
                bid_info = buy_order_graph[0]
                bid_price = bid_info[0]
                bid_volume = bid_info[1]
            except IndexError:
                bid_price = -1
                bid_volume = -1
        except KeyError:
            bid_price = -1
            bid_volume = -1

        try:
            sell_order_graph = result["sell_order_graph"]

            try:
                # lowest_sell_order
                ask_info = sell_order_graph[0]
                ask_price = ask_info[0]
                ask_volume = ask_info[1]
            except IndexError:
                ask_price = -1
                ask_volume = -1
        except KeyError:
            ask_price = -1
            ask_volume = -1

    else:
        if resp_data is not None:
            status_code = resp_data.status_code
            error_reason = resp_data.reason
            if verbose:
                print(f"Wrong status code ({status_code}): {error_reason}.")
            if status_code == HTTPStatus.TOO_MANY_REQUESTS:
                print(
                    "You have been rate-limited. Wait for a while and double-check rate-limits before trying again.",
                )
                raise AssertionError

        bid_price = -1
        bid_volume = -1
        ask_price = -1
        ask_volume = -1

    if verbose:
        print(
            f"Listing: {listing_hash} ; item id: {item_nameid} ; ask: {ask_price:.2f}€ ({ask_volume}) ; bid: {bid_price:.2f}€ ({bid_volume})",
        )

    return bid_price, ask_price, bid_volume, ask_volume


def is_dummy_market_order_data(
    market_order_data: dict[str, float | int | bool],
) -> bool:
    bid_price = market_order_data["bid"]
    ask_price = market_order_data["ask"]
    bid_volume = market_order_data["bid_volume"]
    ask_volume = market_order_data["ask_volume"]

    return bid_price < 0 and ask_price < 0 and bid_volume < 0 and ask_volume < 0


def has_a_recent_timestamp(
    market_order_data: dict[str, float | int | bool],
    threshold_timestamp: int,
) -> bool:
    last_update_timestamp = market_order_data[UPDATE_COOLDOWN_FIELD]

    return threshold_timestamp < last_update_timestamp


def download_market_order_data_batch(
    badge_data: dict[str, dict],
    market_order_dict: dict[str, dict] | None = None,
    verbose: bool = False,
    save_to_disk: bool = True,
    market_order_output_file_name: str | None = None,
    listing_details_output_file_name: str | None = None,
    enforce_cooldown: bool = True,
    allow_to_skip_dummy_data: bool = False,
) -> dict[str, dict]:
    if market_order_output_file_name is None:
        market_order_output_file_name = get_market_order_file_name()

    # Pre-retrieval of item name ids

    listing_hashes = [badge_data[app_id]["listing_hash"] for app_id in badge_data]

    item_nameids = get_item_nameid_batch(
        listing_hashes,
        listing_details_output_file_name=listing_details_output_file_name,
    )

    # Retrieval of market orders (bid, ask)

    cookie = get_cookie_dict()
    cookie = force_update_sessionid(cookie)
    has_secured_cookie = bool(len(cookie) > 0)

    rate_limits = get_steam_api_rate_limits_for_market_order(has_secured_cookie)

    if market_order_dict is None:
        market_order_dict = {}

    query_count = 0

    current_time = get_current_time()
    update_timestamp = to_timestamp(current_time)
    threshold_timestamp = to_timestamp(
        current_time - timedelta(hours=UPDATE_COOLDOWN_IN_HOURS),
    )

    for app_id in badge_data:
        listing_hash = badge_data[app_id]["listing_hash"]

        with suppress(KeyError):
            last_update_timestamp = market_order_dict[listing_hash][
                UPDATE_COOLDOWN_FIELD
            ]
            if (
                enforce_cooldown
                and has_a_recent_timestamp(
                    market_order_dict[listing_hash],
                    threshold_timestamp,
                )
                and (
                    allow_to_skip_dummy_data
                    or not is_dummy_market_order_data(market_order_dict[listing_hash])
                )
            ):
                if verbose:
                    print(
                        f"Skipping download of orders for {listing_hash} (last updated: {last_update_timestamp}).",
                    )
                continue

        bid_price, ask_price, bid_volume, ask_volume = download_market_order_data(
            listing_hash,
            verbose=verbose,
            listing_details_output_file_name=listing_details_output_file_name,
        )

        market_order_dict[listing_hash] = {}
        market_order_dict[listing_hash]["bid"] = bid_price
        market_order_dict[listing_hash]["ask"] = ask_price
        market_order_dict[listing_hash]["bid_volume"] = bid_volume
        market_order_dict[listing_hash]["ask_volume"] = ask_volume
        market_order_dict[listing_hash]["is_marketable"] = item_nameids[listing_hash][
            "is_marketable"
        ]
        market_order_dict[listing_hash][UPDATE_COOLDOWN_FIELD] = update_timestamp

        if query_count >= rate_limits["max_num_queries"]:
            if save_to_disk:
                save_json(market_order_dict, market_order_output_file_name)

            cooldown_duration = rate_limits["cooldown"]
            print(
                f"Number of queries {query_count} reached. Cooldown: {cooldown_duration} seconds",
            )
            time.sleep(cooldown_duration)
            query_count = 0

        time.sleep(rate_limits[INTER_REQUEST_COOLDOWN_FIELD])
        query_count += 1

    if save_to_disk:
        save_json(market_order_dict, market_order_output_file_name)

    return market_order_dict


def load_market_order_data(
    badge_data: dict[str, dict],
    trim_output: bool = False,
    retrieve_market_orders_online: bool = True,
    verbose: bool = False,
) -> dict[str, dict]:
    market_order_dict = load_market_order_data_from_disk()

    if retrieve_market_orders_online:
        market_order_dict = download_market_order_data_batch(
            badge_data,
            save_to_disk=True,
            market_order_dict=market_order_dict,
            verbose=verbose,
        )

    if trim_output:
        trimmed_market_order_dict, app_ids_with_missing_data = trim_market_order_data(
            badge_data,
            market_order_dict,
        )

        if retrieve_market_orders_online and app_ids_with_missing_data:
            raise AssertionError

    else:
        trimmed_market_order_dict = market_order_dict

    return trimmed_market_order_dict


def trim_market_order_data(
    badge_data: dict[str, dict],
    market_order_dict: dict[str, dict],
) -> tuple[dict[str, dict], list[str]]:
    trimmed_market_order_dict: dict[str, dict] = {}
    app_ids_with_missing_data = []

    for app_id in badge_data:
        listing_hash = badge_data[app_id]["listing_hash"]

        try:
            market_data = market_order_dict[listing_hash]
        except KeyError:
            print(
                f"[{listing_hash}] Market order data is not available offline. Allow downloading it!",
            )
            app_ids_with_missing_data.append(app_id)
            continue

        trimmed_market_order_dict[listing_hash] = {}
        trimmed_market_order_dict[listing_hash] = market_data

    print()

    return trimmed_market_order_dict, app_ids_with_missing_data


def load_market_order_data_from_disk(
    market_order_output_file_name: str | None = None,
) -> dict[str, dict]:
    if market_order_output_file_name is None:
        market_order_output_file_name = get_market_order_file_name()

    try:
        market_order_dict = load_json(market_order_output_file_name)
    except FileNotFoundError:
        market_order_dict = {}

    return market_order_dict


def main() -> bool:
    listing_hash = "290970-1849 Booster Pack"

    # Download based on a listing hash

    bid_price, ask_price, bid_volume, ask_volume = download_market_order_data(
        listing_hash,
        verbose=True,
    )

    # Download based on badge data

    app_id = listing_hash.split("-", maxsplit=1)[0]

    badge_data: dict[str, dict] = {}
    badge_data[app_id] = {}
    badge_data[app_id]["listing_hash"] = listing_hash

    download_market_order_data_batch(
        badge_data,
        save_to_disk=False,
        verbose=True,
    )

    # Test listing hashes with special characters

    listing_hashes = [
        # The item name ID will not be retrieved for the following two listhing hashes due to special characters:
        "614910-#monstercakes Booster Pack",
        "505730-Holy Potatoes! We’re in Space?! Booster Pack",
        # This fixes the aforementioned issue:
        "614910-%23monstercakes Booster Pack",
        "505730-Holy Potatoes! We’re in Space%3F! Booster Pack",
    ]
    for listing_hash_to_test in listing_hashes:
        bid_price, ask_price, bid_volume, ask_volume = download_market_order_data(
            listing_hash_to_test,
            verbose=True,
        )

    return True


if __name__ == "__main__":
    main()
