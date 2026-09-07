"""Runtime configuration for the public token documentation page."""

from dataclasses import dataclass
from os import environ


TOKEN_NAME = "Agenvora"
TOKEN_SYMBOL = "$AGNV"
DEFAULT_TWITTER_URL = "https://x.com/agenvora"
DOCUMENTATION_ROUTE = "/docs/token"
CONTRACT_ENDPOINT = "[ENDPOINT_URL]"
REFRESH_INTERVAL_MS = 60_000
REQUEST_TIMEOUT_MS = 8_000


@dataclass(frozen=True)
class TokenDocsSettings:
    token_name: str = TOKEN_NAME
    token_symbol: str = TOKEN_SYMBOL
    documentation_route: str = DOCUMENTATION_ROUTE
    contract_endpoint: str = CONTRACT_ENDPOINT
    twitter_url: str = DEFAULT_TWITTER_URL
    refresh_interval_ms: int = REFRESH_INTERVAL_MS
    request_timeout_ms: int = REQUEST_TIMEOUT_MS


def load_token_docs_settings() -> TokenDocsSettings:
    """Load deploy-time endpoint configuration without embedding token data."""

    return TokenDocsSettings(
        contract_endpoint=environ.get("TOKEN_CONTRACT_ENDPOINT", CONTRACT_ENDPOINT),
        twitter_url=environ.get("AGEN_VORA_TWITTER_URL", DEFAULT_TWITTER_URL),
    )
