# Objective: parse all the options to craft 'Booster Packs', available because I own the corresponding games.
#
# Caveat: this relies:
# - either on a previous manual copy-paste of HTML code to data/booster_game_creator.txt
# - or on a previous manual copy-paste of javascript code to data/booster_game_creator_from_javascript.txt

import json
from pathlib import Path

from src.market_listing import fix_app_name_for_url_query
from src.utils import get_badge_creation_file_name


def parse_javascript_one_liner(
    badges_as_str: str,
    verbose: bool = False,
) -> dict[str, dict]:
    badge_creation_details = {}

    print("Parsing the one-line javascript code displayed with the web browser.")

    badges = json.loads(badges_as_str.lstrip().rstrip(","))
    for badge in badges:
        app_id, next_creation_time = badge["appid"], "available now"
        app_id = str(app_id)
        badge_creation_details[app_id] = {
            "name": (app_name := badge["name"]),
            "gem_value": (gem_value := int(badge["price"])),
        }

        if badge.get("unavailable", False):
            next_creation_time = badge["available_at_time"]
            badge_creation_details[app_id]["next_creation_time"] = next_creation_time

            print(
                f"Loading the next creation time ({next_creation_time}) for {app_name} ({app_id = }) from the Booster Pack Creator list.",
            )

        if verbose:
            print(f"{app_id:<10}{app_name}\t{gem_value} gems\t{next_creation_time}")

    return badge_creation_details


def parse_augmented_steam_drop_down_menu(
    lines: list[str],
    verbose: bool = False,
) -> dict[str, dict]:
    badge_creation_details: dict[str, dict] = {}

    print("Parsing the drop-down menu displayed with Augmented Steam.")

    for line in lines:
        s = line.split()
        # e.g. ['<option', 'value="614910"', 'class="available">#monstercakes', '-', '1200', 'Gems</option>']

        # Hard-coded parsing
        app_id = s[1].split("=")[1].strip('"')
        app_name = s[2].split('available">')[1] + " "
        app_name += " ".join(s[3:-3])
        app_name = app_name.strip()
        gem_value = int(s[-2])

        app_name = fix_app_name_for_url_query(app_name)

        badge_creation_details[app_id] = {}
        badge_creation_details[app_id]["name"] = app_name
        badge_creation_details[app_id]["gem_value"] = gem_value

        if verbose:
            print(f"{app_id}\t{app_name}\t{gem_value}")

    return badge_creation_details


def parse_badge_creation_details(
    badge_creation_file_name: str | None = None,
    from_javascript: bool = False,
    verbose: bool = False,
) -> dict[str, dict]:
    if badge_creation_file_name is None:
        badge_creation_file_name = get_badge_creation_file_name(
            from_javascript=from_javascript,
        )

        if not Path(badge_creation_file_name).exists():
            badge_creation_file_name = get_badge_creation_file_name(
                from_javascript=not from_javascript,
            )

    with Path(badge_creation_file_name).open(encoding="utf-8") as f:
        lines = [line.strip() for line in f if line[0] != "#"]

    if len(lines) > 1:
        badge_creation_details = parse_augmented_steam_drop_down_menu(
            lines,
            verbose=verbose,
        )
    else:
        badges_as_str = lines[0]
        badge_creation_details = parse_javascript_one_liner(
            badges_as_str,
            verbose=verbose,
        )

    return badge_creation_details


def main() -> bool:
    badge_creation_details = parse_badge_creation_details(
        get_badge_creation_file_name(from_javascript=False),
    )

    print(f"#badges = {len(badge_creation_details)}")

    badge_creation_details = parse_badge_creation_details(
        get_badge_creation_file_name(from_javascript=True),
    )

    print(f"#badges = {len(badge_creation_details)}")

    badge_creation_details = parse_badge_creation_details(from_javascript=False)

    print(f"#badges = {len(badge_creation_details)}")

    badge_creation_details = parse_badge_creation_details(from_javascript=True)

    print(f"#badges = {len(badge_creation_details)}")

    return True


if __name__ == "__main__":
    main()
