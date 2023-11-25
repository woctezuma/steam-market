# Objective: retrieve i) the item name id of a listing, and ii) whether a *crafted* item would really be marketable.
import ast
import time
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup

from src.json_utils import load_json, save_json
from src.market_search import load_all_listings
from src.personal_info import (
    get_cookie_dict,
    update_and_save_cookie_to_disk_if_values_changed,
)
from src.utils import (
    TIMEOUT_IN_SECONDS,
    get_cushioned_cooldown_in_seconds,
    get_listing_details_output_file_name,
)


def get_steam_market_listing_url(
    app_id: str | None = None,
    listing_hash: str | None = None,
    render_as_json: bool = True,
    replace_spaces: bool = False,
    replace_parenthesis: bool = False,
) -> str:
    if app_id is None:
        # AppID for the Steam Store. It is the same for all the booster packs.
        app_id = "753"

    if listing_hash is None:
        listing_hash = "511540-MoonQuest Booster Pack"

    # Fix listing hashes so that there is no special character '#' or '?', which would mess with URL query later on
    fixed_listing_hash = fix_app_name_for_url_query(listing_hash)

    if replace_spaces:
        # For Markdown compatibility, replaces the spaces from the str to be used in hyperlinks:
        fixed_listing_hash = fixed_listing_hash.replace(" ", "%20")

    if replace_parenthesis:
        # To fix links in PyCharm's display to listings of **foil** cards, which have '(Foil)' at the end of the url
        # ASCII Encoding Reference: https://www.w3schools.com/tags/ref_urlencode.ASP
        fixed_listing_hash = fixed_listing_hash.replace("(", "%28")
        fixed_listing_hash = fixed_listing_hash.replace(")", "%29")

    market_listing_url = (
        f"https://steamcommunity.com/market/listings/{app_id}/{fixed_listing_hash}/"
    )

    if render_as_json:
        market_listing_url += "render/"

    return market_listing_url


def get_listing_parameters() -> dict[str, str]:
    return {"currency": "3"}


def get_steam_api_rate_limits_for_market_listing(
    has_secured_cookie: bool = False,
) -> dict[str, int]:
    # Objective: return the rate limits of Steam API for the market.

    if has_secured_cookie:
        rate_limits = {
            "max_num_queries": 25,
            "cooldown": get_cushioned_cooldown_in_seconds(num_minutes=3),
        }

    else:
        rate_limits = {
            "max_num_queries": 25,
            "cooldown": get_cushioned_cooldown_in_seconds(num_minutes=5),
        }

    return rate_limits


def figure_out_relevant_id(
    asset_dict: dict[str, dict],
    asset_ids: list[str],
    owner_action_name_of_interest: str,
) -> str | None:
    actions = set()
    last_relevant_asset_id = None

    for i in asset_ids:
        for e in asset_dict[i]["owner_actions"]:
            if e["name"] == owner_action_name_of_interest:
                actions.add(e["link"])
                last_relevant_asset_id = i

    has_different_actions = bool(len(set(actions)) > 1)
    if has_different_actions:
        raise AssertionError

    return last_relevant_asset_id


