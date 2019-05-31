from market_listing import get_item_nameid_batch
from market_order import load_market_order_data
from market_search import load_all_listings, update_all_listings
from utils import convert_listing_hash_to_app_id


def filter_listings(all_listings=None,
                    min_sell_price=15,  # in cents
                    min_num_listings=0,  # to remove listings with very few sellers, who chose unrealistic sell prices
                    verbose=True):
    if all_listings is None:
        all_listings = load_all_listings()

    # Sort listing hashes with respect to the ask

    sorted_listing_hashes = sorted(all_listings,
                                   reverse=True,
                                   key=lambda x: all_listings[x]['sell_price'])

    # *Heuristic* filtering of listing hashes

    filtered_listing_hashes = list(filter(lambda x: all_listings[x]['sell_price'] > min_sell_price and
                                                    all_listings[x]['sell_listings'] > min_num_listings,
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
    marketable_market_order_dict = filter(lambda x: market_order_dict[x]['is_marketable'],
                                          market_order_dict)

    return marketable_market_order_dict


def sort_according_to_buzz(market_order_dict,
                           marketable_market_order_dict=None):
    if marketable_market_order_dict is None:
        marketable_market_order_dict = filter_out_unmarketable_packs(market_order_dict)

    hashes_for_best_bid = sorted(list(marketable_market_order_dict),
                                 reverse=True,
                                 key=lambda x: market_order_dict[x]['bid'])

    return hashes_for_best_bid


def print_packs_with_high_buzz(hashes_for_best_bid,
                               all_listings,
                               market_order_dict,
                               num_packs=10):
    for i, listing_hash in enumerate(hashes_for_best_bid):

        if i >= num_packs:
            break

        print(listing_hash)
        print(all_listings[listing_hash])
        print(market_order_dict[listing_hash])

    return


def main(process_all=False):
    # Load list of all listing hashes

    if process_all:
        update_all_listings()

    all_listings = load_all_listings()

    filtered_listing_hashes = filter_listings(all_listings,
                                              min_sell_price=15,
                                              min_num_listings=0)

    # Pre-retrieval of item name ids

    item_nameids = get_item_nameid_batch(filtered_listing_hashes)

    if process_all:
        # Download market orders

        badge_data = convert_to_badges(filtered_listing_hashes)

        market_order_dict = load_market_order_data(badge_data)

        # Only keep marketable booster packs

        marketable_market_order_dict = filter_out_unmarketable_packs(market_order_dict)

        # Sort by bid value
        hashes_for_best_bid = sort_according_to_buzz(market_order_dict,
                                                     marketable_market_order_dict)

        # Display the highest ranked booster packs

        print_packs_with_high_buzz(hashes_for_best_bid,
                                   all_listings,
                                   market_order_dict)

        # NB: a booster pack costs an amount of gems equal to: 6000 / num_cards
        #
        # TODO manually check the number of cards, store page, market page at:
        #  https://www.steamcardexchange.net/index.php?gamepage-appid-427240

    return


if __name__ == '__main__':
    main()
