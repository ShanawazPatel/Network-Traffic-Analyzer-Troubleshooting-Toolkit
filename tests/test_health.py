"""Unit tests for health monitoring and dropout diagnostics."""
import unittest
from netpulse.diagnostics.health_monitor import HealthMonitor, HealthProbe, DropoutEvent


class TestHealthMonitor(unittest.TestCase):

    def test_dropout_event_serialization(self):
        d = DropoutEvent(start_time=1700000000.0, end_time=1700000005.0, duration_seconds=5.0, failed_probes=3)
        data = d.to_dict()
        self.assertEqual(data["duration_seconds"], 5.0)
        self.assertEqual(data["failed_probes"], 3)
        self.assertIn("formatted_start", data)

    def test_health_report_calculation(self):
        monitor = HealthMonitor(target="127.0.0.1", timeout=0.1)

        monitor.probes = [
            HealthProbe(timestamp=1000.0, seq=1, rtt_ms=10.0, success=True, status="OK"),
            HealthProbe(timestamp=1000.5, seq=2, rtt_ms=12.0, success=True, status="OK"),
            HealthProbe(timestamp=1001.0, seq=3, rtt_ms=11.0, success=True, status="OK"),
            HealthProbe(timestamp=1001.5, seq=4, rtt_ms=15.0, success=True, status="OK"),
        ]

        report = monitor.get_report()

        self.assertEqual(report["verdict"], "HEALTHY")
        self.assertEqual(report["metrics"]["total_probes"], 4)
        self.assertEqual(report["metrics"]["packet_loss_pct"], 0.0)
        self.assertEqual(report["metrics"]["min_rtt_ms"], 10.0)
        self.assertEqual(report["metrics"]["max_rtt_ms"], 15.0)
        self.assertEqual(report["metrics"]["avg_rtt_ms"], 12.0)
        self.assertEqual(report["metrics"]["jitter_ms"], 2.33)

    def test_health_verdict_high_loss(self):
        monitor = HealthMonitor(target="127.0.0.1", timeout=0.1)
        monitor.probes = [
            HealthProbe(timestamp=1000.0, seq=1, rtt_ms=10.0, success=True, status="OK"),
            HealthProbe(timestamp=1000.5, seq=2, rtt_ms=None, success=False, status="TIMEOUT"),
            HealthProbe(timestamp=1001.0, seq=3, rtt_ms=None, success=False, status="TIMEOUT"),
        ]
        report = monitor.get_report()
        self.assertIn("PACKET LOSS", report["verdict"])
        self.assertGreater(report["metrics"]["packet_loss_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
