from market_order import update_market_order_data_batch, load_market_order_data
from market_utils import load_aggregated_badge_data
from transaction_fee import compute_sell_price_without_fee


def determine_whether_an_arbitrage_might_exist(badge_data):
    sell_price_including_fee = badge_data['sell_price']
    sell_price_without_fee = compute_sell_price_without_fee(sell_price_including_fee)

    gem_price_with_fee = badge_data['gem_price']

    an_arbitrage_might_exist = bool(gem_price_with_fee < sell_price_without_fee)

    return an_arbitrage_might_exist


def determine_whether_sell_price_is_unknown(badge_data):
    sell_price_including_fee = badge_data['sell_price']

    sell_price_was_not_retrieved = bool(sell_price_including_fee < 0)
    there_is_no_sell_order = bool(sell_price_including_fee == 0)

    sell_price_is_unknown = sell_price_was_not_retrieved or there_is_no_sell_order

    return sell_price_is_unknown


def filter_out_badges_with_low_sell_price(aggregated_badge_data, verbose=True):
    # Filter out games for which the sell price (ask) is lower than the gem price,
    # because the bid is necessarily lower than the ask, so it will not be worth downloading bid data for these games.

    filtered_badge_data = dict()

    unknown_price_counter = 0

    for app_id in aggregated_badge_data.keys():
        individual_badge_data = aggregated_badge_data[app_id]

        sell_price_is_unknown = determine_whether_sell_price_is_unknown(individual_badge_data)

        an_arbitrage_might_exist = determine_whether_an_arbitrage_might_exist(individual_badge_data)

        if sell_price_is_unknown or an_arbitrage_might_exist:
            filtered_badge_data[app_id] = individual_badge_data

            if sell_price_is_unknown:
                unknown_price_counter += 1

    if verbose:
        print('There are {} booster packs with sell price unknown ({}) or strictly higher than gem price ({}).'.format(
            len(filtered_badge_data), unknown_price_counter, len(filtered_badge_data) - unknown_price_counter))

    return filtered_badge_data


def find_badge_arbitrages(badge_data,
                          market_order_dict=None,
                          verbose=False):
    if market_order_dict is None:
        market_order_dict = update_market_order_data_batch(badge_data)

    badge_arbitrages = dict()

    for app_id in badge_data.keys():
        individual_badge_data = badge_data[app_id]

        gem_price_including_fee = individual_badge_data['gem_price']

        listing_hash = individual_badge_data['listing_hash']

        bid_including_fee = market_order_dict[listing_hash]['bid']
        bid_without_fee = compute_sell_price_without_fee(bid_including_fee)

        if bid_including_fee < 0:
            continue

        delta = bid_without_fee - gem_price_including_fee

        if delta > 0.009:  # a profit of at least 1 cent (we check 0.99 cent due to floating point rounding)
            badge_arbitrages[listing_hash] = dict()
            badge_arbitrages[listing_hash]['app_id'] = app_id

            badge_arbitrages[listing_hash]['name'] = individual_badge_data['name']
            badge_arbitrages[listing_hash]['gem_amount'] = individual_badge_data['gem_amount']
            badge_arbitrages[listing_hash]['gem_price_including_fee'] = individual_badge_data['gem_price']
            badge_arbitrages[listing_hash]['sell_price'] = individual_badge_data['sell_price']

            badge_arbitrages[listing_hash]['ask_including_fee'] = market_order_dict[listing_hash]['ask']
            badge_arbitrages[listing_hash]['bid_including_fee'] = market_order_dict[listing_hash]['bid']
            badge_arbitrages[listing_hash]['is_marketable'] = market_order_dict[listing_hash]['is_marketable']

            badge_arbitrages[listing_hash]['bid_without_fee'] = bid_without_fee
            badge_arbitrages[listing_hash]['profit'] = delta

            if verbose:
                print('{:.2f}€\t{}'.format(delta, listing_hash))

    return badge_arbitrages


def print_arbitrages(badge_arbitrages):
    for listing_hash in sorted(badge_arbitrages.keys(), key=lambda x: badge_arbitrages[x]['profit'], reverse=True):
        arbitrage = badge_arbitrages[listing_hash]

        # Skip unmarketable booster packs
        if not arbitrage['is_marketable']:
            continue

        print('Profit: {:.2f}€\t{}\tcraft pack for {} gems ({:.2f}€)\t sell for {:.2f}€ ({:.2f}€ including fee)'.format(
            arbitrage['profit'],
            listing_hash,
            arbitrage['gem_amount'],
            arbitrage['gem_price_including_fee'],
            arbitrage['bid_without_fee'],
            arbitrage['bid_including_fee'],
        ))

    return


def apply_workflow(retrieve_market_orders_from_scratch=True):
    aggregated_badge_data = load_aggregated_badge_data()

    filtered_badge_data = filter_out_badges_with_low_sell_price(aggregated_badge_data)

    if retrieve_market_orders_from_scratch:
        market_order_dict = update_market_order_data_batch(filtered_badge_data)
    else:
        market_order_dict = load_market_order_data()

    badge_arbitrages = find_badge_arbitrages(filtered_badge_data,
                                             market_order_dict)

    print_arbitrages(badge_arbitrages)

    return True


def main():
    retrieve_market_orders_from_scratch = False

    apply_workflow(retrieve_market_orders_from_scratch=retrieve_market_orders_from_scratch)

    return True


if __name__ == '__main__':
    main()
