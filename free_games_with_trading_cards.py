# Objective: find free games which feature Steam trading cards, and thus allow their owners to craft "Booster Packs".
import collections.abc

import requests
import steamspypi

from market_search import load_all_listings
from personal_info import (
    get_cookie_dict,
    update_and_save_cookie_to_disk_if_values_changed,
)
from utils import convert_listing_hash_to_app_id


def get_user_data_url() -> str:
    user_data_url = 'https://store.steampowered.com/dynamicstore/userdata/'

    return user_data_url


def download_user_data() -> [dict | None]:
    cookie = get_cookie_dict()

    resp_data = requests.get(
        get_user_data_url(),
        cookies=cookie,
    )

    if resp_data.status_code == 200:
        result = resp_data.json()

        jar = dict(resp_data.cookies)
        cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)
    else:
        result = None

    return result


def download_owned_apps(verbose: bool = True) -> list[int]:
    result = download_user_data()

    owned_apps = result['rgOwnedApps']

    if verbose:
        print(f'Owned apps: {len(owned_apps)}')

    return owned_apps


def download_free_apps(method: str = 'price', verbose: bool = True) -> list[int]:
    if method == 'price':
        data = steamspypi.load()

        free_apps = [
            int(game['appid']) for game in data.values()
            if game['initialprice'] is not None  # I don't know what to do in the rare case that price is None.
            and int(game['initialprice']) == 0
        ]

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
        print(f'Free apps (based on {method}): {len(free_apps)}')

    return free_apps


def load_apps_with_trading_cards(verbose: bool = True) -> list[int]:
    all_listings = load_all_listings()

    apps_with_trading_cards = [convert_listing_hash_to_app_id(listing_hash) for listing_hash in all_listings]

    if verbose:
        print(f'Apps with trading cards: {len(apps_with_trading_cards)}')

    return apps_with_trading_cards


def load_free_apps_with_trading_cards(
    free_apps: set[int] = None, list_of_methods: list[str] = None,
    verbose: bool = True,
) -> set[int]:
    if list_of_methods is None:
        list_of_methods = ['price', 'genre', 'tag']

    if free_apps is None:
        free_apps = set()

    for method in list_of_methods:
        new_free_apps = download_free_apps(method=method)

        free_apps.update(new_free_apps)

    if verbose:
        print(f'Free apps: {len(free_apps)}')

    apps_with_trading_cards = load_apps_with_trading_cards()

    free_apps_with_trading_cards = set(free_apps).intersection(apps_with_trading_cards)

    if verbose:
        print(f'Free apps with trading cards: {len(free_apps_with_trading_cards)}')

    return free_apps_with_trading_cards


def load_file(file_name: str, verbose: bool = True) -> list[int]:
    with open(file_name, encoding='utf-8') as f:
        data = [int(line.strip()) for line in f.readlines()]

    if verbose:
        print(f'Loaded apps: {len(data)}')

    return data


def format_for_asf_command_line(
    app_ids: set[int],
    app_prefix: str = None,
) -> list[str]:
    if app_prefix is None:
        # Reference: https://github.com/JustArchiNET/ArchiSteamFarm/wiki/Commands#addlicense-licenses
        app_prefix = 'a/'

    output = [app_prefix + str(app_id) for app_id in sorted(app_ids)]

    return output


def chunks(l: list, n: int) -> collections.abc.Iterator[list]:
    """Yield successive n-sized chunks from l."""
    # Reference: https://stackoverflow.com/a/312464
    for i in range(0, len(l), n):
        yield l[i : i + n]


def group_concatenate_to_str(
    data: list,
    asf_username: str = 'ASF',
    group_size: int = 25,
) -> str:
    asf_command = 'addlicense'
    asf_complete_command = f'{asf_command} {asf_username} '

    prepend_asf_command = bool(asf_username is not None) and bool(len(data) > 0)

    line_sep = '\n'
    space_sep = ' '

    group_sep = line_sep
    if prepend_asf_command:
        group_sep += asf_complete_command

    inner_sep = space_sep

    output = group_sep.join([
        inner_sep.join([
            str(app_id) for app_id in group
        ])
        for group in chunks(data, group_size)
    ])

    if prepend_asf_command:
        # Prepend the ASF command to the first line (missed by .join() calls)
        output = asf_complete_command + output

    return output


def write_to_file(
    data: list[str],
    file_name: str,
    asf_username: str = None,
    group_size: int = 25,
    verbose: bool = True,
) -> None:
    output = group_concatenate_to_str(
        data,
        asf_username=asf_username,
        group_size=group_size,
    )

    with open(file_name, 'w', encoding='utf-8') as f:
        print(output, file=f)

    if verbose:
        print(f'Written apps: {len(data)}')


def main() -> None:
    # Based on SteamDB: https://steamdb.info/search/?a=app_keynames&keyname=243&operator=1
    free_apps = load_file('data/free_apps.txt')

    # Based on SteamSpy:
    free_apps_with_trading_cards = load_free_apps_with_trading_cards(
        free_apps=set(free_apps),
        list_of_methods=None,
    )

    owned_apps = download_owned_apps()

    free_apps_not_owned = set(free_apps_with_trading_cards).difference(owned_apps)

    output = format_for_asf_command_line(free_apps_not_owned)

    write_to_file(output, 'output.txt', asf_username='Wok')


if __name__ == '__main__':
    main()
