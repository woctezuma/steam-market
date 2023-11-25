import requests

from src.json_utils import load_json, save_json
from src.market_gamble_utils import update_all_listings_for_foil_cards
from src.market_listing import (
    get_steam_market_listing_url,
    load_all_listing_details,
    update_all_listing_details,
)
from src.market_search import load_all_listings
from src.personal_info import (
    get_cookie_dict,
    update_and_save_cookie_to_disk_if_values_changed,
)
from src.sack_of_gems import get_num_gems_per_sack_of_gems, load_sack_of_gems_price
from src.utils import (
    TIMEOUT_IN_SECONDS,
    convert_listing_hash_to_app_id,
    get_bullet_point_for_display,
    get_goo_details_file_nam_for_for_foil_cards,
    get_listing_details_output_file_name_for_foil_cards,
    get_listing_output_file_name_for_foil_cards,
)


def get_steam_goo_value_url() -> str:
    return "https://steamcommunity.com/auction/ajaxgetgoovalueforitemtype/"


def get_item_type_no_for_trading_cards(
    listing_hash: str | None = None,
    all_listing_details: dict[str, dict] | None = None,
    listing_details_output_file_name: str | None = None,
    verbose: bool = True,
) -> int:
    # Caveat: the item type is not always equal to 2. Check appID 232770 (POSTAL) for example!
    # Reference: https://gaming.stackexchange.com/a/351941
    #
    # With app_id == 232770 and border_color == 0
    # ===========================================
    # Item type: 2	Goo value: 100      Rare emoticon 5
    # Item type: 3	Goo value: 100      Common emoticon 2
    # Item type: 4	Goo value: 100      Common emoticon 1
    # Item type: 5	Goo value: 100      Uncommon emoticon 4
    # Item type: 6	Goo value: 100      Uncommon emoticon 3
    # Item type: 12	Goo value: 100      Common profile background 1
    # Item type: 13	Goo value: 100      Rare profile background 4
    # Item type: 14	Goo value: 100      Uncommon profile background 2
    # Item type: 15	Goo value: 40       Normal Card 1
    # Item type: 16	Goo value: 40       Normal Card 2
    # Item type: 17	Goo value: 40       Normal Card 3
    # Item type: 18	Goo value: 40       Normal Card 4
    # Item type: 19	Goo value: 40       Normal Card 5
    # Item type: 20	Goo value: 100      Uncommon profile background 3
    # Item type: 21	Goo value: 100      Rare profile background 5

    if listing_hash is None:
        item_type_no = 2

        if verbose:
            print(
                f"Assuming item type is equal to {item_type_no}, which might be wrong.",
            )

    else:
        if listing_details_output_file_name is None:
            listing_details_output_file_name = (
                get_listing_details_output_file_name_for_foil_cards()
            )

        if all_listing_details is None:
            all_listing_details = load_all_listing_details(
                listing_details_output_file_name=listing_details_output_file_name,
            )

        try:
            listing_details = all_listing_details[listing_hash]
        except KeyError:
            # Caveat: the code below is not the intended way to find item types, because we do not take into account
            #         rate limits! This is okay for one listing hash, but this would be an issue for many of them!
            #
            #         Ideally, you should have called update_all_listing_details() with
            #         the FULL list of listing hashes to be processed, stored in variable 'listing_hashes_to_process',
            #         rather than with just ONE listing hash.
            listing_hashes_to_process = [listing_hash]

            if verbose:
                print(
                    f"A query is necessary to download listing details for {listing_hash}.",
                )

            updated_all_listing_details = update_all_listing_details(
                listing_hashes=listing_hashes_to_process,
                listing_details_output_file_name=listing_details_output_file_name,
            )

            listing_details = updated_all_listing_details[listing_hash]

        item_type_no = listing_details["item_type_no"]

        if verbose:
            print(f"Retrieving item type {item_type_no} for {listing_hash}.")

    return item_type_no


def get_border_color_no_for_trading_cards(is_foil: bool = False) -> int:
    # NB: this leads to a goo value 10 times higher than with border_corlor_no equal to zero. However, it seems to
    # be applied without any check, so that the returned goo values are misleading when applied to any item other
    # than a trading card, such as an emoticon and a profile background.
    return 1 if is_foil else 0


