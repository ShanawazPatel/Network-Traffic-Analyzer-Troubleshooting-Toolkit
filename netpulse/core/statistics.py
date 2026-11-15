"""
Network Traffic Statistics & Metrics Engine
===========================================
Aggregates packet throughput, protocol distribution, top talkers,
conversation pairs, and bandwidth utilization metrics in real time.
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Any, List, Tuple
from netpulse.core.parser import DissectedPacket


class TrafficStatistics:
    """Maintains statistical metrics for captured or analyzed network traffic."""

    def __init__(self):
        self.start_time: float = 0.0
        self.last_time: float = 0.0
        self.total_packets: int = 0
        self.total_bytes: int = 0

        self.protocol_counts: Counter = Counter()
        self.protocol_bytes: Counter = Counter()

        self.src_ip_counts: Counter = Counter()
        self.src_ip_bytes: Counter = Counter()

        self.dst_ip_counts: Counter = Counter()
        self.dst_ip_bytes: Counter = Counter()

        self.port_counts: Counter = Counter()
        self.conversations: Counter = Counter()
        self.tcp_flags_counts: Counter = Counter()

        # Rolling window for current throughput calculation
        self._recent_bytes: List[Tuple[float, int]] = []
        self._recent_packets: List[Tuple[float, int]] = []

    def update(self, packet: DissectedPacket):
        """Update metrics with a new dissected packet."""
        ts = packet.timestamp
        if self.start_time == 0.0:
            self.start_time = ts
        self.last_time = max(self.last_time, ts)

        self.total_packets += 1
        self.total_bytes += packet.length

        self.protocol_counts[packet.protocol] += 1
        self.protocol_bytes[packet.protocol] += packet.length

        if packet.src_ip and packet.src_ip != "N/A":
            self.src_ip_counts[packet.src_ip] += 1
            self.src_ip_bytes[packet.src_ip] += packet.length

        if packet.dst_ip and packet.dst_ip != "N/A":
            self.dst_ip_counts[packet.dst_ip] += 1
            self.dst_ip_bytes[packet.dst_ip] += packet.length

        # Track conversation pairs
        if packet.src_ip != "N/A" and packet.dst_ip != "N/A":
            conv = tuple(sorted([packet.src_ip, packet.dst_ip]))
            self.conversations[conv] += 1

        # Ports
        if packet.src_port:
            self.port_counts[packet.src_port] += 1
        if packet.dst_port:
            self.port_counts[packet.dst_port] += 1

        # TCP flags
        if packet.tcp_flags:
            for flag, active in packet.tcp_flags.items():
                if active:
                    self.tcp_flags_counts[flag] += 1

        # Rolling throughput (last 3 seconds window)
        self._recent_bytes.append((ts, packet.length))
        self._recent_packets.append((ts, 1))
        cutoff = ts - 3.0
        self._recent_bytes = [(t, b) for t, b in self._recent_bytes if t >= cutoff]
        self._recent_packets = [(t, p) for t, p in self._recent_packets if t >= cutoff]

    @property
    def duration_seconds(self) -> float:
        """Total duration spanned by traffic in seconds."""
        if self.start_time == 0.0:
            return 0.0
        return max(0.001, self.last_time - self.start_time)

    @property
    def average_pps(self) -> float:
        """Average packets per second."""
        if self.duration_seconds <= 0.0 or self.total_packets == 0:
            return 0.0
        return round(self.total_packets / self.duration_seconds, 2)

    @property
    def average_bandwidth_kbps(self) -> float:
        """Average bandwidth in kilobits per second (Kbps)."""
        if self.duration_seconds <= 0.0 or self.total_bytes == 0:
            return 0.0
        bits = self.total_bytes * 8
        return round(bits / (self.duration_seconds * 1000), 2)

    @property
    def current_pps(self) -> float:
        """Recent packets per second (last 3s)."""
        if not self._recent_packets:
            return 0.0
        window = max(0.5, self.last_time - self._recent_packets[0][0])
        total_p = sum(p for _, p in self._recent_packets)
        return round(total_p / window, 1)

    @property
    def current_bandwidth_kbps(self) -> float:
        """Recent bandwidth in kilobits per second (last 3s)."""
        if not self._recent_bytes:
            return 0.0
        window = max(0.5, self.last_time - self._recent_bytes[0][0])
        total_b = sum(b for _, b in self._recent_bytes)
        return round((total_b * 8) / (window * 1000), 1)

    def get_top_sources(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top source IP addresses by packet count and data volume."""
        return [
            {"ip": ip, "packets": count, "bytes": self.src_ip_bytes[ip]}
            for ip, count in self.src_ip_counts.most_common(limit)
        ]

    def get_top_destinations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top destination IP addresses by packet count and data volume."""
        return [
            {"ip": ip, "packets": count, "bytes": self.dst_ip_bytes[ip]}
            for ip, count in self.dst_ip_counts.most_common(limit)
        ]

    def get_top_ports(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return top communicating port numbers."""
        port_names = {
            80: "HTTP", 443: "HTTPS", 53: "DNS", 22: "SSH", 21: "FTP",
            25: "SMTP", 110: "POP3", 143: "IMAP", 3306: "MySQL", 5432: "PostgreSQL",
            8080: "HTTP-Alt", 8443: "HTTPS-Alt"
        }
        return [
            {"port": port, "service": port_names.get(port, "Unknown"), "count": count}
            for port, count in self.port_counts.most_common(limit)
        ]

    def get_protocol_distribution(self) -> Dict[str, int]:
        """Return dictionary mapping protocol name to packet count."""
        return dict(self.protocol_counts)

    def get_summary(self) -> Dict[str, Any]:
        """Return complete statistical summary."""
        return {
            "total_packets": self.total_packets,
            "total_bytes": self.total_bytes,
            "duration_seconds": round(self.duration_seconds, 2),
            "average_pps": self.average_pps,
            "average_bandwidth_kbps": self.average_bandwidth_kbps,
            "current_pps": self.current_pps,
            "current_bandwidth_kbps": self.current_bandwidth_kbps,
            "protocol_counts": dict(self.protocol_counts),
            "tcp_flags": dict(self.tcp_flags_counts),
            "top_sources": self.get_top_sources(5),
            "top_destinations": self.get_top_destinations(5),
            "top_ports": self.get_top_ports(5),
            "unique_conversations": len(self.conversations)
        }
