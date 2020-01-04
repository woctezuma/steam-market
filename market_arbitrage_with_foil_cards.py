# Objective: find market arbitrages with foil cards, e.g. buy a foil card and turn it into more gems than their cost.
#
# Caveat: the goal is not to make a profit by selling the gems afterwards! The goal is to acquire gems, this is why
# ALL of the computations are performed with fee included: opportunities are compared from the perspective of the buyer.
#
# In summary, we do not care about buy orders here! We only care about sell orders!

import requests

from market_gamble_detector import update_all_listings_for_foil_cards
from market_listing import get_item_nameid_batch
from market_listing import get_listing_details
from market_search import load_all_listings
from personal_info import get_cookie_dict, update_and_save_cookie_to_disk_if_values_changed
from utils import convert_listing_hash_to_app_id
from utils import get_listing_details_output_file_name_for_foil_cards
from utils import get_listing_output_file_name_for_foil_cards


def get_steam_goo_value_url():
    steam_goo_value_url = 'https://steamcommunity.com/auction/ajaxgetgoovalueforitemtype/'

    return steam_goo_value_url


def get_item_type_no_for_trading_cards(listing_hash=None,
                                       verbose=True):
    # Caveat: the item type is not always equal to 2. Check appID 232770 (POSTAL) for example!
    # Reference: https://gaming.stackexchange.com/a/351941
    #
    # With app_id == 232770 and border_color == 0
    # ===========================================
    # Item type: 2	Goo value: 100      Rare emoticon 5
    # Item type: 3	Goo value: 100      Common emoticon 2
    # Item type: 4	Goo value: 100      Common emoticon 1
    # Item type: 5	Goo value: 100      Uncommon emoticon 4
    # Item type: 6	Goo value: 100      Uncommon emoticon 3
    # Item type: 12	Goo value: 100      Common profile background 1
    # Item type: 13	Goo value: 100      Rare profile background 4
    # Item type: 14	Goo value: 100      Uncommon profile background 2
    # Item type: 15	Goo value: 40       Normal Card 1
    # Item type: 16	Goo value: 40       Normal Card 2
    # Item type: 17	Goo value: 40       Normal Card 3
    # Item type: 18	Goo value: 40       Normal Card 4
    # Item type: 19	Goo value: 40       Normal Card 5
    # Item type: 20	Goo value: 100      Uncommon profile background 3
    # Item type: 21	Goo value: 100      Rare profile background 5

    if listing_hash is None:
        item_type_no = 2

        if verbose:
            print('Assuming item type is equal to {}, which might be wrong.'.format(
                item_type_no,
            ))

    else:
        item_type_no = None  # TODO not always equal to 2! CHANGE THIS

        if verbose:
            print('Retrieving item type {} for {}.'.format(
                item_type_no,
                listing_hash,
            ))

    return item_type_no


def get_border_color_no_for_trading_cards(is_foil=False):
    if is_foil:
        # NB: this leads to a goo value 10 times higher than with border_corlor_no equal to zero. However, it seems to
        # be applied without any check, so that the returned goo values are misleading when applied to any item other
        # than a trading card, such as an emoticon and a profile background.
        border_color_no = 1
    else:
        border_color_no = 0

    return border_color_no


def get_steam_goo_value_parameters(app_id,
                                   item_type=None,
                                   listing_hash=None,
                                   is_foil=True,
                                   verbose=True):
    if item_type is None:
        item_type = get_item_type_no_for_trading_cards(listing_hash=listing_hash,
                                                       verbose=verbose)

    border_color = get_border_color_no_for_trading_cards(is_foil=is_foil)

    params = dict()

    params['appid'] = str(app_id)
    params['item_type'] = item_type
    params['border_color'] = border_color

    return params


def query_goo_value(app_id,
                    item_type,
                    verbose=True):
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    url = get_steam_goo_value_url()

    req_data = get_steam_goo_value_parameters(app_id=app_id,
                                              item_type=item_type)

    if has_secured_cookie:
        resp_data = requests.get(url, params=req_data, cookies=cookie)
    else:
        resp_data = requests.get(url, params=req_data)
    status_code = resp_data.status_code

    if status_code == 200:
        result = resp_data.json()

        if has_secured_cookie:
            jar = dict(resp_data.cookies)
            cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

        goo_value = int(result['goo_value'])

        if verbose:
            if goo_value > 0:
                print('AppID: {} ; Item type: {} ; Goo value: {} gems'.format(app_id,
                                                                              item_type,
                                                                              goo_value))

    else:
        goo_value = None

    return goo_value


