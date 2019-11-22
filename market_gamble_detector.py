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

from market_arbitrage import filter_out_badges_with_low_sell_price
from market_buzz_detector import filter_out_unmarketable_packs, sort_according_to_buzz, print_packs_with_high_buzz
from market_listing import get_item_nameid_batch
from market_order import load_market_order_data_from_disk, download_market_order_data_batch
from market_search import get_tag_item_class_no_for_profile_backgrounds, get_tag_item_class_no_for_emoticons
from market_search import update_all_listings, load_all_listings
from utils import get_listing_details_output_file_name_for_emoticons
from utils import get_listing_details_output_file_name_for_profile_backgrounds
from utils import get_listing_output_file_name_for_profile_backgrounds, get_listing_output_file_name_for_emoticons
from utils import get_market_order_file_name_for_profile_backgrounds, get_market_order_file_name_for_emoticons


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


def get_listings(retrieve_listings_from_scratch,
                 listing_output_file_name):
    if retrieve_listings_from_scratch:
        update_all_listings_for_profile_backgrounds()
        update_all_listings_for_emoticons()

    all_listings = load_all_listings(listing_output_file_name)

    return all_listings


def filter_out_candidates_whose_ask_price_is_below_threshold(all_listings,
                                                             price_threshold_in_cents,
                                                             category_name):
    # Build dummy badge data, in order to reuse functions developed for the analysis of Booster Packs

    badge_data = dict()
    for listing_hash in all_listings:
        dummy_app_id = listing_hash
        badge_data[dummy_app_id] = dict()
        badge_data[dummy_app_id]['listing_hash'] = listing_hash
        badge_data[dummy_app_id]['sell_price'] = all_listings[listing_hash]['sell_price']

    # Filter out candidates for which the ask is below a given threshold

    filtered_badge_data = filter_out_badges_with_low_sell_price(badge_data,
                                                                category_name=category_name,
                                                                user_chosen_price_threshold=price_threshold_in_cents)

    return filtered_badge_data


def get_market_orders(filtered_badge_data,
                      retrieve_market_orders_online,
                      focus_on_listing_hashes_never_seen_before,
                      listing_details_output_file_name,
                      market_order_output_file_name):
    # Pre-retrieval of item name ids

    selected_listing_hashes = [filtered_badge_data[app_id]['listing_hash'] for app_id in filtered_badge_data.keys()]

    item_nameids = get_item_nameid_batch(selected_listing_hashes,
                                         listing_details_output_file_name=listing_details_output_file_name)

    # Load market orders (bid, ask) from disk

    market_order_dict = load_market_order_data_from_disk(market_order_output_file_name=market_order_output_file_name)

    # Filter out listing hashes which have already been encountered at least once

    first_encountered_filtered_badge_data = dict()

    for dummy_app_id in filtered_badge_data:
        if filtered_badge_data[dummy_app_id]['listing_hash'] not in market_order_dict:
            first_encountered_filtered_badge_data[dummy_app_id] = filtered_badge_data[dummy_app_id]

    # Retrieval of market orders (bid, ask)

    if focus_on_listing_hashes_never_seen_before:
        badge_data_to_process = first_encountered_filtered_badge_data
    else:
        badge_data_to_process = filtered_badge_data

    if retrieve_market_orders_online and len(badge_data_to_process) > 0:
        market_order_dict = download_market_order_data_batch(badge_data_to_process,
                                                             market_order_dict=market_order_dict,
                                                             market_order_output_file_name=market_order_output_file_name,
                                                             listing_details_output_file_name=listing_details_output_file_name)

    return market_order_dict


def main():
    look_for_profile_backgrounds = True
    price_threshold_in_cents = 100

    retrieve_listings_from_scratch = False
    retrieve_market_orders_online = True
    focus_on_listing_hashes_never_seen_before = True

    num_packs_to_display = 100

    if look_for_profile_backgrounds:
        category_name = 'profile backgrounds'
        listing_output_file_name = get_listing_output_file_name_for_profile_backgrounds()
        listing_details_output_file_name = get_listing_details_output_file_name_for_profile_backgrounds()
        market_order_output_file_name = get_market_order_file_name_for_profile_backgrounds()
    else:
        category_name = 'emoticons'
        listing_output_file_name = get_listing_output_file_name_for_emoticons()
        listing_details_output_file_name = get_listing_details_output_file_name_for_emoticons()
        market_order_output_file_name = get_market_order_file_name_for_emoticons()

    all_listings = get_listings(retrieve_listings_from_scratch,
                                listing_output_file_name)

    filtered_badge_data = filter_out_candidates_whose_ask_price_is_below_threshold(all_listings,
                                                                                   price_threshold_in_cents,
                                                                                   category_name)

    market_order_dict = get_market_orders(filtered_badge_data,
                                          retrieve_market_orders_online,
                                          focus_on_listing_hashes_never_seen_before,
                                          listing_details_output_file_name,
                                          market_order_output_file_name)

    # Only keep marketable booster packs

    marketable_market_order_dict, unknown_market_order_dict = filter_out_unmarketable_packs(market_order_dict)

    # Sort by bid value
    hashes_for_best_bid = sort_according_to_buzz(market_order_dict,
                                                 marketable_market_order_dict)

    # Display the highest ranked booster packs

    print_packs_with_high_buzz(hashes_for_best_bid,
                               market_order_dict,
                               category_name=category_name,
                               num_packs_to_display=num_packs_to_display)

    return True


if __name__ == '__main__':
    main()
