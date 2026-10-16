"""Original teaching fixture, NOT a production OIDC client.

Network exchange and cryptographic validation are delegated to an adapter.
Tests use a fake adapter: no signatures, IdP, browser or cookies are tested.
"""
from dataclasses import dataclass
from typing import Protocol
import base64
import hashlib
import secrets
from urllib.parse import urlencode


@dataclass(frozen=True)
class Config:
    issuer: str = "https://identity.example.test"
    authorization_endpoint: str = "https://identity.example.test/authorize"
    client_id: str = "teaching-client"
    redirect_uri: str = "https://app.example.test/callback"


@dataclass(frozen=True)
class Identity:
    issuer: str
    subject: str


class OidcAdapter(Protocol):
    def exchange_and_validate(self, code: str, verifier: str,
                              nonce: str, config: Config) -> Identity:
        """Exchange code with PKCE; verify signature, issuer, audience, expiry,
        nonce and protocol requirements using a maintained OIDC library.
        Raise on failure. Returning decoded but unverified claims violates
        this contract. This fixture does NOT implement the adapter.
        """
        ...


class LoginFlow:
    def __init__(self, adapter: OidcAdapter, config: Config = Config()):
        self.adapter = adapter
        self.config = config

    def begin(self, browser_session: dict) -> str:
        # Caller must provide a server-side, browser-bound session.
        state, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(3))
        browser_session["pending"] = (state, nonce, verifier)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        return self.config.authorization_endpoint + "?" + urlencode({
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": "openid",
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })

    def callback(self, browser_session: dict, code: str, state: str) -> Identity:
        pending = browser_session.pop("pending", None)
        if pending is None or not secrets.compare_digest(pending[0], state):
            raise ValueError("invalid or consumed login state")
        if not code:
            raise ValueError("missing authorization code")
        identity = self.adapter.exchange_and_validate(
            code, pending[2], pending[1], self.config
        )
        if identity.issuer != self.config.issuer or not identity.subject:
            raise ValueError("invalid identity returned by adapter")
        # A real HTTP integration must rotate the session identifier here.
        browser_session["user"] = (identity.issuer, identity.subject)
        return identity
