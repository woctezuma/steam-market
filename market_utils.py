# Objective: parse all the options to craft 'Booster Packs', available because I own the corresponding games.
#
# Caveat: this relies on a previous manual copy-paste of HTML code to data/booster_game_creator.txt

from market_search import load_all_listings, update_all_listings
from sack_of_gems import get_gem_price
from utils import get_badge_creation_file_name, convert_listing_hash_to_app_id, convert_listing_hash_to_app_name


def parse_badge_creation_details():
    with open(get_badge_creation_file_name(), 'r') as f:
        lines = [l.strip() for l in f.readlines() if l[0] != '#']

    badge_creation_details = dict()

    for l in lines:
        s = l.split()
        # e.g. ['<option', 'value="614910"', 'class="available">#monstercakes', '-', '1200', ',', 'Gems</option>']

        # Hard-coded parsing
        app_id = int(s[1].split('=')[1].strip('"'))
        app_name = s[2].split('available">')[1] + ' '
        app_name += ' '.join(s[3:-4])
        app_name = app_name.strip()
        gem_value = int(s[-3])

        badge_creation_details[app_id] = dict()
        badge_creation_details[app_id]['name'] = app_name
        badge_creation_details[app_id]['gem_value'] = gem_value

    return badge_creation_details


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


if __name__ == '__main__':
    aggregated_badge_data = load_aggregated_badge_data()
