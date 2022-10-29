import json

import requests

from creation_time_utils import (
    get_crafting_cooldown_duration_in_days,
    get_formatted_current_time,
    load_next_creation_time_data,
)
from personal_info import (
    get_cookie_dict,
    update_and_save_cookie_to_disk_if_values_changed,
)
from utils import (
    convert_listing_hash_to_app_id,
    convert_listing_hash_to_app_name,
    get_data_folder,
    get_next_creation_time_file_name,
)


def get_my_steam_profile_id() -> str:
    my_profile_id = '76561198028705366'

    return my_profile_id


def get_steam_inventory_url(profile_id: str = None, app_id: int = 753, context_id: int = 6) -> str:
    if profile_id is None:
        profile_id = get_my_steam_profile_id()

    # References:
    # https://github.com/Alex7Kom/node-steam-tradeoffers/issues/114
    # https://dev.doctormckay.com/topic/332-identifying-steam-items/
    steam_inventory_url = 'https://steamcommunity.com/profiles/' + str(profile_id) + '/inventory/json/'
    steam_inventory_url += str(app_id) + '/' + str(context_id) + '/'

    return steam_inventory_url


def get_steam_inventory_file_name(profile_id: str) -> str:
    steam_inventory_file_name = get_data_folder() + 'inventory_' + str(profile_id) + '.json'

    return steam_inventory_file_name


def load_steam_inventory_from_disk(profile_id: str = None) -> [dict | None]:
    if profile_id is None:
        profile_id = get_my_steam_profile_id()

    try:
        with open(get_steam_inventory_file_name(profile_id), encoding='utf-8') as f:
            steam_inventory = json.load(f)
    except FileNotFoundError:
        steam_inventory = download_steam_inventory(profile_id, save_to_disk=True)

    return steam_inventory


def load_steam_inventory(profile_id: str = None, update_steam_inventory: bool = False) -> [dict | None]:
    if profile_id is None:
        profile_id = get_my_steam_profile_id()

    if update_steam_inventory:
        steam_inventory = download_steam_inventory(profile_id, save_to_disk=True)
    else:
        steam_inventory = load_steam_inventory_from_disk(profile_id=profile_id)

    return steam_inventory


def download_steam_inventory(profile_id: str = None, save_to_disk: bool = True) -> [dict | None]:
    if profile_id is None:
        profile_id = get_my_steam_profile_id()

    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    url = get_steam_inventory_url(profile_id=profile_id)

    if has_secured_cookie:
        resp_data = requests.get(url,
                                 cookies=cookie)
    else:
        resp_data = requests.get(url)

    status_code = resp_data.status_code

    if status_code == 200:
        steam_inventory = resp_data.json()

        if has_secured_cookie:
            jar = dict(resp_data.cookies)
            cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

        if save_to_disk:
            with open(get_steam_inventory_file_name(profile_id), 'w', encoding='utf-8') as f:
                json.dump(steam_inventory, f)
    else:
        print(f'Inventory for profile {profile_id} could not be loaded. Status code {status_code} was returned.')
        steam_inventory = None

    return steam_inventory


def get_session_id(cookie: dict[str, str] = None) -> str:
    if cookie is None:
        cookie = get_cookie_dict()

    session_id = cookie['sessionid']

    return session_id


def get_steam_booster_pack_creation_url() -> str:
    booster_pack_creation_url = 'https://steamcommunity.com/tradingcards/ajaxcreatebooster/'

    return booster_pack_creation_url


def get_booster_pack_creation_parameters(app_id: int,
                                         session_id: str,
                                         is_marketable: bool = True) -> dict[str, str]:
    booster_pack_creation_parameters = dict()

    if is_marketable:
        tradability_preference = 1
    else:
        tradability_preference = 3

    booster_pack_creation_parameters['sessionid'] = str(session_id)
    booster_pack_creation_parameters['appid'] = str(app_id)
    booster_pack_creation_parameters['series'] = '1'
    booster_pack_creation_parameters['tradability_preference'] = str(tradability_preference)

    return booster_pack_creation_parameters


