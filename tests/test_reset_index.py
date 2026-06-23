from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError

from src.data_pipeline.reset_index import (
    delete_index_if_present,
    wait_until_index_is_absent,
)


def test_delete_index_if_present_requests_delete():
    index_client = MagicMock()

    index_was_present = delete_index_if_present(index_client, "farsight-regulations")

    assert index_was_present is True
    index_client.delete_index.assert_called_once_with("farsight-regulations")


def test_delete_index_if_present_treats_missing_index_as_done():
    index_client = MagicMock()
    index_client.delete_index.side_effect = ResourceNotFoundError("not found")

    index_was_present = delete_index_if_present(index_client, "farsight-regulations")

    assert index_was_present is False


def test_wait_until_index_is_absent_returns_when_get_index_404s():
    index_client = MagicMock()
    index_client.get_index.side_effect = [object(), ResourceNotFoundError("not found")]

    with patch("src.data_pipeline.reset_index.time.sleep") as sleep:
        wait_until_index_is_absent(
            index_client,
            "farsight-regulations",
            checks=3,
            sleep_seconds=0,
        )

    assert index_client.get_index.call_count == 2
    sleep.assert_called_once_with(0)


def test_wait_until_index_is_absent_times_out_when_index_remains():
    index_client = MagicMock()
    index_client.get_index.return_value = object()

    with (
        patch("src.data_pipeline.reset_index.time.sleep"),
        pytest.raises(TimeoutError),
    ):
        wait_until_index_is_absent(
            index_client,
            "farsight-regulations",
            checks=2,
            sleep_seconds=0,
        )
