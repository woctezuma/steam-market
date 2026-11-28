import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import responses

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

REPO_ROOT = Path(__file__).resolve().parent

MOCK_LISTING_HTML = """<html><body>
<script>
var g_rgAssets = {"753":{"6":{"123":{"owner_actions":[{"link":"javascript:GetGooValue( '6', '123', 753, 3, 1 )","name":"Turn into Gems..."}]}}}};
var g_rgListingInfo = {"marketable":1};
Market_LoadOrderSpread( 123456789 );
</script>
</body></html>
"""

MOCK_MARKET_ORDER_DATA = {
    "success": 1,
    "sell_order_graph": [[0.25, 10]],
    "buy_order_graph": [[0.2, 100]],
    "highest_buy_order": "20",
    "lowest_sell_order": "25",
}

MOCK_SEARCH_RESULTS = {"success": 1, "total_count": 0, "results": []}

DUMMY_COOKIE = {
    "browserid": "dummy_browserid",
    "sessionid": "dummy_sessionid",
    "steamDidLoginRefresh": "dummy_steamDidLoginRefresh",
    "steamLoginSecure": "dummy_steamLoginSecure",
}

TEST_STATE: dict[str, str] = {}

requests_mock = responses.RequestsMock(assert_all_requests_are_fired=False)
patchers: list[Any] = []


def setUpModule() -> None:
    # Run the whole test suite offline: mock every Steam endpoint, and redirect
    # data files (including the cookie file) to a temporary copy of data/.
    tmp_dir = tempfile.mkdtemp(prefix="steam-market-tests-")
    TEST_STATE["tmp_dir"] = tmp_dir

    data_dir = str(Path(tmp_dir) / "data") + "/"
    shutil.copytree(REPO_ROOT / "data", Path(tmp_dir) / "data")

    cookie_file = Path(tmp_dir) / "personal_info.json"
    cookie_file.write_text(json.dumps(DUMMY_COOKIE), encoding="utf8")

    requests_mock.start()
    requests_mock.add(
        responses.GET,
        re.compile(r"https://steamcommunity\.com/market/listings/\d+/.*"),
        body=MOCK_LISTING_HTML,
        status=200,
        content_type="text/html",
    )
    requests_mock.add(
        responses.GET,
        "https://steamcommunity.com/market/itemordershistogram",
        json=MOCK_MARKET_ORDER_DATA,
        status=200,
    )
    requests_mock.add(
        responses.GET,
        "https://steamcommunity.com/market/search/render/",
        json=MOCK_SEARCH_RESULTS,
        status=200,
    )
    requests_mock.add(responses.GET, "https://steamcommunity.com/", status=200)

    patchers.extend(
        mock.patch(target, return_value=data_dir)
        for target in (
            "src.utils.get_data_folder",
            "src.inventory_utils.get_data_folder",
        )
    )
    patchers.append(
        mock.patch(
            "src.personal_info.get_steam_cookie_file_name",
            return_value=str(cookie_file),
        ),
    )
    patchers.append(mock.patch("time.sleep"))

    for patcher in patchers:
        patcher.start()


def tearDownModule() -> None:
    for patcher in patchers:
        patcher.stop()
    patchers.clear()

    requests_mock.stop()
    requests_mock.reset()

    shutil.rmtree(TEST_STATE["tmp_dir"], ignore_errors=True)


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
        flag = market_arbitrage.apply_workflow(
            retrieve_listings_from_scratch=False,
            retrieve_market_orders_online=False,
        )

        assert flag


class TestMarketOrderMethods(unittest.TestCase):
    @staticmethod
    def test_main() -> None:
        assert market_order.main() is True


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
