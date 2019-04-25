# Objective: retrieve all the listings of 'Booster Packs' on the Steam Market,
#            along with the sell price, and the volume available at this price.

import json
import time
from pathlib import Path

import requests

from utils import get_listing_output_file_name


def get_steam_market_search_url():
    market_search_url = 'https://steamcommunity.com/market/search/render/'

    return market_search_url


def get_search_parameters(start_index=0, delta_index=100):
    params = dict()

    params['norender'] = '1'
    params['category_753_item_class[]'] = 'tag_item_class_5'
    params['sort_dir'] = 'asc'
    params['start'] = str(start_index)
    params['count'] = str(delta_index)

    return params


def get_steam_api_rate_limits_for_market_search():
    # Objective: return the rate limits of Steam API for the market.

    rate_limits = {
        'max_num_queries': 23,
        'cooldown': (5 * 60) + 10,  # 5 minutes plus a cushion
    }

    return rate_limits


def get_all_listings(all_listings=None):
    rate_limits = get_steam_api_rate_limits_for_market_search()

    if all_listings is None:
        all_listings = dict()

    num_listings = None

    query_count = 0
    start_index = 0
    delta_index = 100

    while (num_listings is None) or (start_index < num_listings):

        if num_listings is not None:
            print('[{}/{}]'.format(start_index, num_listings))

        url = get_steam_market_search_url()
        req_data = get_search_parameters(start_index=start_index, delta_index=delta_index)

        if query_count >= rate_limits['max_num_queries']:
            cooldown_duration = rate_limits['cooldown']
            print('Number of queries {} reached. Cooldown: {} seconds'.format(query_count, cooldown_duration))
            time.sleep(cooldown_duration)
            query_count = 0

        resp_data = requests.get(url, params=req_data)
        status_code = resp_data.status_code

        start_index += delta_index
        query_count += 1

        if status_code == 200:
            result = resp_data.json()

            num_listings = result['total_count']

            listings = dict()
            for listing in result['results']:
                listing_hash = listing['hash_name']

                listings[listing_hash] = dict()
                listings[listing_hash]['sell_listings'] = listing['sell_listings']
                listings[listing_hash]['sell_price'] = listing['sell_price']
                listings[listing_hash]['sell_price_text'] = listing['sell_price_text']

        else:
            print('Wrong status code for start_index = {} after {} queries.'.format(start_index, query_count))
            break

        all_listings.update(listings)

    return all_listings


def download_all_listings():
    listing_output_file_name = get_listing_output_file_name()

    if not Path(listing_output_file_name).exists():
        all_listings = get_all_listings()

        with open(listing_output_file_name, 'w') as f:
            json.dump(all_listings, f)

    return True


def update_all_listings():
    # Caveat: this is mostly useful if download_all_listings() failed in the middle of the process, and you want to
    # restart the process without risking to lose anything, in case the process fails again.

    listing_output_file_name = get_listing_output_file_name()

    try:
        with open(listing_output_file_name, 'r') as f:
            all_listings = json.load(f)
            print('Loading {} listings from disk.'.format(len(all_listings)))
    except FileNotFoundError:
        print('Downloading listings from scratch.')
        all_listings = None

    all_listings = get_all_listings(all_listings)

    with open(listing_output_file_name, 'w') as f:
        json.dump(all_listings, f)

    return True


def load_all_listings():
    with open(get_listing_output_file_name(), 'r') as f:
        all_listings = json.load(f)

    return all_listings


if __name__ == '__main__':
    update_all_listings()
