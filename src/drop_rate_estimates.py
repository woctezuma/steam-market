# Objective: provide estimates of the drop-rate of Common/Uncommon/Rare items, for profile backgrounds and for emoticons
#
# NB: with 95% confidence, drop-rates are different for profile backgrounds and for emoticons.
# Reference: http://udsmed.u-strasbg.fr/labiostat/IMG/pdf/proportions-2.pdf (in French)
#
# NB²: we assume that the drop-rates are identical for every game. However, I have suspicions that the drop-rates may
# vary based on the number of items of each rarity.

from src.utils import (
    get_category_name_for_emoticons,
    get_category_name_for_profile_backgrounds,
)


def get_drop_rate_field() -> str:
    return "drop_rate"


def get_badge_count_field() -> str:
    return "badge_count"


def get_rarity_fields() -> list[str]:
    return ["common", "uncommon", "rare"]


def clamp_proportion(input_proportion: float) -> float:
    # Reference: https://en.wikipedia.org/wiki/Clamping_(graphics)
    return min(1.0, max(0.0, input_proportion))


def get_drop_rate_estimates_based_on_item_rarity_pattern(verbose: bool = True) -> dict:
    # Drop-rate estimates conditionally on the item rarity pattern C/UC/R (the numbers of possible items of each rarity)

    drop_rate_estimates: dict = {}

    drop_rate_field = get_drop_rate_field()
    badge_count_field = get_badge_count_field()
    rarity_field = "common"

    drop_rate_estimates[drop_rate_field] = {}
    drop_rate_estimates[badge_count_field] = {}

    # Drop rates for common rarity based on the item rarity pattern (C, UC, R):
    #
    # NB: these are the centers of the binomial proportion confidence intervals (Wilson score intervals)
    # Reference: https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval
    drop_rate_estimates[drop_rate_field][rarity_field] = {
        # Patterns found for profile background and emoticons:
        (1, 1, 1): 0.5538,
        (2, 2, 1): 0.6073,
        (2, 3, 1): 0.5796,
        (3, 1, 1): 0.8036,
        (3, 2, 1): 0.6740,
        (3, 3, 1): 0.4856,
        (3, 4, 3): 0.6135,
        (4, 1, 1): 0.7961,
        (4, 3, 2): 0.6384,
        (5, 1, 1): 0.7299,
        (5, 4, 1): 0.8197,
        # Patterns only found for profile background:
        (1, 1, 2): 0.5891,
        (1, 2, 1): 0.3832,
        (1, 2, 2): 0.5718,
        (1, 3, 1): 0.7306,
        (2, 1, 1): 0.6845,
        (2, 1, 3): 0.4434,
        (2, 2, 2): 0.6214,
        (2, 2, 5): 0.3673,
        (2, 5, 2): 0.3989,
        (4, 2, 2): 0.7078,
        (5, 3, 1): 0.6016,
        (6, 3, 1): 0.6275,
        # Patterns only found for emoticons:
        (2, 1, 2): 0.4705,
        (2, 2, 3): 0.6697,
        (4, 2, 1): 0.8019,
        (4, 3, 1): 0.5461,
        (4, 3, 3): 0.3742,
        (5, 2, 2): 0.4703,
        (5, 3, 2): 0.7254,
        (6, 2, 2): 0.8422,
        (7, 1, 1): 0.6033,
        (8, 1, 1): 0.8528,
    }

    common_drop_rate = drop_rate_estimates[drop_rate_field][rarity_field]

    for pattern in common_drop_rate:
        current_drop_rate = common_drop_rate[pattern]
        drop_rate_estimates[drop_rate_field][rarity_field][pattern] = clamp_proportion(
            current_drop_rate,
        )

    drop_rate_estimates[badge_count_field][rarity_field] = {
        # Patterns found for profile background and emoticons:
        (1, 1, 1): 238,
        (2, 2, 1): 383,
        (2, 3, 1): 15,
        (3, 1, 1): 795,
        (3, 2, 1): 45,
        (3, 3, 1): 31,
        (3, 4, 3): 27,
        (4, 1, 1): 35,
        (4, 3, 2): 7,
        (5, 1, 1): 44,
        (5, 4, 1): 29,
        # Patterns only found for profile background:
        (1, 1, 2): 13,
        (1, 2, 1): 9,
        (1, 2, 2): 24,
        (1, 3, 1): 7,
        (2, 1, 1): 110,
        (2, 1, 3): 5,
        (2, 2, 2): 25,
        (2, 2, 5): 15,
        (2, 5, 2): 11,
        (4, 2, 2): 13,
        (5, 3, 1): 6,
        (6, 3, 1): 4,
        # Patterns only found for emoticons:
        (2, 1, 2): 30,
        (2, 2, 3): 5,
        (4, 2, 1): 21,
        (4, 3, 1): 7,
        (4, 3, 3): 20,
        (5, 2, 2): 13,
        (5, 3, 2): 25,
        (6, 2, 2): 21,
        (7, 1, 1): 1,
        (8, 1, 1): 16,
    }

    drop_rate_estimates["badges"] = 1025

    num_crafted_badges_to_compute_estimates = drop_rate_estimates["badges"]
    num_crafted_items_to_compute_estimates = sum(
        drop_rate_estimates[badge_count_field][rarity_field].values(),
    )

    # For each crafted badge, the user receives two items: one emoticon and one profile background.
    num_items_crafted_per_badge = 2

    if (
        num_crafted_items_to_compute_estimates
        != num_crafted_badges_to_compute_estimates * num_items_crafted_per_badge
    ):
        raise AssertionError

    if verbose:
        print(
            f"Drop-rate estimates after crafting {num_crafted_badges_to_compute_estimates} badges:",
        )

        common_drop_rate = drop_rate_estimates[drop_rate_field][rarity_field]

        for pattern in common_drop_rate:
            print(
                f"- C/UC/R: {pattern}\t--->\t{common_drop_rate[pattern]:.2f} ({rarity_field.capitalize()})",
            )

    return drop_rate_estimates


