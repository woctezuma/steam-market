# Objective: match listing hashes with badge creation details.

import random

from market_listing import get_item_nameid_batch
from market_search import load_all_listings, update_all_listings
from parsing_utils import parse_badge_creation_details
from sack_of_gems import get_gem_price
from utils import convert_listing_hash_to_app_id, convert_listing_hash_to_app_name


def match_badges_with_listing_hashes(badge_creation_details=None,
                                     all_listings=None,
                                     verbose=True):
    # Badges for games which I own

    if badge_creation_details is None:
        badge_creation_details = parse_badge_creation_details()

    badge_app_ids = list(badge_creation_details.keys())

    # Listings for ALL the existing Booster Packs

    if all_listings is None:
        all_listings = load_all_listings()

    all_listing_hashes = list(all_listings.keys())

    # Dictionaries to match appIDs or app names with listing hashes

    listing_matches_with_app_ids = dict()
    listing_matches_with_app_names = dict()
    for listing_hash in all_listing_hashes:
        app_id = convert_listing_hash_to_app_id(listing_hash)
        app_name = convert_listing_hash_to_app_name(listing_hash)

        listing_matches_with_app_ids[app_id] = listing_hash
        listing_matches_with_app_names[app_name] = listing_hash

    # Match badges with listing hashes

    badge_matches = dict()
    for app_id in badge_app_ids:
        app_name = badge_creation_details[app_id]['name']

        try:
            badge_matches[app_id] = listing_matches_with_app_ids[app_id]
        except KeyError:

            try:
                badge_matches[app_id] = listing_matches_with_app_names[app_name]
                if verbose:
                    print('Match for {} (appID = {}) with name instead of id.'.format(app_name, app_id))
            except KeyError:
                badge_matches[app_id] = None
                if verbose:
                    print('No match found for {} (appID = {})'.format(app_name, app_id))

    if verbose:
        print('#badges = {} ; #matching hashes found = {}'.format(len(badge_app_ids), len(badge_matches)))

    return badge_matches


def aggregate_badge_data(badge_creation_details,
                         badge_matches,
                         all_listings=None,
                         retrieve_gem_price_from_scratch=False):
    # Aggregate data:
    #       owned appID --> (gem PRICE, sell price)
    # where:
    # - the gem price is the price required to buy gems on the market to then craft a booster pack for this game,
    # - the sell price is the price which sellers are asking for this booster pack.
    #
    # NB: ensure the same currency is used.

    if all_listings is None:
        all_listings = load_all_listings()

    gem_price = get_gem_price(retrieve_gem_price_from_scratch)

    badge_app_ids = list(badge_creation_details.keys())

    aggregated_badge_data = dict()

    for app_id in badge_app_ids:
        app_name = badge_creation_details[app_id]['name']
        gem_amount_required_to_craft_booster_pack = badge_creation_details[app_id]['gem_value']
        listing_hash = badge_matches[app_id]

        if listing_hash is None:
            # For some reason for Conran - The dinky Raccoon (appID = 612150), there is no listing of any "Booster Pack"
            # Reference: https://steamcommunity.com/market/search?appid=753&category_753_Game%5B0%5D=tag_app_612150
            continue
        else:
            sell_price_in_cents = all_listings[listing_hash]['sell_price']
            sell_price_in_euros = sell_price_in_cents / 100

        aggregated_badge_data[app_id] = dict()
        aggregated_badge_data[app_id]['name'] = app_name
        aggregated_badge_data[app_id]['listing_hash'] = listing_hash
        aggregated_badge_data[app_id]['gem_amount'] = gem_amount_required_to_craft_booster_pack
        aggregated_badge_data[app_id]['gem_price'] = gem_amount_required_to_craft_booster_pack * gem_price
        aggregated_badge_data[app_id]['sell_price'] = sell_price_in_euros

    return aggregated_badge_data


def load_aggregated_badge_data(retrieve_listings_from_scratch=False):
    badge_creation_details = parse_badge_creation_details()

    if retrieve_listings_from_scratch:
        update_all_listings()

    all_listings = load_all_listings()

    badge_matches = match_badges_with_listing_hashes(badge_creation_details,
                                                     all_listings)

    aggregated_badge_data = aggregate_badge_data(badge_creation_details,
                                                 badge_matches,
                                                 all_listings,
                                                 retrieve_listings_from_scratch)

    return aggregated_badge_data


def populate_random_samples_of_badge_data(badge_data=None, num_samples=50):
    if badge_data is None:
        badge_data = load_aggregated_badge_data()

    listing_hashes = [badge_data[app_id]['listing_hash'] for app_id in badge_data.keys()]

    num_samples = min(num_samples, len(listing_hashes))

    listing_hash_samples = [listing_hashes[i]
                            for i in random.sample(range(len(listing_hashes)), k=num_samples)]

    item_nameids = get_item_nameid_batch(listing_hash_samples)

    return True


if __name__ == '__main__':
    aggregated_badge_data = load_aggregated_badge_data()
    populate_random_samples_of_badge_data(aggregated_badge_data, num_samples=50)