def create_booster_pack(app_id: int,
                        is_marketable: bool = True,
                        verbose: bool = True) -> [dict | None]:
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    if not has_secured_cookie:
        raise AssertionError()

    session_id = get_session_id(cookie=cookie)

    url = get_steam_booster_pack_creation_url()
    req_data = get_booster_pack_creation_parameters(app_id=app_id,
                                                    session_id=session_id,
                                                    is_marketable=is_marketable)

    resp_data = requests.post(url,
                              data=req_data,
                              cookies=cookie)

    status_code = resp_data.status_code

    if status_code == 200:
        # Expected result:
        # {"purchase_result":{"communityitemid":"XXX","appid":685400,"item_type":36, "purchaseid":"XXX",
        # "success":1,"rwgrsn":-2}, "goo_amount":"22793","tradable_goo_amount":"22793","untradable_goo_amount":0}
        print(f'\n[appID = {app_id}] Booster pack successfully created.')
        result = resp_data.json()

        jar = dict(resp_data.cookies)
        cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)
    else:
        # NB: 401 means "Unauthorized", which must have something to do with wrong/outdated credentials in the cookie.
        if status_code == 500:
            print(
                f'\n[appID = {app_id}] Booster pack not created, because a pack was created less than 24h ago.')
        else:
            print(f'\n[appID = {app_id}] Booster pack not created, because of status code {status_code}.')
        result = None

    if verbose:
        print(result)

    return result


def get_steam_market_sell_url() -> str:
    steam_market_sell_url = 'https://steamcommunity.com/market/sellitem/'

    return steam_market_sell_url


def get_market_sell_parameters(asset_id: str,
                               price_in_cents: float,  # this is the money which you, as the seller, will receive
                               session_id: str) -> dict[str, str]:
    market_sell_parameters = dict()

    market_sell_parameters['sessionid'] = str(session_id)
    market_sell_parameters['appid'] = '753'
    market_sell_parameters['contextid'] = '6'
    market_sell_parameters['assetid'] = str(asset_id)  # To automatically determine asset ID, use retrieve_asset_id().
    market_sell_parameters['amount'] = '1'
    market_sell_parameters['price'] = str(price_in_cents)

    return market_sell_parameters


def get_request_headers() -> dict[str, str]:
    # Reference: https://dev.doctormckay.com/topic/287-automatic-market-seller/

    request_headers = {
        'Origin': 'https://steamcommunity.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://steamcommunity.com/my/inventory/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3'
    }

    return request_headers


def sell_booster_pack(asset_id: str,
                      price_in_cents: float,  # this is the money which you, as the seller, will receive
                      verbose: bool = True) -> [dict | None]:
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    if not has_secured_cookie:
        raise AssertionError()

    session_id = get_session_id(cookie=cookie)

    # Format the price (in cents) as an integer before sending a request to Steam API
    # Otherwise, a price like 18.0 would still work, but a price like 14.000000000000002 would return status code 400.
    price_in_cents = round(price_in_cents)

    url = get_steam_market_sell_url()
    req_data = get_market_sell_parameters(asset_id=asset_id,
                                          price_in_cents=price_in_cents,
                                          session_id=session_id)

    resp_data = requests.post(url,
                              headers=get_request_headers(),
                              data=req_data,
                              cookies=cookie)

    status_code = resp_data.status_code

    if status_code == 200:
        # Expected result:
        # {"success":true,"requires_confirmation":0}
        result = resp_data.json()

        jar = dict(resp_data.cookies)
        cookie = update_and_save_cookie_to_disk_if_values_changed(cookie, jar)

        if result['success']:
            print(f'Booster pack {asset_id} successfully sold for {price_in_cents} cents.')
        else:
            print(f'Booster pack {asset_id} not sold for {price_in_cents} cents, despite OK status code.')
    else:
        # NB: 400 means "Bad Request".
        print(f'Booster pack {asset_id} not sold for {price_in_cents} cents. Status code {status_code} was returned.')
        result = None

    if verbose:
        print(result)

    return result


