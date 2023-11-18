import json
from pathlib import Path


def load_json(fname: str) -> dict:
    with Path(fname).open(encoding="utf8") as f:
        return json.load(f)


def save_json(data: dict, fname: str, prettify: bool = True, indent: int = 4) -> None:
    with Path(fname).open("w", encoding="utf8") as f:
        if prettify:
            json.dump(data, f, indent=indent)
        else:
            json.dump(data, f)
