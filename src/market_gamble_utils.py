import time

from src.drop_rate_estimates import (
    clamp_proportion,
    get_drop_rate_estimates_based_on_item_rarity_pattern,
    get_drop_rate_field,
    get_rarity_fields,
)
from src.market_arbitrage_utils import filter_out_badges_with_low_sell_price
from src.market_order import (
    download_market_order_data_batch,
    load_market_order_data_from_disk,
)
from src.market_search import (
    get_steam_api_rate_limits_for_market_search,
    get_tag_item_class_no_for_emoticons,
    get_tag_item_class_no_for_profile_backgrounds,
    get_tag_item_class_no_for_trading_cards,
    load_all_listings,
    update_all_listings,
)
from src.personal_info import get_cookie_dict
from src.sack_of_gems import get_gem_amount_required_to_craft_badge, get_gem_price
from src.utils import (
    convert_listing_hash_to_app_id,
    get_category_name_for_booster_packs,
    get_listing_output_file_name_for_emoticons,
    get_listing_output_file_name_for_foil_cards,
    get_listing_output_file_name_for_profile_backgrounds,
)


def update_all_listings_for_foil_cards(start_index: int = 0) -> None:
    print("Downloading listings for foil cards.")

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_foil_cards(),
        tag_item_class_no=get_tag_item_class_no_for_trading_cards(),
        start_index=start_index,
    )


def update_all_listings_for_profile_backgrounds(
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
) -> None:
    print(
        f"Downloading listings for profile backgrounds (rarity_tag={tag_drop_rate_str} ; rarity={rarity}).",
    )

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_profile_backgrounds(
            tag_drop_rate_str=tag_drop_rate_str,
            rarity=rarity,
        ),
        tag_item_class_no=get_tag_item_class_no_for_profile_backgrounds(),
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity,
    )


def update_all_listings_for_emoticons(
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
) -> None:
    print(
        f"Downloading listings for emoticons (rarity_tag={tag_drop_rate_str} ; rarity={rarity}).",
    )

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_emoticons(
            tag_drop_rate_str=tag_drop_rate_str,
            rarity=rarity,
        ),
        tag_item_class_no=get_tag_item_class_no_for_emoticons(),
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity,
    )


def update_all_listings_for_items_other_than_cards(
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
) -> None:
    # Profile Backgrounds

    update_all_listings_for_profile_backgrounds(
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity,
    )

    # Forced cooldown

    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    rate_limits = get_steam_api_rate_limits_for_market_search(has_secured_cookie)

    cooldown_duration = rate_limits["cooldown"]
    print(
        f"Forced cooldown between profile backgrounds and emoticons. Cooldown: {cooldown_duration} seconds",
    )
    time.sleep(cooldown_duration)

    # Emoticons

    update_all_listings_for_emoticons(
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity,
    )


def get_listings(
    listing_output_file_name: str,
    retrieve_listings_from_scratch: bool = False,
) -> dict[str, dict]:
    if retrieve_listings_from_scratch:
        # Caveat: this update is only for items of Common rarity!
        update_all_listings_for_items_other_than_cards(rarity="common")

    return load_all_listings(listing_output_file_name)


