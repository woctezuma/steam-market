# Objective: detect gambles which might be worth a try, i.e. find profile backgrounds and emoticons which:
# - are of "Common" rarity, so reasonably likely to be obtained after a crafting a badge,
# - have high bid orders, so potentially profitable after taking every other factor into account.
#
# Caveat: take into account the NUMBER of items of "Common" rarity! This information can be found on pages such as:
#         https://www.steamcardexchange.net/index.php?gamepage-appid-254880
# For instance, if there are 2 Profile Backgrounds of "Common" rarity, then you can expect to get the one of interest
# after crafting 2 badges, therefore you should expect to be able to sell it for 2x the crafting cost to turn a profit.
#
# NB: a booster pack of 3 cards is always worth 6000/(#cards) gems, so a full set of (#cards) is worth 2000 gems.
# Therefore, the cost of crafting a badge is identical for every game: that is twice the price of a sack of 1000 gems.
# If you pay 0.31 € per sack of gems, which you then turn into booster packs, then your *badge* crafting cost is 0.62 €.

import time

from drop_rate_estimates import get_drop_rate_estimates_based_on_item_rarity_pattern
from drop_rate_estimates import get_drop_rate_field, clamp_proportion
from drop_rate_estimates import get_rarity_fields
from market_arbitrage import filter_out_badges_with_low_sell_price
from market_arbitrage import find_badge_arbitrages, print_arbitrages
from market_buzz_detector import filter_out_unmarketable_packs, sort_according_to_buzz, print_packs_with_high_buzz
from market_listing import get_item_nameid_batch
from market_order import load_market_order_data_from_disk, download_market_order_data_batch
from market_search import get_steam_api_rate_limits_for_market_search
from market_search import get_tag_item_class_no_for_profile_backgrounds, get_tag_item_class_no_for_emoticons
from market_search import get_tag_item_class_no_for_trading_cards
from market_search import update_all_listings, load_all_listings
from personal_info import get_cookie_dict
from sack_of_gems import get_gem_price, get_gem_amount_required_to_craft_badge
from utils import convert_listing_hash_to_app_id
from utils import get_category_name_for_booster_packs
from utils import get_category_name_for_profile_backgrounds, get_category_name_for_emoticons
from utils import get_listing_details_output_file_name_for_emoticons
from utils import get_listing_details_output_file_name_for_profile_backgrounds
from utils import get_listing_output_file_name_for_foil_cards
from utils import get_listing_output_file_name_for_profile_backgrounds, get_listing_output_file_name_for_emoticons
from utils import get_market_order_file_name_for_profile_backgrounds, get_market_order_file_name_for_emoticons


def update_all_listings_for_foil_cards():
    print('Downloading listings for foil cards.')

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_foil_cards(),
        tag_item_class_no=get_tag_item_class_no_for_trading_cards()
    )

    return


def update_all_listings_for_profile_backgrounds(tag_drop_rate_str=None,
                                                rarity=None):
    print('Downloading listings for profile backgrounds (rarity_tag={} ; rarity={}).'.format(
        tag_drop_rate_str,
        rarity,
    ))

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_profile_backgrounds(
            tag_drop_rate_str=tag_drop_rate_str,
            rarity=rarity),
        tag_item_class_no=get_tag_item_class_no_for_profile_backgrounds(),
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity
    )

    return


def update_all_listings_for_emoticons(tag_drop_rate_str=None,
                                      rarity=None):
    print('Downloading listings for emoticons (rarity_tag={} ; rarity={}).'.format(
        tag_drop_rate_str,
        rarity,
    ))

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_emoticons(tag_drop_rate_str=tag_drop_rate_str,
                                                                            rarity=rarity),
        tag_item_class_no=get_tag_item_class_no_for_emoticons(),
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity
    )

    return


def update_all_listings_for_items_other_than_cards(tag_drop_rate_str=None,
                                                   rarity=None):
    # Profile Backgrounds

    update_all_listings_for_profile_backgrounds(tag_drop_rate_str=tag_drop_rate_str,
                                                rarity=rarity)

    # Forced cooldown

    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    rate_limits = get_steam_api_rate_limits_for_market_search(has_secured_cookie)

    cooldown_duration = rate_limits['cooldown']
    print('Forced cooldown between profile backgrounds and emoticons. Cooldown: {} seconds'.format(cooldown_duration))
    time.sleep(cooldown_duration)

    # Emoticons

    update_all_listings_for_emoticons(tag_drop_rate_str=tag_drop_rate_str,
                                      rarity=rarity)

    return


