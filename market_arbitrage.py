# Objective: find market arbitrages, e.g. sell a pack for more (fee excluded) than the cost to craft it (fee included).


from creation_time_utils import (
    determine_whether_a_booster_pack_can_be_crafted,
    fill_in_badges_with_next_creation_times_loaded_from_disk,
    get_current_time,
)
from inventory_utils import create_then_sell_booster_packs_for_batch
from market_listing import get_steam_market_listing_url, update_marketability_status
from market_order import load_market_order_data
from market_utils import load_aggregated_badge_data
from sack_of_gems import print_gem_price_reminder
from transaction_fee import compute_sell_price_without_fee
from utils import (
    convert_listing_hash_to_app_id,
    get_bullet_point_for_display,
    get_steam_store_url,
    get_steamcardexchange_url,
)


def determine_whether_booster_pack_was_crafted_at_least_once(badge_data: dict) -> bool:
    next_creation_time = badge_data['next_creation_time']

    booster_pack_has_been_crafted_at_least_once = bool(next_creation_time is not None)

    return booster_pack_has_been_crafted_at_least_once


def filter_out_badges_never_crafted(
    aggregated_badge_data: dict[int, dict],
    verbose: bool = True,
) -> dict[int, dict]:
    # Filter out games for which a booster pack was never crafted (according to 'data/next_creation_times.json'),
    # thus focus on games which are tracked more closely, because they are likely to show a market arbitrage (again).

    filtered_badge_data = dict()

    for app_id in aggregated_badge_data.keys():
        individual_badge_data = aggregated_badge_data[app_id]

        booster_pack_is_tracked = determine_whether_booster_pack_was_crafted_at_least_once(
            individual_badge_data,
        )

        if booster_pack_is_tracked:
            filtered_badge_data[app_id] = individual_badge_data

    if verbose:
        print(
            'There are {} booster packs which are tracked, as they were crafted at least once. ({} omitted)'.format(
                len(filtered_badge_data),
                len(aggregated_badge_data) - len(filtered_badge_data),
            ),
        )

    return filtered_badge_data


def filter_out_badges_recently_crafted(
    aggregated_badge_data: dict[int, dict],
    verbose: bool = True,
) -> dict[int, dict]:
    # Filter out games for which a booster pack was crafted less than 24 hours ago,
    # and thus which cannot be immediately crafted.

    filtered_badge_data = dict()

    current_time = get_current_time()

    for app_id in aggregated_badge_data.keys():
        individual_badge_data = aggregated_badge_data[app_id]

        booster_pack_can_be_crafted = determine_whether_a_booster_pack_can_be_crafted(
            individual_badge_data,
            current_time,
        )

        if booster_pack_can_be_crafted:
            filtered_badge_data[app_id] = individual_badge_data

    if verbose:
        print(
            'There are {} booster packs which can be immediately crafted. ({} excluded because of cooldown)'.format(
                len(filtered_badge_data),
                len(aggregated_badge_data) - len(filtered_badge_data),
            ),
        )

    return filtered_badge_data


def determine_whether_an_arbitrage_might_exist(
    badge_data: dict,
    user_chosen_price_threshold: float = None,
) -> bool:
    sell_price_including_fee = badge_data['sell_price']
    sell_price_without_fee = compute_sell_price_without_fee(sell_price_including_fee)

    try:
        gem_price_with_fee = badge_data['gem_price']
    except KeyError:
        # This should only happen if the badge data is dummy (for profile backgrounds and emoticons). Typically, the
        # user prefers to rely on a user-chosen price threshold, and did not take the time to fill-in a dummy value for
        # the 'gem_price' field in badge_data.
        gem_price_with_fee = None

    if user_chosen_price_threshold is None:
        # Variable price threshold, automatically computed for each game.
        # Always use this option if you work with BOOSTER PACKS, because the cost to craft a pack changes for each game!
        price_threshold = gem_price_with_fee
    else:
        # Constant price threshold, enforced by the user.
        # Caveat: this is only useful to prune out candidates for PROFILE BACKGROUNDS or EMOTICONS, because the cost to
        #         craft a **badge** does not depend on the game, contrary to the cost to craft a **booster pack**.
        price_threshold = user_chosen_price_threshold

    if price_threshold is None:
        raise AssertionError()

    an_arbitrage_might_exist = bool(price_threshold < sell_price_without_fee)

    return an_arbitrage_might_exist


def determine_whether_sell_price_is_unknown(badge_data: dict) -> bool:
    sell_price_including_fee = badge_data['sell_price']

    sell_price_was_not_retrieved = bool(sell_price_including_fee < 0)
    there_is_no_sell_order = bool(sell_price_including_fee == 0)

    sell_price_is_unknown = sell_price_was_not_retrieved or there_is_no_sell_order

    return sell_price_is_unknown


