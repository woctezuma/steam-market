from typing import Final

from src.utils import get_cushioned_cooldown_in_seconds

INTER_REQUEST_COOLDOWN_FIELD: Final[str] = "cooldown_between_each_request"


def get_rate_limits(
    api_type: str,
    *,
    has_secured_cookie: bool = False,
) -> dict[str, int]:
    if has_secured_cookie:
        base_limits = {
            "market_order": {"queries": 50, "minutes": 1},
            "market_search": {"queries": 50, "minutes": 1},
            "market_listing": {"queries": 25, "minutes": 3},
        }
    else:
        base_limits = {
            "market_order": {"queries": 25, "minutes": 5},
            "market_search": {"queries": 25, "minutes": 5},
            "market_listing": {"queries": 25, "minutes": 5},
        }

    limits = base_limits[api_type]

    return {
        "max_num_queries": limits["queries"],
        "cooldown": get_cushioned_cooldown_in_seconds(num_minutes=limits["minutes"]),
        INTER_REQUEST_COOLDOWN_FIELD: 0,
    }
