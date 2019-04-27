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

    sell_price_is_unknown = bool(sell_price_including_fee < 0)

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
                          verbose=True):
    if market_order_dict is None:
        market_order_dict = update_market_order_data_batch(badge_data)

    badge_arbitrages = dict()

    for app_id in badge_data.keys():
        individual_badge_data = badge_data[app_id]

        gem_price_with_fee = individual_badge_data['gem_price']

        listing_hash = individual_badge_data['listing_hash']

        bid_including_fee = market_order_dict[listing_hash]['bid']
        bid_without_fee = compute_sell_price_without_fee(bid_including_fee)

        if bid_including_fee < 0:
            continue

        delta = bid_without_fee - gem_price_with_fee

        if delta > 0:
            badge_arbitrages[listing_hash] = dict()
            badge_arbitrages[listing_hash]['profit'] = delta

            if verbose:
                print('{:.2f}€\t{}'.format(delta, listing_hash))

    # TODO rank them according to the highest bid
    # TODO manually adapt compute_sell_price_without_fee() to fit Steam's computations perfectly (below 25 cents)

    return badge_arbitrages


def main(retrieve_market_orders_from_scratch=False):
    aggregated_badge_data = load_aggregated_badge_data()

    filtered_badge_data = filter_out_badges_with_low_sell_price(aggregated_badge_data)

    if retrieve_market_orders_from_scratch:
        market_order_dict = update_market_order_data_batch(filtered_badge_data)
    else:
        market_order_dict = load_market_order_data()

    badge_arbitrages = find_badge_arbitrages(filtered_badge_data,
                                             market_order_dict)

    return True


if __name__ == '__main__':
    main()
