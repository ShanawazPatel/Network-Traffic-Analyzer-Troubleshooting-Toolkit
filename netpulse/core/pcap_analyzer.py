"""
Offline PCAP Capture File Forensic Analyzer
===========================================
Reads and parses Wireshark/tcpdump .pcap and .pcapng files, reconstructs session flows,
computes traffic statistics, and detects anomalies for post-incident forensic investigation.
"""

import os
import json
import csv
from typing import Dict, Any, List, Optional, Callable
from netpulse.core.parser import PacketParser, DissectedPacket
from netpulse.core.statistics import TrafficStatistics

try:
    from scapy.all import PcapReader, rdpcap
except ImportError:
    PcapReader = rdpcap = None


class PcapAnalyzer:
    """Forensic analyzer for offline PCAP and PCAPNG capture files."""

    def __init__(self, pcap_path: str):
        if not os.path.exists(pcap_path):
            raise FileNotFoundError(f"PCAP capture file not found: {pcap_path}")

        self.pcap_path = pcap_path
        self.file_size = os.path.getsize(pcap_path)
        self.packets: List[DissectedPacket] = []
        self.statistics = TrafficStatistics()
        self.anomalies: List[Dict[str, Any]] = []

    def analyze(
        self,
        max_packets: Optional[int] = None,
        filter_fn: Optional[Callable[[DissectedPacket], bool]] = None,
        anomaly_engine: Optional[Any] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """Process PCAP file, parse packets, accumulate stats, and detect threats."""
        if not PcapReader:
            raise ImportError("Scapy is required for PCAP analysis.")

        self.packets.clear()
        self.statistics = TrafficStatistics()
        self.anomalies.clear()

        count = 0
        with PcapReader(self.pcap_path) as reader:
            for scapy_pkt in reader:
                dissected = PacketParser.parse(scapy_pkt)

                if filter_fn and not filter_fn(dissected):
                    continue

                self.packets.append(dissected)
                self.statistics.update(dissected)

                # Feed packet to anomaly engine if attached
                if anomaly_engine:
                    threats = anomaly_engine.process_packet(dissected)
                    if threats:
                        self.anomalies.extend(threats)

                count += 1
                if progress_callback and count % 50 == 0:
                    progress_callback(count)

                if max_packets and count >= max_packets:
                    break

        return self.get_report()

    def get_report(self) -> Dict[str, Any]:
        """Generate structured forensic report of analyzed capture."""
        stats = self.statistics.get_summary()
        return {
            "file_info": {
                "file_path": self.pcap_path,
                "file_name": os.path.basename(self.pcap_path),
                "file_size_bytes": self.file_size,
                "file_size_formatted": self._format_size(self.file_size),
                "analyzed_packets": len(self.packets),
                "duration_seconds": stats["duration_seconds"]
            },
            "metrics": {
                "average_pps": stats["average_pps"],
                "average_bandwidth_kbps": stats["average_bandwidth_kbps"],
                "total_bytes": stats["total_bytes"]
            },
            "protocol_breakdown": stats["protocol_counts"],
            "tcp_flags": stats["tcp_flags"],
            "top_sources": stats["top_sources"],
            "top_destinations": stats["top_destinations"],
            "top_ports": stats["top_ports"],
            "unique_conversations": stats["unique_conversations"],
            "anomalies_detected": len(self.anomalies),
            "anomalies": [a.to_dict() if hasattr(a, "to_dict") else a for a in self.anomalies]
        }

    def export_json(self, output_path: str):
        """Export report and packet list to JSON file."""
        report = self.get_report()
        report["packets"] = [p.to_dict() for p in self.packets]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    def export_csv(self, output_path: str):
        """Export analyzed packet list to CSV for spreadsheet inspection."""
        if not self.packets:
            return

        keys = [
            "formatted_time", "protocol", "src_ip", "src_port",
            "dst_ip", "dst_port", "tcp_flags_str", "length", "summary"
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for pkt in self.packets:
                row = {
                    "formatted_time": pkt.formatted_time,
                    "protocol": pkt.protocol,
                    "src_ip": pkt.src_ip,
                    "src_port": pkt.src_port or "",
                    "dst_ip": pkt.dst_ip,
                    "dst_port": pkt.dst_port or "",
                    "tcp_flags_str": pkt.tcp_flags_str,
                    "length": pkt.length,
                    "summary": pkt.summary
                }
                writer.writerow(row)

    @staticmethod
    def _format_size(num_bytes: int) -> str:
        """Format byte size into human readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if num_bytes < 1024.0:
                return f"{num_bytes:.2f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.2f} TB"
