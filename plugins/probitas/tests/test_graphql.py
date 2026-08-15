"""The GraphQL client, with the network stubbed out.

The case that matters is a subgraph answering HTTP 200 with an `errors` block.
A client that only checks the status code reads that as a well-formed reply
with no markets in it, and reports a borrower with a delinquency history as a
borrower with a clean one.
"""

import io
import json
import unittest
import urllib.error
from unittest import mock

from . import support  # noqa: F401

from probitas_lib import graphql  # noqa: E402
from probitas_lib.graphql import GraphQLError, post  # noqa: E402

ENDPOINT = "https://example.com/subgraph"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def answering(payload):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return mock.patch.object(
        graphql._OPENER, "open", return_value=FakeResponse(body)
    )


class TestPost(unittest.TestCase):
    def test_a_good_answer_returns_its_data_block(self):
        with answering({"data": {"markets": []}}):
            self.assertEqual(post(ENDPOINT, "{ markets { id } }"), {"markets": []})

    def test_an_errors_payload_raises_rather_than_reading_as_empty(self):
        with answering({"data": None, "errors": [{"message": "no field `amount`"}]}):
            with self.assertRaises(GraphQLError) as caught:
                post(ENDPOINT, "{ markets { amount } }")
        self.assertIn("no field", str(caught.exception))

    def test_a_missing_data_block_raises(self):
        with answering({}):
            with self.assertRaises(GraphQLError):
                post(ENDPOINT, "{ markets { id } }")

    def test_something_that_is_not_json_raises(self):
        with answering(b"<html>502 Bad Gateway</html>"):
            with self.assertRaises(GraphQLError):
                post(ENDPOINT, "{ markets { id } }")

    def test_a_json_array_is_not_a_response(self):
        with answering([{"data": {}}]):
            with self.assertRaises(GraphQLError):
                post(ENDPOINT, "{ markets { id } }")

    def test_an_http_error_raises_with_its_code(self):
        # A real file object rather than None: on Python 3.9 an HTTPError
        # built with no fp raises KeyError when closed, and leaving it unclosed
        # emits a ResourceWarning instead.
        error = urllib.error.HTTPError(
            ENDPOINT, 503, "unavailable", {}, io.BytesIO(b"")
        )
        self.addCleanup(error.close)
        with mock.patch.object(graphql._OPENER, "open", side_effect=error):
            with self.assertRaises(GraphQLError) as caught:
                post(ENDPOINT, "{ markets { id } }")
        self.assertIn("503", str(caught.exception))

    def test_an_unreachable_host_raises(self):
        with mock.patch.object(
            graphql._OPENER,
            "open",
            side_effect=urllib.error.URLError("name resolution failed"),
        ):
            with self.assertRaises(GraphQLError):
                post(ENDPOINT, "{ markets { id } }")

    def test_an_oversized_response_raises(self):
        oversized = b"x" * (graphql.MAX_RESPONSE_BYTES + 1)
        with answering(oversized):
            with self.assertRaises(GraphQLError) as caught:
                post(ENDPOINT, "{ markets { id } }")
        self.assertIn("over", str(caught.exception))

    def test_a_redirect_is_refused_rather_than_followed(self):
        """An https endpoint must not be able to hand the client to http."""
        handler = graphql._NoRedirects()
        request = mock.Mock(full_url=ENDPOINT)
        with self.assertRaises(GraphQLError) as caught:
            handler.redirect_request(
                request, None, 302, "Found", {}, "http://evil.example/subgraph"
            )
        self.assertIn("refusing to follow", str(caught.exception))

    def test_a_plaintext_endpoint_is_refused(self):
        with self.assertRaises(GraphQLError):
            post("http://example.com/subgraph", "{ markets { id } }")


if __name__ == "__main__":
    unittest.main()