def parse_item_type_no_from_script(last_script: str) -> int | None:
    # Reference: https://gaming.stackexchange.com/a/351941

    start_str = "var g_rgAssets ="
    end_str = "var g_rgListingInfo ="

    asset_ending = ";"
    link_argument_separator = ","

    owner_action_name_of_interest = "Turn into Gems..."
    token_no_of_interest = 3

    try:
        start_index = last_script.index(start_str)
    except ValueError:
        start_index = None

    try:
        end_index = last_script.index(end_str)
    except ValueError:
        end_index = None

    if start_index is not None and end_index is not None:
        assets_raw = last_script[start_index + len(start_str) : end_index]
        assets_stripped = assets_raw.strip().strip(asset_ending)

        try:
            assets = ast.literal_eval(assets_stripped)
        except SyntaxError:
            assets = None

        if assets is None:
            item_type_no = None
        else:
            app_ids = list(assets.keys())
            app_id = app_ids[0]

            context_ids = list(assets[app_id].keys())
            context_id = context_ids[0]

            ids = list(assets[app_id][context_id].keys())
            asset_id = ids[0]

            # There should only be one appID and one contextID.
            if len(app_ids) > 1 or len(context_ids) > 1:
                raise AssertionError

            # There should only be one assetID. However, we can try to run the rest of the code even if there are several.
            if len(ids) > 1:
                asset_dict = assets[app_id][context_id]
                asset_id = figure_out_relevant_id(
                    asset_dict,
                    ids,
                    owner_action_name_of_interest,
                )

            owner_actions = assets[app_id][context_id][asset_id]["owner_actions"]

            # The owner actions should be like:
            #     "owner_actions": [
            #         {
            #             "link": "https://steamcommunity.com/my/gamecards/1017900/?border=1",
            #             "name": "View badge progress"
            #         },
            #         {
            #             "link": "javascript:GetGooValue( '%contextid%', '%assetid%', 1017900, 3, 1 )",
            #             "name": "Turn into Gems..."
            #         }
            #     ]

            actions_of_interest = [
                owner_action
                for owner_action in owner_actions
                if owner_action["name"] == owner_action_name_of_interest
            ]

            links = [owner_action["link"] for owner_action in actions_of_interest]

            javascript_links = [
                link for link in links if link.startswith("javascript:")
            ]

            # There should only be one javascript link.
            if len(javascript_links) > 1:
                raise AssertionError

            try:
                link_of_interest = javascript_links[0]
            except IndexError:
                link_of_interest = ""

            # The link of interest should be like:
            #   "javascript:GetGooValue( '%contextid%', '%assetid%', 1017900, 3, 1 )"
            # where:
            #   - '%contextid%' is a variable containing the context id,
            #   - '%assetid%' is a variable containing the asset id,
            #   - 1017900 is the app id,
            #   - 3 is the item type,
            #   - 1 is the border color.
            tokens = link_of_interest.split(link_argument_separator)

            try:
                item_type_no_as_str = tokens[token_no_of_interest]
            except IndexError:
                item_type_no_as_str = None

            try:
                item_type_no = int(item_type_no_as_str)
            except TypeError:
                item_type_no = None
    else:
        item_type_no = None

    return item_type_no


def parse_marketability_from_script(last_script: str) -> bool | None:
    marketable_key = '"marketable":'

    try:
        is_marketable_index = last_script.index(marketable_key)
    except ValueError:
        is_marketable_index = None

    if is_marketable_index is not None:
        is_marketable_as_str = last_script[is_marketable_index + len(marketable_key)]

        is_marketable = bool(int(is_marketable_as_str) != 0)
    else:
        is_marketable = None

    return is_marketable


def parse_item_name_id_from_script(last_script: str) -> int | None:
    last_script_token = last_script.split("(")[-1]

    item_nameid_str = last_script_token.split(");")[0]

    try:
        item_nameid = int(item_nameid_str)
    except ValueError:
        item_nameid = None

    return item_nameid


def parse_item_name_id(html_doc: str) -> tuple[int | None, bool | None, int | None]:
    soup = BeautifulSoup(html_doc, "html.parser")

    last_script = str(soup.find_all("script")[-1])

    item_nameid = parse_item_name_id_from_script(last_script)

    is_marketable = parse_marketability_from_script(last_script)

    item_type_no = parse_item_type_no_from_script(last_script)

    return item_nameid, is_marketable, item_type_no


