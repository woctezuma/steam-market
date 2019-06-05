# Objective: detect the buzz, for games which I do not own yet, i.e. find packs which are likely to have high bid orders

from market_listing import get_item_nameid_batch
from market_order import load_market_order_data
from market_search import load_all_listings, update_all_listings
from utils import convert_listing_hash_to_app_id, get_steamcardexchange_url, get_steam_store_url


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
                               num_packs_to_display=10):
    print('# Packs with high buy orders\n')

    for i, listing_hash in enumerate(hashes_for_best_bid):

        if i >= num_packs_to_display:
            break

        app_id = convert_listing_hash_to_app_id(listing_hash)

        bid = market_order_dict[listing_hash]['bid']
        bid_volume = market_order_dict[listing_hash]['bid_volume']

        print('{:3}) [[store]({})] [{}]({}) ; bid: {}€ (volume: {})'.format(i + 1,
                                                                            get_steam_store_url(app_id),
                                                                            listing_hash,
                                                                            get_steamcardexchange_url(app_id),
                                                                            bid,
                                                                            bid_volume))

    return


def main(retrieve_listings_from_scratch=False,
         retrieve_market_orders_online=False,
         min_sell_price=30,
         min_num_listings=3,
         num_packs_to_display=10):
    # Load list of all listing hashes

    if retrieve_listings_from_scratch:
        update_all_listings()

    all_listings = load_all_listings()

    # *Heuristic* filtering of listing hashes

    filtered_listing_hashes = filter_listings(all_listings,
                                              min_sell_price=min_sell_price,
                                              min_num_listings=min_num_listings)

    # Pre-retrieval of item name ids

    item_nameids = get_item_nameid_batch(filtered_listing_hashes)

    # Download market orders

    badge_data = convert_to_badges(filtered_listing_hashes)

    market_order_dict = load_market_order_data(badge_data,
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

    return


if __name__ == '__main__':
    main(retrieve_listings_from_scratch=True,
         retrieve_market_orders_online=True,
         min_sell_price=30,
         min_num_listings=3,
         num_packs_to_display=100)
