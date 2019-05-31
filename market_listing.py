# Objective: retrieve i) the item name id of a listing, and ii) whether a *crafted* item would really be marketable.

import json
import time

import requests
from bs4 import BeautifulSoup

from market_search import load_all_listings
from personal_info import get_steam_cookie, get_cookie_dict
from utils import get_listing_details_output_file_name


def get_steam_market_listing_url(app_id=None, listing_hash=None, render_as_json=True):
    if app_id is None:
        # AppID for the Steam Store. It is the same for all the booster packs.
        app_id = 753

    if listing_hash is None:
        listing_hash = '511540-MoonQuest Booster Pack'

    # Fix listing hashes so that there is no special character '#' or '?', which would mess with URL query later on
    fixed_listing_hash = fix_app_name_for_url_query(listing_hash)

    market_listing_url = 'https://steamcommunity.com/market/listings/' + str(app_id) + '/' + fixed_listing_hash + '/'

    if render_as_json:
        market_listing_url += 'render/'

    return market_listing_url


def get_listing_parameters():
    params = dict()

    params['currency'] = '3'

    return params


def get_steam_api_rate_limits_for_market_listing(has_secured_cookie=False):
    # Objective: return the rate limits of Steam API for the market.

    if has_secured_cookie:

        rate_limits = {
            'max_num_queries': 25,
            'cooldown': (3 * 60) + 10,  # 1 minute plus a cushion
        }

    else:

        rate_limits = {
            'max_num_queries': 25,
            'cooldown': (5 * 60) + 10,  # 5 minutes plus a cushion
        }

    return rate_limits