def get_listing_details(
    listing_hash: str,
    cookie: dict[str, str] | None = None,
    render_as_json: bool = False,
) -> tuple[dict[str, dict], int]:
    listing_details: dict[str, dict] = {}

    url = get_steam_market_listing_url(
        listing_hash=listing_hash,
        render_as_json=render_as_json,
    )
    req_data = get_listing_parameters()

    if cookie is None:
        cookie = get_cookie_dict()

    has_secured_cookie = bool(len(cookie) > 0)

    if has_secured_cookie:
        resp_data = requests.get(
            url,
            params=req_data,
            cookies=cookie,
            timeout=TIMEOUT_IN_SECONDS,
        )
    else:
        resp_data = requests.get(url, params=req_data, timeout=TIMEOUT_IN_SECONDS)

    if resp_data.ok:
        html_doc = resp_data.text

        if has_secured_cookie:
            jar = dict(resp_data.cookies)
            cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

        item_nameid, is_marketable, item_type_no = parse_item_name_id(html_doc)

        if item_nameid is None:
            print(f"Item name ID not found for {listing_hash}")

        if is_marketable is None:
            print(f"Marketable status not found for {listing_hash}")

        if item_type_no is None:
            print(f"Item type not found for {listing_hash}")

        listing_details[listing_hash] = {}
        listing_details[listing_hash]["item_nameid"] = item_nameid
        listing_details[listing_hash]["is_marketable"] = is_marketable
        listing_details[listing_hash]["item_type_no"] = item_type_no

    status_code = resp_data.status_code
    return listing_details, status_code


def get_listing_details_batch(
    listing_hashes: list[str] | dict[str, dict],
    all_listing_details: dict[str, dict] | None = None,
    save_to_disk: bool = True,
    listing_details_output_file_name: str | None = None,
) -> dict[str, dict]:
    if listing_details_output_file_name is None:
        listing_details_output_file_name = get_listing_details_output_file_name()

    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    rate_limits = get_steam_api_rate_limits_for_market_listing(has_secured_cookie)

    if all_listing_details is None:
        all_listing_details = {}

    num_listings = len(listing_hashes)

    query_count = 0

    for count, listing_hash in enumerate(listing_hashes):
        if count + 1 % 100 == 0:
            print(f"[{count + 1}/{num_listings}]")

        listing_details, status_code = get_listing_details(
            listing_hash=listing_hash,
            cookie=cookie,
        )

        query_count += 1

        if status_code != HTTPStatus.OK:
            print(
                f"Wrong status code ({status_code}) for {listing_hash} after {query_count} queries.",
            )
            break

        if query_count >= rate_limits["max_num_queries"]:
            if save_to_disk:
                save_json(all_listing_details, listing_details_output_file_name)

            cooldown_duration = rate_limits["cooldown"]
            print(
                f"Number of queries {query_count} reached. Cooldown: {cooldown_duration} seconds",
            )
            time.sleep(cooldown_duration)
            query_count = 0

        all_listing_details.update(listing_details)

    if save_to_disk:
        save_json(all_listing_details, listing_details_output_file_name)

    return all_listing_details


def update_all_listing_details(
    listing_hashes: list[str] | dict[str, dict] | None = None,
    listing_details_output_file_name: str | None = None,
) -> dict[str, dict]:
    # Caveat: this is mostly useful if download_all_listing_details() failed in the middle of the process, and you want
    # to restart the process without risking losing anything, in case the process fails again.

    if listing_details_output_file_name is None:
        listing_details_output_file_name = get_listing_details_output_file_name()

    try:
        all_listing_details = load_json(listing_details_output_file_name)
        print(f"Loading {len(all_listing_details)} listing details from disk.")
    except FileNotFoundError:
        print("Downloading listing details from scratch.")
        all_listing_details = None

    if listing_hashes is None:
        all_listings = load_all_listings()
        listing_hashes = list(all_listings.keys())

    return get_listing_details_batch(
        listing_hashes,
        all_listing_details,
        save_to_disk=True,
        listing_details_output_file_name=listing_details_output_file_name,
    )


def load_all_listing_details(
    listing_details_output_file_name: str | None = None,
) -> dict[str, dict]:
    if listing_details_output_file_name is None:
        listing_details_output_file_name = get_listing_details_output_file_name()

    return load_json(listing_details_output_file_name)


def fix_app_name_for_url_query(app_name: str) -> str:
    app_name = app_name.replace("#", "%23")
    app_name = app_name.replace("?", "%3F")
    app_name = app_name.replace("%", "%25")
    return app_name.replace(":", "%3A")


