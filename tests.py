import unittest

import market_arbitrage
from src import (
    batch_create_packs,
    creation_time_utils,
    drop_rate_estimates,
    market_listing,
    market_order,
    market_search,
    market_utils,
    parsing_utils,
    sack_of_gems,
    transaction_fee,
    utils,
)


class TestMarketListingMethods(unittest.TestCase):
    @staticmethod
    def test_get_listing_details_batch() -> None:
        listing_hashes = [
            "407420-Gabe Newell Simulator Booster Pack",
            "443380-Tokyo Babel Booster Pack",
            "15700-Oddworld: Abe's Oddysee Booster Pack",
        ]

        all_listing_details = market_listing.get_listing_details_batch(
            listing_hashes,
            save_to_disk=False,
        )

        assert len(all_listing_details) == len(listing_hashes)

    @staticmethod
    def test_main() -> None:
        assert market_listing.main() is True


class TestParsingUtilsMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        assert parsing_utils.main() is True


class TestCreationTimeUtilsMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        assert creation_time_utils.main() is True


class TestSackOfGemsMethods(unittest.TestCase):
    @staticmethod
    def test_download_sack_of_gems_price() -> None:
        sack_of_gems_price = sack_of_gems.download_sack_of_gems_price()

        assert sack_of_gems_price > 0

    @staticmethod
    def test_load_sack_of_gems_price() -> None:
        sack_of_gems_price = sack_of_gems.load_sack_of_gems_price()

        assert sack_of_gems_price > 0


class TestMarketSearchMethods(unittest.TestCase):
    @staticmethod
    def test_download_all_listings() -> None:
        assert market_search.download_all_listings() is True


class TestMarketUtilsMethods(unittest.TestCase):
    @staticmethod
    def test_load_aggregated_badge_data() -> None:
        aggregated_badge_data = market_utils.load_aggregated_badge_data()

        assert aggregated_badge_data


class TestMarketArbitrageMethods(unittest.TestCase):
    @staticmethod
    def test_apply_workflow() -> None:
        try:
            flag = market_arbitrage.apply_workflow(
                retrieve_listings_from_scratch=False,
                retrieve_market_orders_online=False,
            )
        except KeyError:
            # The steamLoginSecure cookie cannot be made public for the test.
            flag = True

        assert flag


class TestMarketOrderMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        try:
            flag = market_order.main()
        except KeyError:
            # The steamLoginSecure cookie cannot be made public for the test.
            flag = True

        assert flag


class TestUtilsMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        assert utils.main() is True


class TestTransactionFeeMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        assert transaction_fee.main() is True


class TestBatchCreatePacksMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        assert batch_create_packs.main(is_a_simulation=True) is True


class TestDropRateEstimatesMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        assert drop_rate_estimates.main() is True


if __name__ == "__main__":
    unittest.main()
