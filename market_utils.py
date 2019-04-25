# Objective: retrieve all the options to craft 'Booster Packs', available because I own the corresponding games.
#
# Caveat: this relies on a previous manual copy-paste of HTML code to data/booster_game_creator.txt

from market_search import load_all_listings
from utils import get_badge_creation_file_name, convert_listing_hash_to_app_id, convert_listing_hash_to_app_name


def get_badge_creation_details():
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


def main():
    badge_creation_details = get_badge_creation_details()

    badge_app_ids = list(badge_creation_details.keys())

    all_listings = load_all_listings()

    all_listing_hashes = list(all_listings.keys())

    listing_matches_with_app_ids = dict()
    listing_matches_with_app_names = dict()
    for listing_hash in all_listing_hashes:
        app_id = convert_listing_hash_to_app_id(listing_hash)
        app_name = convert_listing_hash_to_app_name(listing_hash)

        listing_matches_with_app_ids[app_id] = listing_hash
        listing_matches_with_app_names[app_name] = listing_hash

    badge_matches = dict()
    for app_id in badge_app_ids:
        app_name = badge_creation_details[app_id]['name']

        try:
            badge_matches[app_id] = listing_matches_with_app_ids[app_id]
        except KeyError:

            try:
                badge_matches[app_id] = listing_matches_with_app_names[app_name]
                print('Match for {} (appID = {}) with name instead of id.'.format(app_name, app_id))
            except KeyError:
                print('No match found for {} (appID = {})'.format(app_name, app_id))
                continue

    print('#badges = {} ; #matching hashes found = {}'.format(len(badge_app_ids), len(badge_matches)))

    return True


if __name__ == '__main__':
    main()

# TODO Once matches are fine, aggregate data: owned appID --> (gem PRICE, sell price). NB: ensure same currency.
# TODO Filter out games for which the sell price (ask) is lower than the gem price, because the bid is necessarily lower
# TODO Finally, beautifulsoup to get the bid for the remaining games, and rank them according to the highest bid.
