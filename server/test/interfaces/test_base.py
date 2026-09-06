import unittest
from typing import Optional
from unittest import mock

from app.interfaces.base import BaseWSGIApp
from werkzeug.exceptions import BadRequest


class TestPagination(unittest.TestCase):
    """
    Testing of the shared pagination strategy, shared by multiple endpoints.
    """

    __test__ = True

    @staticmethod
    def _build_request(limit: Optional[str] = None, cursor: Optional[str] = None):
        request = mock.Mock()
        def mock_get(key, default = None):
            if key == "limit":
                return limit or default
            elif key == "cursor":
                return cursor or default
            else:
                return default
        request.args.get.side_effect = mock_get
        return request

    def test_pagination_on_empty_set(self):
        page, metadata = BaseWSGIApp._get_slice(self._build_request('3'), [])
        self.assertEqual(0, len(list(page)))
        if not metadata:
            self.fail("no metadata")
        self.assertIsNone(metadata.cursor)

    def test_pagination_with_one_page(self):
        page, metadata = BaseWSGIApp._get_slice(self._build_request("3"), [1, 2])
        self.assertEqual([1, 2], list(page))
        if not metadata:
            self.fail("no metadata")
        self.assertIsNone(metadata.cursor)

    def test_pagination_walks_all_items(self):
        all_objects = [i for i in range(20)]

        pages: list[list] = []
        cursor = None
        for _ in range(1000):
            page, metadata = BaseWSGIApp._get_slice(self._build_request('6', cursor), all_objects)
            result = list(page)
            pages.append(result)
            if not metadata:
                self.fail("no paging_metadata returned")
            cursor = metadata.cursor
            if cursor is None:
                break
            if len(pages) > 4 or len(pages) < 1:
                self.fail("cursor never signalled end")

        self.assertEqual([6, 6, 6, 2], [len(page) for page in pages])
        seen = [i for page in pages for i in page]
        self.assertEqual(len(seen), len(set(seen)), "an item was returned on more than one page")
        self.assertEqual(set(range(20)), set(seen))

    def test_pagination_requires_positive_limit(self):
        with self.assertRaises(BadRequest):
            BaseWSGIApp._get_slice(self._build_request('-1'), [])

    def test_pagination_requires_positive_cursor(self):
        with self.assertRaises(BadRequest):
            BaseWSGIApp._get_slice(self._build_request('5', '-1'), [])
