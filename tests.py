import unittest

import market_listing
import market_search
import market_utils
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

    def test_get_sack_of_gems_price(self):
        sack_of_gems_price = market_listing.get_sack_of_gems_price()

        self.assertGreater(sack_of_gems_price, 0)

    def test_main(self):
        self.assertTrue(market_listing.main())


class TestMarketSearchMethods(unittest.TestCase):

    def test_download_all_listings(self):
        self.assertTrue(market_search.download_all_listings())


class TestMarketUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(market_utils.main())


class TestUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(utils.main())


if __name__ == '__main__':
    unittest.main()