def get_item_nameid(
    listing_hash: str,
    listing_details_output_file_name: str | None = None,
) -> str:
    if listing_details_output_file_name is None:
        listing_details_output_file_name = get_listing_details_output_file_name()

    try:
        listing_details = load_json(listing_details_output_file_name)

        item_nameid = listing_details[listing_hash]["item_nameid"]
    except (FileNotFoundError, KeyError):
        listing_details = update_all_listing_details(
            listing_hashes=[listing_hash],
            listing_details_output_file_name=listing_details_output_file_name,
        )
        item_nameid = listing_details[listing_hash]["item_nameid"]

    return item_nameid


def get_item_nameid_batch(
    listing_hashes: list[str] | dict[str, dict],
    listing_details_output_file_name: str | None = None,
    listing_hashes_to_forcefully_process: list[str] | None = None,
) -> dict[str, dict]:
    if listing_hashes_to_forcefully_process is None:
        listing_hashes_to_forcefully_process = []

    if listing_details_output_file_name is None:
        listing_details_output_file_name = get_listing_details_output_file_name()

    try:
        listing_details = load_json(listing_details_output_file_name)

        item_nameids: dict[str, dict] = {}
        listing_hashes_to_process = []
        for listing_hash in listing_hashes:
            item_nameids[listing_hash] = {}
            try:
                item_nameid = listing_details[listing_hash]["item_nameid"]
                is_marketable = listing_details[listing_hash]["is_marketable"]

                item_nameids[listing_hash]["item_nameid"] = item_nameid
                item_nameids[listing_hash]["is_marketable"] = is_marketable
            except KeyError:
                listing_hashes_to_process.append(listing_hash)

        listing_hashes_to_process += listing_hashes_to_forcefully_process
        listing_hashes_to_process = list(set(listing_hashes_to_process))

        if listing_hashes_to_process:
            listing_details = update_all_listing_details(
                listing_hashes=listing_hashes_to_process.copy(),
                listing_details_output_file_name=listing_details_output_file_name,
            )

            for listing_hash in listing_hashes_to_process:
                if listing_hash not in item_nameids:
                    # This happens if the listing hash is:
                    # - fed through 'listing_hashes_to_forcefully_process'
                    # - yet not fed through 'listing_hashes'
                    item_nameids[listing_hash] = {}

                item_nameid = listing_details[listing_hash]["item_nameid"]
                is_marketable = listing_details[listing_hash]["is_marketable"]

                item_nameids[listing_hash]["item_nameid"] = item_nameid
                item_nameids[listing_hash]["is_marketable"] = is_marketable

    except FileNotFoundError:
        listing_details = update_all_listing_details(
            listing_hashes=listing_hashes,
            listing_details_output_file_name=listing_details_output_file_name,
        )

        item_nameids = {}
        for listing_hash in listing_hashes:
            item_nameids[listing_hash] = {}

            item_nameid = listing_details[listing_hash]["item_nameid"]
            is_marketable = listing_details[listing_hash]["is_marketable"]

            item_nameids[listing_hash]["item_nameid"] = item_nameid
            item_nameids[listing_hash]["is_marketable"] = is_marketable

    return item_nameids


def update_marketability_status(
    few_selected_listing_hashes: list[str],
) -> dict[str, dict]:
    return get_item_nameid_batch(
        listing_hashes=[],
        listing_hashes_to_forcefully_process=few_selected_listing_hashes,
    )


def main() -> bool:
    listing_hashes = [
        "268830-Doctor Who%3A The Adventure Games Booster Pack",
        "290970-1849 Booster Pack",
        "753-Sack of Gems",
        "511540-MoonQuest Booster Pack",
        # The item name ID will not be retrieved for the following two listing hashes due to special characters:
        "614910-#monstercakes Booster Pack",
        "505730-Holy Potatoes! We’re in Space?! Booster Pack",
        # This fixes the aforementioned issue:
        "614910-%23monstercakes Booster Pack",
        "505730-Holy Potatoes! We’re in Space%3F! Booster Pack",
    ]

    update_all_listing_details(listing_hashes)

    return True


if __name__ == "__main__":
    main()
