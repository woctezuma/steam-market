import datetime

from src.json_utils import load_json
from src.utils import get_next_creation_time_file_name


def load_next_creation_time_data(
    next_creation_time_file_name: str | None = None,
) -> dict[str, str]:
    if next_creation_time_file_name is None:
        next_creation_time_file_name = get_next_creation_time_file_name()

    try:
        next_creation_times = load_json(next_creation_time_file_name)
    except FileNotFoundError:
        next_creation_times = {}

    return next_creation_times


def fill_in_badges_with_next_creation_times_loaded_from_disk(
    aggregated_badge_data: dict[str, dict],
    verbose: bool = True,
) -> dict[str, dict]:
    next_creation_times_loaded_from_disk = load_next_creation_time_data()

    app_ids = set(aggregated_badge_data.keys()).intersection(
        next_creation_times_loaded_from_disk.keys(),
    )

    for app_id in app_ids:
        next_creation_time = next_creation_times_loaded_from_disk[app_id]

        previously_loaded_next_creation_time = aggregated_badge_data[app_id][
            "next_creation_time"
        ]
        aggregated_badge_data[app_id]["next_creation_time"] = next_creation_time

        if verbose:
            app_name = aggregated_badge_data[app_id]["name"]
            if previously_loaded_next_creation_time is None:
                print(
                    f"Loading the next creation time ({next_creation_time}) for {app_name} (appID = {app_id}) from disk.",
                )
            else:
                # NB: Data stored in data/next_creation_times.json is assumed to be more up-to-date compared to
                #     data stored in data/booster_game_creator_from_javascript.txt. Indeed, if you  update the .txt
                #     file with data found on your Booster Pack Creator page, then the .json file would be useless,
                #     and you should delete it. Therefore, if the .json file is present on your disk, it can be
                #     assumed that it was created by running this program, thus is more recent than the .txt file.
                print(
                    f"Replacing the next creation time ({previously_loaded_next_creation_time}) for {app_name} (appID = {app_id}) with {next_creation_time}, loaded from disk.",
                )

    return aggregated_badge_data


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


def to_timestamp(date: datetime.datetime) -> int:
    return int(date.timestamp())


def get_creation_time_format(prepend_year: bool = False) -> str:
    # Reference: https://docs.python.org/3/library/time.html#time.strftime

    # The format used in: "14 Sep @ 10:48pm"
    time_format = "%d %b @ %I:%M%p"

    if prepend_year:
        time_format = f"%Y {time_format}"

    return time_format


def get_formatted_time(time_struct: datetime.datetime | None = None) -> str:
    if time_struct is None:
        time_struct = get_current_time()

    return datetime.datetime.strftime(
        time_struct,
        get_creation_time_format(),
    )


def prepend_year_to_time_as_str(
    formatted_time_as_str: str,
    year_to_prepend: int | None = None,
) -> str:
    if year_to_prepend is None:
        current_time = get_current_time()
        year_to_prepend = current_time.year

    return f"{year_to_prepend} {formatted_time_as_str}"


def get_time_struct_from_str(
    formatted_time_as_str: str,
    use_current_year: bool = False,
) -> datetime.datetime:
    if use_current_year:
        current_time = get_current_time()
        current_year = current_time.year

        time_struct = datetime.datetime.strptime(
            prepend_year_to_time_as_str(
                formatted_time_as_str,
                year_to_prepend=current_year,
            ),
            get_creation_time_format(prepend_year=True),
        ).astimezone(datetime.UTC)

    else:
        try:
            time_struct = datetime.datetime.strptime(
                formatted_time_as_str,
                get_creation_time_format(),
            ).astimezone(datetime.UTC)
        except ValueError:
            # For February 29th during a leap year, it is necessary to specify the year before calling strptime().
            # Reference: https://github.com/python/cpython/commit/56027ccd6b9dab4a090e4fef8574933fb9a36ff2

            time_struct = get_time_struct_from_str(
                formatted_time_as_str,
                use_current_year=True,
            )

    return time_struct


def get_formatted_current_time(delay_in_days: int = 0) -> str:
    current_time = get_current_time()

    if delay_in_days != 0:
        current_time += datetime.timedelta(days=delay_in_days)

    return get_formatted_time(current_time)


def get_crafting_cooldown_duration_in_days() -> int:
    # For every game, a booster pack can be crafted every day.
    return 1


def get_crafting_cooldown_duration_in_seconds() -> int:
    return 24 * 3600 * get_crafting_cooldown_duration_in_days()


def determine_whether_a_booster_pack_can_be_crafted(
    badge_data: dict,
    current_time: datetime.datetime | None = None,
) -> bool:
    if current_time is None:
        current_time = get_current_time()

    next_creation_time = badge_data["next_creation_time"]

    if next_creation_time is None:
        a_booster_pack_can_be_crafted = True
    else:
        parsed_next_creation_time = get_time_struct_from_str(next_creation_time)

        if (
            current_time.month == 12
            and current_time.day == 31
            and parsed_next_creation_time.month == parsed_next_creation_time.day == 1
        ):
            # Today is the Dec 31, and the next creation time is the day after, on January 1.
            year_to_be_manually_set = current_time.year + 1
        else:
            year_to_be_manually_set = current_time.year

        # Manually set the year, because it was not stored at creation time, following Valve's time format.
        parsed_next_creation_time = parsed_next_creation_time.replace(
            year=year_to_be_manually_set,
        )

        delta = parsed_next_creation_time - current_time
        delta_in_seconds = delta.total_seconds()

        # parsed_next_creation_time < current_time
        cooldown_has_ended = bool(delta_in_seconds < 0)

        # current_time + cooldown < parsed_next_creation_time
        # NB: this is necessary because we do not keep track of the year.
        cooldown_actually_ended_last_year = bool(
            get_crafting_cooldown_duration_in_seconds() < delta_in_seconds,
        )

        a_booster_pack_can_be_crafted = (
            cooldown_has_ended or cooldown_actually_ended_last_year
        )

    return a_booster_pack_can_be_crafted


def main() -> bool:
    print(get_formatted_current_time())

    return True


if __name__ == "__main__":
    main()
