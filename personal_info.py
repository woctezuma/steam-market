# Reference: https://www.blakeporterneuro.com/learning-python-project-3-scrapping-data-from-steams-community-market/

import json


def get_steam_cookie_file_name():
    steam_cookie_file_name = 'personal_info.json'

    return steam_cookie_file_name


def load_steam_cookie_from_disk(file_name_with_personal_info=None):
    if file_name_with_personal_info is None:
        file_name_with_personal_info = get_steam_cookie_file_name()

    try:
        with open(file_name_with_personal_info, 'r', encoding='utf-8') as f:
            cookie = json.load(f)
    except FileNotFoundError:
        cookie = dict()

    return cookie


def save_steam_cookie_to_disk(cookie,
                              file_name_with_personal_info=None):
    if file_name_with_personal_info is None:
        file_name_with_personal_info = get_steam_cookie_file_name()

    is_cookie_to_be_saved = bool(cookie is not None and len(cookie) > 0)

    if is_cookie_to_be_saved:
        with open(file_name_with_personal_info, 'w', encoding='utf-8') as f:
            json.dump(cookie, f)

    return is_cookie_to_be_saved


def get_cookie_dict(verbose=False):
    cookie = load_steam_cookie_from_disk()

    if verbose:
        for field in cookie.keys():
            print('{}: {}'.format(field, cookie[field]))

    return cookie


def update_cookie_dict(original_cookie,
                       dict_with_new_values,
                       verbose=False):
    cookie = original_cookie

    for field in dict_with_new_values.keys():
        current_value = cookie[field]
        new_value = dict_with_new_values[field]

        if new_value != current_value:
            print('Updating value for cookie field {} from {} to {}.'.format(field, current_value, new_value))
            cookie[field] = new_value

    if verbose:
        for field in cookie.keys():
            print('{}: {}'.format(field, cookie[field]))

    return cookie


def update_and_save_cookie_to_disk_if_values_changed(cookie,
                                                     dict_with_new_values,
                                                     fields=None,
                                                     file_name_with_personal_info=None,
                                                     verbose=False):
    if fields is None:
        fields = ['steamLoginSecure', 'sessionid']

    relevant_fields = set(fields)
    relevant_fields = relevant_fields.intersection(cookie.keys())
    relevant_fields = relevant_fields.intersection(dict_with_new_values.keys())

    is_cookie_to_be_updated = any([dict_with_new_values[field] != cookie[field] for field in relevant_fields])

    if is_cookie_to_be_updated:
        cookie = update_cookie_dict(original_cookie=cookie,
                                    dict_with_new_values=dict_with_new_values,
                                    verbose=verbose)

        is_cookie_to_be_saved = save_steam_cookie_to_disk(cookie=cookie,
                                                          file_name_with_personal_info=file_name_with_personal_info)

    return cookie


def main():
    cookie = get_cookie_dict(verbose=True)

    return


if __name__ == '__main__':
    main()
