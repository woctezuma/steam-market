import json


def load_json(fname: str) -> dict:
    with open(fname, encoding="utf8") as f:
        data = json.load(f)
    return data


def save_json(data: str, fname: str, prettify: bool = True, indent: int = 4) -> None:
    with open(fname, "w", encoding="utf8") as f:
        if prettify:
            json.dump(data, f, indent=indent)
        else:
            json.dump(data, f)
