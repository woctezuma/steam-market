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

    drop_rate_estimates['badges'] = 239

    drop_rate_field = get_drop_rate_field()
    rarity_field = 'common'

    drop_rate_estimates[drop_rate_field] = dict()

    # Drop rates for common rarity based on the item rarity pattern (C, UC, R):
    drop_rate_estimates[drop_rate_field][rarity_field] = {
        (1, 1, 1): 0.6294,
        (1, 2, 1): 0.3832,
        (1, 2, 2): 0.5560,
        (2, 1, 1): 0.5916,
        (2, 2, 1): 0.5060,
        (2, 2, 2): 0.5722,
        (2, 2, 5): 0.5000,
        (2, 3, 1): 0.5566,
        (2, 5, 2): 0.3989,
        (3, 1, 1): 0.7911,
        (3, 2, 1): 0.7726,
        (4, 3, 2): 0.5413,
        (5, 1, 1): 0.6676,
        (3, 4, 3): 0.5337,
        (4, 1, 1): 0.7726,
        (4, 2, 1): 0.7828,
    }

    common_drop_rate = drop_rate_estimates[drop_rate_field][rarity_field]

    for pattern in common_drop_rate:
        current_drop_rate = common_drop_rate[pattern]
        drop_rate_estimates[drop_rate_field][rarity_field][pattern] = clamp_proportion(current_drop_rate)

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

    drop_rate_estimates['badges'] = 236

    category_field = get_category_name_for_profile_backgrounds()
    drop_rate_field = get_drop_rate_field()
    rarity_fields = get_rarity_fields()

    drop_rate_estimates[category_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field]['common'] = 0.6271
    drop_rate_estimates[category_field][drop_rate_field]['uncommon'] = 0.2585
    drop_rate_estimates[category_field][drop_rate_field]['rare'] = 0.1144

    for rarity in rarity_fields:
        current_drop_rate = drop_rate_estimates[category_field][drop_rate_field][rarity]
        drop_rate_estimates[category_field][drop_rate_field][rarity] = clamp_proportion(current_drop_rate)

    category_field = get_category_name_for_emoticons()

    drop_rate_estimates[category_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field] = dict()
    drop_rate_estimates[category_field][drop_rate_field]['common'] = 0.7458
    drop_rate_estimates[category_field][drop_rate_field]['uncommon'] = 0.2034
    drop_rate_estimates[category_field][drop_rate_field]['rare'] = 0.0508

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
