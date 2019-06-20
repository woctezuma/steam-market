# Objective: find free games which feature Steam trading cards, and thus allow their owners to craft "Booster Packs".

import requests
import steamspypi

from market_search import load_all_listings
from personal_info import get_steam_cookie, get_cookie_dict
from utils import convert_listing_hash_to_app_id


def get_user_data_url():
    user_data_url = 'https://store.steampowered.com/dynamicstore/userdata/'

    return user_data_url


def download_user_data():
    cookie_value = get_steam_cookie()

    resp_data = requests.get(get_user_data_url(),
                             cookies=get_cookie_dict(cookie_value))

    if resp_data.status_code == 200:
        result = resp_data.json()
    else:
        result = None

    return result


def download_owned_apps(verbose=True):
    result = download_user_data()

    owned_apps = result['rgOwnedApps']

    if verbose:
        print('Owned apps: {}'.format(len(owned_apps)))

    return owned_apps


def download_free_apps(method=None, verbose=True):
    if method is None:
        data = steamspypi.load()

        free_apps = [int(game['appid']) for game in data.values()
                     if game['initialprice'] is not None  # I don't know what to do in the rare case that price is None.
                     and int(game['initialprice']) == 0]

    else:
        data_request = dict()

        if method == 'genre':
            data_request['request'] = 'genre'
            data_request['genre'] = 'Free to Play'
        else:
            data_request['request'] = 'tag'
            data_request['tag'] = 'Free to Play'

        data = steamspypi.download(data_request)

        free_apps = [int(app_id) for app_id in data.keys()]

    if verbose:
        print('Free apps: {}'.format(len(free_apps)))

    return free_apps


def load_apps_with_trading_cards(verbose=True):
    all_listings = load_all_listings()

    apps_with_trading_cards = [convert_listing_hash_to_app_id(listing_hash) for listing_hash in all_listings]

    if verbose:
        print('Apps with trading cards: {}'.format(len(apps_with_trading_cards)))

    return apps_with_trading_cards


def load_free_apps_with_trading_cards(method=None, verbose=True):
    free_apps = download_free_apps(method=method)

    apps_with_trading_cards = load_apps_with_trading_cards()

    free_apps_with_trading_cards = set(free_apps).intersection(apps_with_trading_cards)

    if verbose:
        print('Free apps with trading cards: {}'.format(len(free_apps_with_trading_cards)))

    return free_apps_with_trading_cards


def load_file(file_name, verbose=True):
    with open(file_name, 'r') as f:
        data = [int(line.strip()) for line in f.readlines()]

    if verbose:
        print('Loaded apps: {}'.format(len(data)))

    return data


def write_to_file(data, file_name, verbose=True):
    output = '\n'.join(str(app_id) for app_id in data)

    with open(file_name, 'w') as f:
        print(output, file=f)

    if verbose:
        print('Written apps: {}'.format(len(data)))

    return


def main():
    method = None  # Choose a value among these three options: None, 'genre', 'tag'
    free_apps_with_trading_cards = load_free_apps_with_trading_cards(method=method)

    owned_apps = download_owned_apps()

    free_apps_not_owned = set(free_apps_with_trading_cards).difference(owned_apps)

    write_to_file(sorted(free_apps_not_owned), 'output.txt')


if __name__ == '__main__':
    main()
