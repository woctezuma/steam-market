# Objective: find market arbitrages with foil cards, e.g. buy a foil card and turn it into more gems than its cost.
#
# Caveat: the goal is not to make a profit by selling the gems afterwards! The goal is to acquire gems, this is why
# ALL of the computations are performed with fee included: opportunities are compared from the perspective of the buyer.
#
# In summary, we do not care about buy orders here! We only care about sell orders!

import json

import requests

from market_gamble_detector import update_all_listings_for_foil_cards
from market_listing import get_item_nameid_batch
from market_listing import load_all_listing_details
from market_listing import update_all_listing_details
from market_search import load_all_listings
from personal_info import get_cookie_dict, update_and_save_cookie_to_disk_if_values_changed
from sack_of_gems import get_num_gems_per_sack_of_gems
from sack_of_gems import load_sack_of_gems_price
from utils import convert_listing_hash_to_app_id
from utils import get_goo_details_file_nam_for_for_foil_cards
from utils import get_listing_details_output_file_name_for_foil_cards
from utils import get_listing_output_file_name_for_foil_cards


def get_steam_goo_value_url():
    steam_goo_value_url = 'https://steamcommunity.com/auction/ajaxgetgoovalueforitemtype/'

    return steam_goo_value_url


def get_item_type_no_for_trading_cards(listing_hash=None,
                                       all_listing_details=None,
                                       listing_details_output_file_name=None,
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
        if listing_details_output_file_name is None:
            listing_details_output_file_name = get_listing_details_output_file_name_for_foil_cards()

        if all_listing_details is None:
            all_listing_details = load_all_listing_details(
                listing_details_output_file_name=listing_details_output_file_name)

        try:
            listing_details = all_listing_details[listing_hash]
        except KeyError:
            # Caveat: the code below is not the intended way to find item types, because we do not take into account
            #         rate limits! This is okay for one listing hash, but this would be an issue for many of them!
            #
            #         Ideally, you should have called update_all_listing_details() with
            #         the FULL list of listing hashes to be processed, stored in variable 'listing_hashes_to_process',
            #         rather than with just ONE listing hash.
            listing_hashes_to_process = [listing_hash]

            if verbose:
                print('A query is necessary to download listing details for {}.'.format(listing_hash))

            updated_all_listing_details = update_all_listing_details(listing_hashes=listing_hashes_to_process,
                                                                     listing_details_output_file_name=listing_details_output_file_name)

            listing_details = updated_all_listing_details[listing_hash]

        item_type_no = listing_details['item_type_no']

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


def find_representative_listing_hashes(groups_by_app_id):
    representative_listing_hashes = []

    for app_id in groups_by_app_id:
        listing_hashes = groups_by_app_id[app_id]

        # Sort with respect to lexicographical order.

        sorted_listing_hashes = sorted(listing_hashes)

        representative_listing_hash = sorted_listing_hashes[0]

        representative_listing_hashes.append(representative_listing_hash)

    return representative_listing_hashes


def filter_listings_with_arbitrary_price_threshold(all_listings,
                                                   listing_hashes_to_filter_from,
                                                   price_threshold_in_cents=None,
                                                   verbose=True):
    if price_threshold_in_cents is not None:

        filtered_cheapest_listing_hashes = []

        for listing_hash in listing_hashes_to_filter_from:
            ask = all_listings[listing_hash]['sell_price']

            if ask < price_threshold_in_cents:
                filtered_cheapest_listing_hashes.append(listing_hash)

    else:

        filtered_cheapest_listing_hashes = listing_hashes_to_filter_from

    if verbose:
        print('#listings (after filtering) = {}'.format(len(filtered_cheapest_listing_hashes)))

    return filtered_cheapest_listing_hashes


def load_all_goo_details(goo_details_file_name=None,
                         verbose=True):
    if goo_details_file_name is None:
        goo_details_file_name = get_goo_details_file_nam_for_for_foil_cards()

    try:
        with open(goo_details_file_name, 'r', encoding='utf-8') as f:
            all_goo_details = json.load(f)
    except FileNotFoundError:
        all_goo_details = dict()

    if verbose:
        print('Loading {} goo details from disk.'.format(len(all_goo_details)))

    return all_goo_details


def save_all_goo_details(all_goo_details,
                         goo_details_file_name=None):
    if goo_details_file_name is None:
        goo_details_file_name = get_goo_details_file_nam_for_for_foil_cards()

    with open(goo_details_file_name, 'w', encoding='utf-8') as f:
        json.dump(all_goo_details, f)

    return


def update_all_goo_details(new_goo_details,
                           goo_details_file_name=None):
    if goo_details_file_name is None:
        goo_details_file_name = get_goo_details_file_nam_for_for_foil_cards()

    all_goo_details = load_all_goo_details(goo_details_file_name)
    all_goo_details.update(new_goo_details)

    save_all_goo_details(all_goo_details,
                         goo_details_file_name)

    return


def filter_out_listing_hashes_if_goo_details_are_already_known_for_app_id(filtered_cheapest_listing_hashes,
                                                                          goo_details_file_name_for_for_foil_cards=None,
                                                                          verbose=True):
    # Filter out listings associated with an appID for which we already know the goo details.

    if goo_details_file_name_for_for_foil_cards is None:
        goo_details_file_name_for_for_foil_cards = get_goo_details_file_nam_for_for_foil_cards()

    previously_downloaded_all_goo_details = load_all_goo_details(goo_details_file_name_for_for_foil_cards,
                                                                 verbose=verbose)

    app_ids_with_previously_downloaded_goo_details = [
        int(app_id)
        for app_id in previously_downloaded_all_goo_details
    ]

    filtered_cheapest_listing_hashes = [
        listing_hash
        for listing_hash in filtered_cheapest_listing_hashes
        if convert_listing_hash_to_app_id(listing_hash) not in app_ids_with_previously_downloaded_goo_details
    ]

    return filtered_cheapest_listing_hashes


def apply_workflow_for_foil_cards(retrieve_listings_from_scratch=False,
                                  filter_out_empty_listings=True,
                                  price_threshold_in_cents_for_a_foil_card=None,
                                  retrieve_gem_price_from_scratch=False,
                                  enforced_sack_of_gems_price=None,  # price in euros
                                  verbose=True):
    listing_output_file_name = get_listing_output_file_name_for_foil_cards()
    listing_details_output_file_name = get_listing_details_output_file_name_for_foil_cards()
    goo_details_file_name_for_for_foil_cards = get_goo_details_file_nam_for_for_foil_cards()

    # Fetch all the listings of foil cards

    all_listings = get_listings_for_foil_cards(retrieve_listings_from_scratch=retrieve_listings_from_scratch,
                                               listing_output_file_name=listing_output_file_name,
                                               verbose=verbose)

    # Group listings by appID

    groups_by_app_id = group_listing_hashes_by_app_id(all_listings,
                                                      filter_out_empty_listings=filter_out_empty_listings,
                                                      verbose=verbose)

    # Find the cheapest listing in each group

    cheapest_listing_hashes = find_cheapest_listing_hashes(all_listings,
                                                           groups_by_app_id)

    # Find the representative listing in each group

    representative_listing_hashes = find_representative_listing_hashes(groups_by_app_id)

    # Filter listings with an arbitrary price threshold
    # NB: This is only useful to speed up the pre-retrieval below, by focusing on the most interesting listings.

    filtered_cheapest_listing_hashes = filter_listings_with_arbitrary_price_threshold(
        all_listings=all_listings,
        listing_hashes_to_filter_from=cheapest_listing_hashes,
        price_threshold_in_cents=price_threshold_in_cents_for_a_foil_card,
        verbose=verbose)

    # Filter out listings associated with an appID for which we already know the goo details.

    filtered_cheapest_listing_hashes = filter_out_listing_hashes_if_goo_details_are_already_known_for_app_id(
        filtered_cheapest_listing_hashes,
        goo_details_file_name_for_for_foil_cards=goo_details_file_name_for_for_foil_cards,
        verbose=verbose)

    # Pre-retrieval of item name ids (and item types at the same time)

    item_nameids = get_item_nameid_batch(filtered_cheapest_listing_hashes,
                                         listing_details_output_file_name=listing_details_output_file_name)

    # Load the price of a sack of 1000 gems

    if enforced_sack_of_gems_price is None:
        sack_of_gems_price_in_euros = load_sack_of_gems_price(
            retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
            verbose=verbose)
    else:
        sack_of_gems_price_in_euros = enforced_sack_of_gems_price

    # Fetch goo values

    all_listing_details = load_all_listing_details(listing_details_output_file_name=listing_details_output_file_name)

    all_goo_details = download_missing_goo_details(groups_by_app_id=groups_by_app_id,
                                                   cheapest_listing_hashes=cheapest_listing_hashes,
                                                   all_listing_details=all_listing_details,
                                                   listing_details_output_file_name=listing_details_output_file_name,
                                                   goo_details_file_name_for_for_foil_cards=goo_details_file_name_for_for_foil_cards,
                                                   verbose=verbose)

    # List unknown item types

    try_again_to_find_item_type = False

    listing_hashes_with_unknown_item_types = find_listing_hashes_with_unknown_item_types(
        groups_by_app_id=groups_by_app_id,
        cheapest_listing_hashes=cheapest_listing_hashes,
        all_listing_details=all_listing_details,
        listing_details_output_file_name=listing_details_output_file_name,
        try_again_to_find_item_type=try_again_to_find_item_type,
        verbose=verbose)

    # List unknown goo values

    try_again_to_find_goo_value = False

    listing_hashes_with_unknown_goo_value = find_listing_hashes_with_unknown_goo_value(cheapest_listing_hashes,
                                                                                       listing_hashes_with_unknown_item_types,
                                                                                       all_goo_details,
                                                                                       groups_by_app_id=groups_by_app_id,
                                                                                       try_again_to_find_goo_value=try_again_to_find_goo_value,
                                                                                       verbose=verbose)

    # Solely for information purpose, count the number of potentially rewarding appIDs.
    #
    # NB: this information is not used, but one could imagine only retrieving the ask price of potentially rewarding
    #     appIDs, so that time is not lost retrieving the ask price of necessarily unrewarding appIDs.
    #     Indeed, this could halve the number of queries, e.g. as of January 2020, there are:
    #     - 8872 appIDs in total,
    #     - out of which 4213 to 4257 are potentially rewarding appIDs, so 47% - 48% of the appIDs.

    potentially_rewarding_app_ids = discard_necessarily_unrewarding_app_ids(all_goo_details,
                                                                            listing_hashes_with_unknown_item_types=listing_hashes_with_unknown_item_types,
                                                                            listing_hashes_with_unknown_goo_value=listing_hashes_with_unknown_goo_value,
                                                                            sack_of_gems_price_in_euros=sack_of_gems_price_in_euros,
                                                                            retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
                                                                            verbose=verbose)

    # Find market arbitrages

    arbitrages = determine_whether_an_arbitrage_might_exist_for_foil_cards(cheapest_listing_hashes,
                                                                           listing_hashes_with_unknown_item_types,
                                                                           all_goo_details,
                                                                           all_listings=all_listings,
                                                                           listing_output_file_name=listing_output_file_name,
                                                                           sack_of_gems_price_in_euros=sack_of_gems_price_in_euros,
                                                                           retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
                                                                           verbose=verbose)

    print_arbitrages_for_foil_cards(arbitrages)

    return True


def get_minimal_ask_price_in_euros_on_steam_market():
    minimal_ask_price_on_steam_market = 0.03  # in euros

    return minimal_ask_price_on_steam_market


def compute_unrewarding_threshold_in_gems(sack_of_gems_price_in_euros=None,
                                          retrieve_gem_price_from_scratch=False,
                                          verbose=True):
    # The minimal price of a card is 0.03€. A sack of 1000 gems can be bought from the Steam Market at the 'ask' price.
    #
    # Therefore, we can safely discard appIDs for which the cards are unrewarding, i.e. cards would be turned into fewer
    # gems than: get_minimal_ask_price_on_steam_market() * get_num_gems_per_sack_of_gems() / load_sack_of_gems_price().
    #
    # For instance, if a sack of 1000 gems costs 0.30€, then a card is unrewarding if it cannot be turned into more than
    # 0.03*1000/0.30 = 100 gems.

    if sack_of_gems_price_in_euros is None:
        # Load the price of a sack of 1000 gems
        sack_of_gems_price_in_euros = load_sack_of_gems_price(
            retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
            verbose=verbose)

    num_gems_per_sack_of_gems = get_num_gems_per_sack_of_gems()

    minimal_ask = get_minimal_ask_price_in_euros_on_steam_market()

    unrewarding_threshold_in_gems = minimal_ask * num_gems_per_sack_of_gems / sack_of_gems_price_in_euros

    return unrewarding_threshold_in_gems


def discard_necessarily_unrewarding_app_ids(all_goo_details,
                                            listing_hashes_with_unknown_item_types=None,
                                            listing_hashes_with_unknown_goo_value=None,
                                            sack_of_gems_price_in_euros=None,
                                            retrieve_gem_price_from_scratch=False,
                                            verbose=True):
    if listing_hashes_with_unknown_item_types is None:
        listing_hashes_with_unknown_item_types = []

    if listing_hashes_with_unknown_goo_value is None:
        listing_hashes_with_unknown_goo_value = []

    listing_hashes_to_omit = listing_hashes_with_unknown_item_types + listing_hashes_with_unknown_goo_value

    app_ids_to_omit = [
        convert_listing_hash_to_app_id(listing_hash)
        for listing_hash in listing_hashes_to_omit
    ]

    unrewarding_threshold_in_gems = compute_unrewarding_threshold_in_gems(
        sack_of_gems_price_in_euros=sack_of_gems_price_in_euros,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
        verbose=verbose)

    potentially_rewarding_app_ids = []

    for app_id in all_goo_details:
        goo_value_in_gems = all_goo_details[app_id]

        app_id_as_int = int(app_id)

        if app_id_as_int in app_ids_to_omit:
            continue

        if goo_value_in_gems is None:
            continue

        if goo_value_in_gems >= unrewarding_threshold_in_gems:
            potentially_rewarding_app_ids.append(app_id_as_int)

    potentially_rewarding_app_ids = sorted(potentially_rewarding_app_ids)

    if verbose:
        print('There are {} potentially rewarding appIDs.'.format(
            len(potentially_rewarding_app_ids),
        ))

    return potentially_rewarding_app_ids


def find_listing_hashes_with_unknown_goo_value(cheapest_listing_hashes,
                                               listing_hashes_with_unknown_item_types,
                                               all_goo_details,
                                               groups_by_app_id,
                                               try_again_to_find_goo_value=False,
                                               verbose=True):
    app_ids_with_unreliable_goo_details = [convert_listing_hash_to_app_id(listing_hash)
                                           for listing_hash in listing_hashes_with_unknown_item_types]

    listing_hashes_with_unknown_goo_value = []

    for listing_hash in cheapest_listing_hashes:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        if app_id in app_ids_with_unreliable_goo_details:
            continue

        goo_value_in_gems = all_goo_details[str(app_id)]

        if goo_value_in_gems is None:
            listing_hashes_with_unknown_goo_value.append(listing_hash)

    if verbose:
        print('Unknown goo values for:\n{}\nTotal: {} listing hashes with unknown goo value.'.format(
            listing_hashes_with_unknown_goo_value,
            len(listing_hashes_with_unknown_goo_value),
        ))

    if try_again_to_find_goo_value:
        listing_hashes_to_process = listing_hashes_with_unknown_goo_value

        if verbose:
            print('Trying again to find goo values for {} listing hashes.'.format(
                len(listing_hashes_to_process),
            ))

            download_missing_goo_details(groups_by_app_id=groups_by_app_id,
                                         cheapest_listing_hashes=cheapest_listing_hashes,
                                         enforced_app_ids_to_process=listing_hashes_to_process)

    return listing_hashes_with_unknown_goo_value


def determine_whether_an_arbitrage_might_exist_for_foil_cards(cheapest_listing_hashes,
                                                              listing_hashes_with_unknown_item_types,
                                                              all_goo_details,
                                                              all_listings=None,
                                                              listing_output_file_name=None,
                                                              sack_of_gems_price_in_euros=None,
                                                              retrieve_gem_price_from_scratch=True,
                                                              verbose=True):
    if sack_of_gems_price_in_euros is None:
        # Load the price of a sack of 1000 gems
        sack_of_gems_price_in_euros = load_sack_of_gems_price(
            retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
            verbose=verbose)

    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name_for_foil_cards()

    if all_listings is None:
        all_listings = load_all_listings(
            listing_output_file_name=listing_output_file_name)

    app_ids_with_unreliable_goo_details = [convert_listing_hash_to_app_id(listing_hash)
                                           for listing_hash in listing_hashes_with_unknown_item_types]

    num_gems_per_sack_of_gems = get_num_gems_per_sack_of_gems()

    sack_of_gems_price_in_cents = 100 * sack_of_gems_price_in_euros

    arbitrages = dict()

    for listing_hash in cheapest_listing_hashes:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        if app_id in app_ids_with_unreliable_goo_details:
            # NB: This is for goo details which were retrieved with the default item type n° (=2), which can be wrong.
            if verbose:
                print('[X]\tUnreliable goo details for {}'.format(listing_hash))
            continue

        goo_value_in_gems = all_goo_details[str(app_id)]

        if goo_value_in_gems is None:
            # NB: This is when the goo value is unknown, despite a correct item type n° used to download goo details.
            if verbose:
                print('[?]\tUnknown goo value for {}'.format(listing_hash))
            continue

        goo_value_in_cents = goo_value_in_gems / num_gems_per_sack_of_gems * sack_of_gems_price_in_cents

        current_listing = all_listings[listing_hash]
        ask_in_cents = current_listing['sell_price']

        if ask_in_cents == 0:
            # NB: The ask cannot be equal to zero. So, we skip the listing because of there must be a bug.
            if verbose:
                print('[!]\tImpossible ask price ({:.2f}€) for {}'.format(
                    ask_in_cents / 100,
                    listing_hash,
                ))
            continue

        profit_in_cents = goo_value_in_cents - ask_in_cents
        is_arbitrage = bool(profit_in_cents > 0)

        if is_arbitrage:
            arbitrage = dict()
            arbitrage['profit'] = profit_in_cents / 100
            arbitrage['ask'] = ask_in_cents / 100
            arbitrage['goo_amount'] = goo_value_in_gems
            arbitrage['goo_value'] = goo_value_in_cents / 100

            arbitrages[listing_hash] = arbitrage

    return arbitrages


def print_arbitrages_for_foil_cards(arbitrages):
    bullet_point = '*   '

    sorted_arbitrages = sorted(arbitrages.keys(),
                               key=lambda x: arbitrages[x]['profit'],
                               reverse=True)

    print('# Results for arbitrages with foil cards')

    for listing_hash in sorted_arbitrages:
        arbitrage = arbitrages[listing_hash]
        equivalent_price_for_sack_of_gems = arbitrage['ask'] / arbitrage['goo_amount'] * get_num_gems_per_sack_of_gems()

        print(
            '{}Profit: {:.2f}€\t{}\t| buy for: {:.2f}€ | turn into {} gems ({:.2f}€) | ~ {:.3f}€ per gem sack'.format(
                bullet_point,
                arbitrage['profit'],
                listing_hash,
                arbitrage['ask'],
                arbitrage['goo_amount'],
                arbitrage['goo_value'],
                equivalent_price_for_sack_of_gems,
            ))

    return


def find_listing_hashes_with_unknown_item_types(groups_by_app_id,
                                                cheapest_listing_hashes,
                                                all_listing_details=None,
                                                listing_details_output_file_name=None,
                                                try_again_to_find_item_type=False,
                                                verbose=True):
    listing_hashes_with_unknown_item_types = []

    for app_id in groups_by_app_id:
        cheapest_listing_hash_for_app_id = find_cheapest_listing_hash_for_app_id(app_id,
                                                                                 groups_by_app_id=groups_by_app_id,
                                                                                 cheapest_listing_hashes=cheapest_listing_hashes)

        item_type = find_item_type_for_app_id(app_id,
                                              groups_by_app_id=groups_by_app_id,
                                              cheapest_listing_hashes=cheapest_listing_hashes,
                                              all_listing_details=all_listing_details,
                                              listing_details_output_file_name=listing_details_output_file_name)
        if item_type is None:
            listing_hashes_with_unknown_item_types.append(cheapest_listing_hash_for_app_id)

    if verbose:
        print('Unknown item types for:\n{}\nTotal: {} listing hashes with unknown item types.'.format(
            listing_hashes_with_unknown_item_types,
            len(listing_hashes_with_unknown_item_types),
        ))

    if try_again_to_find_item_type:
        listing_hashes_to_process = listing_hashes_with_unknown_item_types

        if verbose:
            print('Trying again to find item types for {} listing hashes.'.format(
                len(listing_hashes_to_process),
            ))

            updated_all_listing_details = update_all_listing_details(listing_hashes=listing_hashes_to_process,
                                                                     listing_details_output_file_name=listing_details_output_file_name)

    return listing_hashes_with_unknown_item_types


def download_missing_goo_details(groups_by_app_id,
                                 cheapest_listing_hashes,
                                 all_listing_details=None,
                                 listing_details_output_file_name=None,
                                 goo_details_file_name_for_for_foil_cards=None,
                                 enforced_app_ids_to_process=None,
                                 num_queries_between_save=100,
                                 verbose=True):
    if goo_details_file_name_for_for_foil_cards is None:
        goo_details_file_name_for_for_foil_cards = get_goo_details_file_nam_for_for_foil_cards()

    if enforced_app_ids_to_process is None:
        enforced_app_ids_to_process = []

    all_goo_details = load_all_goo_details(goo_details_file_name_for_for_foil_cards,
                                           verbose=verbose)

    # Convert appIDs to integers, because:
    # - dictionary keys are strings in 'all_goo_details',
    # - appIDs are stored as integers in 'groups_by_app_id'.
    app_ids_with_known_goo_details = [int(app_id)
                                      for app_id in all_goo_details.keys()]

    all_app_ids = set(groups_by_app_id)
    app_ids_with_unknown_goo_details = all_app_ids.difference(app_ids_with_known_goo_details)

    eligible_enforced_app_ids_to_process = all_app_ids.intersection(enforced_app_ids_to_process)

    app_ids_to_process = app_ids_with_unknown_goo_details.union(eligible_enforced_app_ids_to_process)

    query_count = 0

    for app_id in app_ids_to_process:

        goo_value = download_goo_value_for_app_id(app_id=app_id,
                                                  groups_by_app_id=groups_by_app_id,
                                                  cheapest_listing_hashes=cheapest_listing_hashes,
                                                  all_listing_details=all_listing_details,
                                                  listing_details_output_file_name=listing_details_output_file_name,
                                                  verbose=verbose)
        query_count += 1

        all_goo_details[app_id] = goo_value

        if query_count % num_queries_between_save == 0:
            print('Saving after {} queries.'.format(query_count))
            save_all_goo_details(all_goo_details,
                                 goo_details_file_name_for_for_foil_cards)

    # Final save

    if query_count > 0:
        print('Final save after {} queries.'.format(query_count))
        save_all_goo_details(all_goo_details,
                             goo_details_file_name_for_for_foil_cards)

    return all_goo_details


def find_cheapest_listing_hash_for_app_id(app_id,
                                          groups_by_app_id,
                                          cheapest_listing_hashes):
    listing_hashes_for_app_id = groups_by_app_id[app_id]
    cheapest_listing_hash_for_app_id_as_a_set = set(listing_hashes_for_app_id).intersection(cheapest_listing_hashes)

    cheapest_listing_hash_for_app_id = list(cheapest_listing_hash_for_app_id_as_a_set)[0]

    return cheapest_listing_hash_for_app_id


def find_item_type_for_app_id(app_id,
                              groups_by_app_id,
                              cheapest_listing_hashes,
                              all_listing_details=None,
                              listing_details_output_file_name=None):
    if listing_details_output_file_name is None:
        listing_details_output_file_name = get_listing_details_output_file_name_for_foil_cards()

    if all_listing_details is None:
        all_listing_details = load_all_listing_details(
            listing_details_output_file_name=listing_details_output_file_name)

    cheapest_listing_hash_for_app_id = find_cheapest_listing_hash_for_app_id(app_id,
                                                                             groups_by_app_id,
                                                                             cheapest_listing_hashes)

    listing_details = all_listing_details[cheapest_listing_hash_for_app_id]
    item_type = listing_details['item_type_no']

    return item_type


def download_goo_value_for_app_id(app_id,
                                  groups_by_app_id,
                                  cheapest_listing_hashes,
                                  all_listing_details=None,
                                  listing_details_output_file_name=None,
                                  verbose=True):
    item_type = find_item_type_for_app_id(app_id,
                                          groups_by_app_id,
                                          cheapest_listing_hashes,
                                          all_listing_details,
                                          listing_details_output_file_name)

    goo_value = query_goo_value(app_id=app_id,
                                item_type=item_type,
                                verbose=verbose)

    return goo_value


def main():
    retrieve_listings_from_scratch = False
    filter_out_empty_listings = True
    price_threshold_in_cents_for_a_foil_card = None
    retrieve_gem_price_from_scratch = False
    enforced_sack_of_gems_price = None  # price in euros
    verbose = True

    apply_workflow_for_foil_cards(retrieve_listings_from_scratch=retrieve_listings_from_scratch,
                                  filter_out_empty_listings=filter_out_empty_listings,
                                  price_threshold_in_cents_for_a_foil_card=price_threshold_in_cents_for_a_foil_card,
                                  retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
                                  enforced_sack_of_gems_price=enforced_sack_of_gems_price,
                                  verbose=verbose)

    return True


if __name__ == '__main__':
    main()
