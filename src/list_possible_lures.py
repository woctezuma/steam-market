# Objective: list appIDs for which:
# - a booster pack was crafted at least once in the past,
# - the sell price (without the Steam Market fee) is higher than the cost to craft a Booster Pack.

from src.creation_time_utils import load_next_creation_time_data
from src.market_search import load_all_listings
from src.parsing_utils import parse_badge_creation_details
from src.sack_of_gems import get_num_gems_per_sack_of_gems, load_sack_of_gems_price
from src.transaction_fee import compute_sell_price_without_fee
from src.utils import convert_listing_hash_to_app_id


def get_app_ids_of_interest() -> list[str]:
    # List appIDs for which a booster pack was crafted at least once in the past.

    data = load_next_creation_time_data()

    return list(data)


def get_sell_prices_without_fee(
    app_ids: list[str],
    price_offset_in_euros: float = 0.0,
) -> dict[str, float]:
    # Load sell prices (without fee).
    #
    # NB: an arbitrary price offset (greater than or equal to zero) can be input to constrain the problem even more.
    # This is a security: if the price offset is positive (>0), then we know that we can under-cut the lowest sell order
    # and still be able to make a profit if someone agrees to buy from us.

    data = load_all_listings()

    sell_prices = {}

    for listing_hash in data:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        if app_id in app_ids:
            current_data = data[listing_hash]

            sell_price_in_cents = current_data["sell_price"]
            sell_price_in_euros = int(sell_price_in_cents) / 100
            sell_price_after_arbitrary_offset = sell_price_in_euros - abs(
                price_offset_in_euros,
            )
            sell_price_in_euros_without_fee = compute_sell_price_without_fee(
                sell_price_after_arbitrary_offset,
            )

            sell_prices[app_id] = sell_price_in_euros_without_fee

    return sell_prices


def get_gem_amount_for_a_booster_pack(app_ids: list[str]) -> dict[str, int]:
    # Load gem amounts required to craft a Booster Pack.

    data = parse_badge_creation_details(from_javascript=True)

    gem_amounts_for_a_booster_pack = {}

    for app_id in app_ids:
        try:
            current_data = data[app_id]
        except KeyError:
            current_data = {"gem_value": 9999}

        gem_amount = current_data["gem_value"]

        gem_amounts_for_a_booster_pack[app_id] = gem_amount

    return gem_amounts_for_a_booster_pack


def filter_app_ids_with_potential_profit(
    app_ids: list[str],
    sell_prices_without_fee: dict[str, float],
    gem_amounts_for_a_booster_pack: dict[str, int],
    gem_sack_price_in_euros: float | None = None,
    verbose: bool = True,
) -> list[str]:
    # Filter out appIDs for which the sell price (without fee) is lower than the cost to craft a Booster Pack.
    # Indeed, a profit is impossible for these appIDs.

    if gem_sack_price_in_euros is None:
        # If set to None to load from disk the price of a sack of gems:
        gem_sack_price_in_euros = load_sack_of_gems_price()

    num_gems_per_sack = get_num_gems_per_sack_of_gems()

    filtered_app_ids = []

    for app_id in app_ids:
        gem_amount = gem_amounts_for_a_booster_pack[app_id]
        gem_price = gem_amount * gem_sack_price_in_euros / num_gems_per_sack

        sell_price_without_fee = sell_prices_without_fee[app_id]

        profit = sell_price_without_fee - gem_price

        profit_is_possible = bool(profit > 0)

        if profit_is_possible:
            filtered_app_ids.append(app_id)

    if verbose:
        positive = sorted(filtered_app_ids, key=int)
        negative = sorted(set(app_ids).difference(filtered_app_ids), key=int)

        print(
            "\nPositive ({}): {}\n\nNegative ({}): {}\n\nTotal ({})".format(
                len(positive),
                positive,
                len(negative),
                negative,
                len(app_ids),
            ),
        )

    return filtered_app_ids


def remove_app_ids_previously_processed(
    filtered_app_ids: list[str],
    app_ids_previously_processed: list[str] | None = None,
    verbose: bool = True,
) -> list[str]:
    # Manually remove previously processed appIDs from the list of returned appIDs of interest.

    if app_ids_previously_processed is None:
        app_ids_previously_processed = []

    app_ids_to_do = sorted(
        set(filtered_app_ids).difference(app_ids_previously_processed),
        key=int,
    )

    if verbose:
        print(f"\nPositive after trimming ({len(app_ids_to_do)}): {app_ids_to_do}")

    return app_ids_to_do


def main() -> None:
    gem_sack_price_in_euros = 0.40

    # Positive value to ensure under-cutting is possible
    price_offset_in_euros = 0.1

    app_ids_previously_processed = [
        205890,
        359400,
        395620,
        398140,
        448720,
        468250,
        533690,
        554640,
        582350,
        589870,
        599060,
        615340,
        325120,
        257670,
        318090,
        314000,
        558490,
        565020,
        254880,
        554660,
        266150,
        348840,
        304170,
        391210,
        600750,
        345520,
        523060,
        259640,
        442810,
        237760,
        645830,
        272330,
        383690,
        320590,
        544730,
        290140,
        434780,
        522340,
        324710,
        307050,
        499950,
        467320,
        630140,
        395520,
        874240,
        551170,
        300040,
        251150,
        1045520,
        705810,
        533540,
        459820,
        878380,
        253230,
        675630,
        368180,
        679990,
        621880,
        393530,
        99900,
        486460,
        363330,
        421700,
        550470,
        844870,
        331600,
        562260,
        591960,
        310360,
        296550,
        316010,
        250740,
        324470,
        521340,
        33680,
        883860,
        632470,
        451230,
        523680,
        432290,
        223650,
        338340,
        257710,
        287920,
        270010,
        416450,
        261570,
        381640,
        520910,
        345820,
        795100,
        291550,
        413410,
        996580,
        794600,
        413420,
        403700,
        921590,
    ]

    # List appIDs of interest

    app_ids = get_app_ids_of_interest()

    # List data corresponding to appIDs:
    # - sell prices,
    # - gem amounts required to craft a Booster Pack.

    sell_prices_without_fee = get_sell_prices_without_fee(
        app_ids,
        price_offset_in_euros=price_offset_in_euros,
    )
    gem_amounts_for_a_booster_pack = get_gem_amount_for_a_booster_pack(app_ids)

    # Filter out appIDs for which a profit is impossible:

    filtered_app_ids = filter_app_ids_with_potential_profit(
        app_ids,
        sell_prices_without_fee,
        gem_amounts_for_a_booster_pack,
        gem_sack_price_in_euros=gem_sack_price_in_euros,
        verbose=True,
    )

    # Manually remove previously processed appIDs:

    remove_app_ids_previously_processed(
        filtered_app_ids,
        app_ids_previously_processed=[str(i) for i in app_ids_previously_processed],
        verbose=True,
    )


if __name__ == "__main__":
    main()