def get_steam_goo_value_parameters(
    app_id: str,
    item_type: int | None = None,
    listing_hash: str | None = None,
    is_foil: bool = True,
    verbose: bool = True,
) -> dict[str, str | int]:
    if item_type is None:
        item_type = get_item_type_no_for_trading_cards(
            listing_hash=listing_hash,
            verbose=verbose,
        )

    border_color = get_border_color_no_for_trading_cards(is_foil=is_foil)

    params: dict[str, str | int] = {}

    params["appid"] = app_id
    params["item_type"] = item_type
    params["border_color"] = border_color

    return params


def query_goo_value(
    app_id: str,
    item_type: int | None,
    verbose: bool = True,
) -> int | None:
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    url = get_steam_goo_value_url()

    req_data = get_steam_goo_value_parameters(
        app_id=app_id,
        item_type=item_type,
    )

    if has_secured_cookie:
        resp_data = requests.get(
            url,
            params=req_data,
            cookies=cookie,
            timeout=TIMEOUT_IN_SECONDS,
        )
    else:
        resp_data = requests.get(url, params=req_data, timeout=TIMEOUT_IN_SECONDS)

    if resp_data.ok:
        result = resp_data.json()

        if has_secured_cookie:
            jar = dict(resp_data.cookies)
            cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

        goo_value = int(result["goo_value"])

        if verbose and goo_value > 0:
            print(
                f"AppID: {app_id} ; Item type: {item_type} ; Goo value: {goo_value} gems",
            )
    else:
        goo_value = None

    return goo_value


def get_listings_for_foil_cards(
    retrieve_listings_from_scratch: bool,
    listing_output_file_name: str | None = None,
    start_index: int = 0,
    verbose: bool = True,
) -> dict[str, dict]:
    if retrieve_listings_from_scratch:
        update_all_listings_for_foil_cards(start_index=start_index)

    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name_for_foil_cards()

    all_listings = load_all_listings(listing_output_file_name)

    if verbose:
        print(f"#listings = {len(all_listings)}")

    return all_listings


def group_listing_hashes_by_app_id(
    all_listings: dict[str, dict],
    verbose: bool = True,
) -> dict[str, list[str]]:
    groups_by_app_id: dict[str, list[str]] = {}
    for listing_hash in all_listings:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        try:
            groups_by_app_id[app_id].append(listing_hash)
        except KeyError:
            groups_by_app_id[app_id] = [listing_hash]

    if verbose:
        print(f"#app_ids = {len(groups_by_app_id)}")

    return groups_by_app_id


def find_cheapest_listing_hashes(
    all_listings: dict[str, dict],
    groups_by_app_id: dict[str, list[str]],
) -> list[str]:
    cheapest_listing_hashes = []

    for app_id in groups_by_app_id:
        listing_hashes = groups_by_app_id[app_id]

        # Sort with respect to two attributes:
        #   - ascending sell prices,
        #   - **descending** volumes.
        #  So that, in case the sell price is equal for two listings, the listing with the highest volume is favored.

        sorted_listing_hashes = sorted(
            listing_hashes,
            key=lambda x: (
                all_listings[x]["sell_price"],
                -all_listings[x]["sell_listings"],
            ),
        )

        cheapest_listing_hash = sorted_listing_hashes[0]

        cheapest_listing_hashes.append(cheapest_listing_hash)

    return cheapest_listing_hashes


def find_representative_listing_hashes(
    groups_by_app_id: dict[str, list[str]],
    dictionary_of_representative_listing_hashes: dict[str, list[str]] | None = None,
) -> list[str]:
    representative_listing_hashes = []

    for app_id in groups_by_app_id:
        if dictionary_of_representative_listing_hashes is not None:
            try:
                # For retro-compatibility, we try to use representative for which we previously downloaded item name ids
                previously_used_listing_hashes_for_app_id = (
                    dictionary_of_representative_listing_hashes[app_id]
                )
            except KeyError:
                previously_used_listing_hashes_for_app_id = None
        else:
            previously_used_listing_hashes_for_app_id = None

        listing_hashes = groups_by_app_id[app_id]

        # Sort with respect to lexicographical order.

        sorted_listing_hashes = sorted(listing_hashes)

        representative_listing_hash = sorted_listing_hashes[0]

        if (
            previously_used_listing_hashes_for_app_id is None
            or len(previously_used_listing_hashes_for_app_id) == 0
        ):
            # Append the first element found in groups_by_app_id, after sorting by lexicographical order:
            representative_listing_hashes.append(representative_listing_hash)
        else:
            # Concatenate the list of elements previously used, i.e. for which we should already have the item name ids.
            representative_listing_hashes += previously_used_listing_hashes_for_app_id

    return representative_listing_hashes


