"""SQLite-backed public settings for the Agenvora website."""

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
from urllib.parse import urlsplit


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "site_settings.sqlite3"
DATABASE_ENVIRONMENT_VARIABLE = "AGEN_VORA_DB_PATH"
DEFAULT_TWITTER_URL = "https://x.com/agenvora"
DEFAULT_CHAIN = "Solana"
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ADMIN_PASSWORD_KEY = "admin_password_hash"
TWITTER_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}


@dataclass(frozen=True)
class PublicSiteSettings:
    contract_address: str = ""
    contract_address_enabled: bool = False
    chain: str = DEFAULT_CHAIN
    twitter_url: str = DEFAULT_TWITTER_URL
    updated_at: str = ""

    def to_public_config(self) -> dict[str, object]:
        return {
            "contractAddress": self.contract_address if self.contract_address_enabled else "",
            "contractAddressEnabled": self.contract_address_enabled,
            "contractChain": self.chain,
            "contractUpdatedAt": self.updated_at,
            "twitterUrl": self.twitter_url,
        }


def database_path() -> Path:
    configured = os.environ.get(DATABASE_ENVIRONMENT_VARIABLE)
    return Path(configured).expanduser() if configured else DEFAULT_DATABASE_PATH


def _connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)",
        ("contract_address", ""),
    )
    connection.execute(
        "INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)",
        ("contract_address_enabled", "0"),
    )
    connection.execute(
        "INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)",
        ("twitter_url", DEFAULT_TWITTER_URL),
    )
    connection.commit()
    return connection


def _read_values(connection: sqlite3.Connection) -> dict[str, str]:
    return dict(connection.execute("SELECT key, value FROM site_settings"))


def read_site_settings() -> PublicSiteSettings:
    connection = _connect()
    try:
        values = _read_values(connection)
    finally:
        connection.close()
    return PublicSiteSettings(
        contract_address=values.get("contract_address", ""),
        contract_address_enabled=values.get("contract_address_enabled", "0") == "1",
        twitter_url=values.get("twitter_url", DEFAULT_TWITTER_URL),
        updated_at=values.get("contract_updated_at", ""),
    )


def _validate_contract_address(value: str, enabled: bool) -> str:
    address = value.strip()
    if len(address) > 128:
        raise ValueError("Contract Address must be 128 characters or fewer.")
    if any(ord(character) < 32 or ord(character) == 127 for character in address):
        raise ValueError("Contract Address contains unsupported control characters.")
    if enabled and not _is_solana_address(address):
        raise ValueError("Enter a valid Solana Contract Address or turn publishing off.")
    return address


def _is_solana_address(value: str) -> bool:
    if not 32 <= len(value) <= 44 or any(character not in BASE58_ALPHABET for character in value):
        return False
    number = 0
    for character in value:
        number = number * 58 + BASE58_ALPHABET.index(character)
    decoded = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading_zeroes = len(value) - len(value.lstrip("1"))
    return len((b"\0" * leading_zeroes) + decoded) == 32


def _hash_admin_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 300_000)
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii")
    return f"pbkdf2-sha256$300000${encode(salt)}${encode(digest)}"


def set_admin_password(password: str) -> None:
    if len(password) < 12 or len(password) > 256:
        raise ValueError("Admin password must be between 12 and 256 characters.")
    connection = _connect()
    try:
        connection.execute(
            "INSERT INTO site_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (ADMIN_PASSWORD_KEY, _hash_admin_password(password)),
        )
        connection.commit()
    finally:
        connection.close()


def _admin_password_hash() -> str:
    connection = _connect()
    try:
        row = connection.execute(
            "SELECT value FROM site_settings WHERE key = ?", (ADMIN_PASSWORD_KEY,)
        ).fetchone()
    finally:
        connection.close()
    return row[0] if row else ""


def has_admin_password() -> bool:
    return bool(_admin_password_hash())


def verify_admin_password(password: str) -> bool:
    stored = _admin_password_hash()
    try:
        algorithm, iterations, encoded_salt, encoded_digest = stored.split("$", 3)
        if algorithm != "pbkdf2-sha256":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def _validate_twitter_url(value: str) -> str:
    url = value.strip()
    if not url:
        return ""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.hostname not in TWITTER_HOSTS:
        raise ValueError("Twitter URL must be an HTTPS x.com or twitter.com link.")
    return url


def save_site_settings(contract_address: str, contract_address_enabled: bool, twitter_url: str) -> PublicSiteSettings:
    address = _validate_contract_address(contract_address, contract_address_enabled)
    validated_twitter_url = _validate_twitter_url(twitter_url)
    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    values = {
        "contract_address": address,
        "contract_address_enabled": "1" if contract_address_enabled else "0",
        "twitter_url": validated_twitter_url,
        "contract_updated_at": updated_at if contract_address_enabled else "",
    }
    connection = _connect()
    try:
        connection.executemany(
            "INSERT INTO site_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            values.items(),
        )
        connection.commit()
    finally:
        connection.close()
    return read_site_settings()
