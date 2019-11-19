# Create many booster packs (without being sure to sell them)

from inventory_utils import update_and_save_next_creation_times, create_booster_pack
from market_arbitrage import get_filtered_badge_data


def get_manually_selected_app_ids():
    manually_selected_app_ids = [381640, 290140, 338340, 272330, 451230, 359400, 318090, 304170, 499950, 307050, 521340]

    return manually_selected_app_ids


def filter_app_ids_based_on_badge_data(manually_selected_app_ids,
                                       filtered_badge_data=None):
    if filtered_badge_data is None:
        filtered_badge_data = get_filtered_badge_data(retrieve_listings_from_scratch=False,
                                                      enforced_sack_of_gems_price=None,
                                                      minimum_allowed_sack_of_gems_price=None,
                                                      quick_check_with_tracked_booster_packs=False,
                                                      from_javascript=True)

    # Only keep appIDs found in badge data, so that we have access to fields like the name, the hash, and the gem price.
    app_ids = [app_id for app_id in manually_selected_app_ids
               if app_id in filtered_badge_data]

    app_ids = sorted(app_ids,
                     key=lambda x: filtered_badge_data[x]['name'])

    return app_ids, filtered_badge_data


def create_packs_for_app_ids(manually_selected_app_ids,
                             filtered_badge_data=None,
                             is_a_simulation=True,  # Caveat: if False, then packs will be crafted, which costs money!
                             verbose=True):
    app_ids, filtered_badge_data = filter_app_ids_based_on_badge_data(manually_selected_app_ids,
                                                                      filtered_badge_data=filtered_badge_data)

    creation_results = dict()

    for app_id in app_ids:

        if is_a_simulation:
            result = None
        else:
            result = create_booster_pack(app_id=app_id)

        listing_hash = filtered_badge_data[app_id]['listing_hash']
        creation_results[listing_hash] = result

        if verbose:
            print('{}\t{:.3f}€'.format(
                filtered_badge_data[app_id]['name'],
                filtered_badge_data[app_id]['gem_price'])
            )

    next_creation_times = update_and_save_next_creation_times(creation_results)

    return creation_results, next_creation_times


def main(is_a_simulation=True):  # Caveat: if False, then packs will be crafted, which costs money!
    retrieve_listings_from_scratch = False
    enforced_sack_of_gems_price = None
    minimum_allowed_sack_of_gems_price = None
    quick_check_with_tracked_booster_packs = False
    from_javascript = True

    manually_selected_app_ids = get_manually_selected_app_ids()

    filtered_badge_data = get_filtered_badge_data(retrieve_listings_from_scratch=retrieve_listings_from_scratch,
                                                  enforced_sack_of_gems_price=enforced_sack_of_gems_price,
                                                  minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
                                                  quick_check_with_tracked_booster_packs=quick_check_with_tracked_booster_packs,
                                                  from_javascript=from_javascript)

    creation_results, next_creation_times = create_packs_for_app_ids(manually_selected_app_ids,
                                                                     filtered_badge_data=filtered_badge_data,
                                                                     is_a_simulation=is_a_simulation)

    return True


if __name__ == '__main__':
    main(is_a_simulation=True)