def find_eligible_listing_hashes(all_listings: dict[str, dict]) -> list[str]:
    # List eligible listing hashes (positive ask volume, and positive ask price)

    return [
        listing_hash
        for listing_hash in all_listings
        if all_listings[listing_hash]["sell_listings"] > 0
        and all_listings[listing_hash]["sell_price"] > 0
    ]


def filter_listings_with_arbitrary_price_threshold(
    all_listings: dict[str, dict],
    listing_hashes_to_filter_from: list[str],
    price_threshold_in_cents: float | None = None,
    verbose: bool = True,
) -> list[str]:
    if price_threshold_in_cents is not None:
        filtered_cheapest_listing_hashes = []

        for listing_hash in listing_hashes_to_filter_from:
            ask = all_listings[listing_hash]["sell_price"]

            if ask < price_threshold_in_cents:
                filtered_cheapest_listing_hashes.append(listing_hash)

    else:
        filtered_cheapest_listing_hashes = listing_hashes_to_filter_from

    if verbose:
        print(f"#listings (after filtering) = {len(filtered_cheapest_listing_hashes)}")

    return filtered_cheapest_listing_hashes


def load_all_goo_details(
    goo_details_file_name: str | None = None,
    verbose: bool = True,
) -> dict[str, int | None]:
    if goo_details_file_name is None:
        goo_details_file_name = get_goo_details_file_nam_for_for_foil_cards()

    try:
        all_goo_details = load_json(goo_details_file_name)
    except FileNotFoundError:
        all_goo_details = {}

    if verbose:
        print(f"Loading {len(all_goo_details)} goo details from disk.")

    return all_goo_details


def save_all_goo_details(
    all_goo_details: dict[str, int | None],
    goo_details_file_name: str | None = None,
) -> None:
    if goo_details_file_name is None:
        goo_details_file_name = get_goo_details_file_nam_for_for_foil_cards()
    save_json(all_goo_details, goo_details_file_name)


def filter_out_listing_hashes_if_goo_details_are_already_known_for_app_id(
    filtered_cheapest_listing_hashes: list[str],
    goo_details_file_name_for_for_foil_cards: str | None = None,
    verbose: bool = True,
) -> list[str]:
    # Filter out listings associated with an appID for which we already know the goo details.

    if goo_details_file_name_for_for_foil_cards is None:
        goo_details_file_name_for_for_foil_cards = (
            get_goo_details_file_nam_for_for_foil_cards()
        )

    previously_downloaded_all_goo_details = load_all_goo_details(
        goo_details_file_name_for_for_foil_cards,
        verbose=verbose,
    )

    app_ids_with_previously_downloaded_goo_details = list(
        previously_downloaded_all_goo_details.keys(),
    )

    return [
        listing_hash
        for listing_hash in filtered_cheapest_listing_hashes
        if convert_listing_hash_to_app_id(listing_hash)
        not in app_ids_with_previously_downloaded_goo_details
    ]


def propagate_filter_to_representative_listing_hashes(
    listing_hashes_to_propagate_to: list[str],
    listing_hashes_to_propagate_from: list[str],
) -> list[str]:
    filtered_app_ids_based_on_price_threshold = [
        convert_listing_hash_to_app_id(listing_hash)
        for listing_hash in listing_hashes_to_propagate_from
    ]

    return [
        listing_hash
        for listing_hash in listing_hashes_to_propagate_to
        if convert_listing_hash_to_app_id(listing_hash)
        in filtered_app_ids_based_on_price_threshold
    ]


def try_again_to_download_item_type(
    app_ids_with_unreliable_goo_details: list[str],
    filtered_representative_listing_hashes: list[str],
    listing_details_output_file_name: str,
) -> None:
    listing_hashes_to_process = [
        listing_hash
        for listing_hash in filtered_representative_listing_hashes
        if convert_listing_hash_to_app_id(listing_hash)
        in app_ids_with_unreliable_goo_details
    ]

    update_all_listing_details(
        listing_hashes=listing_hashes_to_process,
        listing_details_output_file_name=listing_details_output_file_name,
    )


