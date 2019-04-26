import time

import requests
from bs4 import BeautifulSoup

from market_listing import get_steam_market_listing_url, get_steam_api_rate_limits_for_market_listing
from market_utils import load_aggregated_badge_data
from personal_info import get_steam_cookie, get_cookie_dict
from transaction_fee import compute_sell_price_without_fee


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


def download_bid_data(listing_hash):
    cookie_value = get_steam_cookie()
    has_secured_cookie = bool(cookie_value is not None)

    url = get_steam_market_listing_url(listing_hash=listing_hash, render_as_json=False)

    if has_secured_cookie:
        cookie = get_cookie_dict(cookie_value)
        resp_data = requests.get(url, cookies=cookie)
    else:
        resp_data = requests.get(url)

    soup = BeautifulSoup(resp_data.text)

    for element in soup.find_all(class_='market_commodity_order_summary'):
        print(element)
        # TODO

    bid_price = -1

    return bid_price


def download_bid_data_batch(badge_data):
    cookie_value = get_steam_cookie()
    has_secured_cookie = bool(cookie_value is not None)

    rate_limits = get_steam_api_rate_limits_for_market_listing(has_secured_cookie)

    bid_dict = dict()
    query_count = 0

    for app_id in badge_data.keys():
        listing_hash = badge_data[app_id]['listing_hash']
        bid_price = download_bid_data(listing_hash)

        bid_dict[app_id] = bid_price

        if query_count >= rate_limits['max_num_queries']:
            cooldown_duration = rate_limits['cooldown']
            print('Number of queries {} reached. Cooldown: {} seconds'.format(query_count, cooldown_duration))
            time.sleep(cooldown_duration)
            query_count = 0

        query_count += 1

    return bid_dict


def find_badge_arbitrages(badge_data):
    # TODO rank them according to the highest bid

    return


def main():
    aggregated_badge_data = load_aggregated_badge_data()

    filtered_badge_data = filter_out_badges_with_low_sell_price(aggregated_badge_data)

    # bid_dict = download_bid_data_batch(filtered_badge_data)

    listing_hash = '290970-1849 Booster Pack'
    bid_price = download_bid_data(listing_hash)

    return True


if __name__ == '__main__':
    main()
