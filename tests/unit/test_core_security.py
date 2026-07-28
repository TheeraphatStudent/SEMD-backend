from __future__ import annotations

import unittest

from core.security import check_url_safety


class UrlSafetyTests(unittest.TestCase):
    def test_accepts_normal_public_url(self):
        result = check_url_safety('https://example.com/path?query=1')
        self.assertTrue(result.is_safe)

    def test_accepts_http_scheme(self):
        result = check_url_safety('http://example.com')
        self.assertTrue(result.is_safe)

    def test_rejects_unsupported_scheme(self):
        for url in ('javascript:alert(1)', 'file:///etc/passwd', 'ftp://example.com', 'data:text/html,x'):
            with self.subTest(url=url):
                self.assertFalse(check_url_safety(url).is_safe)

    def test_rejects_loopback(self):
        for url in ('http://127.0.0.1/', 'http://127.0.0.1:8080/admin', 'http://[::1]/'):
            with self.subTest(url=url):
                self.assertFalse(check_url_safety(url).is_safe)

    def test_rejects_localhost_hostname(self):
        self.assertFalse(check_url_safety('http://localhost/').is_safe)

    def test_rejects_private_ipv4_ranges(self):
        for url in ('http://10.0.0.1/', 'http://172.16.0.1/', 'http://192.168.1.1/'):
            with self.subTest(url=url):
                self.assertFalse(check_url_safety(url).is_safe)

    def test_rejects_link_local(self):
        self.assertFalse(check_url_safety('http://169.254.1.1/').is_safe)

    def test_rejects_cloud_metadata_endpoint(self):
        self.assertFalse(check_url_safety('http://169.254.169.254/latest/meta-data/').is_safe)

    def test_rejects_carrier_grade_nat(self):
        self.assertFalse(check_url_safety('http://100.64.0.1/').is_safe)

    def test_rejects_embedded_credentials(self):
        self.assertFalse(check_url_safety('http://user:pass@example.com/').is_safe)

    def test_rejects_numeric_encoded_host(self):
        for url in ('http://2130706433/', 'http://0x7f000001/', 'http://017700000001/'):
            with self.subTest(url=url):
                self.assertFalse(check_url_safety(url).is_safe)

    def test_rejects_empty_or_missing_host(self):
        for url in ('', 'http://', 'not-a-url'):
            with self.subTest(url=url):
                self.assertFalse(check_url_safety(url).is_safe)

    def test_rejects_private_ipv6(self):
        self.assertFalse(check_url_safety('http://[fd00::1]/').is_safe)


if __name__ == '__main__':
    unittest.main()