def try_again_to_download_goo_value(
    app_ids_with_unknown_goo_value: list[str],
    filtered_representative_listing_hashes: list[str],
    groups_by_app_id: dict[str, list[str]],
) -> None:
    filtered_representative_app_ids = [
        convert_listing_hash_to_app_id(listing_hash)
        for listing_hash in filtered_representative_listing_hashes
    ]
    app_ids_to_process = list(
        set(app_ids_with_unknown_goo_value).intersection(
            filtered_representative_app_ids,
        ),
    )

    download_missing_goo_details(
        groups_by_app_id=groups_by_app_id,
        listing_candidates=filtered_representative_listing_hashes,
        enforced_app_ids_to_process=app_ids_to_process,
    )


def get_minimal_ask_price_in_euros_on_steam_market() -> float:
    return 0.03  # in euros


def compute_unrewarding_threshold_in_gems(
    sack_of_gems_price_in_euros: float | None = None,
    retrieve_gem_price_from_scratch: bool = False,
    verbose: bool = True,
) -> float:
    # The minimal price of a card is 0.03€. A sack of 1000 gems can be bought from the Steam Market at the 'ask' price.
    #
    # Therefore, we can safely discard appIDs for which the cards are unrewarding, i.e. cards would be turned into fewer
    # gems than: get_minimal_ask_price_on_steam_market() * get_num_gems_per_sack_of_gems() / load_sack_of_gems_price().
    #
    # For instance, if a sack of 1000 gems costs 0.30€, then a card is unrewarding if it cannot be turned into more than
    # 0.03*1000/0.30 = 100 gems.

    if sack_of_gems_price_in_euros is None:
        # Load the price of a sack of 1000 gems
        sack_of_gems_price_in_euros = load_sack_of_gems_price(
            retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
            verbose=verbose,
        )

    num_gems_per_sack_of_gems = get_num_gems_per_sack_of_gems()

    minimal_ask = get_minimal_ask_price_in_euros_on_steam_market()

    return minimal_ask * num_gems_per_sack_of_gems / sack_of_gems_price_in_euros


def discard_necessarily_unrewarding_app_ids(
    all_goo_details: dict[str, int | None],
    app_ids_with_unreliable_goo_details: list[str] | None = None,
    app_ids_with_unknown_goo_value: list[str] | None = None,
    sack_of_gems_price_in_euros: float | None = None,
    retrieve_gem_price_from_scratch: bool = False,
    verbose: bool = True,
) -> list[str]:
    if app_ids_with_unreliable_goo_details is None:
        app_ids_with_unreliable_goo_details = []

    if app_ids_with_unknown_goo_value is None:
        app_ids_with_unknown_goo_value = []

    app_ids_to_omit = (
        app_ids_with_unreliable_goo_details + app_ids_with_unknown_goo_value
    )

    unrewarding_threshold_in_gems = compute_unrewarding_threshold_in_gems(
        sack_of_gems_price_in_euros=sack_of_gems_price_in_euros,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
        verbose=verbose,
    )

    potentially_rewarding_app_ids = []

    for app_id in all_goo_details:
        goo_value_in_gems = all_goo_details[app_id]

        if app_id in app_ids_to_omit:
            continue

        if goo_value_in_gems is None:
            continue

        if goo_value_in_gems >= unrewarding_threshold_in_gems:
            potentially_rewarding_app_ids.append(app_id)

    potentially_rewarding_app_ids = sorted(potentially_rewarding_app_ids, key=int)

    if verbose:
        print(
            f"There are {len(potentially_rewarding_app_ids)} potentially rewarding appIDs.",
        )

    return potentially_rewarding_app_ids


def safe_read_from_dict(
    input_dict: dict[str, int | None],
    input_key: int | str,
) -> int | None:
    input_key_as_str = str(input_key)

    try:
        value = input_dict[input_key_as_str]
    except KeyError:
        value = None

    return value


def find_listing_hashes_with_unknown_goo_value(
    listing_candidates: list[str],
    app_ids_with_unreliable_goo_details: list[str],
    all_goo_details: dict[str, int | None],
    verbose: bool = True,
) -> list[str]:
    app_ids_with_unknown_goo_value = []

    for listing_hash in listing_candidates:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        if app_id in app_ids_with_unreliable_goo_details:
            continue

        goo_value_in_gems = safe_read_from_dict(
            input_dict=all_goo_details,
            input_key=app_id,
        )

        if goo_value_in_gems is None:
            app_ids_with_unknown_goo_value.append(app_id)

    if verbose:
        print(
            "Unknown goo values for:\n{}\nTotal: {} appIDs with unknown goo value.".format(
                app_ids_with_unknown_goo_value,
                len(app_ids_with_unknown_goo_value),
            ),
        )

    return app_ids_with_unknown_goo_value


