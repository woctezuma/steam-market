# Objective: find market arbitrages, e.g. sell a pack for more (fee excluded) than the cost to craft it (fee included).


from src.inventory_utils import create_then_sell_booster_packs_for_batch
from src.market_arbitrage_utils import (
    convert_arbitrages_for_batch_create_then_sell,
    find_badge_arbitrages,
    get_filtered_badge_data,
    print_arbitrages,
    update_badge_arbitrages_with_latest_market_order_data,
)
from src.market_listing import update_marketability_status
from src.market_order import load_market_order_data
from src.sack_of_gems import print_gem_price_reminder


def apply_workflow(
    retrieve_listings_from_scratch: bool = True,
    retrieve_market_orders_online: bool = True,
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
    automatically_create_then_sell_booster_packs: bool = False,
    profit_threshold: float = 0.01,  # profit in euros
    quick_check_with_tracked_booster_packs: bool = False,
    enforce_update_of_marketability_status: bool = False,
    from_javascript: bool = False,
    profile_id: str | None = None,
    verbose: bool = False,
) -> bool:
    if quick_check_with_tracked_booster_packs:
        print("Quick-check of booster packs with a track record.")

        retrieve_listings_from_scratch = False
        retrieve_market_orders_online = True

        print(
            "Overwriting two arguments:\n\ti) retrieve listings: {},\n\tii) retrieve market orders: {}.".format(
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

    print("# Reminder of the gem price")
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
        "# Results after *slow* update of market order data for *many potential* arbitrages",
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
            latest_badge_arbitrages[listing_hash]["is_marketable"] = item_nameids[
                listing_hash
            ]["is_marketable"]

    print(
        "# Results after *quick* update of market order data for *a few detected* arbitrages",
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


if __name__ == "__main__":
    main()
