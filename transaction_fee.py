def get_steam_transaction_fee() -> float:
    # Reference: https://support.steampowered.com/kb_article.php?ref=6088-UDXM-7214#steamfee

    return 0.05


def get_game_specific_transaction_fee() -> float:
    # Reference: https://support.steampowered.com/kb_article.php?ref=6088-UDXM-7214#steamfee

    return 0.10


def get_ground_truth_sell_price_without_fee(sell_price_including_fee: float) -> float:
    # Reference: https://steamcommunity.com/discussions/forum/1/1679190184065722423/

    # Manual fit of the fee cost for small prices (less than or equal to 0.66€)
    if sell_price_including_fee <= 0.21:
        total_fee_price = 0.02
    elif sell_price_including_fee <= 0.32:
        total_fee_price = 0.03
    elif sell_price_including_fee <= 0.43:
        total_fee_price = 0.04
    elif sell_price_including_fee == 0.44:
        total_fee_price = 0.05
    elif sell_price_including_fee <= 0.55:
        total_fee_price = 0.06
    elif sell_price_including_fee <= 0.66:
        total_fee_price = 0.07
    else:
        raise AssertionError

    sell_price_without_fee = sell_price_including_fee - total_fee_price
    return float(f"{sell_price_without_fee:.2f}")


def compute_sell_price_without_fee(sell_price_including_fee: float) -> float:
    # Caveat: this is not exact! The price without fee can be off by 1 cent!

    price = sell_price_including_fee

    ###

    steam_transaction_fee = get_steam_transaction_fee()

    steam_transaction_fee_price = max(
        0.01,
        price / (1 + steam_transaction_fee) * steam_transaction_fee,
    )
    price -= steam_transaction_fee_price

    ###

    game_specific_transaction_fee = get_game_specific_transaction_fee()

    game_specific_transaction_fee_price = max(
        0.01,
        price / (1 + game_specific_transaction_fee) * game_specific_transaction_fee,
    )
    price -= game_specific_transaction_fee_price

    ###

    total_fee_price = steam_transaction_fee_price + game_specific_transaction_fee_price

    sell_price_without_fee = sell_price_including_fee - total_fee_price
    sell_price_without_fee = float(f"{sell_price_without_fee:.2f}")

    # Manually adjust the fee cost for small prices (until I have access to the right formula)
    if sell_price_including_fee <= 0.66:
        sell_price_without_fee = get_ground_truth_sell_price_without_fee(
            sell_price_including_fee,
        )

    return sell_price_without_fee


def main() -> bool:
    print("With fee\t\tWithout fee")
    for i in range(3, 25):
        sell_price_including_fee = i / 100
        sell_price_without_fee = compute_sell_price_without_fee(
            sell_price_including_fee,
        )
        print(f"{sell_price_including_fee:.2f}€\t--->\t{sell_price_without_fee:.2f}€")

    return True


if __name__ == "__main__":
    main()
