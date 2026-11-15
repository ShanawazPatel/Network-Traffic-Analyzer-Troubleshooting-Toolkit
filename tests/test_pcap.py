"""Unit tests for offline PCAP forensic analyzer."""
import os
import json
import tempfile
import unittest
from netpulse.core.pcap_analyzer import PcapAnalyzer
from netpulse.detector.anomaly_engine import AnomalyEngine

SAMPLE_PCAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "demo_traffic.pcap")


class TestPcapAnalyzer(unittest.TestCase):

    def test_pcap_analyzer_metrics(self):
        self.assertTrue(os.path.exists(SAMPLE_PCAP), "Demo PCAP must exist")

        analyzer = PcapAnalyzer(SAMPLE_PCAP)
        engine = AnomalyEngine()
        report = analyzer.analyze(anomaly_engine=engine)

        self.assertEqual(report["file_info"]["analyzed_packets"], 94)
        self.assertGreater(report["anomalies_detected"], 0)
        self.assertIn("TCP", report["protocol_breakdown"])
        self.assertIn("DNS", report["protocol_breakdown"])
        self.assertIn("HTTP", report["protocol_breakdown"])
        self.assertIn("ICMP", report["protocol_breakdown"])
        self.assertIn("ARP", report["protocol_breakdown"])

    def test_pcap_export_json(self):
        analyzer = PcapAnalyzer(SAMPLE_PCAP)
        analyzer.analyze()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            out_file = tf.name

        try:
            analyzer.export_json(out_file)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("file_info", data)
            self.assertIn("packets", data)
            self.assertEqual(len(data["packets"]), 94)
        finally:
            if os.path.exists(out_file):
                os.remove(out_file)

    def test_pcap_export_csv(self):
        analyzer = PcapAnalyzer(SAMPLE_PCAP)
        analyzer.analyze()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
            out_file = tf.name

        try:
            analyzer.export_csv(out_file)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 95)  # 1 header + 94 packet rows
        finally:
            if os.path.exists(out_file):
                os.remove(out_file)


if __name__ == "__main__":
    unittest.main()
