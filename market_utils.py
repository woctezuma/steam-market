from market_search import load_all_listings
from utils import get_badge_creation_file_name


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

    listing_hashes = list(filter(lambda s: int(s.split('-')[0]) in badge_app_ids, all_listings.keys()))

    print('#badges = {} ; #matching hashes found = {}'.format(len(badge_app_ids), len(listing_hashes)))

    return True


if __name__ == '__main__':
    main()
