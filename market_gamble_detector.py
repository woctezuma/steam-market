# Objective: detect gambles which might be worth a try, i.e. find profile backgrounds and emoticons which:
# - are of "Common" rarity, so reasonably likely to be obtained after a crafting a badge,
# - have high bid orders, so potentially profitable after taking every other factor into account.
#
# Caveat: take into account the NUMBER of items of "Common" rarity! This information can be found on pages such as:
#         https://www.steamcardexchange.net/index.php?gamepage-appid-254880
# For instance, if there are 2 Profile Backgrounds of "Common" rarity, then you can expect to get the one of interest
# after crafting 2 badges, therefore you should expect to be able to sell it for 2x the crafting cost to turn a profit.
#
# NB: a booster pack of 3 cards is always worth 6000/(#cards) gems, so a full set of (#cards) is worth 2000 gems.
# Therefore, the cost of crafting a badge is identical for every game: that is twice the price of a sack of 1000 gems.
# If you pay 0.31 € per sack of gems, which you then turn into booster packs, then your *badge* crafting cost is 0.62 €.

from market_search import get_tag_item_class_no_for_profile_backgrounds, get_tag_item_class_no_for_emoticons
from market_search import update_all_listings
from utils import get_listing_output_file_name_for_profile_backgrounds, get_listing_output_file_name_for_emoticons


def update_all_listings_for_profile_backgrounds():
    print('Downloading listings for profile backgrounds.')

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_profile_backgrounds(),
        tag_item_class_no=get_tag_item_class_no_for_profile_backgrounds()
    )

    return


def update_all_listings_for_emoticons():
    print('Downloading listings for emoticons.')

    update_all_listings(
        listing_output_file_name=get_listing_output_file_name_for_emoticons(),
        tag_item_class_no=get_tag_item_class_no_for_emoticons()
    )

    return


def main():
    update_all_listings_for_profile_backgrounds()
    update_all_listings_for_emoticons()

    # TODO maybe stop early, since listings are sorted by descending price.
    # TODO get the bid values for some of these.

    return True


if __name__ == '__main__':
    main()
