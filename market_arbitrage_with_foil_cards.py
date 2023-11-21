# Objective: find market arbitrages with foil cards, e.g. buy a foil card and turn it into more gems than its cost.
#
# Caveat: the goal is not to make a profit by selling the gems afterwards! The goal is to acquire gems, this is why
# ALL the computations are performed with fee included: opportunities are compared from the perspective of the buyer.
#
# In summary, we do not care about buy orders here! We only care about sell orders!
from src.market_foil_utils import (
    build_dictionary_of_representative_listing_hashes,
    determine_whether_an_arbitrage_might_exist_for_foil_cards,
    discard_necessarily_unrewarding_app_ids,
    download_missing_goo_details,
    filter_listings_with_arbitrary_price_threshold,
    filter_out_listing_hashes_if_goo_details_are_already_known_for_app_id,
    find_app_ids_with_unknown_item_type_for_their_representatives,
    find_cheapest_listing_hashes,
    find_eligible_listing_hashes,
    find_listing_hashes_with_unknown_goo_value,
    find_representative_listing_hashes,
    get_listings_for_foil_cards,
    group_listing_hashes_by_app_id,
    print_arbitrages_for_foil_cards,
    propagate_filter_to_representative_listing_hashes,
    try_again_to_download_goo_value,
    try_again_to_download_item_type,
)
from src.market_listing import get_item_nameid_batch, load_all_listing_details
from src.sack_of_gems import load_sack_of_gems_price
from src.utils import (
    get_goo_details_file_nam_for_for_foil_cards,
    get_listing_details_output_file_name_for_foil_cards,
    get_listing_output_file_name_for_foil_cards,
)


