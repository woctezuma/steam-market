# Objective: detect the buzz, for games which I do not own yet, i.e. find packs which are likely to have high bid orders

from src.market_arbitrage_utils import (
    filter_out_badges_with_low_sell_price,
    find_badge_arbitrages,
    print_arbitrages,
)
from src.market_buzz_utils import (
    fill_in_badge_data_with_data_from_steam_card_exchange,
    filter_listings,
    filter_out_unmarketable_packs,
    print_packs_with_high_buzz,
    sort_according_to_buzz,
)
from src.market_listing import get_item_nameid_batch
from src.market_order import load_market_order_data
from src.market_search import load_all_listings, update_all_listings
from src.market_utils import filter_out_dubious_listing_hashes


def main(
    retrieve_listings_from_scratch: bool = False,
    retrieve_market_orders_online: bool = False,
    force_update_from_steam_card_exchange: bool = False,
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
    use_a_constant_price_threshold: bool = False,
    min_sell_price: float = 30,
    min_num_listings: int = 3,
    num_packs_to_display: int = 10,
    verbose: bool = False,
) -> None:
    # Load list of all listing hashes

    if retrieve_listings_from_scratch:
        update_all_listings()

    all_listings = load_all_listings()

    all_listings = filter_out_dubious_listing_hashes(all_listings)

    # Import information from SteamCardExchange

    aggregated_badge_data = fill_in_badge_data_with_data_from_steam_card_exchange(
        all_listings,
        force_update_from_steam_card_exchange=force_update_from_steam_card_exchange,
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
    )

    # *Heuristic* filtering of listing hashes

    if use_a_constant_price_threshold:
        filtered_listing_hashes = filter_listings(
            all_listings,
            min_sell_price=min_sell_price,
            min_num_listings=min_num_listings,
        )

        filtered_listings = {
            k: v for k, v in all_listings.items() if k in filtered_listing_hashes
        }

        filtered_badge_data = fill_in_badge_data_with_data_from_steam_card_exchange(
            filtered_listings,
            force_update_from_steam_card_exchange=force_update_from_steam_card_exchange,
            enforced_sack_of_gems_price=enforced_sack_of_gems_price,
            minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        )

    else:
        filtered_badge_data = filter_out_badges_with_low_sell_price(
            aggregated_badge_data,
        )

        filtered_listing_hashes = [
            badge["listing_hash"] for badge in filtered_badge_data.values()
        ]

    # Pre-retrieval of item name ids

    get_item_nameid_batch(filtered_listing_hashes)

    # Download market orders

    market_order_dict = load_market_order_data(
        filtered_badge_data,
        trim_output=True,
        retrieve_market_orders_online=retrieve_market_orders_online,
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


if __name__ == "__main__":
    main(
        retrieve_listings_from_scratch=True,
        retrieve_market_orders_online=True,
        force_update_from_steam_card_exchange=True,
        enforced_sack_of_gems_price=None,
        minimum_allowed_sack_of_gems_price=None,
        use_a_constant_price_threshold=False,
        min_sell_price=30,
        min_num_listings=3,
        num_packs_to_display=100,
        verbose=True,
    )
