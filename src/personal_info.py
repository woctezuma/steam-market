# Reference: https://www.blakeporterneuro.com/learning-python-project-3-scrapping-data-from-steams-community-market/

from src.json_utils import load_json, save_json


def get_steam_cookie_file_name() -> str:
    return "personal_info.json"


def load_steam_cookie_from_disk(
    file_name_with_personal_info: str | None = None,
) -> dict[str, str]:
    if file_name_with_personal_info is None:
        file_name_with_personal_info = get_steam_cookie_file_name()

    try:
        cookie = load_json(file_name_with_personal_info)
    except FileNotFoundError:
        cookie = {}

    return cookie


def save_steam_cookie_to_disk(
    cookie: dict[str, str],
    file_name_with_personal_info: str | None = None,
) -> bool:
    if file_name_with_personal_info is None:
        file_name_with_personal_info = get_steam_cookie_file_name()

    is_cookie_to_be_saved = bool(cookie is not None and len(cookie) > 0)

    if is_cookie_to_be_saved:
        save_json(cookie, file_name_with_personal_info)

    return is_cookie_to_be_saved


def get_cookie_dict(verbose: bool = False) -> dict[str, str]:
    cookie = load_steam_cookie_from_disk()

    if verbose:
        for field in cookie:
            print(f"{field}: {cookie[field]}")

    return cookie


def update_cookie_dict(
    original_cookie: dict[str, str],
    dict_with_new_values: dict[str, str],
    verbose: bool = False,
) -> dict[str, str]:
    cookie = original_cookie

    for field in dict_with_new_values:
        try:
            current_value = cookie[field]
        except KeyError:
            current_value = None
        new_value = dict_with_new_values[field]

        if new_value != current_value:
            print(
                f"Updating value for cookie field {field} from {current_value} to {new_value}.",
            )
            cookie[field] = new_value

    if verbose:
        for field in cookie:
            print(f"{field}: {cookie[field]}")

    return cookie


def update_and_save_cookie_to_disk_if_values_changed(
    cookie: dict[str, str],
    dict_with_new_values: dict[str, str],
    fields: list[str] | None = None,
    file_name_with_personal_info: str | None = None,
    verbose: bool = False,
) -> dict[str, str]:
    if fields is None:
        fields = ["steamLoginSecure", "sessionid", "steamDidLoginRefresh"]

    relevant_fields = set(fields)
    relevant_fields = relevant_fields.intersection(cookie.keys())
    relevant_fields = relevant_fields.intersection(dict_with_new_values.keys())

    is_cookie_to_be_updated = any(
        dict_with_new_values[field] != cookie[field] for field in relevant_fields
    )

    if is_cookie_to_be_updated:
        cookie = update_cookie_dict(
            original_cookie=cookie,
            dict_with_new_values=dict_with_new_values,
            verbose=verbose,
        )

        save_steam_cookie_to_disk(
            cookie=cookie,
            file_name_with_personal_info=file_name_with_personal_info,
        )

    return cookie


def main() -> None:
    get_cookie_dict(verbose=True)


if __name__ == "__main__":
    main()