def determine_whether_an_arbitrage_might_exist_for_foil_cards(
    eligible_listing_hashes: list[str],
    all_goo_details: dict[str, int | None],
    app_ids_with_unreliable_goo_details: list[str] | None = None,
    app_ids_with_unknown_goo_value: list[str] | None = None,
    all_listings: dict[str, dict] | None = None,
    listing_output_file_name: str | None = None,
    sack_of_gems_price_in_euros: float | None = None,
    retrieve_gem_price_from_scratch: bool = True,
    verbose: bool = True,
) -> dict[str, dict[str, float]]:
    if sack_of_gems_price_in_euros is None:
        # Load the price of a sack of 1000 gems
        sack_of_gems_price_in_euros = load_sack_of_gems_price(
            retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
            verbose=verbose,
        )

    if listing_output_file_name is None:
        listing_output_file_name = get_listing_output_file_name_for_foil_cards()

    if all_listings is None:
        all_listings = load_all_listings(
            listing_output_file_name=listing_output_file_name,
        )

    if app_ids_with_unreliable_goo_details is None:
        app_ids_with_unreliable_goo_details = []

    if app_ids_with_unknown_goo_value is None:
        app_ids_with_unknown_goo_value = []

    num_gems_per_sack_of_gems = get_num_gems_per_sack_of_gems()

    sack_of_gems_price_in_cents = 100 * sack_of_gems_price_in_euros

    arbitrages = {}

    for listing_hash in eligible_listing_hashes:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        if app_id in app_ids_with_unreliable_goo_details:
            # NB: This is for goo details which were retrieved with the default item type n° (=2), which can be wrong.
            if verbose:
                print(f"[X]\tUnreliable goo details for {listing_hash}")
            continue

        goo_value_in_gems = safe_read_from_dict(
            input_dict=all_goo_details,
            input_key=app_id,
        )

        if app_id in app_ids_with_unknown_goo_value or goo_value_in_gems is None:
            # NB: This is when the goo value is unknown, despite a correct item type n° used to download goo details.
            if verbose:
                print(f"[?]\tUnknown goo value for {listing_hash}")
            continue

        goo_value_in_cents = (
            goo_value_in_gems / num_gems_per_sack_of_gems * sack_of_gems_price_in_cents
        )

        current_listing = all_listings[listing_hash]
        ask_in_cents = current_listing["sell_price"]

        if ask_in_cents == 0:
            # NB: The ask cannot be equal to zero. So, we skip the listing because of there must be a bug.
            if verbose:
                print(
                    f"[!]\tImpossible ask price ({ask_in_cents / 100:.2f}€) for {listing_hash}",
                )
            continue

        profit_in_cents = goo_value_in_cents - ask_in_cents
        is_arbitrage = bool(profit_in_cents > 0)

        if is_arbitrage:
            arbitrage = {}
            arbitrage["profit"] = profit_in_cents / 100
            arbitrage["ask"] = ask_in_cents / 100
            arbitrage["goo_amount"] = goo_value_in_gems
            arbitrage["goo_value"] = goo_value_in_cents / 100

            arbitrages[listing_hash] = arbitrage

    return arbitrages


def print_arbitrages_for_foil_cards(
    arbitrages: dict[str, dict[str, float]],
    use_numbered_bullet_points: bool = False,
) -> None:
    bullet_point = get_bullet_point_for_display(
        use_numbered_bullet_points=use_numbered_bullet_points,
    )

    sorted_arbitrages = sorted(
        arbitrages.keys(),
        key=lambda x: arbitrages[x]["profit"],
        reverse=True,
    )

    print("# Results for arbitrages with foil cards")

    for listing_hash in sorted_arbitrages:
        arbitrage = arbitrages[listing_hash]

        markdown_compatible_steam_market_url = get_steam_market_listing_url(
            listing_hash=listing_hash,
            render_as_json=False,
            replace_spaces=True,
            replace_parenthesis=True,
        )

        listing_hash_formatted_for_markdown = (
            f"[{listing_hash}]({markdown_compatible_steam_market_url})"
        )

        equivalent_price_for_sack_of_gems = (
            arbitrage["ask"] / arbitrage["goo_amount"] * get_num_gems_per_sack_of_gems()
        )

        print(
            "{}Profit: {:.2f}€\t{}\t| buy for: {:.2f}€ | turn into {} gems ({:.2f}€) | ~ {:.3f}€ per gem sack".format(
                bullet_point,
                arbitrage["profit"],
                listing_hash_formatted_for_markdown,
                arbitrage["ask"],
                arbitrage["goo_amount"],
                arbitrage["goo_value"],
                equivalent_price_for_sack_of_gems,
            ),
        )


