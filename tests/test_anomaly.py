"""Unit tests for threat detection heuristic rules."""
import time
import unittest
from netpulse.core.parser import DissectedPacket
from netpulse.detector.rules import (
    SynFloodRule, PortScanRule, ArpSpoofRule, DnsTunnelRule,
    SuspiciousPayloadRule, shannon_entropy
)
from netpulse.detector.alerts import Severity
from netpulse.detector.anomaly_engine import AnomalyEngine


class TestAnomalyRules(unittest.TestCase):

    def test_shannon_entropy(self):
        self.assertEqual(shannon_entropy("aaaaaaa"), 0.0)
        h = shannon_entropy("dGhpcy1pcy1hLXNlY3JldC1leGZpbHRyYXRpb24")
        self.assertGreater(h, 4.0)

    def test_syn_flood_detection(self):
        rule = SynFloodRule(threshold=5, window_seconds=2.0)
        now = time.time()
        alert = None

        for i in range(5):
            pkt = DissectedPacket(
                timestamp=now + (i * 0.1),
                length=64,
                protocol="TCP",
                src_ip="10.0.0.99",
                dst_ip="10.0.0.1",
                dst_port=443,
                tcp_flags={"SYN": True, "ACK": False}
            )
            res = rule.evaluate(pkt)
            if res:
                alert = res

        self.assertIsNotNone(alert)
        self.assertEqual(alert.rule_name, "SYN Flood DoS Attack")
        self.assertEqual(alert.severity, Severity.CRITICAL)

    def test_stealth_null_scan_detection(self):
        rule = PortScanRule()
        pkt = DissectedPacket(
            timestamp=time.time(),
            length=60,
            protocol="TCP",
            src_ip="192.168.1.55",
            dst_ip="192.168.1.1",
            dst_port=80,
            tcp_flags={"SYN": False, "ACK": False, "FIN": False, "RST": False}
        )
        alert = rule.evaluate(pkt)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.rule_name, "TCP NULL Stealth Scan")
        self.assertEqual(alert.severity, Severity.HIGH)

    def test_stealth_xmas_scan_detection(self):
        rule = PortScanRule()
        pkt = DissectedPacket(
            timestamp=time.time(),
            length=60,
            protocol="TCP",
            src_ip="192.168.1.55",
            dst_ip="192.168.1.1",
            dst_port=80,
            tcp_flags={"FIN": True, "PSH": True, "URG": True, "SYN": False, "ACK": False}
        )
        alert = rule.evaluate(pkt)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.rule_name, "TCP XMAS Stealth Scan")

    def test_arp_spoof_detection(self):
        rule = ArpSpoofRule()
        now = time.time()

        pkt1 = DissectedPacket(
            timestamp=now,
            length=42,
            protocol="ARP",
            src_ip="192.168.1.1",
            src_mac="00:11:22:33:44:55",
            dst_ip="192.168.1.100"
        )
        self.assertIsNone(rule.evaluate(pkt1))

        pkt2 = DissectedPacket(
            timestamp=now + 1.0,
            length=42,
            protocol="ARP",
            src_ip="192.168.1.1",
            src_mac="de:ad:be:ef:13:37",
            dst_ip="192.168.1.100"
        )
        alert = rule.evaluate(pkt2)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.rule_name, "ARP Spoofing / Poisoning")
        self.assertEqual(alert.severity, Severity.CRITICAL)

    def test_dns_tunneling_detection(self):
        rule = DnsTunnelRule(length_threshold=40)
        pkt = DissectedPacket(
            timestamp=time.time(),
            length=120,
            protocol="DNS",
            src_ip="192.168.1.50",
            dst_ip="8.8.8.8",
            dns_query="c2VjcmV0LWRhdGEtdG9rZW4tZXhmaWx0cmF0aW9uLXByb3RvY29s.c2.net"
        )
        alert = rule.evaluate(pkt)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.rule_name, "DNS Tunneling / Exfiltration")

    def test_sqli_payload_detection(self):
        rule = SuspiciousPayloadRule()
        pkt = DissectedPacket(
            timestamp=time.time(),
            length=150,
            protocol="HTTP",
            src_ip="10.0.0.5",
            dst_ip="10.0.0.1",
            dst_port=80,
            payload_len=80,
            payload_preview="GET /users?id=1' OR '1'='1 HTTP/1.1"
        )
        alert = rule.evaluate(pkt)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.rule_name, "SQL Injection Attempt")


if __name__ == "__main__":
    unittest.main()
