import json

import requests

from personal_info import get_cookie_dict
from utils import get_data_folder, convert_listing_hash_to_app_id


def get_my_steam_profile_id():
    my_profile_id = '76561198028705366'

    return my_profile_id


def get_steam_inventory_url(profile_id=None, app_id=753, context_id=6):
    if profile_id is None:
        profile_id = get_my_steam_profile_id()

    # References:
    # https://github.com/Alex7Kom/node-steam-tradeoffers/issues/114
    # https://dev.doctormckay.com/topic/332-identifying-steam-items/
    steam_inventory_url = 'https://steamcommunity.com/profiles/' + str(profile_id) + '/inventory/json/'
    steam_inventory_url += str(app_id) + '/' + str(context_id) + '/'

    return steam_inventory_url


def get_steam_inventory_file_name(profile_id):
    steam_inventory_file_name = get_data_folder() + 'inventory_' + str(profile_id) + '.json'

    return steam_inventory_file_name


def load_steam_inventory_from_disk(profile_id=None):
    if profile_id is None:
        profile_id = get_my_steam_profile_id()

    try:
        with open(get_steam_inventory_file_name(profile_id), 'r') as f:
            steam_inventory = json.load(f)
    except FileNotFoundError:
        steam_inventory = download_steam_inventory(profile_id, save_to_disk=True)

    return steam_inventory


def load_steam_inventory(profile_id=None, update_steam_inventory=False):
    if profile_id is None:
        profile_id = get_my_steam_profile_id()

    if update_steam_inventory:
        steam_inventory = download_steam_inventory(profile_id, save_to_disk=True)
    else:
        steam_inventory = load_steam_inventory_from_disk(profile_id=profile_id)

    return steam_inventory


def download_steam_inventory(profile_id=None, save_to_disk=True):
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

        if save_to_disk:
            with open(get_steam_inventory_file_name(profile_id), 'w') as f:
                json.dump(steam_inventory, f)
    else:
        print('Inventory for profile {} could not be loaded. Status code {} was returned.'.format(profile_id,
                                                                                                  status_code))
        steam_inventory = None

    return steam_inventory


def get_session_id(cookie=None):
    if cookie is None:
        cookie = get_cookie_dict()

    session_id = cookie['sessionid']

    return session_id


def get_steam_booster_pack_creation_url():
    booster_pack_creation_url = 'https://steamcommunity.com/tradingcards/ajaxcreatebooster/'

    return booster_pack_creation_url


def get_booster_pack_creation_parameters(app_id, session_id):
    booster_pack_creation_parameters = dict()

    booster_pack_creation_parameters['sessionid'] = str(session_id)
    booster_pack_creation_parameters['appid'] = str(app_id)
    booster_pack_creation_parameters['series'] = '1'
    booster_pack_creation_parameters['tradability_preference'] = '2'

    return booster_pack_creation_parameters


def create_booster_pack(app_id, verbose=True):
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    if not has_secured_cookie:
        raise AssertionError()

    session_id = get_session_id(cookie=cookie)

    url = get_steam_booster_pack_creation_url()
    req_data = get_booster_pack_creation_parameters(app_id=app_id,
                                                    session_id=session_id)

    resp_data = requests.post(url,
                              data=req_data,
                              cookies=cookie)

    status_code = resp_data.status_code

    if status_code == 200:
        # Expected result:
        # {"purchase_result":{"communityitemid":"XXX","appid":685400,"item_type":36, "purchaseid":"XXX",
        # "success":1,"rwgrsn":-2}, "goo_amount":"22793","tradable_goo_amount":"22793","untradable_goo_amount":0}
        result = resp_data.json()
    else:
        # NB: 401 means "Unauthorized", which must have something to do with wrong/outdated credentials in the cookie.
        print('Creation of a booster pack failed with status code {} (appID = {})'.format(status_code,
                                                                                          app_id))
        result = None

    if verbose:
        print(result)

    return result


def get_steam_market_sell_url():
    steam_market_sell_url = 'https://steamcommunity.com/market/sellitem/'

    return steam_market_sell_url


def get_market_sell_parameters(asset_id, price_in_cents, session_id):
    market_sell_parameters = dict()

    market_sell_parameters['sessionid'] = str(session_id)
    market_sell_parameters['appid'] = '753'
    market_sell_parameters['contextid'] = '6'
    market_sell_parameters['assetid'] = str(asset_id)  # To automatically determine asset ID, use retrieve_asset_id().
    market_sell_parameters['amount'] = '1'
    market_sell_parameters['price'] = str(price_in_cents)

    return market_sell_parameters


def sell_booster_pack(asset_id, price_in_cents, verbose=True):
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    if not has_secured_cookie:
        raise AssertionError()

    session_id = get_session_id(cookie=cookie)

    url = get_steam_market_sell_url()
    req_data = get_market_sell_parameters(asset_id=asset_id,
                                          price_in_cents=price_in_cents,
                                          session_id=session_id)

    resp_data = requests.post(url,
                              data=req_data,
                              cookies=cookie)

    status_code = resp_data.status_code

    if status_code == 200:
        # Expected result:
        # {"success":true,"requires_confirmation":0}
        result = resp_data.json()
    else:
        # NB: 400 means "Bad Request".
        print('Booster pack {} could not be sold for {} cents. Status code {} was returned.'.format(asset_id,
                                                                                                    price_in_cents,
                                                                                                    status_code))
        result = None

    if verbose:
        print(result)

    return result


def retrieve_asset_id(listing_hash,
                      steam_inventory=None,
                      verbose=True):
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

        if verbose:
            print(matched_element)

    else:
        print('There is no match in the inventory for {}.'.format(listing_hash))

    try:
        asset_id = matched_element['id']
    except KeyError:
        asset_id = None

    return asset_id


def main():
    listing_hash = '292030-The Witcher 3: Wild Hunt Booster Pack'
    price_in_cents = 30  # A high value to be safe during testing
    update_steam_inventory = True

    app_id = convert_listing_hash_to_app_id(listing_hash)
    result = create_booster_pack(app_id=app_id)

    steam_inventory = load_steam_inventory(update_steam_inventory=update_steam_inventory)

    asset_id = retrieve_asset_id(listing_hash=listing_hash, steam_inventory=steam_inventory)

    if asset_id is not None:
        result = sell_booster_pack(asset_id=asset_id, price_in_cents=price_in_cents)

    return


if __name__ == '__main__':
    main()