def find_app_ids_with_unknown_item_type_for_their_representatives(
    groups_by_app_id: dict[str, list[str]],
    listing_candidates: list[str],
    all_listing_details: dict[str, dict] | None = None,
    listing_details_output_file_name: str | None = None,
    verbose: bool = True,
) -> list[str]:
    dictionary_of_representative_listing_hashes = (
        build_dictionary_of_representative_listing_hashes(
            all_listing_details,
            listing_details_output_file_name,
        )
    )

    app_ids_with_unreliable_goo_details = []

    for app_id in groups_by_app_id:
        item_type = find_item_type_for_app_id(
            app_id,
            groups_by_app_id=groups_by_app_id,
            listing_candidates=listing_candidates,
            all_listing_details=all_listing_details,
            listing_details_output_file_name=listing_details_output_file_name,
            dictionary_of_representative_listing_hashes=dictionary_of_representative_listing_hashes,
        )
        if item_type is None:
            app_ids_with_unreliable_goo_details.append(app_id)

    if verbose:
        print(
            "Unknown item types for:\n{}\nTotal: {} appIDs with unknown item type for their representative listing hashes.".format(
                app_ids_with_unreliable_goo_details,
                len(app_ids_with_unreliable_goo_details),
            ),
        )

    return app_ids_with_unreliable_goo_details


def download_missing_goo_details(
    groups_by_app_id: dict[str, list[str]],
    listing_candidates: list[str],
    all_listing_details: dict[str, dict] | None = None,
    listing_details_output_file_name: str | None = None,
    goo_details_file_name_for_for_foil_cards: str | None = None,
    enforced_app_ids_to_process: list[str] | None = None,
    num_queries_between_save: int = 100,
    verbose: bool = True,
) -> dict[str, int | None]:
    if goo_details_file_name_for_for_foil_cards is None:
        goo_details_file_name_for_for_foil_cards = (
            get_goo_details_file_nam_for_for_foil_cards()
        )

    if enforced_app_ids_to_process is None:
        enforced_app_ids_to_process = []

    dictionary_of_representative_listing_hashes = (
        build_dictionary_of_representative_listing_hashes(
            all_listing_details,
            listing_details_output_file_name,
        )
    )

    all_goo_details: dict[str, int | None] = load_all_goo_details(
        goo_details_file_name_for_for_foil_cards,
        verbose=verbose,
    )

    all_app_ids = set(groups_by_app_id)
    app_ids_with_unknown_goo_details = all_app_ids.difference(
        all_goo_details,
    )

    eligible_enforced_app_ids_to_process = all_app_ids.intersection(
        enforced_app_ids_to_process,
    )

    app_ids_to_process = app_ids_with_unknown_goo_details.union(
        eligible_enforced_app_ids_to_process,
    )

    query_count = 0

    for app_id in app_ids_to_process:
        goo_value = download_goo_value_for_app_id(
            app_id=app_id,
            groups_by_app_id=groups_by_app_id,
            listing_candidates=listing_candidates,
            all_listing_details=all_listing_details,
            listing_details_output_file_name=listing_details_output_file_name,
            dictionary_of_representative_listing_hashes=dictionary_of_representative_listing_hashes,
            verbose=verbose,
        )
        query_count += 1

        all_goo_details[app_id] = goo_value

        if query_count % num_queries_between_save == 0:
            print(f"Saving after {query_count} queries.")
            save_all_goo_details(
                all_goo_details,
                goo_details_file_name_for_for_foil_cards,
            )

    # Final save

    if query_count > 0:
        print(f"Final save after {query_count} queries.")
        save_all_goo_details(
            all_goo_details,
            goo_details_file_name_for_for_foil_cards,
        )

    return all_goo_details


