import unittest

import market_arbitrage
import market_listing
import market_order
import market_search
import market_utils
import parsing_utils
import sack_of_gems
import transaction_fee
import utils


class TestMarketListingMethods(unittest.TestCase):

    def test_get_listing_details_batch(self):
        listing_hashes = [
            "407420-Gabe Newell Simulator Booster Pack",
            "443380-Tokyo Babel Booster Pack",
            "15700-Oddworld: Abe's Oddysee Booster Pack",
        ]

        all_listing_details = market_listing.get_listing_details_batch(listing_hashes)

        self.assertEqual(len(all_listing_details), len(listing_hashes))

    def test_main(self):
        self.assertTrue(market_listing.main())


class TestParsingUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(parsing_utils.main())


class TestSackOfGemsMethods(unittest.TestCase):

    def test_download_sack_of_gems_price(self):
        sack_of_gems_price = sack_of_gems.download_sack_of_gems_price()

        self.assertGreater(sack_of_gems_price, 0)

    def test_load_sack_of_gems_price(self):
        sack_of_gems_price = sack_of_gems.load_sack_of_gems_price()

        self.assertGreater(sack_of_gems_price, 0)


class TestMarketSearchMethods(unittest.TestCase):

    def test_download_all_listings(self):
        self.assertTrue(market_search.download_all_listings())


class TestMarketUtilsMethods(unittest.TestCase):

    def test_load_aggregated_badge_data(self):
        aggregated_badge_data = market_utils.load_aggregated_badge_data()

        self.assertGreater(len(aggregated_badge_data), 0)


class TestMarketArbitrageMethods(unittest.TestCase):

    def test_apply_workflow(self):
        self.assertTrue(market_arbitrage.apply_workflow(retrieve_market_orders_from_scratch=False))


class TestMarketOrderMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(market_order.main())


class TestUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(utils.main())


class TestTransactionFeeMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(transaction_fee.main())


if __name__ == '__main__':
    unittest.main()