def parse_item_name_id(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')

    last_script = str(soup.find_all('script')[-1])

    last_script_token = last_script.split('(')[-1]

    item_nameid_str = last_script_token.split(');')[0]

    try:
        item_nameid = int(item_nameid_str)
    except ValueError:
        item_nameid = None

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

    return item_nameid, is_marketable


def get_listing_details(listing_hash=None, cookie_value=None, render_as_json=False):
    listing_details = dict()

    url = get_steam_market_listing_url(listing_hash=listing_hash, render_as_json=render_as_json)
    req_data = get_listing_parameters()

    has_secured_cookie = bool(cookie_value is not None)

    if has_secured_cookie:
        cookie = get_cookie_dict(cookie_value)
        resp_data = requests.get(url, params=req_data, cookies=cookie)
    else:
        resp_data = requests.get(url, params=req_data)

    status_code = resp_data.status_code

    if status_code == 200:
        html_doc = resp_data.text

        item_nameid, is_marketable = parse_item_name_id(html_doc)

        if item_nameid is None:
            print('Item name ID not found for {}'.format(listing_hash))

        if is_marketable is None:
            print('Marketable status not found for {}'.format(listing_hash))

        listing_details[listing_hash] = dict()
        listing_details[listing_hash]['item_nameid'] = item_nameid
        listing_details[listing_hash]['is_marketable'] = is_marketable

    return listing_details, status_code


def get_listing_details_batch(listing_hashes, all_listing_details=None, save_to_disk=True):
    cookie_value = get_steam_cookie()
    has_secured_cookie = bool(cookie_value is not None)

    rate_limits = get_steam_api_rate_limits_for_market_listing(has_secured_cookie)

    if all_listing_details is None:
        all_listing_details = dict()

    num_listings = len(listing_hashes)

    query_count = 0

    for count, listing_hash in enumerate(listing_hashes):

        if count + 1 % 100 == 0:
            print('[{}/{}]'.format(count + 1, num_listings))

        listing_details, status_code = get_listing_details(listing_hash=listing_hash, cookie_value=cookie_value)

        query_count += 1

        if status_code != 200:
            print('Wrong status code ({}) for {} after {} queries.'.format(status_code, listing_hash, query_count))
            break

        if query_count >= rate_limits['max_num_queries']:
            if save_to_disk:
                with open(get_listing_details_output_file_name(), 'w') as f:
                    json.dump(all_listing_details, f)

            cooldown_duration = rate_limits['cooldown']
            print('Number of queries {} reached. Cooldown: {} seconds'.format(query_count, cooldown_duration))
            time.sleep(cooldown_duration)
            query_count = 0

        all_listing_details.update(listing_details)

    if save_to_disk:
        with open(get_listing_details_output_file_name(), 'w') as f:
            json.dump(all_listing_details, f)

    return all_listing_details


def update_all_listing_details(listing_hashes=None):
    # Caveat: this is mostly useful if download_all_listing_details() failed in the middle of the process, and you want
    # to restart the process without risking to lose anything, in case the process fails again.

    try:
        with open(get_listing_details_output_file_name(), 'r') as f:
            all_listing_details = json.load(f)
            print('Loading {} listing details from disk.'.format(len(all_listing_details)))
    except FileNotFoundError:
        print('Downloading listing details from scratch.')
        all_listing_details = None

    if listing_hashes is None:
        all_listings = load_all_listings()
        listing_hashes = list(all_listings.keys())

    all_listing_details = get_listing_details_batch(listing_hashes, all_listing_details, save_to_disk=True)

    return all_listing_details


def load_all_listing_details():
    with open(get_listing_details_output_file_name(), 'r') as f:
        all_listing_details = json.load(f)

    return all_listing_details


def fix_app_name_for_url_query(app_name):
    app_name = app_name.replace('#', '%23')
    app_name = app_name.replace('?', '%3F')
    app_name = app_name.replace('%', '%25')

    return app_name


def main():
    listing_hashes = [
        '268830-Doctor Who%3A The Adventure Games Booster Pack',
        '290970-1849 Booster Pack',
        '753-Sack of Gems',
        '511540-MoonQuest Booster Pack',
        # The item name ID will not be retrieved for the following two listing hashes due to special characters:
        '614910-#monstercakes Booster Pack',
        '505730-Holy Potatoes! We’re in Space?! Booster Pack',
        # This fixes the aforementioned issue:
        '614910-%23monstercakes Booster Pack',
        '505730-Holy Potatoes! We’re in Space%3F! Booster Pack',
    ]

    listing_details = update_all_listing_details(listing_hashes)

    return True


def get_item_nameid(listing_hash):
    try:
        with open(get_listing_details_output_file_name(), 'r') as f:
            listing_details = json.load(f)

        item_nameid = listing_details[listing_hash]['item_nameid']
    except (FileNotFoundError, KeyError):
        listing_details = update_all_listing_details(listing_hashes=[listing_hash])
        item_nameid = listing_details[listing_hash]['item_nameid']

    return item_nameid


def get_item_nameid_batch(listing_hashes):
    try:
        with open(get_listing_details_output_file_name(), 'r') as f:
            listing_details = json.load(f)

        item_nameids = dict()
        listing_hashes_to_process = []
        for listing_hash in listing_hashes:
            item_nameids[listing_hash] = dict()
            try:
                item_nameid = listing_details[listing_hash]['item_nameid']
                is_marketable = listing_details[listing_hash]['is_marketable']

                item_nameids[listing_hash]['item_nameid'] = item_nameid
                item_nameids[listing_hash]['is_marketable'] = is_marketable
            except KeyError:
                listing_hashes_to_process.append(listing_hash)

        if len(listing_hashes_to_process) > 0:
            listing_details = update_all_listing_details(listing_hashes=listing_hashes_to_process)

            for listing_hash in listing_hashes_to_process:
                item_nameid = listing_details[listing_hash]['item_nameid']
                is_marketable = listing_details[listing_hash]['is_marketable']

                item_nameids[listing_hash]['item_nameid'] = item_nameid
                item_nameids[listing_hash]['is_marketable'] = is_marketable

    except FileNotFoundError:
        listing_details = update_all_listing_details(listing_hashes=listing_hashes)

        item_nameids = dict()
        for listing_hash in listing_hashes:
            item_nameids[listing_hash] = dict()

            item_nameid = listing_details[listing_hash]['item_nameid']
            is_marketable = listing_details[listing_hash]['is_marketable']

            item_nameids[listing_hash]['item_nameid'] = item_nameid
            item_nameids[listing_hash]['is_marketable'] = is_marketable

    return item_nameids


if __name__ == '__main__':
    main()