def get_listings(listing_output_file_name,
                 retrieve_listings_from_scratch=False):
    if retrieve_listings_from_scratch:
        # Caveat: this update is only for items of Common rarity!
        update_all_listings_for_items_other_than_cards(rarity='common')

    return load_all_listings(listing_output_file_name)


def filter_out_candidates_whose_ask_price_is_below_threshold(all_listings,
                                                             item_rarity_patterns_per_app_id=None,
                                                             price_threshold_in_cents=None,
                                                             category_name=None,
                                                             drop_rate_estimates_for_common_rarity=None,
                                                             gem_price_in_euros=None,
                                                             verbose=True):
    if gem_price_in_euros is None:
        gem_price_in_euros = get_gem_price()

    if drop_rate_estimates_for_common_rarity is None:
        if category_name is not None and category_name != get_category_name_for_booster_packs():
            drop_rate_estimates = get_drop_rate_estimates_based_on_item_rarity_pattern(verbose=verbose)
            drop_rate_field = get_drop_rate_field()
            rarity_field = 'common'
            drop_rate_estimates_for_common_rarity = drop_rate_estimates[drop_rate_field][rarity_field]
        else:
            drop_rate_estimates_for_common_rarity = dict()

    gem_amount_required_to_craft_badge = get_gem_amount_required_to_craft_badge()

    badge_price = gem_amount_required_to_craft_badge * gem_price_in_euros

    # Build dummy badge data, in order to reuse functions developed for the analysis of Booster Packs

    badge_data = dict()
    for listing_hash in all_listings:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        item_rarity_pattern = item_rarity_patterns_per_app_id[app_id]

        num_items_of_common_rarity = item_rarity_pattern['common']
        num_items_of_uncommon_rarity = item_rarity_pattern['uncommon']
        num_items_of_rare_rarity = item_rarity_pattern['rare']

        item_rarity_pattern_as_tuple = (num_items_of_common_rarity,
                                        num_items_of_uncommon_rarity,
                                        num_items_of_rare_rarity)

        try:
            drop_rate_for_common_rarity = drop_rate_estimates_for_common_rarity[item_rarity_pattern_as_tuple]
        except KeyError:
            drop_rate_for_common_rarity = 1  # Here, 1 would represent 100% chance to receive an item of common rarity.

        drop_rate_for_common_rarity = clamp_proportion(drop_rate_for_common_rarity)

        item_price_by_crafting_badges = num_items_of_common_rarity * badge_price / drop_rate_for_common_rarity

        sell_price_in_cents = all_listings[listing_hash]['sell_price']
        sell_price_in_euros = sell_price_in_cents / 100

        # In order to distinguish items linked to the same appID, dummy appIDs are introduced:
        dummy_app_id = listing_hash

        badge_data[dummy_app_id] = dict()
        badge_data[dummy_app_id]['listing_hash'] = listing_hash
        badge_data[dummy_app_id]['sell_price'] = sell_price_in_euros
        badge_data[dummy_app_id]['gem_price'] = item_price_by_crafting_badges

    # Filter out candidates for which the ask is below a given threshold

    filtered_badge_data = filter_out_badges_with_low_sell_price(badge_data,
                                                                category_name=category_name,
                                                                user_chosen_price_threshold=price_threshold_in_cents)

    return filtered_badge_data


def get_market_orders(filtered_badge_data,
                      retrieve_market_orders_online,
                      focus_on_listing_hashes_never_seen_before,
                      listing_details_output_file_name,
                      market_order_output_file_name):
    # Load market orders (bid, ask) from disk

    market_order_dict = load_market_order_data_from_disk(market_order_output_file_name=market_order_output_file_name)

    # Filter out listing hashes which have already been encountered at least once

    first_encountered_filtered_badge_data = dict()

    for dummy_app_id in filtered_badge_data:
        if filtered_badge_data[dummy_app_id]['listing_hash'] not in market_order_dict:
            first_encountered_filtered_badge_data[dummy_app_id] = filtered_badge_data[dummy_app_id]

    # Retrieval of market orders (bid, ask)

    if focus_on_listing_hashes_never_seen_before:
        badge_data_to_process = first_encountered_filtered_badge_data
    else:
        badge_data_to_process = filtered_badge_data

    if retrieve_market_orders_online and len(badge_data_to_process) > 0:
        market_order_dict = download_market_order_data_batch(badge_data_to_process,
                                                             market_order_dict=market_order_dict,
                                                             market_order_output_file_name=market_order_output_file_name,
                                                             listing_details_output_file_name=listing_details_output_file_name)

    # After the **most comprehensive** dictionary of market orders has been loaded from disk by:
    #       `load_market_order_data_from_disk()`
    # then partially updated, and saved to disk by:
    #       `download_market_order_data_batch()`
    # we can edit the dictionary to filter out listing hashes which were not requested by the user, following the input:
    #       `filtered_badge_data`
    # and finally return the trimmed dictionary as the output of the current function call:
    #       `get_market_orders(filtered_badge_data, ...)`

    available_listing_hashes = [listing_hash for listing_hash in market_order_dict]

    selected_listing_hashes = [filtered_badge_data[app_id]['listing_hash'] for app_id in filtered_badge_data.keys()]

    for listing_hash in available_listing_hashes:
        if listing_hash not in selected_listing_hashes:
            del market_order_dict[listing_hash]

    return market_order_dict


