"""
Intrusion & Anomaly Detection Engine (IDS)
==========================================
Coordinates active detection rules, processes dissected packets against
behavioral heuristics, and emits structured security threat alerts.
"""

from collections import Counter
from typing import List, Callable, Optional, Dict, Any
from netpulse.core.parser import DissectedPacket
from netpulse.detector.alerts import ThreatAlert
from netpulse.detector.rules import (
    SynFloodRule,
    PortScanRule,
    ArpSpoofRule,
    DnsTunnelRule,
    SuspiciousPayloadRule,
    VolumetricSpikeRule
)


class AnomalyEngine:
    """Central anomaly and threat detection engine."""

    def __init__(self):
        self.rules = [
            SynFloodRule(),
            PortScanRule(),
            ArpSpoofRule(),
            DnsTunnelRule(),
            SuspiciousPayloadRule(),
            VolumetricSpikeRule()
        ]
        self.alerts: List[ThreatAlert] = []
        self._alert_callbacks: List[Callable[[ThreatAlert], None]] = []
        self.severity_counts: Counter = Counter()
        self.rule_counts: Counter = Counter()

    def add_alert_callback(self, callback: Callable[[ThreatAlert], None]):
        """Register a callback for newly triggered alerts."""
        self._alert_callbacks.append(callback)

    def process_packet(self, packet: DissectedPacket) -> List[ThreatAlert]:
        """Evaluate a packet against all detection rules and return any generated alerts."""
        triggered: List[ThreatAlert] = []

        for rule in self.rules:
            try:
                alert = rule.evaluate(packet)
                if alert:
                    triggered.append(alert)
                    self.alerts.append(alert)
                    self.severity_counts[alert.severity] += 1
                    self.rule_counts[alert.rule_name] += 1

                    for cb in self._alert_callbacks:
                        try:
                            cb(alert)
                        except Exception:
                            pass
            except Exception:
                continue

        return triggered

    def get_summary(self) -> Dict[str, Any]:
        """Return threat detection summary statistics."""
        return {
            "total_alerts": len(self.alerts),
            "by_severity": dict(self.severity_counts),
            "by_rule": dict(self.rule_counts),
            "recent_alerts": [a.to_dict() for a in self.alerts[-10:]]
        }

    def clear(self):
        """Reset alerts and rules state."""
        self.alerts.clear()
        self.severity_counts.clear()
        self.rule_counts.clear()
        for rule in self.rules:
            if hasattr(rule, "syn_history"):
                rule.syn_history.clear()
                rule.cooldown.clear()
            if hasattr(rule, "scanned_ports"):
                rule.scanned_ports.clear()
                rule.cooldown.clear()
            if hasattr(rule, "ip_to_mac"):
                rule.ip_to_mac.clear()
                rule.cooldown.clear()
            if hasattr(rule, "timestamps"):
                rule.timestamps.clear()
