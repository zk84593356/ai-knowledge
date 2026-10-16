"""Tests of the ORIGINAL demo orchestration, not cryptographic OIDC tests."""
import base64
import hashlib
from pathlib import Path
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).parent / "fixtures/oidc-demo"))
from login import Config, Identity, LoginFlow


class FakeAdapter:
    def __init__(self, failure=False, issuer=None, subject="demo-user"):
        self.calls = []
        self.failure = failure
        self.issuer = issuer
        self.subject = subject

    def exchange_and_validate(self, code, verifier, nonce, config):
        self.calls.append((code, verifier, nonce, config))
        if self.failure:
            raise ValueError("simulated validation rejection")
        return Identity(self.issuer or config.issuer, self.subject)


class OidcDemoTests(unittest.TestCase):
    def setUp(self):
        self.adapter = FakeAdapter()
        self.flow = LoginFlow(self.adapter)
        self.session = {}
        self.params = parse_qs(urlsplit(self.flow.begin(self.session)).query)
        self.pending = self.session["pending"]

    def test_authorization_request_binds_nonce_state_and_s256(self):
        state, nonce, verifier = self.pending
        self.assertEqual(self.params["scope"], ["openid"])
        self.assertEqual(self.params["response_type"], ["code"])
        self.assertEqual(self.params["state"], [state])
        self.assertEqual(self.params["nonce"], [nonce])
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(self.params["code_challenge"], [challenge])
        self.assertEqual(self.params["code_challenge_method"], ["S256"])
        self.assertNotIn(verifier, str(self.params))

    def test_success_passes_original_binding_and_sets_identity(self):
        identity = self.flow.callback(self.session, "demo-code", self.pending[0])
        self.assertEqual(self.adapter.calls[0][:3], ("demo-code", self.pending[2], self.pending[1]))
        self.assertEqual(self.session["user"], (identity.issuer, identity.subject))
        self.assertNotIn("pending", self.session)

    def test_wrong_state_stops_before_adapter(self):
        with self.assertRaises(ValueError):
            self.flow.callback(self.session, "demo-code", "wrong-state")
        self.assertFalse(self.adapter.calls)
        self.assertNotIn("user", self.session)

    def test_second_browser_cannot_use_first_browser_state(self):
        other = {}
        self.flow.begin(other)
        with self.assertRaises(ValueError):
            self.flow.callback(other, "demo-code", self.pending[0])
        self.assertFalse(self.adapter.calls)

    def test_callback_cannot_be_replayed(self):
        self.flow.callback(self.session, "demo-code", self.pending[0])
        with self.assertRaises(ValueError):
            self.flow.callback(self.session, "demo-code", self.pending[0])
        self.assertEqual(len(self.adapter.calls), 1)

    def test_empty_code_stops_before_adapter(self):
        with self.assertRaises(ValueError):
            self.flow.callback(self.session, "", self.pending[0])
        self.assertFalse(self.adapter.calls)

    def test_adapter_rejection_does_not_create_user(self):
        self.adapter.failure = True
        with self.assertRaises(ValueError):
            self.flow.callback(self.session, "demo-code", self.pending[0])
        self.assertNotIn("user", self.session)

    def test_wrong_issuer_or_empty_subject_rejected(self):
        for adapter in (FakeAdapter(issuer="https://other.example.test"), FakeAdapter(subject="")):
            with self.subTest(adapter=adapter):
                flow, session = LoginFlow(adapter), {}
                flow.begin(session)
                state = session["pending"][0]
                with self.assertRaises(ValueError):
                    flow.callback(session, "demo-code", state)
                self.assertNotIn("user", session)
