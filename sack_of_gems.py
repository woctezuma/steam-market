import json

from market_listing import get_listing_details
from market_order import download_market_order_data
from personal_info import get_steam_cookie
from utils import get_sack_of_gems_listing_file_name


def get_listing_hash_for_gems():
    listing_hash_for_gems = '753-Sack of Gems'

    return listing_hash_for_gems


def get_num_gems_per_sack_of_gems():
    num_gems_per_sack_of_gems = 1000

    return num_gems_per_sack_of_gems


def download_sack_of_gems_price():
    cookie_value = get_steam_cookie()
    listing_hash = get_listing_hash_for_gems()

    listing_details, status_code = get_listing_details(listing_hash=listing_hash,
                                                       cookie_value=cookie_value)

    if status_code == 200:
        item_nameid = listing_details[listing_hash]['item_nameid']

        bid_price, ask_price = download_market_order_data(listing_hash, item_nameid)
        listing_details[listing_hash]['bid'] = bid_price
        listing_details[listing_hash]['ask'] = ask_price

        sack_of_gems_price = ask_price

        with open(get_sack_of_gems_listing_file_name(), 'w') as f:
            json.dump(listing_details, f)
    else:
        sack_of_gems_price = -1

    return sack_of_gems_price


def load_sack_of_gems_price(verbose=True):
    try:
        with open(get_sack_of_gems_listing_file_name(), 'r') as f:
            listing_details = json.load(f)

        listing_hash = get_listing_hash_for_gems()

        sack_of_gems_price = listing_details[listing_hash]['ask']
    except FileNotFoundError:
        sack_of_gems_price = download_sack_of_gems_price()

    if verbose:
        print('A sack of {} gems can be bought for {:.2f} €.'.format(get_num_gems_per_sack_of_gems(),
                                                                     sack_of_gems_price))

    return sack_of_gems_price


def get_gem_price(verbose=False):
    sack_of_gems_price = load_sack_of_gems_price(verbose=verbose)

    num_gems_per_sack_of_gems = get_num_gems_per_sack_of_gems()

    gem_price = sack_of_gems_price / num_gems_per_sack_of_gems

    return gem_price


def main():
    sack_of_gems_price = load_sack_of_gems_price(verbose=True)

    return True


if __name__ == '__main__':
    main()
