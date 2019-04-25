import unittest

import market_listing
import market_search
import market_utils
import utils


class TestMarketListingMethods(unittest.TestCase):

    def test_main(self):
        listing_hashes = [
            "407420-Gabe Newell Simulator Booster Pack",
            "443380-Tokyo Babel Booster Pack",
            "15700-Oddworld: Abe's Oddysee Booster Pack",
        ]

        all_listing_details = market_listing.get_all_listing_details(listing_hashes)

        self.assertEqual(len(all_listing_details) == len(listing_hashes))


class TestMarketSearchMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(market_search.download_all_listings())


class TestMarketUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(market_utils.main())


class TestUtilsMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(utils.main())


if __name__ == '__main__':
    unittest.main()