def count_listing_hashes_per_app_id(all_listings):
    # For each appID, count the number of known listing hashes.
    #
    # Caveat: this piece of information relies on the downloaded listings, it is NOT NECESSARILY accurate!
    #         Errors can happen, so manually double-check any information before using it for critical usage!
    #
    # If 'all_listings' is constrained to items of 'Common' rarity, then this is the number of **different** items of
    # such rarity. This information is useful to know whether a gamble is worth a try: the more items of Common rarity,
    # the harder it is to receive the item which you are specifically after, by crafting a badge.

    listing_hashes_per_app_id = {}

    for listing_hash in all_listings:
        app_id = convert_listing_hash_to_app_id(listing_hash)
        try:
            listing_hashes_per_app_id[app_id] += 1
        except KeyError:
            listing_hashes_per_app_id[app_id] = 1

    return listing_hashes_per_app_id


def get_listings_with_other_rarity_tags(look_for_profile_backgrounds,
                                        retrieve_listings_with_another_rarity_tag_from_scratch=False):
    if retrieve_listings_with_another_rarity_tag_from_scratch:
        other_rarity_fields = set(get_rarity_fields()).difference({'common'})
        for rarity_tag in other_rarity_fields:
            update_all_listings_for_items_other_than_cards(rarity=rarity_tag)

    if look_for_profile_backgrounds:
        all_listings_for_uncommon = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_profile_backgrounds(rarity='uncommon')
        )
        all_listings_for_rare = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_profile_backgrounds(rarity='rare')
        )

    else:
        all_listings_for_uncommon = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_emoticons(rarity='uncommon')
        )
        all_listings_for_rare = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_emoticons(rarity='rare')
        )

    return all_listings_for_uncommon, all_listings_for_rare


def enumerate_item_rarity_patterns(listing_hashes_per_app_id_for_common,
                                   listing_hashes_per_app_id_for_uncommon,
                                   listing_hashes_per_app_id_for_rare):
    all_app_ids = set(listing_hashes_per_app_id_for_common)
    all_app_ids = all_app_ids.union(listing_hashes_per_app_id_for_uncommon)
    all_app_ids = all_app_ids.union(listing_hashes_per_app_id_for_rare)

    item_rarity_patterns_per_app_id = {}

    for app_id in all_app_ids:
        item_rarity_patterns_per_app_id[app_id] = {}

        try:
            num_common = listing_hashes_per_app_id_for_common[app_id]
        except KeyError:
            num_common = None

        try:
            num_uncommon = listing_hashes_per_app_id_for_uncommon[app_id]
        except KeyError:
            num_uncommon = None

        try:
            num_rare = listing_hashes_per_app_id_for_rare[app_id]
        except KeyError:
            num_rare = None

        item_rarity_patterns_per_app_id[app_id]['common'] = num_common
        item_rarity_patterns_per_app_id[app_id]['uncommon'] = num_uncommon
        item_rarity_patterns_per_app_id[app_id]['rare'] = num_rare

    return item_rarity_patterns_per_app_id