def get_drop_rate_estimates(verbose: bool = True) -> dict:
    # Drop-rate estimates conditionally on the category (profile backgrounds, emoticons)

    drop_rate_estimates: dict = {}

    category_field = get_category_name_for_profile_backgrounds()
    drop_rate_field = get_drop_rate_field()
    rarity_fields = get_rarity_fields()

    drop_rate_estimates[category_field] = {}
    drop_rate_estimates[category_field][drop_rate_field] = {}
    drop_rate_estimates[category_field][drop_rate_field]["common"] = 0.6609
    drop_rate_estimates[category_field][drop_rate_field]["uncommon"] = 0.2264
    drop_rate_estimates[category_field][drop_rate_field]["rare"] = 0.1146

    for rarity in rarity_fields:
        current_drop_rate = drop_rate_estimates[category_field][drop_rate_field][rarity]
        drop_rate_estimates[category_field][drop_rate_field][rarity] = clamp_proportion(
            current_drop_rate,
        )

    category_field = get_category_name_for_emoticons()

    drop_rate_estimates[category_field] = {}
    drop_rate_estimates[category_field][drop_rate_field] = {}
    drop_rate_estimates[category_field][drop_rate_field]["common"] = 0.7299
    drop_rate_estimates[category_field][drop_rate_field]["uncommon"] = 0.1865
    drop_rate_estimates[category_field][drop_rate_field]["rare"] = 0.0855

    for rarity in rarity_fields:
        current_drop_rate = drop_rate_estimates[category_field][drop_rate_field][rarity]
        drop_rate_estimates[category_field][drop_rate_field][rarity] = clamp_proportion(
            current_drop_rate,
        )

    drop_rate_estimates["badges"] = 1025

    if verbose:
        print(
            "Drop-rate estimates after crafting {} badges:".format(
                drop_rate_estimates["badges"],
            ),
        )

        for category_field in (
            get_category_name_for_profile_backgrounds(),
            get_category_name_for_emoticons(),
        ):
            print(
                "- {}:\n\t{:.2f} (Common), {:.2f} (Uncommon), {:.2f} (Rare) ; sum = {:.2f} (expected: 1.00)".format(
                    category_field,
                    drop_rate_estimates[category_field][drop_rate_field]["common"],
                    drop_rate_estimates[category_field][drop_rate_field]["uncommon"],
                    drop_rate_estimates[category_field][drop_rate_field]["rare"],
                    sum(
                        p
                        for p in drop_rate_estimates[category_field][
                            drop_rate_field
                        ].values()
                    ),
                ),
            )

    return drop_rate_estimates


def main() -> bool:
    get_drop_rate_estimates(verbose=True)

    get_drop_rate_estimates_based_on_item_rarity_pattern(
        verbose=True,
    )

    return True


if __name__ == "__main__":
    main()
