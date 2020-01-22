# Objective: provide estimates of the drop-rate of Common/Uncommon/Rare items, for profile backgrounds and for emoticons
#
# NB: with 95% confidence, drop-rates are different for profile backgrounds and for emoticons.
# Reference: http://udsmed.u-strasbg.fr/labiostat/IMG/pdf/proportions-2.pdf (in French)
#
# NB²: we assume that the drop-rates are identical for every games. However, I have suspicions that the drop-rates may
# vary based on the number of items of each rarity.

def get_drop_rate_estimates(verbose=True):
    drop_rate_estimates = dict()

    drop_rate_estimates['badges'] = 236

    drop_rate_estimates['profile_backgrounds'] = dict()
    drop_rate_estimates['profile_backgrounds']['drop_rate'] = dict()
    drop_rate_estimates['profile_backgrounds']['drop_rate']['common'] = 0.6271
    drop_rate_estimates['profile_backgrounds']['drop_rate']['uncommon'] = 0.2585
    drop_rate_estimates['profile_backgrounds']['drop_rate']['rare'] = 0.1144

    drop_rate_estimates['emoticons'] = dict()
    drop_rate_estimates['emoticons']['drop_rate'] = dict()
    drop_rate_estimates['emoticons']['drop_rate']['common'] = 0.7458
    drop_rate_estimates['emoticons']['drop_rate']['uncommon'] = 0.2034
    drop_rate_estimates['emoticons']['drop_rate']['rare'] = 0.0508

    if verbose:
        print('Drop-rate estimates after crafting {} badges:'.format(
            drop_rate_estimates['badges']
        ))

        for field in ['profile_backgrounds', 'emoticons']:
            print('- {}:\n\t{:.2f} (Common), {:.2f} (Uncommon), {:.2f} (Rare) ; sum = {:.2f}'.format(
                field,
                drop_rate_estimates[field]['drop_rate']['common'],
                drop_rate_estimates[field]['drop_rate']['uncommon'],
                drop_rate_estimates[field]['drop_rate']['rare'],
                sum(p for p in drop_rate_estimates[field]['drop_rate'].values())
            ))

    return drop_rate_estimates


def main():
    drop_rate_estimates = get_drop_rate_estimates(verbose=True)

    return True


if __name__ == '__main__':
    main()
