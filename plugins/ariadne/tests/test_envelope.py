"""The DSSE envelope: the PAE bytes, both base64 alphabets, and the rule that
a payload is never re-serialised before it is checked."""

import base64
import hashlib
import json
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, safejson, statement  # noqa: E402

DIGEST = hashlib.sha256(b"a").hexdigest()
TYPE = "https://ariadne.wildcat.finance/example/v1"

STATEMENT = {
    "_type": statement.STATEMENT_TYPE,
    # The runs of ?  and > are deliberate. Base64 of ordinary ASCII never
    # reaches index 62 or 63, so a payload of plain JSON encodes identically
    # under both alphabets and would make the alphabet tests below vacuous. Six
    # consecutive 0x3f bytes guarantee a '/' and six 0x3e bytes guarantee a '+',
    # whatever the alignment.
    "subject": [{"name": "a??????>>>>>>b", "digest": {"sha256": DIGEST}}],
    "predicateType": TYPE,
    "predicate": {"claims": []},
}


def payload_bytes():
    """Statement bytes whose two base64 encodings differ."""
    data = json.dumps(STATEMENT).encode("utf-8")
    assert base64.b64encode(data) != base64.urlsafe_b64encode(data)
    return data


class PaeTests(unittest.TestCase):
    def test_pae_matches_a_byte_string_computed_by_hand(self):
        self.assertEqual(
            envelope.pae("application/vnd.in-toto+json", b'{"a":1}'),
            b'DSSEv1 28 application/vnd.in-toto+json 7 {"a":1}',
        )

    def test_lengths_count_bytes_rather_than_characters(self):
        body = "é".encode("utf-8")
        self.assertEqual(len(body), 2)
        self.assertIn(b" 2 ", envelope.pae("t:x", body))

    def test_an_empty_body_still_carries_its_length(self):
        self.assertEqual(envelope.pae("t:x", b""), b"DSSEv1 3 t:x 0 ")

    def test_a_body_that_is_not_bytes_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError):
            envelope.pae("t:x", "a string")


class Base64Tests(unittest.TestCase):
    def test_both_alphabets_decode_to_the_same_bytes(self):
        data = b"\xfb\xff\xfe\x00"
        standard = base64.b64encode(data).decode("ascii")
        urlsafe = base64.urlsafe_b64encode(data).decode("ascii")
        self.assertNotEqual(standard, urlsafe)
        self.assertEqual(envelope.decode_base64(standard), data)
        self.assertEqual(envelope.decode_base64(urlsafe), data)

    def test_a_string_mixing_the_alphabets_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError) as caught:
            envelope.decode_base64("+_==")
        self.assertIn("mixes", str(caught.exception))

    def test_unpadded_input_is_accepted(self):
        data = b"\xfb\xff\xfe\x00"
        self.assertEqual(
            envelope.decode_base64(base64.b64encode(data).decode("ascii").rstrip("=")),
            data,
        )

    def test_a_non_base64_string_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError):
            envelope.decode_base64("not base64 at all!!")

    def test_a_non_string_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError):
            envelope.decode_base64(17)


class EnvelopeTests(unittest.TestCase):
    def test_payload_bytes_survive_a_read_unchanged(self):
        data = payload_bytes()
        document = envelope.read(
            json.dumps(
                {
                    "payloadType": envelope.PAYLOAD_TYPE,
                    "payload": base64.b64encode(data).decode("ascii"),
                    "signatures": [],
                }
            ).encode("utf-8")
        )
        self.assertEqual(document.payload, data)

    def test_a_urlsafe_payload_reads_to_the_same_bytes_as_a_standard_one(self):
        data = payload_bytes()
        read = []
        for encoded in (
            base64.b64encode(data).decode("ascii"),
            base64.urlsafe_b64encode(data).decode("ascii"),
        ):
            document = envelope.read(
                json.dumps(
                    {"payloadType": envelope.PAYLOAD_TYPE, "payload": encoded}
                ).encode("utf-8")
            )
            read.append(document.payload)
        self.assertEqual(read[0], data)
        self.assertEqual(read[0], read[1])

    def test_signing_input_is_pae_over_the_payload_as_received(self):
        data = payload_bytes()
        found = envelope.Envelope(data)
        self.assertEqual(
            found.signing_input(), envelope.pae(envelope.PAYLOAD_TYPE, data)
        )

    def test_a_missing_payload_type_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError) as caught:
            envelope.Envelope.from_dict({"payload": "e30="})
        self.assertIn("payloadType", str(caught.exception))

    def test_a_signature_without_a_sig_field_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError) as caught:
            envelope.Envelope.from_dict(
                {
                    "payload": "e30=",
                    "payloadType": envelope.PAYLOAD_TYPE,
                    "signatures": [{"keyid": "k"}],
                }
            )
        self.assertIn("no sig", str(caught.exception))

    def test_signatures_must_be_an_array(self):
        with self.assertRaises(envelope.EnvelopeError):
            envelope.Envelope.from_dict(
                {
                    "payload": "e30=",
                    "payloadType": envelope.PAYLOAD_TYPE,
                    "signatures": {"sig": "AA=="},
                }
            )

    def test_an_envelope_field_dsse_does_not_define_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError) as caught:
            envelope.Envelope.from_dict(
                {
                    "payload": "e30=",
                    "payloadType": envelope.PAYLOAD_TYPE,
                    "verificationMaterial": {"trust": "me"},
                }
            )
        self.assertIn("verificationMaterial", str(caught.exception))

    def test_a_signature_field_dsse_does_not_define_is_refused(self):
        with self.assertRaises(envelope.EnvelopeError) as caught:
            envelope.Envelope.from_dict(
                {
                    "payload": "e30=",
                    "payloadType": envelope.PAYLOAD_TYPE,
                    "signatures": [{"sig": "AA==", "cert": "-----BEGIN"}],
                }
            )
        self.assertIn("cert", str(caught.exception))

    def test_wrap_writes_an_unsigned_envelope_that_reads_back(self):
        data = payload_bytes()
        written = envelope.wrap(data).to_json()
        document = envelope.read(written.encode("utf-8"))
        self.assertEqual(document.payload, data)
        self.assertFalse(document.signed)


