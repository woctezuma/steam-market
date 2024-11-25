def get_tag_drop_rate_str(rarity: str | None = None) -> str:
    if rarity is None:
        rarity = "common"

    if rarity == "extraordinary":
        tag_drop_rate_no = 3
    elif rarity == "rare":
        tag_drop_rate_no = 2
    elif rarity == "uncommon":
        tag_drop_rate_no = 1
    else:
        # Rarity: Common
        tag_drop_rate_no = 0

    return f"tag_droprate_{tag_drop_rate_no}"
