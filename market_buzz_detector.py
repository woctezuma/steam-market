# Objective: detect the buzz, for games which I do not own yet, i.e. find packs which are likely to have high bid orders

from download_steam_card_exchange import parse_data_from_steam_card_exchange
from market_arbitrage import filter_out_badges_with_low_sell_price
from market_arbitrage import find_badge_arbitrages, print_arbitrages
from market_listing import get_item_nameid_batch, get_steam_market_listing_url
from market_order import load_market_order_data
from market_search import load_all_listings, update_all_listings
from market_utils import filter_out_dubious_listing_hashes
from sack_of_gems import get_gem_price
from utils import convert_listing_hash_to_app_id, get_steamcardexchange_url, get_steam_store_url
from utils import convert_listing_hash_to_app_name
from utils import get_category_name_for_booster_packs


def filter_listings(all_listings=None,
                    min_sell_price=30,  # in cents
                    min_num_listings=20,  # to remove listings with very few sellers, who chose unrealistic sell prices
                    verbose=True):
    if all_listings is None:
        all_listings = load_all_listings()

    # Sort listing hashes with respect to the ask

    sorted_listing_hashes = sorted(all_listings,
                                   reverse=True,
                                   key=lambda x: all_listings[x]['sell_price'])

    # *Heuristic* filtering of listing hashes

    filtered_listing_hashes = list(filter(lambda x: all_listings[x]['sell_price'] >= min_sell_price and
                                                    all_listings[x]['sell_listings'] >= min_num_listings,
                                          sorted_listing_hashes))

    if verbose:
        print('{} hashes found.\n'.format(len(filtered_listing_hashes)))

    return filtered_listing_hashes


def convert_to_badges(filtered_listing_hashes,
                      max_num_badges=None):
    badge_data = dict()

    for i, listing_hash in enumerate(filtered_listing_hashes):

        if max_num_badges is not None and i >= max_num_badges:
            break

        app_id = convert_listing_hash_to_app_id(listing_hash)

        badge_data[app_id] = dict()
        badge_data[app_id]['listing_hash'] = listing_hash

    return badge_data


def filter_out_unmarketable_packs(market_order_dict):
    marketable_market_order_dict = dict()
    unknown_market_order_dict = dict()

    for listing_hash in market_order_dict:
        try:
            is_marketable = market_order_dict[listing_hash]['is_marketable']
        except KeyError:
            print('Marketable status not found for {}'.format(listing_hash))
            unknown_market_order_dict[listing_hash] = market_order_dict[listing_hash]

            is_marketable = False  # avoid taking any risk: ASSUME the booster pack is NOT marketable

        if is_marketable:
            marketable_market_order_dict[listing_hash] = market_order_dict[listing_hash]

    return marketable_market_order_dict, unknown_market_order_dict


def sort_according_to_buzz(market_order_dict,
                           marketable_market_order_dict=None):
    if marketable_market_order_dict is None:
        marketable_market_order_dict, unknown_market_order_dict = filter_out_unmarketable_packs(market_order_dict)

    hashes_for_best_bid = sorted(list(marketable_market_order_dict),
                                 reverse=True,
                                 key=lambda x: market_order_dict[x]['bid'])

    return hashes_for_best_bid


def print_packs_with_high_buzz(hashes_for_best_bid,
                               market_order_dict,
                               item_rarity_patterns_per_app_id=None,
                               category_name=None,
                               num_packs_to_display=10):
    if category_name is None:
        category_name = get_category_name_for_booster_packs()

    print('# {} with high buy orders\n'.format(category_name.capitalize()))

    for i, listing_hash in enumerate(hashes_for_best_bid):

        if i >= num_packs_to_display:
            break

        app_id = convert_listing_hash_to_app_id(listing_hash)
        app_name = convert_listing_hash_to_app_name(listing_hash)

        bid = market_order_dict[listing_hash]['bid']
        bid_volume = market_order_dict[listing_hash]['bid_volume']

        markdown_compatible_steam_market_url = get_steam_market_listing_url(listing_hash=listing_hash,
                                                                            render_as_json=False,
                                                                            replace_spaces=True)

        if category_name != get_category_name_for_booster_packs():
            # Display the listing hash, because we cannot extract the app name from the listing hash for:
            # - profile backgrounds,
            # - and emoticons.
            app_name = listing_hash

        try:
            item_rarity_pattern = item_rarity_patterns_per_app_id[app_id]

            num_different_items_of_common_rarity = item_rarity_pattern['common']
            num_different_items_of_uncommon_rarity = item_rarity_pattern['uncommon']
            num_different_items_of_rare_rarity = item_rarity_pattern['rare']

            item_rarity_pattern_info = ' ; rarity pattern C/UC/R: {}/{}/{} items'.format(
                num_different_items_of_common_rarity,
                num_different_items_of_uncommon_rarity,
                num_different_items_of_rare_rarity,
            )
        except TypeError:
            item_rarity_pattern_info = ''

        print('{:3}) [[store]({})][[market]({})] [{}]({}) ; bid: {}€ (volume: {}){}'.format(
            i + 1,
            get_steam_store_url(app_id),
            markdown_compatible_steam_market_url,
            app_name,
            get_steamcardexchange_url(app_id),
            bid,
            bid_volume,
            item_rarity_pattern_info))

    return


