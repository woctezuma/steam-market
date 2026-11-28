# Objective: detect the buzz, for games which I do not own yet, i.e. find packs which are likely to have high bid orders

import argparse
from typing import Final

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

DEFAULT_MIN_SELL_PRICE: Final[int] = 30
DEFAULT_MIN_NUM_LISTINGS: Final[int] = 3
DEFAULT_NUM_PACKS_TO_DISPLAY: Final[int] = 10


def apply_workflow(
    *,
    retrieve_listings_from_scratch: bool = False,
    retrieve_market_orders_online: bool = False,
    force_update_from_steam_card_exchange: bool = False,
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
    use_a_constant_price_threshold: bool = False,
    min_sell_price: int = DEFAULT_MIN_SELL_PRICE,
    min_num_listings: int = DEFAULT_MIN_NUM_LISTINGS,
    num_packs_to_display: int = DEFAULT_NUM_PACKS_TO_DISPLAY,
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
        _unknown_market_order_dict,
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


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect the buzz, for games which I do not own yet, i.e. find packs which are likely to have high bid orders.",
    )

    parser.add_argument(
        "--retrieve-listings-from-scratch",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--retrieve-market-orders-online",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--force-update-from-steam-card-exchange",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--enforced-sack-of-gems-price", type=float, default=None)
    parser.add_argument(
        "--minimum-allowed-sack-of-gems-price",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--use-a-constant-price-threshold",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument("--min-sell-price", type=int, default=30)
    parser.add_argument("--min-num-listings", type=int, default=3)
    parser.add_argument("--num-packs-to-display", type=int, default=100)
    parser.add_argument(
        "--verbose",
        action=argparse.BooleanOptionalAction,
        default=True,
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_argument_parser().parse_args(argv)

    apply_workflow(**vars(args))


if __name__ == "__main__":
    main()