def find_representative_listing_hash_for_app_id(
    app_id: str,
    groups_by_app_id: dict[str, list[str]],
    listing_candidates: list[str] | None = None,
    dictionary_of_representative_listing_hashes: dict[str, list[str]] | None = None,
) -> str:
    if listing_candidates is None:
        listing_candidates = find_representative_listing_hashes(
            groups_by_app_id,
            dictionary_of_representative_listing_hashes,
        )

    if dictionary_of_representative_listing_hashes is not None:
        try:
            # For retro-compatibility, we try to use representative for which we previously downloaded item name ids
            previously_used_listing_hashes_for_app_id = (
                dictionary_of_representative_listing_hashes[app_id]
            )
        except KeyError:
            previously_used_listing_hashes_for_app_id = None
    else:
        previously_used_listing_hashes_for_app_id = None

    listing_hashes_for_app_id = groups_by_app_id[app_id]
    representative_listing_hash_for_app_id_as_a_set = set(
        listing_hashes_for_app_id,
    ).intersection(listing_candidates)

    if (
        previously_used_listing_hashes_for_app_id is not None
        and len(previously_used_listing_hashes_for_app_id) > 0
    ):
        representative_listing_hash_for_app_id_as_a_set = (
            representative_listing_hash_for_app_id_as_a_set.intersection(
                previously_used_listing_hashes_for_app_id,
            )
        )

    # Sort with respect to lexicographical order.
    sorted_representative_listing_hash_for_app_id_as_list = sorted(
        representative_listing_hash_for_app_id_as_a_set,
    )

    return (
        next(iter(sorted_representative_listing_hash_for_app_id_as_list))
        if sorted_representative_listing_hash_for_app_id_as_list
        else ""
    )


def find_item_type_for_app_id(
    app_id: str,
    groups_by_app_id: dict[str, list[str]],
    listing_candidates: list[str],
    all_listing_details: dict[str, dict] | None = None,
    listing_details_output_file_name: str | None = None,
    dictionary_of_representative_listing_hashes: dict[str, list[str]] | None = None,
    verbose: bool = False,
) -> int | None:
    if listing_details_output_file_name is None:
        listing_details_output_file_name = (
            get_listing_details_output_file_name_for_foil_cards()
        )

    if all_listing_details is None:
        all_listing_details = load_all_listing_details(
            listing_details_output_file_name=listing_details_output_file_name,
        )

    representative_listing_hash_for_app_id = (
        find_representative_listing_hash_for_app_id(
            app_id,
            groups_by_app_id,
            listing_candidates,
            dictionary_of_representative_listing_hashes,
        )
    )

    try:
        listing_details = all_listing_details[representative_listing_hash_for_app_id]
    except KeyError:
        listing_details = {"item_type_no": None}
        if verbose:
            print(
                f"Unknown item type for listing hash = {representative_listing_hash_for_app_id}",
            )

    return listing_details["item_type_no"]


def download_goo_value_for_app_id(
    app_id: str,
    groups_by_app_id: dict[str, list[str]],
    listing_candidates: list[str],
    all_listing_details: dict[str, dict] | None = None,
    listing_details_output_file_name: str | None = None,
    dictionary_of_representative_listing_hashes: dict[str, list[str]] | None = None,
    verbose: bool = True,
) -> int | None:
    item_type = find_item_type_for_app_id(
        app_id,
        groups_by_app_id,
        listing_candidates,
        all_listing_details,
        listing_details_output_file_name,
        dictionary_of_representative_listing_hashes,
    )

    return query_goo_value(
        app_id=app_id,
        item_type=item_type,
        verbose=verbose,
    )


def build_dictionary_of_representative_listing_hashes(
    all_listing_details: dict[str, dict] | None = None,
    listing_details_output_file_name: str | None = None,
) -> dict[str, list[str]]:
    if listing_details_output_file_name is None:
        listing_details_output_file_name = (
            get_listing_details_output_file_name_for_foil_cards()
        )

    if all_listing_details is None:
        all_listing_details = load_all_listing_details(
            listing_details_output_file_name=listing_details_output_file_name,
        )

    dictionary_of_representative_listing_hashes: dict[str, list[str]] = {}

    for listing_hash in all_listing_details:
        app_id = convert_listing_hash_to_app_id(listing_hash)

        listing_details = all_listing_details[listing_hash]

        try:
            listing_details["item_type_no"]
        except KeyError:
            continue

        try:
            dictionary_of_representative_listing_hashes[app_id].append(listing_hash)
        except KeyError:
            dictionary_of_representative_listing_hashes[app_id] = [listing_hash]

    return dictionary_of_representative_listing_hashes