def apply_workflow_for_foil_cards(
    retrieve_listings_from_scratch: bool = False,
    price_threshold_in_cents_for_a_foil_card: float | None = None,
    retrieve_gem_price_from_scratch: bool = False,
    enforced_sack_of_gems_price: float | None = None,  # price in euros
    start_index: int = 0,
    verbose: bool = True,
) -> bool:
    listing_output_file_name = get_listing_output_file_name_for_foil_cards()
    listing_details_output_file_name = (
        get_listing_details_output_file_name_for_foil_cards()
    )
    goo_details_file_name_for_for_foil_cards = (
        get_goo_details_file_nam_for_for_foil_cards()
    )

    # Fetch all the listings of foil cards

    all_listings = get_listings_for_foil_cards(
        retrieve_listings_from_scratch=retrieve_listings_from_scratch,
        listing_output_file_name=listing_output_file_name,
        start_index=start_index,
        verbose=verbose,
    )

    # Group listings by appID

    groups_by_app_id = group_listing_hashes_by_app_id(
        all_listings,
        verbose=verbose,
    )

    # Find the cheapest listing in each group

    cheapest_listing_hashes = find_cheapest_listing_hashes(
        all_listings,
        groups_by_app_id,
    )

    # Find the representative listing in each group

    # For retro-compatibility, we try to use representative for which we previously downloaded item name ids
    dictionary_of_representative_listing_hashes = (
        build_dictionary_of_representative_listing_hashes(
            listing_details_output_file_name=listing_details_output_file_name,
        )
    )

    representative_listing_hashes = find_representative_listing_hashes(
        groups_by_app_id,
        dictionary_of_representative_listing_hashes,
    )

    # List eligible listing hashes (positive ask volume, and positive ask price)

    eligible_listing_hashes = find_eligible_listing_hashes(all_listings)

    # Filter listings with an arbitrary price threshold
    # NB: This is only useful to speed up the pre-retrieval below, by focusing on the most interesting listings.

    filtered_cheapest_listing_hashes = filter_listings_with_arbitrary_price_threshold(
        all_listings=all_listings,
        listing_hashes_to_filter_from=cheapest_listing_hashes,
        price_threshold_in_cents=price_threshold_in_cents_for_a_foil_card,
        verbose=verbose,
    )

    filtered_representative_listing_hashes = (
        propagate_filter_to_representative_listing_hashes(
            listing_hashes_to_propagate_to=representative_listing_hashes,
            listing_hashes_to_propagate_from=filtered_cheapest_listing_hashes,
        )
    )

    # Filter out listings associated with an appID for which we already know the goo details.

    filtered_representative_listing_hashes_with_missing_goo_details = filter_out_listing_hashes_if_goo_details_are_already_known_for_app_id(
        filtered_representative_listing_hashes,
        goo_details_file_name_for_for_foil_cards=goo_details_file_name_for_for_foil_cards,
        verbose=verbose,
    )

    # Pre-retrieval of item name ids (and item types at the same time)

    get_item_nameid_batch(
        filtered_representative_listing_hashes_with_missing_goo_details,
        listing_details_output_file_name=listing_details_output_file_name,
    )

    # Load the price of a sack of 1000 gems

    if enforced_sack_of_gems_price is None:
        sack_of_gems_price_in_euros = load_sack_of_gems_price(
            retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
            verbose=verbose,
        )
    else:
        sack_of_gems_price_in_euros = enforced_sack_of_gems_price

    # Fetch goo values

    all_listing_details = load_all_listing_details(
        listing_details_output_file_name=listing_details_output_file_name,
    )

    all_goo_details = download_missing_goo_details(
        groups_by_app_id=groups_by_app_id,
        listing_candidates=filtered_representative_listing_hashes_with_missing_goo_details,
        all_listing_details=all_listing_details,
        listing_details_output_file_name=listing_details_output_file_name,
        goo_details_file_name_for_for_foil_cards=goo_details_file_name_for_for_foil_cards,
        verbose=verbose,
    )

    # List unknown item types

    try_again_to_find_item_type = False

    app_ids_with_unreliable_goo_details = (
        find_app_ids_with_unknown_item_type_for_their_representatives(
            groups_by_app_id=groups_by_app_id,
            listing_candidates=filtered_representative_listing_hashes,
            all_listing_details=all_listing_details,
            listing_details_output_file_name=listing_details_output_file_name,
            verbose=verbose,
        )
    )

    if try_again_to_find_item_type:
        try_again_to_download_item_type(
            app_ids_with_unreliable_goo_details,
            filtered_representative_listing_hashes,
            listing_details_output_file_name,
        )

    # List unknown goo values

    try_again_to_find_goo_value = False

    app_ids_with_unknown_goo_value = find_listing_hashes_with_unknown_goo_value(
        listing_candidates=filtered_representative_listing_hashes,
        app_ids_with_unreliable_goo_details=app_ids_with_unreliable_goo_details,
        all_goo_details=all_goo_details,
        verbose=verbose,
    )

    if try_again_to_find_goo_value:
        try_again_to_download_goo_value(
            app_ids_with_unknown_goo_value,
            filtered_representative_listing_hashes,
            groups_by_app_id,
        )

    # Solely for information purpose, count the number of potentially rewarding appIDs.
    #
    # NB: this information is not used, but one could imagine only retrieving the ask price of potentially rewarding
    #     appIDs, so that time is not lost retrieving the ask price of necessarily unrewarding appIDs.
    #     Indeed, this could halve the number of queries, e.g. as of January 2020, there are:
    #     - 8872 appIDs in total,
    #     - out of which 4213 to 4257 are potentially rewarding appIDs, so 47% - 48% of the appIDs.

    discard_necessarily_unrewarding_app_ids(
        all_goo_details=all_goo_details,
        app_ids_with_unreliable_goo_details=app_ids_with_unreliable_goo_details,
        app_ids_with_unknown_goo_value=app_ids_with_unknown_goo_value,
        sack_of_gems_price_in_euros=sack_of_gems_price_in_euros,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
        verbose=verbose,
    )

    # Find market arbitrages

    arbitrages = determine_whether_an_arbitrage_might_exist_for_foil_cards(
        eligible_listing_hashes,
        all_goo_details=all_goo_details,
        app_ids_with_unreliable_goo_details=app_ids_with_unreliable_goo_details,
        app_ids_with_unknown_goo_value=app_ids_with_unknown_goo_value,
        all_listings=all_listings,
        listing_output_file_name=listing_output_file_name,
        sack_of_gems_price_in_euros=sack_of_gems_price_in_euros,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
        verbose=verbose,
    )

    print_arbitrages_for_foil_cards(
        arbitrages,
        use_numbered_bullet_points=True,
    )

    return True


def main() -> bool:
    retrieve_listings_from_scratch = True
    price_threshold_in_cents_for_a_foil_card = None
    retrieve_gem_price_from_scratch = True
    enforced_sack_of_gems_price = None  # price in euros
    start_index = 0  # to resume the update in case of wrong status code
    verbose = True

    apply_workflow_for_foil_cards(
        retrieve_listings_from_scratch=retrieve_listings_from_scratch,
        price_threshold_in_cents_for_a_foil_card=price_threshold_in_cents_for_a_foil_card,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        start_index=start_index,
        verbose=verbose,
    )

    return True


if __name__ == "__main__":
    main()
