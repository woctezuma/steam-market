import json
import time

import requests

from market_listing import get_steam_api_rate_limits_for_market_listing
from personal_info import get_steam_cookie, get_cookie_dict
from utils import get_market_order_file_name


def get_steam_market_order_url():
    steam_market_order_url = 'https://steamcommunity.com/market/itemordershistogram'

    return steam_market_order_url


def get_market_order_parameters(item_nameid):
    params = dict()

    params['country'] = 'FR'
    params['language'] = 'english'
    params['currency'] = '3'
    params['item_nameid'] = str(item_nameid)
    params['two_factor'] = '0'

    return params


def get_item_nameid(listing_hash):
    item_nameid = 28419077  # TODO

    return item_nameid


def download_market_order_data(listing_hash, item_nameid=None, verbose=False):
    cookie_value = get_steam_cookie()
    has_secured_cookie = bool(cookie_value is not None)

    if item_nameid is None:
        item_nameid = get_item_nameid(listing_hash)

    url = get_steam_market_order_url()
    req_data = get_market_order_parameters(item_nameid=item_nameid)

    if has_secured_cookie:
        cookie = get_cookie_dict(cookie_value)
        resp_data = requests.get(url, params=req_data, cookies=cookie)
    else:
        resp_data = requests.get(url, params=req_data)

    status_code = resp_data.status_code

    if status_code == 200:
        result = resp_data.json()

        try:
            # highest_buy_order
            bid_price = result['buy_order_graph'][0][0]
        except KeyError or IndexError:
            bid_price = -1

        try:
            # lowest_sell_order
            ask_price = result['sell_order_graph'][0][0]
        except KeyError or IndexError:
            ask_price = -1

    else:
        bid_price = -1
        ask_price = -1

    if verbose:
        print('Listing: {} ; item id: {} ; ask: {}€ ; bid: {}€'.format(listing_hash, item_nameid, ask_price, bid_price))

    return bid_price, ask_price


def download_market_order_data_batch(badge_data, market_order_dict=None):
    cookie_value = get_steam_cookie()
    has_secured_cookie = bool(cookie_value is not None)

    rate_limits = get_steam_api_rate_limits_for_market_listing(has_secured_cookie)

    if market_order_dict is None:
        market_order_dict = dict()

    query_count = 0

    for app_id in badge_data.keys():
        listing_hash = badge_data[app_id]['listing_hash']
        bid_price, ask_price = download_market_order_data(listing_hash)

        market_order_dict[app_id]['bid'] = bid_price
        market_order_dict[app_id]['ask'] = ask_price

        if query_count >= rate_limits['max_num_queries']:
            cooldown_duration = rate_limits['cooldown']
            print('Number of queries {} reached. Cooldown: {} seconds'.format(query_count, cooldown_duration))
            time.sleep(cooldown_duration)
            query_count = 0

        query_count += 1

    with open(get_market_order_file_name(), 'w') as f:
        json.dump(market_order_dict, f)

    return market_order_dict


def update_market_order_data_batch(badge_data):
    market_order_dict = load_market_order_data()

    market_order_dict = download_market_order_data_batch(badge_data,
                                                         market_order_dict=market_order_dict)

    return market_order_dict


def load_market_order_data():
    try:
        with open(get_market_order_file_name(), 'r') as f:
            market_order_dict = json.load(f)
    except FileNotFoundError:
        market_order_dict = None

    return market_order_dict


def main():
    listing_hash = '290970-1849 Booster Pack'
    item_nameid = 28419077

    bid_price, ask_price = download_market_order_data(listing_hash, item_nameid, verbose=True)

    return True


if __name__ == '__main__':
    main()
