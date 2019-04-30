# Objective: parse all the options to craft 'Booster Packs', available because I own the corresponding games.
#
# Caveat: this relies:
# - either on a previous manual copy-paste of HTML code to data/booster_game_creator.txt
# - or on a previous manual copy-paste of javascript code to data/booster_game_creator_from_javascript.txt

from pathlib import Path

from market_listing import fix_app_name_for_url_query
from utils import get_badge_creation_file_name


def fix_unicode_characters_in_app_name_from_javascript_code(app_name):
    app_name = app_name.replace('\\u2122', '™')
    app_name = app_name.replace('\\u00fc', 'ü')
    app_name = app_name.replace('\\u00e9', 'é')
    app_name = app_name.replace('\\u00db', 'Û')
    app_name = app_name.replace('\\u795e', '神')
    app_name = app_name.replace('\\u5927', '大')
    app_name = app_name.replace('\\u2019', '’')
    app_name = app_name.replace('\\u7d76', '絶')
    app_name = app_name.replace('\\u666f', '景')
    app_name = app_name.replace('\\u7248', '版')

    return app_name


def get_sub_string(input_str, key_start_str, key_end_str=None):
    search_start_index = input_str.index(key_start_str)
    sub_string_start_index = search_start_index + len(key_start_str)
    sub_string = input_str[sub_string_start_index:]

    try:
        search_end_index = sub_string.index(key_end_str)
        sub_string_end_index = search_end_index
        sub_string = sub_string[:sub_string_end_index]
    except ValueError:
        pass

    return sub_string


def parse_javascript_one_liner(badges_as_str, verbose=False):
    badge_creation_details = dict()

    print('Parsing the one-line javascript code displayed with the web browser.')

    badges_as_list = badges_as_str.split('},{')

    for badge_as_str in badges_as_list:

        field_separator = ','

        app_id = get_sub_string(badge_as_str, '"appid":', field_separator + '"name":')
        app_name = get_sub_string(badge_as_str, '"name":', field_separator + '"series":')
        gem_value = get_sub_string(badge_as_str, '"price":', field_separator + '"unavailable":')

        app_id = int(app_id)
        app_name = fix_unicode_characters_in_app_name_from_javascript_code(app_name.strip('"'))
        gem_value = int(gem_value.strip('"'))

        badge_creation_details[app_id] = dict()
        badge_creation_details[app_id]['name'] = app_name
        badge_creation_details[app_id]['gem_value'] = gem_value

        if verbose:
            print('{}\t{}\t{}'.format(app_id, app_name, gem_value))

        if '\\u' in app_name:
            # Manually add the characters to replace in fix_unicode_characters_in_app_name_from_javascript_code()
            print('[warning] unicode characters not interpreted correctly in:\t{}'.format(app_name))

    return badge_creation_details


def parse_augmented_steam_drop_down_menu(lines, verbose=False):
    badge_creation_details = dict()

    print('Parsing the drop-down menu displayed with Augmented Steam.')

    for l in lines:
        s = l.split()
        # e.g. ['<option', 'value="614910"', 'class="available">#monstercakes', '-', '1200', ',', 'Gems</option>']

        # Hard-coded parsing
        app_id = int(s[1].split('=')[1].strip('"'))
        app_name = s[2].split('available">')[1] + ' '
        app_name += ' '.join(s[3:-4])
        app_name = app_name.strip()
        gem_value = int(s[-3])

        app_name = fix_app_name_for_url_query(app_name)

        badge_creation_details[app_id] = dict()
        badge_creation_details[app_id]['name'] = app_name
        badge_creation_details[app_id]['gem_value'] = gem_value

        if verbose:
            print('{}\t{}\t{}'.format(app_id, app_name, gem_value))

    return badge_creation_details


def parse_badge_creation_details(badge_creation_file_name=None, from_javascript=False, verbose=False):
    if badge_creation_file_name is None:
        badge_creation_file_name = get_badge_creation_file_name(from_javascript=from_javascript)

        if not Path(badge_creation_file_name).exists():
            badge_creation_file_name = get_badge_creation_file_name(from_javascript=not from_javascript)

    with open(badge_creation_file_name, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l[0] != '#']

    if len(lines) > 1:
        badge_creation_details = parse_augmented_steam_drop_down_menu(lines, verbose=verbose)
    else:
        badges_as_str = lines[0]
        badge_creation_details = parse_javascript_one_liner(badges_as_str, verbose=verbose)

    return badge_creation_details


def main():
    badge_creation_details = parse_badge_creation_details(get_badge_creation_file_name(from_javascript=False))

    print('#badges = {}'.format(len(badge_creation_details)))

    badge_creation_details = parse_badge_creation_details(get_badge_creation_file_name(from_javascript=True))

    print('#badges = {}'.format(len(badge_creation_details)))

    badge_creation_details = parse_badge_creation_details(from_javascript=False)

    print('#badges = {}'.format(len(badge_creation_details)))

    badge_creation_details = parse_badge_creation_details(from_javascript=True)

    print('#badges = {}'.format(len(badge_creation_details)))

    return True


if __name__ == '__main__':
    main()
