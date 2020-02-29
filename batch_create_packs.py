# Create many booster packs (without being sure to sell them)

from creation_time_utils import get_formatted_time, get_time_struct_from_str
from inventory_utils import update_and_save_next_creation_times, create_booster_pack
from market_arbitrage import get_filtered_badge_data


def get_manually_selected_app_ids():
    manually_selected_app_ids = [
        270010,  # Time Rifters (6 cards, 3 C, 1 UC, 1 R)
        # 325120,  # Notch - The Innocent LunA: Eclipsed SinnerS (7 cards, 2 C, 5 UC, 2 R)
        # 409070,  # Fist Slash: Of Ultimate Fury (6 cards, 3 C, 2 UC, 1R)
        254880,  # MoonBase Commander (6 cards, 2 C, 1 UC, 1 R)
        554660,  # Puzzle Poker (6 cards, 1 C, 1 UC, 1 R)
        # 307050,  # Shan Gui (5 cards, 1 C, 2 UC, 2 R)
        # 339000,  # Ukrainian Ninja (5 cards, 2 C, 3 UC, 1 R)
        210170,  # Spirits (6 cards, 1 C, 1 UC, 1 R)
        351090,  # Regency Solitaire (6 cards, 3 C, 1 UC, 1 R)
        # 499950,  # Metal Assault - Gigaslave - Europe (6 cards, 1 C, 2 UC, 1 R)
        # 272330,  # Shadow Blade: Reload (6 cards, 3 C, 1 UC, 1 R)
        # 398140,  # Ino (5 cards, 1 C, 1 UC, 1 R)

        562260,  # WAVESHAPER
        383690,  # Mu Complex
        558490,  # Crossroad Mysteries: The Broken Deal

        342250,  # Aspectus: Rinascimento Chronicles
        522340,  # Ghostlords (8 cards, emoticons: 4C, 3 UC, 3R)
    ]

    return manually_selected_app_ids


def filter_app_ids_based_on_badge_data(manually_selected_app_ids,
                                       check_ask_price=False,
                                       filtered_badge_data=None):
    if filtered_badge_data is None:
        filtered_badge_data = get_filtered_badge_data(retrieve_listings_from_scratch=False,
                                                      enforced_sack_of_gems_price=None,
                                                      minimum_allowed_sack_of_gems_price=None,
                                                      quick_check_with_tracked_booster_packs=False,
                                                      check_ask_price=check_ask_price,
                                                      from_javascript=True)

    # Only keep appIDs found in badge data, so that we have access to fields like the name, the hash, and the gem price.
    app_ids = [app_id for app_id in manually_selected_app_ids
               if app_id in filtered_badge_data]

    app_ids = sorted(app_ids,
                     key=lambda x: filtered_badge_data[x]['name'])

    return app_ids, filtered_badge_data


def create_packs_for_app_ids(manually_selected_app_ids,
                             filtered_badge_data=None,
                             check_ask_price=False,
                             is_a_simulation=True,  # Caveat: if False, then packs will be crafted, which costs money!
                             is_marketable=True,  # Caveat: if False, packs will be crafted with un-marketable gems!
                             verbose=True):
    app_ids, filtered_badge_data = filter_app_ids_based_on_badge_data(manually_selected_app_ids,
                                                                      check_ask_price=check_ask_price,
                                                                      filtered_badge_data=filtered_badge_data)

    creation_results = dict()

    for app_id in app_ids:

        if is_a_simulation:
            result = None
        else:
            result = create_booster_pack(app_id=app_id,
                                         is_marketable=is_marketable)

        listing_hash = filtered_badge_data[app_id]['listing_hash']
        creation_results[listing_hash] = result

        if verbose:
            print('{}\t{:.3f}€'.format(
                filtered_badge_data[app_id]['name'],
                filtered_badge_data[app_id]['gem_price'])
            )

    next_creation_times = update_and_save_next_creation_times(creation_results)

    if verbose:
        ignored_app_ids = set(manually_selected_app_ids).difference(app_ids)
        print('There are {} ignored appIDs: {}'.format(
            len(ignored_app_ids),
            ignored_app_ids)
        )

        # Below, the parameter 'use_current_year' is toggled ON, because the year information is necessary to deal with
        # February 29th during leap years.
        next_creation_times_for_manually_selected_app_ids = [
            get_time_struct_from_str(
                next_creation_times[app_id],
                use_current_year=True,
            )
            for app_id in manually_selected_app_ids
            if app_id in next_creation_times
        ]

        try:
            soonest_creation_time = min(
                next_creation_times_for_manually_selected_app_ids
            )
        except ValueError:
            soonest_creation_time = None

        print('The soonest creation time is {}.'.format(
            get_formatted_time(soonest_creation_time)
        ))

    return creation_results, next_creation_times


def main(is_a_simulation=True,  # Caveat: if False, then packs will be crafted, which costs money!
         is_marketable=True):  # Caveat: if False, packs will be crafted with unmarketable gems!
    retrieve_listings_from_scratch = False
    enforced_sack_of_gems_price = None
    minimum_allowed_sack_of_gems_price = None
    quick_check_with_tracked_booster_packs = False
    check_ask_price = False
    #
    # NB: check_ask_price is set to False so that booster packs are created even if the creation cost is close to the
    #     lowest sell order. Otherwise, booster packs could be skipped if (creation cost) > ((lowest sell order) - fees)
    #
    # NB²: It only makes sense to set check_ask_price to True in market_arbitrage.py,
    #      because, in this case, we want to SELL the packs which we create rather than opening them for their content.
    #
    from_javascript = True

    manually_selected_app_ids = get_manually_selected_app_ids()

    filtered_badge_data = get_filtered_badge_data(retrieve_listings_from_scratch=retrieve_listings_from_scratch,
                                                  enforced_sack_of_gems_price=enforced_sack_of_gems_price,
                                                  minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
                                                  quick_check_with_tracked_booster_packs=quick_check_with_tracked_booster_packs,
                                                  check_ask_price=check_ask_price,
                                                  from_javascript=from_javascript)

    creation_results, next_creation_times = create_packs_for_app_ids(manually_selected_app_ids,
                                                                     filtered_badge_data=filtered_badge_data,
                                                                     check_ask_price=check_ask_price,
                                                                     is_a_simulation=is_a_simulation,
                                                                     is_marketable=is_marketable)

    return True


if __name__ == '__main__':
    main(is_a_simulation=False,
         is_marketable=True)