def main(look_for_profile_backgrounds=True,  # if True, profile backgrounds, otherwise, emoticons.
         retrieve_listings_from_scratch=False,
         retrieve_listings_with_another_rarity_tag_from_scratch=False,
         retrieve_market_orders_online=True,
         focus_on_listing_hashes_never_seen_before=True,
         price_threshold_in_cents=None,
         drop_rate_estimates_for_common_rarity=None,
         num_packs_to_display=10):
    if look_for_profile_backgrounds:
        category_name = get_category_name_for_profile_backgrounds()
        listing_output_file_name = get_listing_output_file_name_for_profile_backgrounds()
        listing_details_output_file_name = get_listing_details_output_file_name_for_profile_backgrounds()
        market_order_output_file_name = get_market_order_file_name_for_profile_backgrounds()
    else:
        category_name = get_category_name_for_emoticons()
        listing_output_file_name = get_listing_output_file_name_for_emoticons()
        listing_details_output_file_name = get_listing_details_output_file_name_for_emoticons()
        market_order_output_file_name = get_market_order_file_name_for_emoticons()

    # Load list of all listing hashes with common rarity tag

    all_listings = get_listings(listing_output_file_name=listing_output_file_name,
                                retrieve_listings_from_scratch=retrieve_listings_from_scratch)

    # Count the number of **different** items with common rarity tag for each appID

    listing_hashes_per_app_id_for_common = count_listing_hashes_per_app_id(all_listings)

    # Load list of all listing hashes with other rarity tags (uncommon and rare)

    all_listings_for_uncommon, all_listings_for_rare = get_listings_with_other_rarity_tags(
        look_for_profile_backgrounds=look_for_profile_backgrounds,
        retrieve_listings_with_another_rarity_tag_from_scratch=retrieve_listings_with_another_rarity_tag_from_scratch,
    )

    # Count the number of **different** items with other rarity tags (uncommon and rare)  for each appID

    listing_hashes_per_app_id_for_uncommon = count_listing_hashes_per_app_id(all_listings_for_uncommon)
    listing_hashes_per_app_id_for_rare = count_listing_hashes_per_app_id(all_listings_for_rare)

    # Enumerate patterns C/UC/R for each appID

    item_rarity_patterns_per_app_id = enumerate_item_rarity_patterns(listing_hashes_per_app_id_for_common,
                                                                     listing_hashes_per_app_id_for_uncommon,
                                                                     listing_hashes_per_app_id_for_rare)

    # *Heuristic* filtering of listing hashes

    filtered_badge_data = filter_out_candidates_whose_ask_price_is_below_threshold(all_listings,
                                                                                   item_rarity_patterns_per_app_id=item_rarity_patterns_per_app_id,
                                                                                   price_threshold_in_cents=price_threshold_in_cents,
                                                                                   drop_rate_estimates_for_common_rarity=drop_rate_estimates_for_common_rarity,
                                                                                   category_name=category_name)

    # Pre-retrieval of item name ids

    selected_listing_hashes = [filtered_badge_data[app_id]['listing_hash'] for app_id in filtered_badge_data.keys()]

    item_nameids = get_item_nameid_batch(selected_listing_hashes,
                                         listing_details_output_file_name=listing_details_output_file_name)

    # Download market orders

    market_order_dict = get_market_orders(filtered_badge_data,
                                          retrieve_market_orders_online,
                                          focus_on_listing_hashes_never_seen_before,
                                          listing_details_output_file_name,
                                          market_order_output_file_name)

    # Only keep marketable booster packs

    marketable_market_order_dict, unknown_market_order_dict = filter_out_unmarketable_packs(market_order_dict)

    # Sort by bid value
    hashes_for_best_bid = sort_according_to_buzz(market_order_dict,
                                                 marketable_market_order_dict)

    # Display the highest ranked booster packs

    print_packs_with_high_buzz(hashes_for_best_bid,
                               market_order_dict,
                               item_rarity_patterns_per_app_id=item_rarity_patterns_per_app_id,
                               category_name=category_name,
                               num_packs_to_display=num_packs_to_display)

    # Detect potential arbitrages

    badge_arbitrages = find_badge_arbitrages(filtered_badge_data,
                                             market_order_dict)

    print('\n# Results for detected *potential* arbitrages\n')
    print_arbitrages(badge_arbitrages,
                     use_numbered_bullet_points=True,
                     use_hyperlink=True)

    return True


if __name__ == '__main__':
    main(look_for_profile_backgrounds=True,  # if True, profile backgrounds, otherwise, emoticons.
         retrieve_listings_from_scratch=False,
         retrieve_listings_with_another_rarity_tag_from_scratch=False,
         retrieve_market_orders_online=True,
         focus_on_listing_hashes_never_seen_before=True,
         price_threshold_in_cents=None,
         drop_rate_estimates_for_common_rarity=None,
         num_packs_to_display=100)
