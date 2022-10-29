# Objective: automatically download the number of cards per set from SteamCardExchange.net

import json
import time

import requests

from utils import get_steam_card_exchange_file_name


def get_current_unix_time_in_ms() -> int:
    # Reference: https://stackoverflow.com/a/56394660

    current_unix_time_in_ms = time.time_ns() // 1000000

    return current_unix_time_in_ms


def get_steamcardexchange_api_end_point_url() -> str:
    steamcardexchange_api_end_point_url = 'https://www.steamcardexchange.net/api/request.php'

    return steamcardexchange_api_end_point_url


def get_steamcardexchange_api_params() -> dict[str, str]:
    current_unix_time_in_ms = get_current_unix_time_in_ms()

    steamcardexchange_api_params = {
        'GetBoosterPrices': '',
        '_': str(current_unix_time_in_ms),
    }

    return steamcardexchange_api_params


def save_data_from_steam_card_exchange(response: dict,
                                       steam_card_exchange_file_name: str = None) -> None:
    if steam_card_exchange_file_name is None:
        steam_card_exchange_file_name = get_steam_card_exchange_file_name()

    if response is not None:
        with open(steam_card_exchange_file_name, 'w', encoding='utf-8') as f:
            json.dump(response, f)

    return


def download_data_from_steam_card_exchange(steam_card_exchange_file_name: str = None,
                                           save_to_disk: bool = True) -> [dict | None]:
    if steam_card_exchange_file_name is None:
        steam_card_exchange_file_name = get_steam_card_exchange_file_name()

    print('Downloading data from scratch.')

    url = get_steamcardexchange_api_end_point_url()
    req_data = get_steamcardexchange_api_params()

    resp_data = requests.get(url=url, params=req_data)

    status_code = resp_data.status_code

    if status_code == 200:
        response = resp_data.json()
    else:
        print(f'Data could not be downloaded from SteamCardExchange. Status code {status_code} was returned.')
        response = None

    if save_to_disk and bool(response is not None):
        save_data_from_steam_card_exchange(response,
                                           steam_card_exchange_file_name=steam_card_exchange_file_name)

    return response


def load_data_from_steam_card_exchange(steam_card_exchange_file_name: str = None) -> [dict | None]:
    if steam_card_exchange_file_name is None:
        steam_card_exchange_file_name = get_steam_card_exchange_file_name()

    try:
        print('Loading data from disk.')
        with open(steam_card_exchange_file_name, 'r', encoding='utf-8') as f:
            response = json.load(f)
    except FileNotFoundError:
        print('Data could not be found on the disk.')
        response = download_data_from_steam_card_exchange(steam_card_exchange_file_name=steam_card_exchange_file_name,
                                                          save_to_disk=True)

    return response


def compute_gem_amount_required_to_craft_booster_pack(num_cards_per_set: int) -> float:
    gem_amount_required_to_craft_booster_pack = 6000 / num_cards_per_set

    return gem_amount_required_to_craft_booster_pack


def parse_data_from_steam_card_exchange(response: dict = None,
                                        force_update_from_steam_card_exchange: bool = False,
                                        steam_card_exchange_file_name: str = None) -> dict[int, dict]:
    if steam_card_exchange_file_name is None:
        steam_card_exchange_file_name = get_steam_card_exchange_file_name()

    if response is None:
        if force_update_from_steam_card_exchange:
            response = download_data_from_steam_card_exchange(steam_card_exchange_file_name)
        else:
            response = load_data_from_steam_card_exchange(steam_card_exchange_file_name)

    # Build dict: app_id -> num_cards_per_set

    dico = dict()

    for app_info in response['data']:
        app_id = int(app_info[0][0])
        app_name = app_info[0][1]
        num_cards_per_set = int(app_info[1])

        if num_cards_per_set == 0:
            print(f'No card found for {app_name} (appID = {app_id})')
            continue

        dico[app_id] = dict()
        dico[app_id]['app_id'] = app_id
        dico[app_id]['name'] = app_name
        dico[app_id]['num_cards_per_set'] = num_cards_per_set
        dico[app_id]['gem_amount'] = compute_gem_amount_required_to_craft_booster_pack(num_cards_per_set)

    print(f'{len(dico)} games found in the database.')

    return dico


def main(force_update: bool = False) -> bool:
    if force_update:
        response = download_data_from_steam_card_exchange()
    else:
        response = load_data_from_steam_card_exchange()

    dico = parse_data_from_steam_card_exchange(response)

    return True


if __name__ == '__main__':
    main(force_update=False)