class DocumentTests(unittest.TestCase):
    def test_a_bare_statement_reads_as_unsigned(self):
        document = envelope.read(json.dumps(STATEMENT).encode("utf-8"))
        self.assertIsNone(document.envelope)
        self.assertFalse(document.signed)
        self.assertIn("unsigned", document.signature_state)

    def test_an_envelope_with_no_signatures_reads_as_unsigned(self):
        document = envelope.read(envelope.wrap(payload_bytes()).to_json())
        self.assertIn("unsigned", document.signature_state)

    def test_a_signed_envelope_reports_signatures_present_and_unchecked(self):
        found = envelope.Envelope(
            payload_bytes(),
            signatures=[envelope.Signature(base64.b64encode(b"nonsense").decode())],
        )
        document = envelope.read(found.to_json())
        self.assertTrue(document.signed)
        self.assertIn("not checked", document.signature_state)

    def test_no_signature_state_claims_an_author_or_a_verification(self):
        """Gate 7. The tool checks no signature, so no wording may imply it has."""
        states = [
            envelope.Document(None, b"", None).signature_state,
            envelope.Document(None, b"", envelope.Envelope(b"{}")).signature_state,
            envelope.Document(
                None,
                b"",
                envelope.Envelope(b"{}", signatures=[envelope.Signature("AA==")]),
            ).signature_state,
        ]
        for state in states:
            lowered = state.lower()
            for word in ("verified", "authentic", "trusted", "signed by"):
                self.assertNotIn(word, lowered, state)

    def test_an_envelope_missing_its_payload_type_is_told_so(self):
        """Dispatch is on `_type`, so a broken envelope gets an envelope's
        message rather than being read as a statement with no `_type`."""
        with self.assertRaises(envelope.EnvelopeError) as caught:
            envelope.read(json.dumps({"payload": "e30="}).encode("utf-8"))
        self.assertIn("payloadType", str(caught.exception))

    def test_nesting_deep_enough_to_exhaust_the_stack_is_a_refusal(self):
        depth = 200000
        data = ('{"a":' * depth + "1" + "}" * depth).encode("utf-8")
        with self.assertRaises(safejson.InputError) as caught:
            envelope.read(data)
        self.assertIn("nested deeper", str(caught.exception))

    def test_a_deeply_nested_payload_is_a_refusal_too(self):
        depth = 200000
        payload = ('{"a":' * depth + "1" + "}" * depth).encode("utf-8")
        wrapped = envelope.wrap(payload).to_json()
        with self.assertRaises(safejson.InputError) as caught:
            envelope.read(wrapped)
        self.assertIn("nested deeper", str(caught.exception))

    def test_a_document_that_is_neither_shape_says_so(self):
        with self.assertRaises(envelope.EnvelopeError) as caught:
            envelope.read(json.dumps({"subject": []}).encode("utf-8"))
        self.assertIn("neither", str(caught.exception))

    def test_junk_is_refused_rather_than_guessed_at(self):
        with self.assertRaises(envelope.EnvelopeError):
            envelope.read(b"[]")
        with self.assertRaises(safejson.InputError):
            envelope.read(b"{oh no")


if __name__ == "__main__":
    unittest.main()