def filter_out_candidates_whose_ask_price_is_below_threshold(
    all_listings: dict[str, dict],
    item_rarity_patterns_per_app_id: dict[str, dict],
    price_threshold_in_cents: float | None = None,
    category_name: str | None = None,
    drop_rate_estimates_for_common_rarity: dict[tuple[int, int, int], float]
    | None = None,
    gem_price_in_euros: float | None = None,
    verbose: bool = True,
) -> dict[str, dict]:
    if gem_price_in_euros is None:
        gem_price_in_euros = get_gem_price()

    if drop_rate_estimates_for_common_rarity is None:
        if (
            category_name is not None
            and category_name != get_category_name_for_booster_packs()
        ):
            drop_rate_estimates = get_drop_rate_estimates_based_on_item_rarity_pattern(
                verbose=verbose,
            )
            drop_rate_field = get_drop_rate_field()
            rarity_field = "common"
            drop_rate_estimates_for_common_rarity = drop_rate_estimates[
                drop_rate_field
            ][rarity_field]
        else:
            drop_rate_estimates_for_common_rarity = {}

    gem_amount_required_to_craft_badge = get_gem_amount_required_to_craft_badge()

    badge_price = gem_amount_required_to_craft_badge * gem_price_in_euros

    # Build dummy badge data, in order to reuse functions developed for the analysis of Booster Packs

    badge_data: dict[str, dict] = {}
    for listing_hash in all_listings:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        item_rarity_pattern = item_rarity_patterns_per_app_id[app_id]

        num_items_of_common_rarity = item_rarity_pattern["common"]
        num_items_of_uncommon_rarity = item_rarity_pattern["uncommon"]
        num_items_of_rare_rarity = item_rarity_pattern["rare"]

        item_rarity_pattern_as_tuple = (
            num_items_of_common_rarity,
            num_items_of_uncommon_rarity,
            num_items_of_rare_rarity,
        )

        try:
            drop_rate_for_common_rarity = drop_rate_estimates_for_common_rarity[
                item_rarity_pattern_as_tuple
            ]
        except KeyError:
            drop_rate_for_common_rarity = 1  # Here, 1 would represent 100% chance to receive an item of common rarity.

        drop_rate_for_common_rarity = clamp_proportion(drop_rate_for_common_rarity)

        item_price_by_crafting_badges = (
            num_items_of_common_rarity * badge_price / drop_rate_for_common_rarity
        )

        sell_price_in_cents = all_listings[listing_hash]["sell_price"]
        sell_price_in_euros = sell_price_in_cents / 100

        # In order to distinguish items linked to the same appID, dummy appIDs are introduced:
        dummy_app_id = listing_hash

        badge_data[dummy_app_id] = {}
        badge_data[dummy_app_id]["listing_hash"] = listing_hash
        badge_data[dummy_app_id]["sell_price"] = sell_price_in_euros
        badge_data[dummy_app_id]["gem_price"] = item_price_by_crafting_badges

    # Filter out candidates for which the ask is below a given threshold

    return filter_out_badges_with_low_sell_price(
        badge_data,
        category_name=category_name,
        user_chosen_price_threshold=price_threshold_in_cents,
    )


def get_market_orders(
    filtered_badge_data: dict[str, dict],
    retrieve_market_orders_online: bool,
    focus_on_listing_hashes_never_seen_before: bool,
    listing_details_output_file_name: str,
    market_order_output_file_name: str,
    enforce_cooldown: bool = True,
    allow_to_skip_dummy_data: bool = False,
    verbose: bool = False,
) -> dict[str, dict]:
    # Load market orders (bid, ask) from disk

    market_order_dict = load_market_order_data_from_disk(
        market_order_output_file_name=market_order_output_file_name,
    )

    # Filter out listing hashes which have already been encountered at least once

    first_encountered_filtered_badge_data = {}

    for dummy_app_id in filtered_badge_data:
        if filtered_badge_data[dummy_app_id]["listing_hash"] not in market_order_dict:
            first_encountered_filtered_badge_data[dummy_app_id] = filtered_badge_data[
                dummy_app_id
            ]

    # Retrieval of market orders (bid, ask)

    if focus_on_listing_hashes_never_seen_before:
        badge_data_to_process = first_encountered_filtered_badge_data
    else:
        badge_data_to_process = filtered_badge_data

    if retrieve_market_orders_online and badge_data_to_process:
        market_order_dict = download_market_order_data_batch(
            badge_data_to_process,
            market_order_dict=market_order_dict,
            market_order_output_file_name=market_order_output_file_name,
            listing_details_output_file_name=listing_details_output_file_name,
            verbose=verbose,
            enforce_cooldown=enforce_cooldown,
            allow_to_skip_dummy_data=allow_to_skip_dummy_data,
        )

    # After the **most comprehensive** dictionary of market orders has been loaded from disk by:
    #       `load_market_order_data_from_disk()`
    # then partially updated, and saved to disk by:
    #       `download_market_order_data_batch()`
    # we can edit the dictionary to filter out listing hashes which were not requested by the user, following the input:
    #       `filtered_badge_data`
    # and finally return the trimmed dictionary as the output of the current function call:
    #       `get_market_orders(filtered_badge_data, ...)`

    available_listing_hashes = list(market_order_dict.keys())

    selected_listing_hashes = [
        filtered_badge_data[app_id]["listing_hash"] for app_id in filtered_badge_data
    ]

    for listing_hash in available_listing_hashes:
        if listing_hash not in selected_listing_hashes:
            del market_order_dict[listing_hash]

    return market_order_dict


