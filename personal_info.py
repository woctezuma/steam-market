# Reference: https://www.blakeporterneuro.com/learning-python-project-3-scrapping-data-from-steams-community-market/

import json


def load_steam_cookie_from_disk(file_name_with_personal_info='personal_info.json'):
    try:
        with open(file_name_with_personal_info, 'r') as f:
            cookie = json.load(f)
    except FileNotFoundError:
        cookie = dict()

    return cookie


def get_cookie_dict(verbose=False):
    cookie = load_steam_cookie_from_disk()

    if verbose:
        for field in cookie.keys():
            print('{}: {}'.format(field, cookie[field]))

    return cookie


def main():
    cookie = get_cookie_dict(verbose=True)

    return


if __name__ == '__main__':
    main()
