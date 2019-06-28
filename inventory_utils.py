import requests

from personal_info import get_cookie_dict


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


def create_booster_pack(app_id):
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    if not has_secured_cookie:
        raise AssertionError()

    session_id = cookie['sessionid']

    url = get_steam_booster_pack_creation_url()
    req_data = get_booster_pack_creation_parameters(app_id=app_id,
                                                    session_id=session_id)

    resp_data = requests.get(url,
                             params=req_data,
                             cookies=cookie)

    status_code = resp_data.status_code

    if status_code == 200:
        # Expected result:
        # {"purchase_result":{"communityitemid":"XXX","appid":685400,"item_type":36, "purchaseid":"XXX",
        # "success":1,"rwgrsn":-2}, "goo_amount":"22793","tradable_goo_amount":"22793","untradable_goo_amount":0}
        result = resp_data.json()
    else:
        print('Creation of a booster pack failed with status code {} (appID = {})'.format(status_code,
                                                                                          app_id))
        result = None

    return result


def get_steam_market_sell_url():
    steam_market_sell_url = 'https://steamcommunity.com/market/sellitem/'

    return steam_market_sell_url


def get_market_sell_parameters(asset_id, price_in_cents, session_id):
    market_sell_parameters = dict()

    market_sell_parameters['sessionid'] = str(session_id)
    market_sell_parameters['appid'] = '753'
    market_sell_parameters['contextid'] = '6'
    market_sell_parameters['asset_id'] = str(asset_id)  # TODO automatically determine asset ID
    market_sell_parameters['amount'] = '1'
    market_sell_parameters['price'] = str(price_in_cents)

    return market_sell_parameters


def sell_booster_pack(asset_id, price_in_cents):
    cookie = get_cookie_dict()
    has_secured_cookie = bool(len(cookie) > 0)

    if not has_secured_cookie:
        raise AssertionError()

    session_id = cookie['sessionid']

    url = get_steam_market_sell_url()
    req_data = get_market_sell_parameters(asset_id=asset_id,
                                          price_in_cents=price_in_cents,
                                          session_id=session_id)

    resp_data = requests.get(url,
                             params=req_data,
                             cookies=cookie)

    status_code = resp_data.status_code

    if status_code == 200:
        # Expected result:
        # {"success":true,"requires_confirmation":0}
        result = resp_data.json()
    else:
        print('Booster pack {} could not be sold for {} cents. Status code {} was returned.'.format(asset_id,
                                                                                                    price_in_cents,
                                                                                                    status_code))
        result = None

    return result


def main():
    app_id = 685400  # Skelly Selest: https://www.steamcardexchange.net/index.php?gamepage-appid-685400
    result = create_booster_pack(app_id=app_id)

    print(result)

    return


if __name__ == '__main__':
    main()
