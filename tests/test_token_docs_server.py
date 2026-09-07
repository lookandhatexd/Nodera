import os
from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from http.server import ThreadingHTTPServer

from Nodera import SiteHandler
from site_settings import save_site_settings


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class TokenDocsServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = TemporaryDirectory()
        cls.original_db_path = os.environ.get("AGEN_VORA_DB_PATH")
        cls.original_admin_password = os.environ.get("AGEN_VORA_ADMIN_PASSWORD")
        os.environ["AGEN_VORA_DB_PATH"] = str(Path(cls.database.name) / "site.sqlite3")
        os.environ["AGEN_VORA_ADMIN_PASSWORD"] = "test-password"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), SiteHandler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        if cls.original_db_path is None:
            os.environ.pop("AGEN_VORA_DB_PATH", None)
        else:
            os.environ["AGEN_VORA_DB_PATH"] = cls.original_db_path
        if cls.original_admin_password is None:
            os.environ.pop("AGEN_VORA_ADMIN_PASSWORD", None)
        else:
            os.environ["AGEN_VORA_ADMIN_PASSWORD"] = cls.original_admin_password
        cls.database.cleanup()

    def request(self, path):
        return urlopen(f"{self.base_url}{path}")

    def admin_request(self, path, method="GET", form=None):
        credentials = b64encode(b"admin:test-password").decode("ascii")
        body = urlencode(form).encode("utf-8") if form is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Authorization": f"Basic {credentials}"},
        )
        return urlopen(request)

    def test_home_and_documentation_routes(self):
        with self.request("/") as response:
            self.assertEqual(response.status, 200)
            body = response.read()
            self.assertIn(b'href="/docs/token"', body)
            self.assertIn(b'id="homeTokenCa"', body)
            self.assertIn(b'>CA</p>', body)
            self.assertIn(b'Contract Address to be announced.', body)
            self.assertIn(b'/assets/token-docs/home-token-ca.mjs', body)
            self.assertIn(b'"contractAddress":""', body)
            self.assertIn(b'"contractAddressEnabled":false', body)
            self.assertIn(b'"twitterUrl":"https://x.com/agenvora"', body)
            decoded = body.decode("utf-8")
            self.assertLess(decoded.index('href="#protocol">Protocol'), decoded.index('href="#economy">$AGNV'))
            self.assertEqual(body.count(b'class="provider-icon"'), 5)
            for icon_id in (b"logo-openai", b"logo-anthropic", b"logo-gemini", b"icon-open-models", b"icon-custom-agents"):
                self.assertIn(b'href="#' + icon_id + b'"', body)
        with self.request("/docs/token") as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("Agenvora Documentation", body)
            self.assertIn("Official $AGNV contract details and verification guidance", body)
            self.assertIn(">Token details<", body)
            self.assertIn(">Name<", body)
            self.assertIn(">Symbol<", body)
            self.assertNotIn("Token overview", body)
            self.assertNotIn("Configured name", body)
            self.assertNotIn("Configured symbol", body)
            self.assertNotIn("Address source", body)
            self.assertIn('"contractEndpoint":""', body)
            self.assertIn('href="https://x.com/agenvora"', body)

    def test_trailing_slash_redirects_to_canonical_route(self):
        opener = build_opener(NoRedirect)
        with self.assertRaises(HTTPError) as caught:
            opener.open(Request(f"{self.base_url}/docs/token/"))
        try:
            self.assertEqual(caught.exception.code, 308)
            self.assertEqual(caught.exception.headers["Location"], "/docs/token")
        finally:
            caught.exception.close()

    def test_static_assets_are_strictly_mapped(self):
        with self.request("/assets/token-docs/token-contract.validation.mjs") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), "text/javascript")
            self.assertIn(b"validateTokenContractResponse", response.read())
        with self.request("/assets/token-docs/home-token-ca.mjs") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), "text/javascript")
            self.assertIn(b"HomeTokenContractAddress", response.read())
        with self.assertRaises(HTTPError) as caught:
            self.request("/assets/token-docs/../config.py")
        try:
            self.assertEqual(caught.exception.code, 404)
        finally:
            caught.exception.close()

    def test_documentation_security_and_cache_headers(self):
        with self.request("/docs/token") as response:
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
            self.assertEqual(response.headers["Permissions-Policy"], "clipboard-write=(self)")

    def test_token_docs_uses_database_contract_settings(self):
        original = os.environ.get("TOKEN_CONTRACT_ENDPOINT")
        os.environ["TOKEN_CONTRACT_ENDPOINT"] = "https://contracts.example.test/token?name=</script>"
        try:
            with self.request("/docs/token") as response:
                body = response.read().decode("utf-8")
                self.assertIn('"contractEndpoint":""', body)
                self.assertNotIn("contracts.example.test", body)
            with self.request("/") as response:
                body = response.read().decode("utf-8")
                self.assertNotIn("contracts.example.test", body)
        finally:
            if original is None:
                os.environ.pop("TOKEN_CONTRACT_ENDPOINT", None)
            else:
                os.environ["TOKEN_CONTRACT_ENDPOINT"] = original

    def test_no_production_contract_address_is_hardcoded(self):
        project_root = Path(__file__).resolve().parents[1]
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (project_root / "token_docs").rglob("*")
            if path.is_file() and path.suffix in {".py", ".mjs", ".css", ".d.ts"}
        )
        self.assertNotRegex(source, r"0x[a-fA-F0-9]{40}")

    def test_admin_requires_auth_and_persists_public_settings(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/admin")
        self.assertEqual(caught.exception.code, 401)
        caught.exception.close()

        with self.admin_request("/admin") as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"Site settings", response.read())

        address = "11111111111111111111111111111111"
        with self.admin_request(
            "/admin",
            method="POST",
            form={
                "contract_address": address,
                "contract_address_enabled": "on",
                "twitter_url": "https://x.com/launch",
            },
        ) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"Settings saved.", response.read())

        with self.request("/") as response:
            body = response.read()
            self.assertIn(address.encode("ascii"), body)
            self.assertIn(b'"contractAddressEnabled":true', body)
            self.assertIn(b'https://x.com/launch', body)

        with self.request("/docs/token") as response:
            body = response.read().decode("utf-8")
            self.assertIn('"contractEndpoint":"/api/contract"', body)
        with self.request("/api/contract") as response:
            self.assertEqual(response.status, 200)
            self.assertIn(address, response.read().decode("utf-8"))

        save_site_settings("", False, "https://x.com/agenvora")


if __name__ == "__main__":
    unittest.main()