def filter_out_badges_with_low_sell_price(
    aggregated_badge_data: dict[int | str, dict],
    user_chosen_price_threshold: float = None,
    category_name: str = None,
    verbose: bool = True,
) -> dict[int | str, dict]:
    # Filter out games for which the sell price (ask) is lower than the gem price,
    # because the bid is necessarily lower than the ask, so it will not be worth downloading bid data for these games.

    if category_name is None:
        category_name = 'booster packs'

    if user_chosen_price_threshold is None:
        threshold_name = 'gem price'
    else:
        threshold_name = f'user-chosen price threshold {user_chosen_price_threshold / 100:.2f} €'

    filtered_badge_data = dict()

    unknown_price_counter = 0

    for app_id in aggregated_badge_data.keys():
        individual_badge_data = aggregated_badge_data[app_id]

        sell_price_is_unknown = determine_whether_sell_price_is_unknown(
            individual_badge_data,
        )

        an_arbitrage_might_exist = determine_whether_an_arbitrage_might_exist(
            individual_badge_data,
            user_chosen_price_threshold=user_chosen_price_threshold,
        )

        if sell_price_is_unknown or an_arbitrage_might_exist:
            filtered_badge_data[app_id] = individual_badge_data

            if sell_price_is_unknown:
                unknown_price_counter += 1

    if verbose:
        print(
            'There are {} {} with sell price unknown ({}) or strictly higher than {} ({}).'.format(
                len(filtered_badge_data),
                category_name,
                unknown_price_counter,
                threshold_name,
                len(filtered_badge_data) - unknown_price_counter,
            ),
        )

    return filtered_badge_data


def find_badge_arbitrages(
    badge_data: dict,
    market_order_dict: dict[str, dict] = None,
    verbose: bool = False,
) -> dict[str, dict]:
    if market_order_dict is None:
        market_order_dict = load_market_order_data(
            badge_data,
            retrieve_market_orders_online=True,
            verbose=verbose,
        )

    badge_arbitrages = dict()

    for app_id in badge_data.keys():
        individual_badge_data = badge_data[app_id]

        gem_price_including_fee = individual_badge_data['gem_price']

        listing_hash = individual_badge_data['listing_hash']

        try:
            bid_including_fee = market_order_dict[listing_hash]['bid']
        except KeyError:
            bid_including_fee = -1

            if verbose:
                print(
                    'Bid not found for {}. Reason is likely that you asked not to retrieve market orders.'.format(
                        listing_hash,
                    ),
                )

        bid_without_fee = compute_sell_price_without_fee(bid_including_fee)

        if bid_including_fee < 0:
            continue

        delta = bid_without_fee - gem_price_including_fee

        # Check whether there is a profit to be made
        is_an_arbitrage = bool(delta > 0)

        if is_an_arbitrage:
            badge_arbitrages[listing_hash] = dict()

            # Warning: for profile backgrounds and emoticons, you cannot trust the value of app_id stored here,
            #          because app_id is a dummy variable, which is simply a copy of listing_hash.
            #
            #          However, for booster packs, app_id is correct, because there is a one-to-one mapping between
            #          appIDs and listing hashes of booster packs.
            badge_arbitrages[listing_hash]['app_id'] = app_id

            try:
                badge_arbitrages[listing_hash]['name'] = individual_badge_data['name']
            except KeyError:
                badge_arbitrages[listing_hash]['name'] = None
            try:
                badge_arbitrages[listing_hash]['gem_amount'] = individual_badge_data['gem_amount']
            except KeyError:
                badge_arbitrages[listing_hash]['gem_amount'] = None
            badge_arbitrages[listing_hash]['gem_price_including_fee'] = individual_badge_data['gem_price']
            badge_arbitrages[listing_hash]['sell_price'] = individual_badge_data['sell_price']

            badge_arbitrages[listing_hash]['ask_including_fee'] = market_order_dict[listing_hash]['ask']
            badge_arbitrages[listing_hash]['bid_including_fee'] = market_order_dict[listing_hash]['bid']
            badge_arbitrages[listing_hash]['ask_volume'] = market_order_dict[listing_hash]['ask_volume']
            badge_arbitrages[listing_hash]['bid_volume'] = market_order_dict[listing_hash]['bid_volume']
            badge_arbitrages[listing_hash]['is_marketable'] = market_order_dict[listing_hash]['is_marketable']

            badge_arbitrages[listing_hash]['bid_without_fee'] = bid_without_fee
            badge_arbitrages[listing_hash]['profit'] = delta

            if verbose:
                print(f'{delta:.2f}€\t{listing_hash}')

    return badge_arbitrages


