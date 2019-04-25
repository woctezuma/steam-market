from pathlib import Path


def get_data_folder():
    data_folder = 'data/'
    Path(data_folder).mkdir(exist_ok=True)

    return data_folder


def get_badge_creation_file_name():
    badge_creation_file_name = get_data_folder() + 'booster_game_creator.txt'
    return badge_creation_file_name


def get_listing_output_file_name():
    listing_output_file_name = get_data_folder() + 'listings.json'
    return listing_output_file_name


def get_listing_details_output_file_name():
    listing_details_output_file_name = get_data_folder() + 'listing_details.json'
    return listing_details_output_file_name


def main():
    for file_name in [get_badge_creation_file_name(),
                      get_listing_output_file_name(),
                      get_listing_details_output_file_name()]:
        print(file_name)

    return True


if __name__ == '__main__':
    main()
