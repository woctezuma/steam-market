# Objective: retrieve the price which sellers ask for a 'Sack of Gems'.

import json

from market_listing import get_listing_details
from market_order import download_market_order_data
from personal_info import get_cookie_dict
from utils import get_sack_of_gems_listing_file_name


def get_listing_hash_for_gems():
    listing_hash_for_gems = '753-Sack of Gems'

    return listing_hash_for_gems


def get_num_gems_per_sack_of_gems():
    num_gems_per_sack_of_gems = 1000

    return num_gems_per_sack_of_gems


def download_sack_of_gems_price(sack_of_gems_listing_file_name=None):
    if sack_of_gems_listing_file_name is None:
        sack_of_gems_listing_file_name = get_sack_of_gems_listing_file_name()

    cookie = get_cookie_dict()
    listing_hash = get_listing_hash_for_gems()

    listing_details, status_code = get_listing_details(listing_hash=listing_hash,
                                                       cookie=cookie)

    if status_code == 200:
        item_nameid = listing_details[listing_hash]['item_nameid']

        bid_price, ask_price, bid_volume, ask_volume = download_market_order_data(listing_hash, item_nameid)
        listing_details[listing_hash]['bid'] = bid_price
        listing_details[listing_hash]['ask'] = ask_price
        listing_details[listing_hash]['bid_volume'] = bid_volume
        listing_details[listing_hash]['ask_volume'] = ask_volume

        sack_of_gems_price = ask_price

        with open(sack_of_gems_listing_file_name, 'w', encoding='utf-8') as f:
            json.dump(listing_details, f)
    else:
        raise AssertionError()

    return sack_of_gems_price


def load_sack_of_gems_price(retrieve_gem_price_from_scratch=False,
                            verbose=True,
                            sack_of_gems_listing_file_name=None):
    if sack_of_gems_listing_file_name is None:
        sack_of_gems_listing_file_name = get_sack_of_gems_listing_file_name()

    if retrieve_gem_price_from_scratch:
        sack_of_gems_price = download_sack_of_gems_price(sack_of_gems_listing_file_name)
    else:

        try:
            with open(sack_of_gems_listing_file_name, 'r', encoding='utf-8') as f:
                listing_details = json.load(f)

            listing_hash = get_listing_hash_for_gems()

            sack_of_gems_price = listing_details[listing_hash]['ask']
        except FileNotFoundError:
            sack_of_gems_price = download_sack_of_gems_price(sack_of_gems_listing_file_name)

    if verbose:
        print('A sack of {} gems can be bought for {:.2f} €.'.format(get_num_gems_per_sack_of_gems(),
                                                                     sack_of_gems_price))

    return sack_of_gems_price


def get_gem_price(enforced_sack_of_gems_price=None,
                  minimum_allowed_sack_of_gems_price=None,
                  retrieve_gem_price_from_scratch=False,
                  verbose=True):
    if enforced_sack_of_gems_price is None:
        sack_of_gems_price = load_sack_of_gems_price(retrieve_gem_price_from_scratch, verbose=verbose)
    else:
        sack_of_gems_price = enforced_sack_of_gems_price
        print('[manual input] A sack of {} gems can allegedly be bought for {:.2f} €.'.format(
            get_num_gems_per_sack_of_gems(),
            sack_of_gems_price))

    if minimum_allowed_sack_of_gems_price is not None:
        sack_of_gems_price = max(minimum_allowed_sack_of_gems_price, sack_of_gems_price)
        print('[manual adjustment] The price of a sack of gems is set to {:.2f} € (minimum allowed: {:.2f} €).'.format(
            sack_of_gems_price,
            minimum_allowed_sack_of_gems_price))

    num_gems_per_sack_of_gems = get_num_gems_per_sack_of_gems()

    gem_price = sack_of_gems_price / num_gems_per_sack_of_gems

    return gem_price


def print_gem_price_reminder(enforced_sack_of_gems_price=None,
                             minimum_allowed_sack_of_gems_price=None,
                             retrieve_gem_price_from_scratch=None):
    if retrieve_gem_price_from_scratch is None:
        retrieve_gem_price_from_scratch = bool(enforced_sack_of_gems_price is None)

    gem_price = get_gem_price(enforced_sack_of_gems_price=enforced_sack_of_gems_price,
                              minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
                              retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch)

    return


def get_gem_amount_required_to_craft_badge():
    # This is a constant value of 2000 gems for a badge, because a badge requires a set of N cards, which are obtained
    # after opening N/3 booster packs, and a booster pack costs 6000/N gems.

    gem_amount_required_to_craft_badge = 2000

    return gem_amount_required_to_craft_badge


def main():
    print('Loaded from the disk:')
    sack_of_gems_price = load_sack_of_gems_price(retrieve_gem_price_from_scratch=False,
                                                 verbose=True)
    print('\nDownloaded as a market listing:')
    sack_of_gems_price = load_sack_of_gems_price(retrieve_gem_price_from_scratch=True,
                                                 verbose=True)

    return True


if __name__ == '__main__':
    main()
