# Objective: retrieve the price which sellers ask for a 'Sack of Gems'.

from http import HTTPStatus

from src.json_utils import load_json, save_json
from src.market_listing import get_listing_details
from src.market_order import download_market_order_data
from src.personal_info import get_cookie_dict
from src.utils import get_sack_of_gems_listing_file_name


def get_listing_hash_for_gems() -> str:
    return "753-Sack of Gems"


def get_num_gems_per_sack_of_gems() -> int:
    return 1000


def download_sack_of_gems_price(
    sack_of_gems_listing_file_name: str | None = None,
    verbose: bool = True,
) -> float:
    if sack_of_gems_listing_file_name is None:
        sack_of_gems_listing_file_name = get_sack_of_gems_listing_file_name()

    cookie = get_cookie_dict()
    listing_hash = get_listing_hash_for_gems()

    listing_details, status_code = get_listing_details(
        listing_hash=listing_hash,
        cookie=cookie,
    )

    if status_code == HTTPStatus.OK:
        item_nameid = listing_details[listing_hash]["item_nameid"]

        bid_price, ask_price, bid_volume, ask_volume = download_market_order_data(
            listing_hash,
            item_nameid,
            verbose,
        )
        listing_details[listing_hash]["bid"] = bid_price
        listing_details[listing_hash]["ask"] = ask_price
        listing_details[listing_hash]["bid_volume"] = bid_volume
        listing_details[listing_hash]["ask_volume"] = ask_volume

        sack_of_gems_price = ask_price

        save_json(listing_details, sack_of_gems_listing_file_name)
    else:
        raise AssertionError

    return sack_of_gems_price


def load_sack_of_gems_price(
    retrieve_gem_price_from_scratch: bool = False,
    verbose: bool = True,
    sack_of_gems_listing_file_name: str | None = None,
) -> float:
    if sack_of_gems_listing_file_name is None:
        sack_of_gems_listing_file_name = get_sack_of_gems_listing_file_name()

    if retrieve_gem_price_from_scratch:
        sack_of_gems_price = download_sack_of_gems_price(sack_of_gems_listing_file_name)
    else:
        try:
            listing_details = load_json(sack_of_gems_listing_file_name)

            listing_hash = get_listing_hash_for_gems()

            sack_of_gems_price = listing_details[listing_hash]["ask"]
        except FileNotFoundError:
            sack_of_gems_price = download_sack_of_gems_price(
                sack_of_gems_listing_file_name,
            )

    if verbose:
        print(
            f"A sack of {get_num_gems_per_sack_of_gems()} gems can be bought for {sack_of_gems_price:.2f} €.",
        )

    return sack_of_gems_price


def get_gem_price(
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
    retrieve_gem_price_from_scratch: bool = False,
    verbose: bool = True,
) -> float:
    if enforced_sack_of_gems_price is None:
        sack_of_gems_price = load_sack_of_gems_price(
            retrieve_gem_price_from_scratch,
            verbose=verbose,
        )
    else:
        sack_of_gems_price = enforced_sack_of_gems_price
        print(
            "[manual input] A sack of {} gems can allegedly be bought for {:.2f} €.".format(
                get_num_gems_per_sack_of_gems(),
                sack_of_gems_price,
            ),
        )

    if minimum_allowed_sack_of_gems_price is not None:
        sack_of_gems_price = max(minimum_allowed_sack_of_gems_price, sack_of_gems_price)
        print(
            "[manual adjustment] The price of a sack of gems is set to {:.2f} € (minimum allowed: {:.2f} €).".format(
                sack_of_gems_price,
                minimum_allowed_sack_of_gems_price,
            ),
        )

    num_gems_per_sack_of_gems = get_num_gems_per_sack_of_gems()

    return sack_of_gems_price / num_gems_per_sack_of_gems


def print_gem_price_reminder(
    enforced_sack_of_gems_price: float | None = None,
    minimum_allowed_sack_of_gems_price: float | None = None,
    retrieve_gem_price_from_scratch: bool | None = None,
) -> None:
    if retrieve_gem_price_from_scratch is None:
        retrieve_gem_price_from_scratch = bool(enforced_sack_of_gems_price is None)

    get_gem_price(
        enforced_sack_of_gems_price=enforced_sack_of_gems_price,
        minimum_allowed_sack_of_gems_price=minimum_allowed_sack_of_gems_price,
        retrieve_gem_price_from_scratch=retrieve_gem_price_from_scratch,
    )


def get_gem_amount_required_to_craft_badge() -> int:
    # This is a constant value of 2000 gems for a badge, because a badge requires a set of N cards, which are obtained
    # after opening N/3 booster packs, and a booster pack costs 6000/N gems.

    return 2000


def main() -> bool:
    print("Loaded from the disk:")
    load_sack_of_gems_price(
        retrieve_gem_price_from_scratch=False,
        verbose=True,
    )
    print("\nDownloaded as a market listing:")
    load_sack_of_gems_price(
        retrieve_gem_price_from_scratch=True,
        verbose=True,
    )

    return True


if __name__ == "__main__":
    main()
