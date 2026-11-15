"""Unit tests for multi-threaded port scanner."""
import unittest
from netpulse.diagnostics.port_scanner import PortScanner, PortScanResult


class TestPortScanner(unittest.TestCase):

    def test_target_ip_resolution(self):
        scanner = PortScanner("127.0.0.1")
        self.assertEqual(scanner.target_ip, "127.0.0.1")

    def test_scan_result_serialization(self):
        res = PortScanResult(
            port=80,
            state="open",
            service="HTTP",
            banner="Apache/2.4",
            rtt_ms=1.45
        )
        d = res.to_dict()
        self.assertEqual(d["port"], 80)
        self.assertEqual(d["state"], "open")
        self.assertEqual(d["service"], "HTTP")
        self.assertEqual(d["banner"], "Apache/2.4")
        self.assertEqual(d["rtt_ms"], 1.45)

    def test_port_scanner_run(self):
        scanner = PortScanner("127.0.0.1", timeout=0.1, max_threads=10)
        rep = scanner.scan(ports=[49991, 49992])

        self.assertEqual(rep["target"], "127.0.0.1")
        self.assertEqual(rep["scanned_ports_count"], 2)
        self.assertIn("scan_duration_seconds", rep)
        self.assertIsInstance(rep["open_ports"], list)


if __name__ == "__main__":
    unittest.main()
