import json
import time
from pathlib import Path

import requests

from market_search import load_all_listings
from utils import get_listing_details_output_file_name


def get_steam_market_listing_url(app_id=None, listing_hash=None):
    if app_id is None:
        app_id = 753

    if listing_hash is None:
        listing_hash = '511540-MoonQuest Booster Pack'

    market_listing_url = 'https://steamcommunity.com/market/listings/' + str(app_id) + '/' + listing_hash + '/render/'

    return market_listing_url


def get_listing_parameters():
    params = dict()

    params['currency'] = '3'

    return params


def get_steam_api_rate_limits_for_market_listing():
    # Objective: return the rate limits of Steam API for the market.

    rate_limits = {
        'max_num_queries': 25,
        'cooldown': (5 * 60) + 10,  # 5 minutes plus a cushion
    }

    return rate_limits


def get_listing_details(listing_hash=None, currency_symbol='€'):
    listing_details = dict()

    url = get_steam_market_listing_url(listing_hash=listing_hash)
    req_data = get_listing_parameters()

    resp_data = requests.get(url, params=req_data)
    status_code = resp_data.status_code

    if status_code == 200:
        result = resp_data.json()

        html = result['results_html']

        tokens = html.split()

        price_headers = [l for (c, l) in enumerate(tokens[:-1]) if currency_symbol in tokens[c + 1]]
        price_values = [l for l in tokens if currency_symbol in l]

        if len(price_headers) > 0 and len(price_headers) != 3:
            print('Unexpected number of price headers = {}. Likely due to zero sell order.'.format(len(price_headers)))
            print(price_headers)

        try:
            chosen_index = 0
            chosen_price_header = price_headers[chosen_index]  # e.g. 'market_listing_price_with_fee">'
            chosen_price_value = price_values[chosen_index]  # e.g. '6,64€'

            listing_details[listing_hash] = dict()
            listing_details[listing_hash]['price_header'] = chosen_price_header.strip('">')
            listing_details[listing_hash]['for_sale'] = float(chosen_price_value.strip('€').replace(',', '.'))
            listing_details[listing_hash]['buy_request'] = 0  # missing from the html code
        except IndexError:
            pass

    return listing_details, status_code


def get_all_listing_details(listing_hashes):
    rate_limits = get_steam_api_rate_limits_for_market_listing()

    all_listing_details = dict()
    num_listings = len(listing_hashes)

    query_count = 0

    for count, listing_hash in enumerate(listing_hashes):

        if count + 1 % 100 == 0:
            print('[{}/{}]'.format(count + 1, num_listings))

        listing_details, status_code = get_listing_details(listing_hash=listing_hash)

        if query_count >= rate_limits['max_num_queries']:
            cooldown_duration = rate_limits['cooldown']
            print('Number of queries {} reached. Cooldown: {} seconds'.format(query_count, cooldown_duration))
            time.sleep(cooldown_duration)
            query_count = 0

        query_count += 1

        if status_code != 200:
            print('Wrong status code for {} after {} queries.'.format(listing_hash, query_count))
            break

        all_listing_details.update(listing_details)

    return all_listing_details


def download_all_listing_details():
    listing_details__output_file_name = get_listing_details_output_file_name()

    if not Path(listing_details__output_file_name).exists():
        all_listings = load_all_listings()

        all_listing_details = get_all_listing_details(all_listings.keys())

        with open(listing_details__output_file_name, 'w') as f:
            json.dump(all_listing_details, f)

    return True


def load_all_listing_details():
    with open(get_listing_details_output_file_name(), 'r') as f:
        all_listing_details = json.load(f)

    return all_listing_details


if __name__ == '__main__':
    download_all_listing_details()