def print_arbitrages(
    badge_arbitrages: dict[str, dict],
    use_numbered_bullet_points: bool = False,
    use_hyperlink: bool = False,
) -> None:
    bullet_point = get_bullet_point_for_display(
        use_numbered_bullet_points=use_numbered_bullet_points,
    )

    for listing_hash in sorted(
        badge_arbitrages.keys(),
        key=lambda x: badge_arbitrages[x]['profit'],
        reverse=True,
    ):
        arbitrage = badge_arbitrages[listing_hash]

        # Skip unmarketable booster packs
        if not arbitrage['is_marketable']:
            continue

        if use_hyperlink:
            app_id = convert_listing_hash_to_app_id(listing_hash)

            markdown_compatible_steam_market_url = get_steam_market_listing_url(
                listing_hash=listing_hash,
                render_as_json=False,
                replace_spaces=True,
            )

            listing_hash_formatted_for_markdown = '[[store]({})][[market]({})] [{}]({})'.format(
                get_steam_store_url(app_id),
                markdown_compatible_steam_market_url,
                listing_hash,
                get_steamcardexchange_url(app_id),
            )
        else:
            listing_hash_formatted_for_markdown = listing_hash

        gem_amount = arbitrage['gem_amount']

        if gem_amount is None:
            gem_amount_as_str = gem_amount
        else:
            gem_amount_as_str = f'{gem_amount:.0f}'

        print(
            '{}Profit: {:.2f}€\t{}\t| craft pack: {} gems ({:.2f}€) | sell for {:.2f}€ ({:.2f}€ incl. fee) (#={})'.format(
                bullet_point,
                arbitrage['profit'],
                listing_hash_formatted_for_markdown,
                gem_amount_as_str,
                arbitrage['gem_price_including_fee'],
                arbitrage['bid_without_fee'],
                arbitrage['bid_including_fee'],
                arbitrage['bid_volume'],
            ),
        )


def convert_arbitrages_for_batch_create_then_sell(
    badge_arbitrages: dict[str, dict],
    profit_threshold: float = 0.01,  # profit in euros
    verbose: bool = True,
) -> dict[str, float]:
    # Code inspired from print_arbitrages()

    price_dict_for_listing_hashes = dict()

    for listing_hash in sorted(
        badge_arbitrages.keys(),
        key=lambda x: badge_arbitrages[x]['profit'],
        reverse=True,
    ):
        arbitrage = badge_arbitrages[listing_hash]

        # Skip unmarketable booster packs
        if not arbitrage['is_marketable']:
            continue

        if arbitrage['profit'] < profit_threshold:
            break

        price_in_cents = 100 * arbitrage['bid_without_fee']
        price_dict_for_listing_hashes[listing_hash] = price_in_cents

    if verbose:
        print(price_dict_for_listing_hashes)

    return price_dict_for_listing_hashes


def update_badge_arbitrages_with_latest_market_order_data(
    badge_data: dict[int, dict],
    arbitrage_data: dict[str, dict],
    retrieve_market_orders_online: bool = True,
    verbose: bool = False,
) -> dict[str, dict]:
    # Objective: ensure that we have the latest market orders before trying to automatically create & sell booster packs

    # Based on arbitrage_data, select the badge_data for which we want to download (again) the latest market orders:
    selected_badge_data = dict()

    for listing_hash in arbitrage_data.keys():
        arbitrage = arbitrage_data[listing_hash]

        if arbitrage['is_marketable'] and arbitrage['profit'] > 0:
            app_id = convert_listing_hash_to_app_id(listing_hash)
            selected_badge_data[app_id] = badge_data[app_id]

    market_order_dict = load_market_order_data(
        badge_data=selected_badge_data,
        retrieve_market_orders_online=retrieve_market_orders_online,
        verbose=verbose,
    )

    latest_badge_arbitrages = find_badge_arbitrages(
        badge_data=selected_badge_data,
        market_order_dict=market_order_dict,
        verbose=verbose,
    )

    return latest_badge_arbitrages


def get_filtered_badge_data(
    retrieve_listings_from_scratch: bool = True,
    enforced_sack_of_gems_price: float = None,
    minimum_allowed_sack_of_gems_price: float = None,
    quick_check_with_tracked_booster_packs: bool = False,
    check_ask_price: bool = True,
    from_javascript: bool = False,
) -> dict[int, dict]:
    aggregated_badge_data = load_aggregated_badge_data(
        retrieve_listings_from_scratch,
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        from_javascript=from_javascript,
    )

    aggregated_badge_data = fill_in_badges_with_next_creation_times_loaded_from_disk(
        aggregated_badge_data,
    )

    if check_ask_price:
        filtered_badge_data = filter_out_badges_with_low_sell_price(
            aggregated_badge_data,
        )
    else:
        filtered_badge_data = aggregated_badge_data

    filtered_badge_data = filter_out_badges_recently_crafted(filtered_badge_data)

    if quick_check_with_tracked_booster_packs:
        filtered_badge_data = filter_out_badges_never_crafted(filtered_badge_data)

    return filtered_badge_data