def retrieve_asset_id(listing_hash: str,
                      steam_inventory: dict = None,
                      focus_on_marketable_items: bool = True,
                      verbose: bool = True) -> str:
    if steam_inventory is None:
        steam_inventory = load_steam_inventory()

    descriptions = steam_inventory['rgDescriptions']

    matched_element = dict()

    for element in descriptions:
        if descriptions[element]['market_hash_name'] == listing_hash:
            matched_element['market_hash_name'] = descriptions[element]['market_hash_name']
            matched_element['appid'] = descriptions[element]['appid']
            matched_element['classid'] = descriptions[element]['classid']
            matched_element['instanceid'] = descriptions[element]['instanceid']
            matched_element['type'] = descriptions[element]['type']
            matched_element['marketable'] = descriptions[element]['marketable']

            is_marketable_as_int = matched_element['marketable']
            is_marketable = bool(is_marketable_as_int != 0)

            if is_marketable or (not focus_on_marketable_items):
                if verbose:
                    print('\nItem found without requiring to go through the entire inventory.')
                break

    has_been_matched = bool(len(matched_element) > 0)

    if has_been_matched:

        community_inventory = steam_inventory['rgInventory']

        for element in community_inventory:
            if community_inventory[element]['classid'] == matched_element['classid'] \
                    and community_inventory[element]['instanceid'] == matched_element['instanceid']:
                matched_element['id'] = community_inventory[element]['id']
                matched_element['amount'] = community_inventory[element]['amount']
                matched_element['pos'] = community_inventory[element]['pos']
                break

        print(f'\nItem matched in the inventory for {listing_hash}.')
    else:
        print(f'\nNo matched item in the inventory for {listing_hash}.')

    if verbose:
        print(matched_element)

    try:
        asset_id = matched_element['id']
    except KeyError:
        asset_id = None

    return asset_id


def create_booster_packs_for_batch(listing_hashes: list[str]) -> dict[str, dict | None]:
    results = dict()

    for listing_hash in listing_hashes:
        app_id = convert_listing_hash_to_app_id(listing_hash)
        result = create_booster_pack(app_id=app_id)

        results[listing_hash] = result

    return results


def sell_booster_packs_for_batch(price_dict_for_listing_hashes: dict[str, float],
                                 update_steam_inventory: bool = True,
                                 focus_on_marketable_items: bool = True) -> dict[str, dict | None]:
    results = dict()

    steam_inventory = load_steam_inventory(update_steam_inventory=update_steam_inventory)

    for (listing_hash, price_in_cents) in price_dict_for_listing_hashes.items():

        asset_id = retrieve_asset_id(listing_hash=listing_hash,
                                     steam_inventory=steam_inventory,
                                     focus_on_marketable_items=focus_on_marketable_items)

        if asset_id is not None:
            result = sell_booster_pack(asset_id=asset_id, price_in_cents=price_in_cents)

            results[listing_hash] = result

    return results


def create_then_sell_booster_packs_for_batch(price_dict_for_listing_hashes: dict,
                                             update_steam_inventory: bool = True,
                                             focus_on_marketable_items: bool = True) -> tuple[
        dict[str, dict | None], dict[str, dict | None]]:
    listing_hashes = list(price_dict_for_listing_hashes.keys())

    creation_results = create_booster_packs_for_batch(listing_hashes)

    sale_results = sell_booster_packs_for_batch(price_dict_for_listing_hashes,
                                                update_steam_inventory=update_steam_inventory,
                                                focus_on_marketable_items=focus_on_marketable_items)

    next_creation_times = update_and_save_next_creation_times(creation_results)

    return creation_results, sale_results


def update_and_save_next_creation_times(creation_results: dict[str, dict | None],
                                        verbose: bool = True,
                                        next_creation_time_file_name: str = None) -> dict[int, str]:
    if next_creation_time_file_name is None:
        next_creation_time_file_name = get_next_creation_time_file_name()

    next_creation_times = load_next_creation_time_data(next_creation_time_file_name)

    delay_in_days = get_crafting_cooldown_duration_in_days()
    formatted_next_creation_time = get_formatted_current_time(delay_in_days=delay_in_days)

    save_to_disk = False
    is_first_displayed_line = True

    for listing_hash in creation_results:
        result = creation_results[listing_hash]

        if result is not None:
            app_id = convert_listing_hash_to_app_id(listing_hash)
            next_creation_times[app_id] = formatted_next_creation_time

            save_to_disk = True

            if verbose:

                # Print an empty line the first time, to clearly separate the block from what was previously displayed.
                if is_first_displayed_line:
                    print('')
                    is_first_displayed_line = False

                app_name = convert_listing_hash_to_app_name(listing_hash)
                print(f'Saving the next creation time ({formatted_next_creation_time}) for {app_name} (appID = {app_id}) to disk.')

    if save_to_disk:
        with open(next_creation_time_file_name, 'w', encoding='utf-8') as f:
            json.dump(next_creation_times, f)

    return next_creation_times


def main() -> None:
    listing_hash = '292030-The Witcher 3: Wild Hunt Booster Pack'
    price_in_cents = 23  # this is the money which you, as the seller, will receive

    price_dict_for_listing_hashes = {listing_hash: price_in_cents}

    creation_results, sale_results = create_then_sell_booster_packs_for_batch(price_dict_for_listing_hashes)


if __name__ == '__main__':
    main()