def count_listing_hashes_per_app_id(all_listings: dict[str, dict]) -> dict[str, int]:
    # For each appID, count the number of known listing hashes.
    #
    # Caveat: this piece of information relies on the downloaded listings, it is NOT NECESSARILY accurate!
    #         Errors can happen, so manually double-check any information before using it for critical usage!
    #
    # If 'all_listings' is constrained to items of 'Common' rarity, then this is the number of **different** items of
    # such rarity. This information is useful to know whether a gamble is worth a try: the more items of Common rarity,
    # the harder it is to receive the item which you are specifically after, by crafting a badge.

    listing_hashes_per_app_id: dict[str, int] = {}

    for listing_hash in all_listings:
        app_id = convert_listing_hash_to_app_id(listing_hash)
        try:
            listing_hashes_per_app_id[app_id] += 1
        except KeyError:
            listing_hashes_per_app_id[app_id] = 1

    return listing_hashes_per_app_id


def get_listings_with_other_rarity_tags(
    look_for_profile_backgrounds: bool,
    retrieve_listings_with_another_rarity_tag_from_scratch: bool = False,
) -> tuple[dict[str, dict], dict[str, dict]]:
    if retrieve_listings_with_another_rarity_tag_from_scratch:
        other_rarity_fields = set(get_rarity_fields()).difference({"common"})
        for rarity_tag in other_rarity_fields:
            update_all_listings_for_items_other_than_cards(rarity=rarity_tag)

    if look_for_profile_backgrounds:
        all_listings_for_uncommon = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_profile_backgrounds(
                rarity="uncommon",
            ),
        )
        all_listings_for_rare = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_profile_backgrounds(
                rarity="rare",
            ),
        )

    else:
        all_listings_for_uncommon = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_emoticons(
                rarity="uncommon",
            ),
        )
        all_listings_for_rare = load_all_listings(
            listing_output_file_name=get_listing_output_file_name_for_emoticons(
                rarity="rare",
            ),
        )

    return all_listings_for_uncommon, all_listings_for_rare


def enumerate_item_rarity_patterns(
    listing_hashes_per_app_id_for_common: dict[str, int],
    listing_hashes_per_app_id_for_uncommon: dict[str, int],
    listing_hashes_per_app_id_for_rare: dict[str, int],
) -> dict[str, dict]:
    all_app_ids = set(listing_hashes_per_app_id_for_common)
    all_app_ids = all_app_ids.union(listing_hashes_per_app_id_for_uncommon)
    all_app_ids = all_app_ids.union(listing_hashes_per_app_id_for_rare)

    item_rarity_patterns_per_app_id: dict[str, dict] = {}

    for app_id in all_app_ids:
        item_rarity_patterns_per_app_id[app_id] = {}

        try:
            num_common = listing_hashes_per_app_id_for_common[app_id]
        except KeyError:
            num_common = None

        try:
            num_uncommon = listing_hashes_per_app_id_for_uncommon[app_id]
        except KeyError:
            num_uncommon = None

        try:
            num_rare = listing_hashes_per_app_id_for_rare[app_id]
        except KeyError:
            num_rare = None

        item_rarity_patterns_per_app_id[app_id]["common"] = num_common
        item_rarity_patterns_per_app_id[app_id]["uncommon"] = num_uncommon
        item_rarity_patterns_per_app_id[app_id]["rare"] = num_rare

    return item_rarity_patterns_per_app_id
