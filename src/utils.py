from pathlib import Path

TIMEOUT_IN_SECONDS = 5


def get_cushioned_cooldown_in_seconds(num_minutes: int) -> int:
    num_seconds = num_minutes * 60
    cushion_in_seconds = 10

    return num_seconds + cushion_in_seconds


def get_data_folder() -> str:
    data_folder = "data/"
    Path(data_folder).mkdir(exist_ok=True)

    return data_folder


def get_badge_creation_file_name(from_javascript: bool = False) -> str:
    badge_creation_file_name = get_data_folder() + "booster_game_creator"

    if from_javascript:
        badge_creation_file_name += "_from_javascript"

    badge_creation_file_name += ".txt"

    return badge_creation_file_name


def get_steam_card_exchange_file_name() -> str:
    return get_data_folder() + "steam_card_exchange.json"


def get_listing_output_file_name_suffix(
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
) -> str:
    from src.market_search import get_tag_drop_rate_str

    if tag_drop_rate_str is None:
        tag_drop_rate_str = get_tag_drop_rate_str(rarity=rarity)

    if tag_drop_rate_str == get_tag_drop_rate_str(rarity="common"):
        suffix = ""
    else:
        suffix = f"_rarity_{tag_drop_rate_str}"

    return suffix


def get_listing_output_file_name_for_profile_backgrounds(
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
) -> str:
    suffix = get_listing_output_file_name_suffix(
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity,
    )

    return get_data_folder() + f"listings_for_profile_backgrounds{suffix}.json"


def get_listing_output_file_name_for_emoticons(
    tag_drop_rate_str: str | None = None,
    rarity: str | None = None,
) -> str:
    suffix = get_listing_output_file_name_suffix(
        tag_drop_rate_str=tag_drop_rate_str,
        rarity=rarity,
    )

    return get_data_folder() + f"listings_for_emoticons{suffix}.json"


def get_listing_output_file_name_for_foil_cards() -> str:
    return get_data_folder() + "listings_for_foil_cards.json"


def get_listing_output_file_name() -> str:
    return get_data_folder() + "listings.json"


def get_listing_details_output_file_name_for_profile_backgrounds() -> str:
    return get_data_folder() + "listing_details_for_profile_backgrounds.json"


def get_listing_details_output_file_name_for_emoticons() -> str:
    return get_data_folder() + "listing_details_for_emoticons.json"


def get_listing_details_output_file_name_for_foil_cards() -> str:
    return get_data_folder() + "listing_details_for_foil_cards.json"


def get_listing_details_output_file_name() -> str:
    return get_data_folder() + "listing_details.json"


def get_goo_details_file_nam_for_for_foil_cards() -> str:
    return get_data_folder() + "goo_details_for_foil_cards.json"


def get_sack_of_gems_listing_file_name() -> str:
    return get_data_folder() + "listing_sack_of_gems.json"


def get_market_order_file_name_for_profile_backgrounds() -> str:
    return get_data_folder() + "market_orders_for_profile_backgrounds.json"


def get_market_order_file_name_for_emoticons() -> str:
    return get_data_folder() + "market_orders_for_emoticons.json"


def get_market_order_file_name() -> str:
    return get_data_folder() + "market_orders.json"


def get_next_creation_time_file_name() -> str:
    return get_data_folder() + "next_creation_times.json"


def main() -> bool:
    for file_name in (
        get_badge_creation_file_name(from_javascript=False),
        get_badge_creation_file_name(from_javascript=True),
        get_listing_output_file_name(),
        get_sack_of_gems_listing_file_name(),
        get_market_order_file_name(),
        get_next_creation_time_file_name(),
        get_listing_details_output_file_name(),
    ):
        print(file_name)

    return True


def convert_listing_hash_to_app_id(listing_hash: str) -> str:
    return listing_hash.split("-")[0]


def get_listing_hash_suffixe() -> str:
    return " Booster Pack"


def convert_listing_hash_to_app_name(listing_hash: str) -> str:
    tokens = listing_hash.split("-")[1:]

    app_name = "-".join(tokens) if len(tokens) > 1 else tokens[0]

    return app_name[: -len(get_listing_hash_suffixe())]


def convert_to_listing_hash(
    app_id: str,
    app_name: str,
    listing_hash_suffixe: str | None = None,
) -> str:
    if listing_hash_suffixe is None:
        listing_hash_suffixe = get_listing_hash_suffixe()

    return f"{app_id}-{app_name}{listing_hash_suffixe}"


def get_steamcardexchange_url(app_id: str) -> str:
    # This page shows the number of cards, and provides links to the store page and the market pages.
    # NB: this allows to compute the crafting cost of a booster pack costs, as an amount of gems equal to 6000/num_cards
    return f"https://www.steamcardexchange.net/index.php?gamepage-appid-{app_id}"


def get_steam_store_url(app_id: str) -> str:
    return f"https://store.steampowered.com/app/{app_id}/"


def get_category_name_for_booster_packs() -> str:
    return "booster packs"


def get_category_name_for_profile_backgrounds() -> str:
    return "profile backgrounds"


def get_category_name_for_emoticons() -> str:
    return "emoticons"


def get_bullet_point_for_display(use_numbered_bullet_points: bool = False) -> str:
    # Return a string, which consists of a bullet point followed by three spaces, to display lists in Markdown format.
    #
    # NB: if the list of bullet points is long, Numbered bullet points improve readability on GitHub Gist.

    bullet_point_character = "1." if use_numbered_bullet_points else "*"

    three_spaces_indentation = "   "

    return f"{bullet_point_character}{three_spaces_indentation}"


if __name__ == "__main__":
    main()
