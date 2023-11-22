from src.download_steam_card_exchange import parse_data_from_steam_card_exchange
from src.market_listing import get_steam_market_listing_url
from src.market_search import load_all_listings
from src.sack_of_gems import get_gem_price
from src.utils import (
    convert_listing_hash_to_app_id,
    convert_listing_hash_to_app_name,
    get_category_name_for_booster_packs,
    get_steam_store_url,
    get_steamcardexchange_url,
)


def filter_listings(
    all_listings: dict[str, dict] | None = None,
    min_sell_price: float = 30,  # in cents
    min_num_listings: int = 20,
    # to remove listings with very few sellers, who chose unrealistic sell prices
    verbose: bool = True,
) -> list[str]:
    if all_listings is None:
        all_listings = load_all_listings()

    # Sort listing hashes with respect to the ask

    sorted_listing_hashes = sorted(
        all_listings,
        reverse=True,
        key=lambda x: all_listings[x]["sell_price"],
    )

    # *Heuristic* filtering of listing hashes

    filtered_listing_hashes = list(
        filter(
            lambda x: all_listings[x]["sell_price"] >= min_sell_price
            and all_listings[x]["sell_listings"] >= min_num_listings,
            sorted_listing_hashes,
        ),
    )

    if verbose:
        print(f"{len(filtered_listing_hashes)} hashes found.\n")

    return filtered_listing_hashes


def convert_to_badges(
    filtered_listing_hashes: dict[str, dict] | list[str],
    max_num_badges: int | None = None,
) -> dict[str, dict]:
    badge_data: dict[str, dict] = {}

    for i, listing_hash in enumerate(filtered_listing_hashes):
        if max_num_badges is not None and i >= max_num_badges:
            break

        app_id = convert_listing_hash_to_app_id(listing_hash)

        badge_data[app_id] = {}
        badge_data[app_id]["listing_hash"] = listing_hash

    return badge_data


def filter_out_unmarketable_packs(
    market_order_dict: dict[str, dict],
) -> tuple[dict[str, dict], dict[str, dict]]:
    marketable_market_order_dict = {}
    unknown_market_order_dict = {}

    for listing_hash in market_order_dict:
        try:
            is_marketable = market_order_dict[listing_hash]["is_marketable"]
        except KeyError:
            print(f"Marketable status not found for {listing_hash}")
            unknown_market_order_dict[listing_hash] = market_order_dict[listing_hash]

            is_marketable = False  # avoid taking any risk: ASSUME the booster pack is NOT marketable

        if is_marketable:
            marketable_market_order_dict[listing_hash] = market_order_dict[listing_hash]

    return marketable_market_order_dict, unknown_market_order_dict


def sort_according_to_buzz(
    market_order_dict: dict[str, dict],
    marketable_market_order_dict: dict[str, dict] | None = None,
) -> list[str]:
    if marketable_market_order_dict is None:
        (
            marketable_market_order_dict,
            unknown_market_order_dict,
        ) = filter_out_unmarketable_packs(market_order_dict)

    return sorted(
        marketable_market_order_dict,
        reverse=True,
        key=lambda x: market_order_dict[x]["bid"],
    )


def print_packs_with_high_buzz(
    hashes_for_best_bid: list[str],
    market_order_dict: dict[str, dict],
    item_rarity_patterns_per_app_id: dict[str, dict] | None = None,
    category_name: str | None = None,
    num_packs_to_display: int = 10,
) -> None:
    if item_rarity_patterns_per_app_id is None:
        item_rarity_patterns_per_app_id = {}

    if category_name is None:
        category_name = get_category_name_for_booster_packs()

    print(f"# {category_name.capitalize()} with high buy orders\n")

    for i, listing_hash in enumerate(hashes_for_best_bid):
        if i >= num_packs_to_display:
            break

        app_id = convert_listing_hash_to_app_id(listing_hash)
        app_name = convert_listing_hash_to_app_name(listing_hash)

        bid = market_order_dict[listing_hash]["bid"]
        bid_volume = market_order_dict[listing_hash]["bid_volume"]

        markdown_compatible_steam_market_url = get_steam_market_listing_url(
            listing_hash=listing_hash,
            render_as_json=False,
            replace_spaces=True,
        )

        if category_name != get_category_name_for_booster_packs():
            # Display the listing hash, because we cannot extract the app name from the listing hash for:
            # - profile backgrounds,
            # - and emoticons.
            app_name = listing_hash

        try:
            item_rarity_pattern = item_rarity_patterns_per_app_id[app_id]

            num_different_items_of_common_rarity = item_rarity_pattern["common"]
            num_different_items_of_uncommon_rarity = item_rarity_pattern["uncommon"]
            num_different_items_of_rare_rarity = item_rarity_pattern["rare"]

            item_rarity_pattern_info = (
                " ; rarity pattern C/UC/R: {}/{}/{} items".format(
                    num_different_items_of_common_rarity,
                    num_different_items_of_uncommon_rarity,
                    num_different_items_of_rare_rarity,
                )
            )
        except (TypeError, KeyError):
            item_rarity_pattern_info = ""

        print(
            "{:3}) [[store]({})][[market]({})] [{}]({}) ; bid: {}€ (volume: {}){}".format(
                i + 1,
                get_steam_store_url(app_id),
                markdown_compatible_steam_market_url,
                app_name,
                get_steamcardexchange_url(app_id),
                bid,
                bid_volume,
                item_rarity_pattern_info,
            ),
        )


def fill_in_badge_data_with_data_from_steam_card_exchange(
    all_listings: dict[str, dict],
    aggregated_badge_data: dict[str, dict] | None = None,
    force_update_from_steam_card_exchange: bool = False,
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
) -> dict[str, dict]:
    if aggregated_badge_data is None:
        aggregated_badge_data = {}  # solely to silence an error for mypy type-hinting
        aggregated_badge_data = convert_to_badges(all_listings)

    dico = parse_data_from_steam_card_exchange(
        force_update_from_steam_card_exchange=force_update_from_steam_card_exchange,
    )

    retrieve_gem_price_from_scratch = bool(enforced_sack_of_gems_price is None)

    gem_price = get_gem_price(
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
    )

    for app_id in aggregated_badge_data:
        listing_hash = aggregated_badge_data[app_id]["listing_hash"]

        sell_price_in_cents = all_listings[listing_hash]["sell_price"]
        sell_price_in_euros = sell_price_in_cents / 100

        try:
            data_from_steam_card_exchange = dico[app_id]
        except KeyError:
            print(f"No data found for appID={app_id}.")
            data_from_steam_card_exchange = {
                "name": None,
                "gem_amount": 1200,  # by default, use the highest possible value
            }

        aggregated_badge_data[app_id]["name"] = data_from_steam_card_exchange["name"]
        gem_amount_required_to_craft_booster_pack = data_from_steam_card_exchange[
            "gem_amount"
        ]

        aggregated_badge_data[app_id][
            "gem_amount"
        ] = gem_amount_required_to_craft_booster_pack
        aggregated_badge_data[app_id]["gem_price"] = (
            gem_amount_required_to_craft_booster_pack * gem_price
        )
        aggregated_badge_data[app_id]["sell_price"] = sell_price_in_euros

    return aggregated_badge_data
