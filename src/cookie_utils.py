import requests

from src.personal_info import update_and_save_cookie_to_disk_if_values_changed
from src.utils import TIMEOUT_IN_SECONDS

STEAM_COMMUNITY_URL = "https://steamcommunity.com/"
MINIMAL_COOKIE_FIELDS = ["steamLoginSecure"]


def filter_cookie_fields(
    cookie: dict[str, str],
    fields_to_filter_in: list[str],
) -> dict[str, str]:
    filtered_cookie = {}
    for field in fields_to_filter_in:
        filtered_cookie[field] = cookie[field]

    return filtered_cookie


def force_update_sessionid(cookie: dict[str, str]) -> dict[str, str]:
    filtered_cookie = filter_cookie_fields(cookie, MINIMAL_COOKIE_FIELDS)
    r = requests.get(
        url=STEAM_COMMUNITY_URL,
        cookies=filtered_cookie,
        timeout=TIMEOUT_IN_SECONDS,
    )

    if r.ok:
        response_cookie = dict(r.cookies)
        cookie = update_and_save_cookie_to_disk_if_values_changed(
            cookie,
            response_cookie,
        )

    return cookie
