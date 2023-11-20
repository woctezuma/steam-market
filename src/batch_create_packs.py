# Create many booster packs (without being sure to sell them)

from src.creation_time_utils import get_formatted_time, get_time_struct_from_str
from src.inventory_utils import create_booster_pack, update_and_save_next_creation_times
from src.market_arbitrage_utils import get_filtered_badge_data


def get_manually_selected_app_ids() -> list[str]:
    return [
        "1286830",  # STAR WARS™: The Old Republic™ (750 gems)
        "33680",  # Eversion (1000 gems)
        "520680",  # Lost Cities (1200 gems)
    ]


def filter_app_ids_based_on_badge_data(
    manually_selected_app_ids: list[str],
    check_ask_price: bool = False,
    filtered_badge_data: dict[str, dict] | None = None,
) -> tuple[list[str], dict[str, dict]]:
    if filtered_badge_data is None:
        filtered_badge_data = get_filtered_badge_data(
            retrieve_listings_from_scratch=False,
            enforced_sack_of_gems_price=None,
            minimum_allowed_sack_of_gems_price=None,
            quick_check_with_tracked_booster_packs=False,
            check_ask_price=check_ask_price,
            from_javascript=True,
        )

    # Only keep appIDs found in badge data, so that we have access to fields like the name, the hash, and the gem price.
    app_ids = [
        app_id for app_id in manually_selected_app_ids if app_id in filtered_badge_data
    ]

    app_ids = sorted(
        app_ids,
        key=lambda x: filtered_badge_data[x]["name"],
    )

    return app_ids, filtered_badge_data


def create_packs_for_app_ids(
    manually_selected_app_ids: list[str],
    filtered_badge_data: dict[str, dict] | None = None,
    check_ask_price: bool = False,
    is_a_simulation: bool = True,
    # Caveat: if False, then packs will be crafted, which costs money!
    is_marketable: bool = True,
    # Caveat: if False, packs will be crafted with un-marketable gems!
    verbose: bool = True,
) -> tuple[dict[str, dict | None], dict[str, str]]:
    app_ids, filtered_badge_data = filter_app_ids_based_on_badge_data(
        manually_selected_app_ids,
        check_ask_price=check_ask_price,
        filtered_badge_data=filtered_badge_data,
    )

    creation_results = {}

    for app_id in app_ids:
        if is_a_simulation:
            result = None
        else:
            result = create_booster_pack(
                app_id=app_id,
                is_marketable=is_marketable,
            )

        listing_hash = filtered_badge_data[app_id]["listing_hash"]
        creation_results[listing_hash] = result

        if verbose:
            print(
                "{}\t{:.3f}€".format(
                    filtered_badge_data[app_id]["name"],
                    filtered_badge_data[app_id]["gem_price"],
                ),
            )

    next_creation_times = update_and_save_next_creation_times(creation_results)

    if verbose:
        ignored_app_ids = set(manually_selected_app_ids).difference(app_ids)
        print(f"There are {len(ignored_app_ids)} ignored appIDs: {ignored_app_ids}")

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
                next_creation_times_for_manually_selected_app_ids,
            )
        except ValueError:
            soonest_creation_time = None

        print(
            f"The soonest creation time is {get_formatted_time(soonest_creation_time)}.",
        )

    return creation_results, next_creation_times


def main(
    retrieve_listings_from_scratch: bool = False,
    # Set to True & run once if you get "No match found for" games you own.
    is_a_simulation: bool = True,  # Caveat: if False, then packs will be crafted, which costs money!
    is_marketable: bool = True,  # Caveat: if False, packs will be crafted with unmarketable gems!
) -> bool:
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

    filtered_badge_data = get_filtered_badge_data(
        retrieve_listings_from_scratch=retrieve_listings_from_scratch,
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        quick_check_with_tracked_booster_packs=quick_check_with_tracked_booster_packs,
        check_ask_price=check_ask_price,
        from_javascript=from_javascript,
    )

    creation_results, next_creation_times = create_packs_for_app_ids(
        manually_selected_app_ids,
        filtered_badge_data=filtered_badge_data,
        check_ask_price=check_ask_price,
        is_a_simulation=is_a_simulation,
        is_marketable=is_marketable,
    )

    return True


if __name__ == "__main__":
    main(
        retrieve_listings_from_scratch=False,
        is_a_simulation=False,
        is_marketable=True,
    )
