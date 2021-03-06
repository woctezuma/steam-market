from pathlib import Path


def get_cushioned_cooldown_in_seconds(num_minutes):
    num_seconds = num_minutes * 60
    cushion_in_seconds = 10

    cushioned_cooldown_in_seconds = num_seconds + cushion_in_seconds

    return cushioned_cooldown_in_seconds


def get_data_folder():
    data_folder = 'data/'
    Path(data_folder).mkdir(exist_ok=True)

    return data_folder


def get_badge_creation_file_name(from_javascript=False):
    badge_creation_file_name = get_data_folder() + 'booster_game_creator'

    if from_javascript:
        badge_creation_file_name += '_from_javascript'

    badge_creation_file_name += '.txt'

    return badge_creation_file_name


def get_steam_card_exchange_file_name():
    steam_card_exchange_file_name = get_data_folder() + 'steam_card_exchange.json'

    return steam_card_exchange_file_name


def get_listing_output_file_name_suffix(tag_drop_rate_str=None,
                                        rarity=None):
    from market_search import get_tag_drop_rate_str

    if tag_drop_rate_str is None:
        tag_drop_rate_str = get_tag_drop_rate_str(rarity=rarity)

    if tag_drop_rate_str == get_tag_drop_rate_str(rarity == 'common'):
        suffix = ''
    else:
        suffix = '_rarity_{}'.format(tag_drop_rate_str)

    return suffix


def get_listing_output_file_name_for_profile_backgrounds(tag_drop_rate_str=None,
                                                         rarity=None):
    suffix = get_listing_output_file_name_suffix(tag_drop_rate_str=tag_drop_rate_str,
                                                 rarity=rarity)

    listing_output_file_name = get_data_folder() + 'listings_for_profile_backgrounds' + suffix + '.json'
    return listing_output_file_name


def get_listing_output_file_name_for_emoticons(tag_drop_rate_str=None,
                                               rarity=None):
    suffix = get_listing_output_file_name_suffix(tag_drop_rate_str=tag_drop_rate_str,
                                                 rarity=rarity)

    listing_output_file_name = get_data_folder() + 'listings_for_emoticons' + suffix + '.json'
    return listing_output_file_name


def get_listing_output_file_name_for_foil_cards():
    listing_output_file_name = get_data_folder() + 'listings_for_foil_cards.json'
    return listing_output_file_name


def get_listing_output_file_name():
    listing_output_file_name = get_data_folder() + 'listings.json'
    return listing_output_file_name


def get_listing_details_output_file_name_for_profile_backgrounds():
    listing_details_output_file_name = get_data_folder() + 'listing_details_for_profile_backgrounds.json'
    return listing_details_output_file_name


def get_listing_details_output_file_name_for_emoticons():
    listing_details_output_file_name = get_data_folder() + 'listing_details_for_emoticons.json'
    return listing_details_output_file_name


def get_listing_details_output_file_name_for_foil_cards():
    listing_details_output_file_name = get_data_folder() + 'listing_details_for_foil_cards.json'
    return listing_details_output_file_name


def get_listing_details_output_file_name():
    listing_details_output_file_name = get_data_folder() + 'listing_details.json'
    return listing_details_output_file_name


def get_goo_details_file_nam_for_for_foil_cards():
    goo_details_file_nam_for_for_foil_cards = get_data_folder() + 'goo_details_for_foil_cards.json'
    return goo_details_file_nam_for_for_foil_cards


def get_sack_of_gems_listing_file_name():
    sack_of_gems_listing_file_name = get_data_folder() + 'listing_sack_of_gems.json'

    return sack_of_gems_listing_file_name


def get_market_order_file_name_for_profile_backgrounds():
    market_order_file_name = get_data_folder() + 'market_orders_for_profile_backgrounds.json'
    return market_order_file_name


def get_market_order_file_name_for_emoticons():
    market_order_file_name = get_data_folder() + 'market_orders_for_emoticons.json'
    return market_order_file_name


def get_market_order_file_name():
    market_order_file_name = get_data_folder() + 'market_orders.json'

    return market_order_file_name


def get_next_creation_time_file_name():
    next_creation_time_file_name = get_data_folder() + 'next_creation_times.json'

    return next_creation_time_file_name


def main():
    for file_name in [get_badge_creation_file_name(from_javascript=False),
                      get_badge_creation_file_name(from_javascript=True),
                      get_listing_output_file_name(),
                      get_sack_of_gems_listing_file_name(),
                      get_market_order_file_name(),
                      get_next_creation_time_file_name(),
                      get_listing_details_output_file_name()]:
        print(file_name)

    return True


def convert_listing_hash_to_app_id(listing_hash):
    app_id = int(listing_hash.split('-')[0])

    return app_id


def get_listing_hash_suffixe():
    listing_hash_suffixe = ' Booster Pack'

    return listing_hash_suffixe


def convert_listing_hash_to_app_name(listing_hash):
    tokens = listing_hash.split('-')[1:]

    if len(tokens) > 1:
        app_name = '-'.join(tokens)
    else:
        app_name = tokens[0]

    app_name = app_name[:-len(get_listing_hash_suffixe())]

    return app_name


def convert_to_listing_hash(app_id, app_name, listing_hash_suffixe=None):
    if listing_hash_suffixe is None:
        listing_hash_suffixe = get_listing_hash_suffixe()

    listing_hash = str(app_id) + '-' + app_name + listing_hash_suffixe

    return listing_hash


def get_steamcardexchange_url(app_id):
    # This page shows the number of cards, and provides links to the store page and the market pages.
    # NB: this allows to compute the crafting cost of a booster pack costs, as an amount of gems equal to 6000/num_cards
    steamcardexchange_url = 'https://www.steamcardexchange.net/index.php?gamepage-appid-' + str(app_id)

    return steamcardexchange_url


def get_steam_store_url(app_id):
    steam_store_url = 'https://store.steampowered.com/app/' + str(app_id) + '/'

    return steam_store_url


def get_category_name_for_booster_packs():
    category_name = 'booster packs'

    return category_name


def get_category_name_for_profile_backgrounds():
    category_name = 'profile backgrounds'

    return category_name


def get_category_name_for_emoticons():
    category_name = 'emoticons'

    return category_name


def get_bullet_point_for_display(use_numbered_bullet_points=False):
    # Return a string, which consists of a bullet point followed by three spaces, to display lists in Markdown format.
    #
    # NB: if the list of bullet points is long, Numbered bullet points improve readability on Github Gist.

    if use_numbered_bullet_points:
        bullet_point_character = '1.'
    else:
        bullet_point_character = '*'

    three_spaces_indentation = '   '

    bullet_point = '{}{}'.format(
        bullet_point_character,
        three_spaces_indentation,
    )

    return bullet_point


if __name__ == '__main__':
    main()