def fill_in_badge_data_with_data_from_steam_card_exchange(all_listings,
                                                          aggregated_badge_data=None,
                                                          force_update_from_steam_card_exchange=False,
                                                          enforced_sack_of_gems_price=None,
                                                          minimum_allowed_sack_of_gems_price=None):
    if aggregated_badge_data is None:
        aggregated_badge_data = convert_to_badges(all_listings)

    dico = parse_data_from_steam_card_exchange(
        force_update_from_steam_card_exchange=force_update_from_steam_card_exchange)

    retrieve_gem_price_from_scratch = bool(enforced_sack_of_gems_price is None)

    gem_price = get_gem_price(enforced_sack_of_gems_price=enforced_sack_of_gems_price,
                              minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
                              retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch)

    for app_id in aggregated_badge_data:
        listing_hash = aggregated_badge_data[app_id]['listing_hash']

        sell_price_in_cents = all_listings[listing_hash]['sell_price']
        sell_price_in_euros = sell_price_in_cents / 100

        try:
            data_from_steam_card_exchange = dico[app_id]
        except KeyError:
            print('No data found for appID={}.'.format(app_id))
            data_from_steam_card_exchange = {
                'name': None,
                'gem_amount': 1200,  # by default, use the highest possible value
            }

        aggregated_badge_data[app_id]['name'] = data_from_steam_card_exchange['name']
        gem_amount_required_to_craft_booster_pack = data_from_steam_card_exchange['gem_amount']

        aggregated_badge_data[app_id]['gem_amount'] = gem_amount_required_to_craft_booster_pack
        aggregated_badge_data[app_id]['gem_price'] = gem_amount_required_to_craft_booster_pack * gem_price
        aggregated_badge_data[app_id]['sell_price'] = sell_price_in_euros

    return aggregated_badge_data


def main(retrieve_listings_from_scratch=False,
         retrieve_market_orders_online=False,
         force_update_from_steam_card_exchange=False,
         enforced_sack_of_gems_price=None,
         minimum_allowed_sack_of_gems_price=None,
         use_a_constant_price_threshold=False,
         min_sell_price=30,
         min_num_listings=3,
         num_packs_to_display=10):
    # Load list of all listing hashes

    if retrieve_listings_from_scratch:
        update_all_listings()

    all_listings = load_all_listings()

    all_listings = filter_out_dubious_listing_hashes(all_listings)

    # Import information from SteamCardExchange

    aggregated_badge_data = fill_in_badge_data_with_data_from_steam_card_exchange(all_listings,
                                                                                  force_update_from_steam_card_exchange=force_update_from_steam_card_exchange,
                                                                                  enforced_sack_of_gems_price=enforced_sack_of_gems_price,
                                                                                  minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price)

    # *Heuristic* filtering of listing hashes

    if use_a_constant_price_threshold:
        filtered_listing_hashes = filter_listings(all_listings,
                                                  min_sell_price=min_sell_price,
                                                  min_num_listings=min_num_listings)

        filtered_badge_data = fill_in_badge_data_with_data_from_steam_card_exchange(filtered_listing_hashes,
                                                                                    force_update_from_steam_card_exchange=force_update_from_steam_card_exchange,
                                                                                    enforced_sack_of_gems_price=enforced_sack_of_gems_price,
                                                                                    minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price)

    else:
        filtered_badge_data = filter_out_badges_with_low_sell_price(aggregated_badge_data)

        filtered_listing_hashes = [filtered_badge_data[app_id]['listing_hash']
                                   for app_id in filtered_badge_data]

    # Pre-retrieval of item name ids

    item_nameids = get_item_nameid_batch(filtered_listing_hashes)

    # Download market orders

    market_order_dict = load_market_order_data(filtered_badge_data,
                                               trim_output=True,
                                               retrieve_market_orders_online=retrieve_market_orders_online)

    # Only keep marketable booster packs

    marketable_market_order_dict, unknown_market_order_dict = filter_out_unmarketable_packs(market_order_dict)

    # Sort by bid value
    hashes_for_best_bid = sort_according_to_buzz(market_order_dict,
                                                 marketable_market_order_dict)

    # Display the highest ranked booster packs

    print_packs_with_high_buzz(hashes_for_best_bid,
                               market_order_dict,
                               num_packs_to_display=num_packs_to_display)

    # Detect potential arbitrages

    badge_arbitrages = find_badge_arbitrages(filtered_badge_data,
                                             market_order_dict)

    print('\n# Results for detected *potential* arbitrages\n')
    print_arbitrages(badge_arbitrages,
                     use_hyperlink=True)

    return


if __name__ == '__main__':
    main(retrieve_listings_from_scratch=True,
         retrieve_market_orders_online=True,
         force_update_from_steam_card_exchange=True,
         enforced_sack_of_gems_price=None,
         minimum_allowed_sack_of_gems_price=None,
         use_a_constant_price_threshold=False,
         min_sell_price=30,
         min_num_listings=3,
         num_packs_to_display=100)
