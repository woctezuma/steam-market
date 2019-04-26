import json
import time

import requests

from market_listing import get_steam_api_rate_limits_for_market_listing
from market_utils import load_aggregated_badge_data
from personal_info import get_steam_cookie, get_cookie_dict
from transaction_fee import compute_sell_price_without_fee
from utils import get_market_order_file_name


def filter_out_badges_with_low_sell_price(aggregated_badge_data, verbose=True):
    # Filter out games for which the sell price (ask) is lower than the gem price,
    # because the bid is necessarily lower than the ask, so it will not be worth downloading bid data for these games.

    filtered_badge_data = dict()

    unknown_price_counter = 0

    for app_id in aggregated_badge_data.keys():
        sell_price_including_fee = aggregated_badge_data[app_id]['sell_price']
        sell_price_without_fee = compute_sell_price_without_fee(sell_price_including_fee)

        gem_price_with_fee = aggregated_badge_data[app_id]['gem_price']

        if (sell_price_including_fee < 0) or (gem_price_with_fee < sell_price_without_fee):
            filtered_badge_data[app_id] = aggregated_badge_data[app_id]

            if sell_price_including_fee < 0:
                unknown_price_counter += 1

    if verbose:
        print('There are {} booster packs with sell price unknown ({}) or strictly higher than gem price ({}).'.format(
            len(filtered_badge_data), unknown_price_counter, len(filtered_badge_data) - unknown_price_counter))

    return filtered_badge_data


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


def download_market_order_data(listing_hash):
    cookie_value = get_steam_cookie()
    has_secured_cookie = bool(cookie_value is not None)

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
            bid_price_in_cents = int(result['highest_buy_order'])
            bid_price = bid_price_in_cents / 100
        except KeyError:
            bid_price = -1

        try:
            ask_price_in_cents = int(result['lowest_sell_order'])
            ask_price = ask_price_in_cents / 100
        except KeyError:
            ask_price = -1

    else:
        bid_price = -1
        ask_price = -1

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
    market_order_dict = load_market_order_data_batch(badge_data)

    market_order_dict = download_market_order_data_batch(badge_data,
                                                         market_order_dict=market_order_dict)

    return market_order_dict


def load_market_order_data_batch(badge_data):
    try:
        with open(get_market_order_file_name(), 'r') as f:
            market_order_dict = json.load(f)
    except FileNotFoundError:
        market_order_dict = None

    return market_order_dict


def find_badge_arbitrages(badge_data):
    # TODO rank them according to the highest bid

    return


def main():
    aggregated_badge_data = load_aggregated_badge_data()

    filtered_badge_data = filter_out_badges_with_low_sell_price(aggregated_badge_data)

    # market_order_dict = update_market_order_data_batch(filtered_badge_data)

    listing_hash = '290970-1849 Booster Pack'
    bid_price, ask_price = download_market_order_data(listing_hash)

    print(bid_price)
    print(ask_price)

    return True


if __name__ == '__main__':
    main()
