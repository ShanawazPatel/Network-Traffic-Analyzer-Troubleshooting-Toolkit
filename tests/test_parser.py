"""Unit tests for packet dissector and header parser."""
import unittest
from scapy.all import Ether, IP, TCP, UDP, ICMP, ARP, DNS, DNSQR, Raw
from netpulse.core.parser import PacketParser, DissectedPacket


class TestPacketParser(unittest.TestCase):

    def test_parse_tcp_packet(self):
        pkt = Ether(src="00:11:22:33:44:55", dst="aa:bb:cc:dd:ee:ff") / \
              IP(src="192.168.1.10", dst="10.0.0.1", ttl=64) / \
              TCP(sport=44321, dport=80, flags="S", seq=12345, window=65535)

        dissected = PacketParser.parse(pkt)

        self.assertEqual(dissected.protocol, "TCP")
        self.assertEqual(dissected.src_ip, "192.168.1.10")
        self.assertEqual(dissected.dst_ip, "10.0.0.1")
        self.assertEqual(dissected.src_port, 44321)
        self.assertEqual(dissected.dst_port, 80)
        self.assertEqual(dissected.ttl, 64)
        self.assertEqual(dissected.seq, 12345)
        self.assertEqual(dissected.window, 65535)
        self.assertTrue(dissected.tcp_flags["SYN"])
        self.assertFalse(dissected.tcp_flags["ACK"])
        self.assertIn("[SYN]", dissected.tcp_flags_str)

    def test_parse_dns_query(self):
        pkt = Ether() / IP(src="192.168.1.10", dst="8.8.8.8") / \
              UDP(sport=53000, dport=53) / \
              DNS(rd=1, qd=DNSQR(qname="google.com"))

        dissected = PacketParser.parse(pkt)

        self.assertEqual(dissected.protocol, "DNS")
        self.assertEqual(dissected.dns_query, "google.com")
        self.assertEqual(dissected.dns_qtype, "A")
        self.assertIn("DNS Query", dissected.summary)

    def test_parse_arp_packet(self):
        pkt = Ether() / ARP(op=2, hwsrc="00:11:22:33:44:55", psrc="192.168.1.1",
                            hwdst="aa:bb:cc:dd:ee:ff", pdst="192.168.1.100")

        dissected = PacketParser.parse(pkt)

        self.assertEqual(dissected.protocol, "ARP")
        self.assertEqual(dissected.src_ip, "192.168.1.1")
        self.assertEqual(dissected.dst_ip, "192.168.1.100")
        self.assertIn("ARP Reply", dissected.summary)

    def test_parse_http_payload(self):
        http_data = b"GET /api/v1/health HTTP/1.1\r\nHost: example.org\r\n\r\n"
        pkt = Ether() / IP(src="192.168.1.10", dst="93.184.216.34") / \
              TCP(sport=49152, dport=80, flags="PA") / Raw(load=http_data)

        dissected = PacketParser.parse(pkt)

        self.assertEqual(dissected.protocol, "HTTP")
        self.assertEqual(dissected.http_method, "GET")
        self.assertEqual(dissected.http_path, "/api/v1/health")
        self.assertEqual(dissected.http_host, "example.org")
        self.assertEqual(dissected.payload_len, len(http_data))
        self.assertIn("GET /api/v1/health", dissected.payload_preview)

    def test_to_dict_serialization(self):
        pkt = Ether() / IP(src="1.1.1.1", dst="2.2.2.2") / ICMP(type=8, code=0)
        dissected = PacketParser.parse(pkt)
        d = dissected.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d["src_ip"], "1.1.1.1")
        self.assertEqual(d["dst_ip"], "2.2.2.2")
        self.assertEqual(d["protocol"], "ICMP")
        self.assertIn("formatted_time", d)


if __name__ == "__main__":
    unittest.main()
