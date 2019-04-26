def get_steam_transaction_fee():
    # Reference: https://support.steampowered.com/kb_article.php?ref=6088-UDXM-7214#steamfee

    steam_transaction_fee = 0.05

    return steam_transaction_fee


def get_game_specific_transaction_fee():
    # Reference: https://support.steampowered.com/kb_article.php?ref=6088-UDXM-7214#steamfee

    game_specific_transaction_fee = 0.10

    return game_specific_transaction_fee


def compute_sell_price_without_fee(sell_price_including_fee):
    # Caveat: this is not exact! The price without fee can be off by 1 cent!

    price = sell_price_including_fee

    ###

    steam_transaction_fee = get_steam_transaction_fee()

    steam_transaction_fee_price = max(0.01,
                                      price / (1 + steam_transaction_fee)
                                      * steam_transaction_fee
                                      )
    price -= steam_transaction_fee_price

    ###

    game_specific_transaction_fee = get_game_specific_transaction_fee()

    game_specific_transaction_fee_price = max(0.01,
                                              price / (1 + game_specific_transaction_fee)
                                              * game_specific_transaction_fee
                                              )
    price -= game_specific_transaction_fee_price

    ###

    total_fee_price = steam_transaction_fee_price + game_specific_transaction_fee_price

    sell_price_without_fee = sell_price_including_fee - total_fee_price
    sell_price_without_fee = float('{0:.2f}'.format(sell_price_without_fee))

    return sell_price_without_fee


def main():
    print('With fee\t\tWithout fee')
    for i in range(3, 25):
        sell_price_including_fee = i / 100
        sell_price_without_fee = compute_sell_price_without_fee(sell_price_including_fee)
        print('{:.2f}€\t--->\t{:.2f}€'.format(sell_price_including_fee, sell_price_without_fee))

    return True


if __name__ == '__main__':
    main()
