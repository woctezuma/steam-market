# Objective: provide estimates of the drop-rate of Common/Uncommon/Rare items, for profile backgrounds and for emoticons
#
# NB: with 95% confidence, drop-rates are different for profile backgrounds and for emoticons.
# Reference: http://udsmed.u-strasbg.fr/labiostat/IMG/pdf/proportions-2.pdf (in French)
#
# NB²: we assume that the drop-rates are identical for every game. However, I have suspicions that the drop-rates may
# vary based on the number of items of each rarity.

from utils import get_category_name_for_profile_backgrounds, get_category_name_for_emoticons


def get_drop_rate_field():
    drop_rate_field = 'drop_rate'

    return drop_rate_field


def get_badge_count_field():
    badge_count_field = 'badge_count'

    return badge_count_field


def get_rarity_fields():
    rarity_fields = ['common', 'uncommon', 'rare']

    return rarity_fields


def clamp_proportion(input_proportion):
    # Reference: https://en.wikipedia.org/wiki/Clamping_(graphics)
    clampped_proportion = min(1, max(0, input_proportion))

    return clampped_proportion


def get_drop_rate_estimates_based_on_item_rarity_pattern(verbose=True):
    # Drop-rate estimates conditionally on the item rarity pattern C/UC/R (the numbers of possible items of each rarity)

    drop_rate_estimates = dict()

    drop_rate_estimates['badges'] = 240

    drop_rate_field = get_drop_rate_field()
    badge_count_field = get_badge_count_field()
    rarity_field = 'common'

    drop_rate_estimates[drop_rate_field] = dict()
    drop_rate_estimates[badge_count_field] = dict()

    # Drop rates for common rarity based on the item rarity pattern (C, UC, R):
    #
    # NB: these are the centers of the binomial proportion confidence intervals (Wilson score intervals)
    # Reference: https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval
    drop_rate_estimates[drop_rate_field][rarity_field] = {
        (1, 1, 1): 0.6304,
        (1, 2, 1): 0.3832,
        (1, 2, 2): 0.5718,
        (2, 1, 1): 0.6493,
        (2, 2, 2): 0.6200,
        (2, 2, 5): 0.3989,
        (2, 5, 2): 0.3989,
        (3, 1, 1): 0.8013,
        (3, 2, 1): 0.7726,
        (4, 3, 2): 0.6384,
        (5, 1, 1): 0.7049,
        (3, 4, 3): 0.5000,
        (4, 1, 1): 0.7726,
        (4, 2, 1): 0.7828,
        (4, 3, 3): 0.5731,
        (6, 2, 2): 0.6033,
    }

    common_drop_rate = drop_rate_estimates[drop_rate_field][rarity_field]

    for pattern in common_drop_rate:
        current_drop_rate = common_drop_rate[pattern]
        drop_rate_estimates[drop_rate_field][rarity_field][pattern] = clamp_proportion(current_drop_rate)

    drop_rate_estimates[badge_count_field][rarity_field] = {
        (1, 1, 1): 69,
        (1, 2, 1): 9,
        (1, 2, 2): 14,
        (2, 1, 1): 18,
        (2, 2, 1): 71,
        (2, 2, 2): 10,
        (2, 2, 5): 2,
        (2, 3, 1): 15,
        (2, 5, 2): 11,
        (3, 1, 1): 192,
        (3, 2, 1): 9,
        (4, 3, 2): 7,
        (5, 1, 1): 23,
        (3, 4, 3): 12,
        (4, 1, 1): 9,
        (4, 2, 1): 5,
        (4, 3, 3): 3,
        (6, 2, 2): 1,
    }

    num_crafted_badges_to_compute_estimates = drop_rate_estimates['badges']
    num_crafted_items_to_compute_estimates = sum(drop_rate_estimates[badge_count_field][rarity_field].values())

    # For each crafted badge, the user receives two items: one emoticon and one profile background.
    num_items_crafted_per_badge = 2

    if num_crafted_items_to_compute_estimates != num_crafted_badges_to_compute_estimates * num_items_crafted_per_badge:
        raise AssertionError()

    if verbose:
        print('Drop-rate estimates after crafting {} badges:'.format(
            drop_rate_estimates['badges']
        ))

        common_drop_rate = drop_rate_estimates[drop_rate_field][rarity_field]

        for pattern in common_drop_rate:
            print('- C/UC/R: {}\t--->\t{:.2f} ({})'.format(
                pattern,
                common_drop_rate[pattern],
                rarity_field.capitalize()
            ))

    return drop_rate_estimates


def get_drop_rate_estimates(verbose=True):
    # Drop-rate estimates conditionally on the category (profile backgrounds, emoticons)

    drop_rate_estimates = dict()

    drop_rate_estimates['badges'] = 451

    category_field = get_category_name_for_profile_backgrounds()
    drop_rate_field = get_drop_rate_field()
    rarity_fields = get_rarity_fields()

    drop_rate_estimates[category_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field]['common'] = 0.6475
    drop_rate_estimates[category_field][drop_rate_field]['uncommon'] = 0.2373
    drop_rate_estimates[category_field][drop_rate_field]['rare'] = 0.1153

    for rarity in rarity_fields:
        current_drop_rate = drop_rate_estimates[category_field][drop_rate_field][rarity]
        drop_rate_estimates[category_field][drop_rate_field][rarity] = clamp_proportion(current_drop_rate)

    category_field = get_category_name_for_emoticons()

    drop_rate_estimates[category_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field]['common'] = 0.7384
    drop_rate_estimates[category_field][drop_rate_field]['uncommon'] = 0.1840
    drop_rate_estimates[category_field][drop_rate_field]['rare'] = 0.0776

    for rarity in rarity_fields:
        current_drop_rate = drop_rate_estimates[category_field][drop_rate_field][rarity]
        drop_rate_estimates[category_field][drop_rate_field][rarity] = clamp_proportion(current_drop_rate)

    if verbose:
        print('Drop-rate estimates after crafting {} badges:'.format(
            drop_rate_estimates['badges']
        ))

        for category_field in [
            get_category_name_for_profile_backgrounds(),
            get_category_name_for_emoticons(),
        ]:
            print('- {}:\n\t{:.2f} (Common), {:.2f} (Uncommon), {:.2f} (Rare) ; sum = {:.2f} (expected: 1.00)'.format(
                category_field,
                drop_rate_estimates[category_field][drop_rate_field]['common'],
                drop_rate_estimates[category_field][drop_rate_field]['uncommon'],
                drop_rate_estimates[category_field][drop_rate_field]['rare'],
                sum(p for p in drop_rate_estimates[category_field][drop_rate_field].values())
            ))

    return drop_rate_estimates


def main():
    drop_rate_estimates = get_drop_rate_estimates(verbose=True)

    drop_rate_estimates = get_drop_rate_estimates_based_on_item_rarity_pattern(verbose=True)

    return True


if __name__ == '__main__':
    main()