def get_listings_for_foil_cards(retrieve_listings_from_scratch,
                                listing_output_file_name=None,
                                verbose=True):
    if retrieve_listings_from_scratch:
        update_all_listings_for_foil_cards()

    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name_for_foil_cards()

    all_listings = load_all_listings(listing_output_file_name)

    if verbose:
        print('#listings = {}'.format(len(all_listings)))

    return all_listings


def group_listing_hashes_by_app_id(all_listings,
                                   filter_out_empty_listings=True,
                                   verbose=True):
    groups_by_app_id = dict()
    for listing_hash in all_listings:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        if filter_out_empty_listings:
            volume = all_listings[listing_hash]['sell_listings']

            if volume == 0:
                continue

        try:
            groups_by_app_id[app_id].append(listing_hash)
        except KeyError:
            groups_by_app_id[app_id] = [listing_hash]

    if verbose:
        print('#app_ids = {}'.format(len(groups_by_app_id)))

    return groups_by_app_id


def find_cheapest_listing_hashes(all_listings,
                                 groups_by_app_id):
    cheapest_listing_hashes = []

    for app_id in groups_by_app_id:
        listing_hashes = groups_by_app_id[app_id]

        # Sort with respect to two attributes:
        #   - ascending sell prices,
        #   - **descending** volumes.
        #  So that, in case the sell price is equal for two listings, the listing with the highest volume is favored.

        sorted_listing_hashes = sorted(listing_hashes,
                                       key=lambda x: (all_listings[x]['sell_price'],
                                                      - all_listings[x]['sell_listings'],))

        cheapest_listing_hash = sorted_listing_hashes[0]

        cheapest_listing_hashes.append(cheapest_listing_hash)

    return cheapest_listing_hashes


def main(retrieve_listings_from_scratch=False,
         filter_out_empty_listings=True,
         price_threshold_in_cents_for_a_foil_card=15,
         verbose=True):
    listing_output_file_name = get_listing_output_file_name_for_foil_cards()
    listing_details_output_file_name = get_listing_details_output_file_name_for_foil_cards()

    all_listings = get_listings_for_foil_cards(retrieve_listings_from_scratch=retrieve_listings_from_scratch,
                                               listing_output_file_name=listing_output_file_name,
                                               verbose=verbose)

    groups_by_app_id = group_listing_hashes_by_app_id(all_listings,
                                                      filter_out_empty_listings=filter_out_empty_listings,
                                                      verbose=verbose)

    cheapest_listing_hashes = find_cheapest_listing_hashes(all_listings,
                                                           groups_by_app_id)

    # Filter listings with an arbitrary price threshold

    if price_threshold_in_cents_for_a_foil_card is not None:

        filtered_cheapest_listing_hashes = []

        for listing_hash in cheapest_listing_hashes:
            ask = all_listings[listing_hash]['sell_price']

            if ask < price_threshold_in_cents_for_a_foil_card:
                filtered_cheapest_listing_hashes.append(listing_hash)

    else:

        filtered_cheapest_listing_hashes = cheapest_listing_hashes

    # Pre-retrieval of item name ids (and item types at the same time)

    item_nameids = get_item_nameid_batch(filtered_cheapest_listing_hashes,
                                         listing_details_output_file_name=listing_details_output_file_name)

    process_all = False

    if process_all:

        listing_hash = '1017900-Minoan Labrys (Foil)'
        listing_details, status_code = get_listing_details(listing_hash=listing_hash)

        print(listing_details)

        listing_hash = '753-Sack of Gems'
        listing_details, status_code = get_listing_details(listing_hash=listing_hash)

        print(listing_details)

        app_id = 232770
        max_num_items = 30
        for item_type in range(max_num_items):
            query_goo_value(app_id=app_id,
                            item_type=item_type)

    return True


if __name__ == '__main__':
    main()
