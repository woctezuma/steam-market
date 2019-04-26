from market_utils import load_aggregated_badge_data
from transaction_fee import compute_sell_price_without_fee


def filter_out_badges_with_low_sell_price(aggregated_badge_data, verbose=True):
    # Filter out games for which the sell price (ask) is lower than the gem price,
    # because the bid is necessarily lower than the ask, so it will not be worth downloading bid data for these games.

    filtered_badge_data = dict()

    unknown_price_counter = 0

    for app_id in aggregated_badge_data.keys():
        sell_price_including_fee = aggregated_badge_data[app_id]['sell_price']
        sell_price_without_fee = compute_sell_price_without_fee(sell_price_including_fee)

        gem_price_with_fee = aggregated_badge_data[app_id]['gem_price']

        if (sell_price_including_fee < 0) or (gem_price_with_fee < sell_price_without_fee):
            filtered_badge_data[app_id] = aggregated_badge_data[app_id]

            if sell_price_including_fee < 0:
                unknown_price_counter += 1

    if verbose:
        print('There are {} booster packs with sell price unknown ({}) or strictly higher than gem price ({}).'.format(
            len(filtered_badge_data), unknown_price_counter, len(filtered_badge_data) - unknown_price_counter))

    return filtered_badge_data


def download_bid_data(aggregated_badge_data):
    # TODO Finally, beautifulsoup to get the bid for the remaining games, and rank them according to the highest bid.
    return


def find_badge_arbitrages(aggregated_badge_data):
    return


def main():
    aggregated_badge_data = load_aggregated_badge_data()

    filtered_badge_data = filter_out_badges_with_low_sell_price(aggregated_badge_data)

    return True


if __name__ == '__main__':
    main()
