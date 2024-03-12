# Objective: match listing hashes with badge creation details.

import random

from src.market_listing import get_item_nameid_batch
from src.market_search import load_all_listings, update_all_listings
from src.parsing_utils import parse_badge_creation_details
from src.sack_of_gems import get_gem_price
from src.utils import convert_listing_hash_to_app_id, convert_listing_hash_to_app_name


def determine_whether_listing_hash_is_dubious(listing_hash: str) -> bool:
    dubious_str = "#Economy_TradingCards_"

    return bool(dubious_str in listing_hash)


def filter_out_dubious_listing_hashes(
    all_listings: dict[str, dict],
    verbose: bool = True,
) -> dict[str, dict]:
    # Filter out listing hashes which hint at a dubious market listing for the booster pack. For instance:
    #   362680-Fran Bow #Economy_TradingCards_ItemType_BoosterPack
    #   844870-#Economy_TradingCards_Type_GameType

    filtered_listings = {}

    for listing_hash in all_listings:
        individual_market_listing = all_listings[listing_hash]

        booster_pack_is_dubious = determine_whether_listing_hash_is_dubious(
            listing_hash,
        )

        if not booster_pack_is_dubious:
            filtered_listings[listing_hash] = individual_market_listing
        elif verbose:
            print(f"Omitting dubious listing hash: {listing_hash}")

    if verbose:
        print(
            f"There are {len(filtered_listings)} seemingly valid market listings. ({len(all_listings) - len(filtered_listings)} omitted because of a dubious listing hash)",
        )

    return filtered_listings


def match_badges_with_listing_hashes(
    badge_creation_details: dict[str, dict] | None = None,
    all_listings: dict[str, dict] | None = None,
    verbose: bool = True,
) -> dict[str, str | None]:
    # Badges for games which I own

    if badge_creation_details is None:
        badge_creation_details = parse_badge_creation_details()

    badge_app_ids = list(badge_creation_details.keys())

    # Listings for ALL the existing Booster Packs

    if all_listings is None:
        all_listings = load_all_listings()

    all_listing_hashes = list(all_listings.keys())

    # Dictionaries to match appIDs or app names with listing hashes

    listing_matches_with_app_ids = {}
    listing_matches_with_app_names = {}
    for listing_hash in all_listing_hashes:
        app_id = convert_listing_hash_to_app_id(listing_hash)
        app_name = convert_listing_hash_to_app_name(listing_hash)

        listing_matches_with_app_ids[app_id] = listing_hash
        listing_matches_with_app_names[app_name] = listing_hash

    # Match badges with listing hashes

    badge_matches: dict[str, str | None] = {}
    for app_id in badge_app_ids:
        app_name = badge_creation_details[app_id]["name"]

        try:
            badge_matches[app_id] = listing_matches_with_app_ids[app_id]
        except KeyError:
            try:
                badge_matches[app_id] = listing_matches_with_app_names[app_name]
                if verbose:
                    print(
                        f"Match for {app_name} (appID = {app_id}) with name instead of id.",
                    )
            except KeyError:
                badge_matches[app_id] = None
                if verbose:
                    print(f"No match found for {app_name} (appID = {app_id})")

    if verbose:
        print(
            f"#badges = {len(badge_app_ids)} ; #matching hashes found = {len(badge_matches)}",
        )

    return badge_matches


def aggregate_badge_data(
    badge_creation_details: dict[str, dict],
    badge_matches: dict[str, str | None],
    all_listings: dict[str, dict] | None = None,
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
    retrieve_gem_price_from_scratch: bool = False,
) -> dict[str, dict]:
    # Aggregate data:
    #       owned appID --> (gem PRICE, sell price)
    # where:
    # - the gem price is the price required to buy gems on the market to then craft a booster pack for this game,
    # - the sell price is the price which sellers are asking for this booster pack.
    #
    # NB: ensure the same currency is used.

    if all_listings is None:
        all_listings = load_all_listings()

    gem_price = get_gem_price(
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
    )

    if gem_price <= 0:
        print(f"[ERROR] The price of a gem is non-positive: {gem_price}€.")
        raise AssertionError

    badge_app_ids = list(badge_creation_details.keys())

    aggregated_badge_data: dict[str, dict] = {}

    for app_id in badge_app_ids:
        app_name = badge_creation_details[app_id]["name"]
        gem_amount_required_to_craft_booster_pack = badge_creation_details[app_id][
            "gem_value"
        ]
        try:
            next_creation_time = badge_creation_details[app_id]["next_creation_time"]
        except KeyError:
            next_creation_time = None
        listing_hash = badge_matches[app_id]

        if listing_hash is None:
            # For some reason for Conran - The dinky Raccoon (appID = 612150), there is no listing of any "Booster Pack"
            # Reference: https://steamcommunity.com/market/search?appid=753&category_753_Game%5B0%5D=tag_app_612150
            continue

        sell_price_in_cents = all_listings[listing_hash]["sell_price"]
        sell_price_in_euros = sell_price_in_cents / 100

        aggregated_badge_data[app_id] = {}
        aggregated_badge_data[app_id]["name"] = app_name
        aggregated_badge_data[app_id]["listing_hash"] = listing_hash
        aggregated_badge_data[app_id]["gem_amount"] = (
            gem_amount_required_to_craft_booster_pack
        )
        aggregated_badge_data[app_id]["gem_price"] = (
            gem_amount_required_to_craft_booster_pack * gem_price
        )
        aggregated_badge_data[app_id]["sell_price"] = sell_price_in_euros
        aggregated_badge_data[app_id]["next_creation_time"] = next_creation_time

    return aggregated_badge_data


def load_aggregated_badge_data(
    retrieve_listings_from_scratch: bool = False,
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
    from_javascript: bool = False,
) -> dict[str, dict]:
    badge_creation_details = parse_badge_creation_details(
        from_javascript=from_javascript,
    )

    if retrieve_listings_from_scratch:
        update_all_listings()

    all_listings = load_all_listings()

    all_listings = filter_out_dubious_listing_hashes(all_listings)

    badge_matches = match_badges_with_listing_hashes(
        badge_creation_details,
        all_listings,
    )

    retrieve_gem_price_from_scratch = bool(enforced_sack_of_gems_price is None)

    return aggregate_badge_data(
        badge_creation_details,
        badge_matches,
        all_listings=all_listings,
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
    )


def populate_random_samples_of_badge_data(
    badge_data: dict[str, dict] | None = None,
    num_samples: int = 50,
) -> bool:
    if badge_data is None:
        badge_data = load_aggregated_badge_data()

    listing_hashes = [badge_data[app_id]["listing_hash"] for app_id in badge_data]

    num_samples = min(num_samples, len(listing_hashes))

    listing_hash_samples = [
        listing_hashes[i]
        for i in random.sample(range(len(listing_hashes)), k=num_samples)
    ]

    get_item_nameid_batch(listing_hash_samples)

    return True


def main(populate_all_item_name_ids: bool = False) -> bool:
    if populate_all_item_name_ids:
        # Pre-retrieval of ALL the MISSING item name ids.
        # Caveat: this may require a long time, due to API rate limits.

        all_listings = load_all_listings()
        get_item_nameid_batch(listing_hashes=all_listings)

    else:
        aggregated_badge_data = load_aggregated_badge_data()
        populate_random_samples_of_badge_data(aggregated_badge_data, num_samples=50)

    return True


if __name__ == "__main__":
    main(populate_all_item_name_ids=False)
