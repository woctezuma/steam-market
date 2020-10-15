# Objective: retrieve all the listings of 'Booster Packs' on the Steam Market,
#            along with the sell price, and the volume available at this price.

import json
import time
from pathlib import Path

import requests

from personal_info import get_cookie_dict, update_and_save_cookie_to_disk_if_values_changed
from utils import get_listing_output_file_name


def get_steam_market_search_url():
    market_search_url = 'https://steamcommunity.com/market/search/render/'

    return market_search_url


def get_tag_item_class_no_for_trading_cards():
    tag_item_class_no = 2
    return tag_item_class_no


def get_tag_item_class_no_for_profile_backgrounds():
    tag_item_class_no = 3
    return tag_item_class_no


def get_tag_item_class_no_for_emoticons():
    tag_item_class_no = 4
    return tag_item_class_no


def get_tag_item_class_no_for_booster_packs():
    tag_item_class_no = 5
    return tag_item_class_no


def get_tag_drop_rate_str(rarity=None):
    if rarity is None:
        rarity = 'common'

    if rarity == 'extraordinary':
        tag_drop_rate_no = 3
    elif rarity == 'rare':
        tag_drop_rate_no = 2
    elif rarity == 'uncommon':
        tag_drop_rate_no = 1
    else:
        # Rarity: Common
        tag_drop_rate_no = 0

    tag_drop_rate_str = 'tag_droprate_{}'.format(tag_drop_rate_no)

    return tag_drop_rate_str


def get_search_parameters(start_index=0,
                          delta_index=100,
                          tag_item_class_no=None,
                          tag_drop_rate_str=None,
                          rarity=None,
                          is_foil_trading_card=True):
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
    column_to_sort_by = 'name'
    sort_direction = 'asc'

    params = dict()

    params['norender'] = '1'
    params['category_753_Game[]'] = 'any'
    params['category_753_droprate[]'] = tag_drop_rate_str
    params['category_753_item_class[]'] = 'tag_item_class_' + str(tag_item_class_no)
    params['appid'] = '753'
    params['sort_column'] = column_to_sort_by
    params['sort_dir'] = sort_direction
    params['start'] = str(start_index)
    params['count'] = str(delta_index)

    if tag_item_class_no == get_tag_item_class_no_for_trading_cards():

        if is_foil_trading_card:
            params['category_753_cardborder[]'] = 'tag_cardborder_1'
        else:
            params['category_753_cardborder[]'] = 'tag_cardborder_0'

    return params


def get_steam_api_rate_limits_for_market_search(has_secured_cookie=False):
    # Objective: return the rate limits of Steam API for the market.

    if has_secured_cookie:

        rate_limits = {
            'max_num_queries': 50,
            'cooldown': (1 * 60) + 10,  # 1 minute plus a cushion
        }

    else:

        rate_limits = {
            'max_num_queries': 20,
            'cooldown': (5 * 60) + 10,  # 5 minutes plus a cushion
        }

    return rate_limits


def get_all_listings(all_listings=None,
                     url=None,
                     tag_item_class_no=None,
                     tag_drop_rate_str=None,
                     rarity=None):
    if url is None:
        url = get_steam_market_search_url()

    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    rate_limits = get_steam_api_rate_limits_for_market_search(has_secured_cookie)

    if all_listings is None:
        all_listings = dict()

    num_listings = None

    query_count = 0
    start_index = 0
    delta_index = 100

    while (num_listings is None) or (start_index < num_listings):

        if num_listings is not None:
            print('[{}/{}]'.format(start_index, num_listings))

        req_data = get_search_parameters(start_index=start_index,
                                         delta_index=delta_index,
                                         tag_item_class_no=tag_item_class_no,
                                         tag_drop_rate_str=tag_drop_rate_str,
                                         rarity=rarity)

        if query_count >= rate_limits['max_num_queries']:
            cooldown_duration = rate_limits['cooldown']
            print('Number of queries {} reached. Cooldown: {} seconds'.format(query_count, cooldown_duration))
            time.sleep(cooldown_duration)
            query_count = 0

        try:
            if has_secured_cookie:
                resp_data = requests.get(url, params=req_data, cookies=cookie)
            else:
                resp_data = requests.get(url, params=req_data)
        except requests.exceptions.ConnectionError:
            resp_data = None

        try:
            status_code = resp_data.status_code
        except AttributeError:
            status_code = None

        start_index += delta_index
        query_count += 1

        if status_code == 200:
            result = resp_data.json()

            if has_secured_cookie:
                jar = dict(resp_data.cookies)
                cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

            num_listings_based_on_latest_query = result['total_count']

            if num_listings is not None:
                num_listings = max(num_listings, num_listings_based_on_latest_query)
            else:
                num_listings = num_listings_based_on_latest_query

            listings = dict()
            for listing in result['results']:
                listing_hash = listing['hash_name']

                listings[listing_hash] = dict()
                listings[listing_hash]['sell_listings'] = listing['sell_listings']
                listings[listing_hash]['sell_price'] = listing['sell_price']
                listings[listing_hash]['sell_price_text'] = listing['sell_price_text']

        else:
            print('Wrong status code ({}) for start_index = {} after {} queries.'.format(status_code,
                                                                                         start_index,
                                                                                         query_count,
                                                                                         ))
            if status_code is None:
                continue
            else:
                break

        all_listings.update(listings)

    return all_listings


def download_all_listings(listing_output_file_name=None,
                          url=None,
                          tag_item_class_no=None):
    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name()

    if not Path(listing_output_file_name).exists():
        all_listings = get_all_listings(url=url,
                                        tag_item_class_no=tag_item_class_no)

        with open(listing_output_file_name, 'w', encoding='utf-8') as f:
            json.dump(all_listings, f)

    return True


def update_all_listings(listing_output_file_name=None,
                        url=None,
                        tag_item_class_no=None,
                        tag_drop_rate_str=None,
                        rarity=None):
    # Caveat: this is mostly useful if download_all_listings() failed in the middle of the process, and you want to
    # restart the process without risking to lose anything, in case the process fails again.

    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name()

    try:
        all_listings = load_all_listings(listing_output_file_name=listing_output_file_name)
        print('Loading {} listings from disk.'.format(len(all_listings)))
    except FileNotFoundError:
        print('Downloading listings from scratch.')
        all_listings = None

    all_listings = get_all_listings(all_listings,
                                    url=url,
                                    tag_item_class_no=tag_item_class_no,
                                    tag_drop_rate_str=tag_drop_rate_str,
                                    rarity=rarity)

    with open(listing_output_file_name, 'w', encoding='utf-8') as f:
        json.dump(all_listings, f)

    return True


def load_all_listings(listing_output_file_name=None):
    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name()

    try:
        with open(listing_output_file_name, 'r', encoding='utf-8') as f:
            all_listings = json.load(f)
    except FileNotFoundError:
        print('File {} not found. Initializing listings with an empty dictionary.'.format(listing_output_file_name))
        all_listings = dict()

    return all_listings


if __name__ == '__main__':
    update_all_listings()
