# Objective: detect gambles which might be worth a try, i.e. find profile backgrounds and emoticons which:
# - are of "Common" rarity, so reasonably likely to be obtained after a crafting a badge,
# - have high bid orders, so potentially profitable after taking every other factor into account.
#
# Caveat: take into account the NUMBER of items of "Common" rarity! This information can be found on pages such as:
#         https://www.steamcardexchange.net/index.php?gamepage-appid-254880
# For instance, if there are 2 Profile Backgrounds of "Common" rarity, then you can expect to get the one of interest
# after crafting 2 badges, therefore you should expect to be able to sell it for 2x the crafting cost to turn a profit.
#
# NB: a booster pack of 3 cards is always worth 6000/(#cards) gems, so a full set of (#cards) is worth 2000 gems.
# Therefore, the cost of crafting a badge is identical for every game: that is twice the price of a sack of 1000 gems.
# If you pay 0.31 € per sack of gems, which you then turn into booster packs, then your *badge* crafting cost is 0.62 €.

from src.market_arbitrage_utils import find_badge_arbitrages, print_arbitrages
from src.market_buzz_utils import (
    filter_out_unmarketable_packs,
    print_packs_with_high_buzz,
    sort_according_to_buzz,
)
from src.market_gamble_utils import (
    count_listing_hashes_per_app_id,
    enumerate_item_rarity_patterns,
    filter_out_candidates_whose_ask_price_is_below_threshold,
    get_listings,
    get_listings_with_other_rarity_tags,
    get_market_orders,
)
from src.market_listing import get_item_nameid_batch
from src.utils import (
    get_category_name_for_emoticons,
    get_category_name_for_profile_backgrounds,
    get_listing_details_output_file_name_for_emoticons,
    get_listing_details_output_file_name_for_profile_backgrounds,
    get_listing_output_file_name_for_emoticons,
    get_listing_output_file_name_for_profile_backgrounds,
    get_market_order_file_name_for_emoticons,
    get_market_order_file_name_for_profile_backgrounds,
)


def main(
    look_for_profile_backgrounds: bool = True,  # if True, profile backgrounds, otherwise, emoticons.
    retrieve_listings_from_scratch: bool = False,
    retrieve_listings_with_another_rarity_tag_from_scratch: bool = False,
    retrieve_market_orders_online: bool = True,
    focus_on_listing_hashes_never_seen_before: bool = True,
    price_threshold_in_cents: float | None = None,
    drop_rate_estimates_for_common_rarity: dict[tuple[int, int, int], float]
    | None = None,
    num_packs_to_display: int = 10,
    enforce_cooldown: bool = True,
    allow_to_skip_dummy_data: bool = False,
    verbose: bool = False,
) -> bool:
    if look_for_profile_backgrounds:
        category_name = get_category_name_for_profile_backgrounds()
        listing_output_file_name = (
            get_listing_output_file_name_for_profile_backgrounds()
        )
        listing_details_output_file_name = (
            get_listing_details_output_file_name_for_profile_backgrounds()
        )
        market_order_output_file_name = (
            get_market_order_file_name_for_profile_backgrounds()
        )
    else:
        category_name = get_category_name_for_emoticons()
        listing_output_file_name = get_listing_output_file_name_for_emoticons()
        listing_details_output_file_name = (
            get_listing_details_output_file_name_for_emoticons()
        )
        market_order_output_file_name = get_market_order_file_name_for_emoticons()

    # Load list of all listing hashes with common rarity tag

    all_listings = get_listings(
        listing_output_file_name=listing_output_file_name,
        retrieve_listings_from_scratch=retrieve_listings_from_scratch,
    )

    # Count the number of **different** items with common rarity tag for each appID

    listing_hashes_per_app_id_for_common = count_listing_hashes_per_app_id(all_listings)

    # Load list of all listing hashes with other rarity tags (uncommon and rare)

    (
        all_listings_for_uncommon,
        all_listings_for_rare,
    ) = get_listings_with_other_rarity_tags(
        look_for_profile_backgrounds=look_for_profile_backgrounds,
        retrieve_listings_with_another_rarity_tag_from_scratch=retrieve_listings_with_another_rarity_tag_from_scratch,
    )

    # Count the number of **different** items with other rarity tags (uncommon and rare)  for each appID

    listing_hashes_per_app_id_for_uncommon = count_listing_hashes_per_app_id(
        all_listings_for_uncommon,
    )
    listing_hashes_per_app_id_for_rare = count_listing_hashes_per_app_id(
        all_listings_for_rare,
    )

    # Enumerate patterns C/UC/R for each appID

    item_rarity_patterns_per_app_id = enumerate_item_rarity_patterns(
        listing_hashes_per_app_id_for_common,
        listing_hashes_per_app_id_for_uncommon,
        listing_hashes_per_app_id_for_rare,
    )

    # *Heuristic* filtering of listing hashes

    filtered_badge_data = filter_out_candidates_whose_ask_price_is_below_threshold(
        all_listings,
        item_rarity_patterns_per_app_id=item_rarity_patterns_per_app_id,
        price_threshold_in_cents=price_threshold_in_cents,
        drop_rate_estimates_for_common_rarity=drop_rate_estimates_for_common_rarity,
        category_name=category_name,
    )

    # Pre-retrieval of item name ids

    selected_listing_hashes = [
        badge["listing_hash"] for badge in filtered_badge_data.values()
    ]

    get_item_nameid_batch(
        selected_listing_hashes,
        listing_details_output_file_name=listing_details_output_file_name,
    )

    # Download market orders

    market_order_dict = get_market_orders(
        filtered_badge_data,
        retrieve_market_orders_online,
        focus_on_listing_hashes_never_seen_before,
        listing_details_output_file_name,
        market_order_output_file_name,
        enforce_cooldown=enforce_cooldown,
        allow_to_skip_dummy_data=allow_to_skip_dummy_data,
        verbose=verbose,
    )

    # Only keep marketable booster packs

    (
        marketable_market_order_dict,
        unknown_market_order_dict,
    ) = filter_out_unmarketable_packs(market_order_dict)

    # Sort by bid value
    hashes_for_best_bid = sort_according_to_buzz(
        market_order_dict,
        marketable_market_order_dict,
    )

    # Display the highest ranked booster packs

    print_packs_with_high_buzz(
        hashes_for_best_bid,
        market_order_dict,
        item_rarity_patterns_per_app_id=item_rarity_patterns_per_app_id,
        category_name=category_name,
        num_packs_to_display=num_packs_to_display,
    )

    # Detect potential arbitrages

    badge_arbitrages = find_badge_arbitrages(
        filtered_badge_data,
        market_order_dict,
        verbose=verbose,
    )

    print("\n# Results for detected *potential* arbitrages\n")
    print_arbitrages(
        badge_arbitrages,
        use_numbered_bullet_points=True,
        use_hyperlink=True,
    )

    return True


if __name__ == "__main__":
    main(
        look_for_profile_backgrounds=True,  # if True, profile backgrounds, otherwise, emoticons.
        retrieve_listings_from_scratch=False,
        retrieve_listings_with_another_rarity_tag_from_scratch=False,
        retrieve_market_orders_online=True,
        focus_on_listing_hashes_never_seen_before=True,
        price_threshold_in_cents=None,
        drop_rate_estimates_for_common_rarity=None,
        num_packs_to_display=100,
        enforce_cooldown=True,
        allow_to_skip_dummy_data=False,
        verbose=True,
    )
