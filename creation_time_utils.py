import datetime


def get_current_time():
    current_time = datetime.datetime.today()

    return current_time


def get_creation_time_format():
    # Reference: https://docs.python.org/3/library/time.html#time.strftime

    # The format used in: '14 Sep @ 10:48pm'
    time_format = '%d %b @ %I:%M%p'

    return time_format


def get_crafting_cooldown_duration_in_seconds():
    # For every game, a booster pack can be crafted every day.
    crafting_cooldown_duration_in_seconds = 24 * 3600

    return crafting_cooldown_duration_in_seconds


def determine_whether_a_booster_pack_can_be_crafted(badge_data,
                                                    current_time=None):
    if current_time is None:
        current_time = get_current_time()

    next_creation_time = badge_data['next_creation_time']

    if next_creation_time is None:
        a_booster_pack_can_be_crafted = True
    else:
        parsed_next_creation_time = datetime.datetime.strptime(next_creation_time,
                                                               get_creation_time_format())

        # Manually set the year, because it was not stored at creation time, following Valve's time format.
        parsed_next_creation_time = parsed_next_creation_time.replace(year=current_time.year)

        delta = parsed_next_creation_time - current_time
        delta_in_seconds = delta.total_seconds()

        # parsed_next_creation_time < current_time
        cooldown_has_ended = bool(delta_in_seconds < 0)

        # current_time + cooldown < parsed_next_creation_time
        # NB: this is necessary because we do not keep track of the year.
        cooldown_actually_ended_last_year = bool(get_crafting_cooldown_duration_in_seconds() < delta_in_seconds)

        a_booster_pack_can_be_crafted = cooldown_has_ended or cooldown_actually_ended_last_year

    return a_booster_pack_can_be_crafted


def main():
    formatted_current_date = datetime.datetime.strftime(get_current_time(),
                                                        get_creation_time_format())

    print(formatted_current_date)

    return True


if __name__ == '__main__':
    main()