def apply_workflow(
    retrieve_listings_from_scratch: bool = True,
    retrieve_market_orders_online: bool = True,
    enforced_sack_of_gems_price: float = None,
    minimum_allowed_sack_of_gems_price: float = None,
    automatically_create_then_sell_booster_packs: bool = False,
    profit_threshold: float = 0.01,  # profit in euros
    quick_check_with_tracked_booster_packs: bool = False,
    enforce_update_of_marketability_status: bool = False,
    from_javascript: bool = False,
    profile_id: str = None,
    verbose: bool = False,
) -> bool:
    if quick_check_with_tracked_booster_packs:
        print('Quick-check of booster packs with a track record.')

        retrieve_listings_from_scratch = False
        retrieve_market_orders_online = True

        print(
            'Overwriting two arguments:\n\ti) retrieve listings: {},\n\tii) retrieve market orders: {}.'.format(
                retrieve_listings_from_scratch,
                retrieve_market_orders_online,
            ),
        )

    filtered_badge_data = get_filtered_badge_data(
        retrieve_listings_from_scratch=retrieve_listings_from_scratch,
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        quick_check_with_tracked_booster_packs=quick_check_with_tracked_booster_packs,
        check_ask_price=True,  # only set to False in batch_create_packs.py
        from_javascript=from_javascript,
    )

    market_order_dict = load_market_order_data(
        filtered_badge_data,
        retrieve_market_orders_online=retrieve_market_orders_online,
        verbose=verbose,
    )

    badge_arbitrages = find_badge_arbitrages(
        filtered_badge_data,
        market_order_dict,
        verbose=verbose,
    )

    print('# Reminder of the gem price')
    print_gem_price_reminder(
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        retrieve_gem_price_from_scratch=False,
    )
    # NB: Here, we set 'retrieve_gem_price_from_scratch' to False, so that:
    # - we ensure that the price displayed is equal to the price used for the computations of the arbitrages,
    # - we avoid any issue with status codes, which could happen due to rate limits, after we downloaded the last batch
    #   of market orders, because there was no cooldown at the end.

    print(
        '# Results after *slow* update of market order data for *many potential* arbitrages',
    )
    print_arbitrages(badge_arbitrages)

    latest_badge_arbitrages = update_badge_arbitrages_with_latest_market_order_data(
        badge_data=filtered_badge_data,
        arbitrage_data=badge_arbitrages,
        retrieve_market_orders_online=True,
        verbose=verbose,
    )
    # Update marketability status
    if enforce_update_of_marketability_status:
        few_selected_listing_hashes = list(latest_badge_arbitrages.keys())
        item_nameids = update_marketability_status(
            few_selected_listing_hashes=few_selected_listing_hashes,
        )

        # Override values which had been previously loaded into memory
        #
        # Caveat: the file with the updated marketability status is listing_details.json,
        #         the file market_orders.json was **not** updated and would have the wrong marketability status!
        for listing_hash in few_selected_listing_hashes:
            latest_badge_arbitrages[listing_hash]['is_marketable'] = item_nameids[listing_hash]['is_marketable']

    print(
        '# Results after *quick* update of market order data for *a few detected* arbitrages',
    )
    print_arbitrages(latest_badge_arbitrages)

    if automatically_create_then_sell_booster_packs:
        price_dict_for_listing_hashes = convert_arbitrages_for_batch_create_then_sell(
            latest_badge_arbitrages,
            profit_threshold=profit_threshold,
        )

        creation_results, sale_results = create_then_sell_booster_packs_for_batch(
            price_dict_for_listing_hashes,
            focus_on_marketable_items=True,
            profile_id=profile_id,
        )

    return True


def main() -> bool:
    retrieve_listings_from_scratch = True
    retrieve_market_orders_online = True
    enforced_sack_of_gems_price = None
    minimum_allowed_sack_of_gems_price = None
    automatically_create_then_sell_booster_packs = True
    profit_threshold = 0.0  # profit in euros
    quick_check_with_tracked_booster_packs = False
    enforce_update_of_marketability_status = True
    from_javascript = True
    profile_id = None
    verbose = True

    apply_workflow(
        retrieve_listings_from_scratch=retrieve_listings_from_scratch,
        retrieve_market_orders_online=retrieve_market_orders_online,
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        automatically_create_then_sell_booster_packs=automatically_create_then_sell_booster_packs,
        profit_threshold=profit_threshold,
        quick_check_with_tracked_booster_packs=quick_check_with_tracked_booster_packs,
        enforce_update_of_marketability_status=enforce_update_of_marketability_status,
        from_javascript=from_javascript,
        profile_id=profile_id,
        verbose=verbose,
    )

    return True


if __name__ == '__main__':
    main()
