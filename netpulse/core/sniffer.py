"""
Live Packet Sniffer Engine
==========================
Captures live network traffic across physical or virtual interfaces using Scapy,
applies Berkeley Packet Filters (BPF), writes to PCAP files, and dispatches packets
to registered parsing and threat-detection callbacks.
"""

import threading
import time
from typing import Callable, Optional, List
from netpulse.core.parser import PacketParser, DissectedPacket

try:
    from scapy.all import sniff, PcapWriter, conf
except ImportError:
    sniff = PcapWriter = conf = None


class PacketSniffer:
    """Multi-threaded live packet sniffer with BPF filtering and PCAP export."""

    def __init__(
        self,
        interface: Optional[str] = None,
        bpf_filter: Optional[str] = None,
        packet_count: int = 0,
        output_pcap: Optional[str] = None,
        promiscuous: bool = True
    ):
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.packet_count = packet_count
        self.output_pcap = output_pcap
        self.promiscuous = promiscuous

        self._callbacks: List[Callable[[DissectedPacket], None]] = []
        self._raw_callbacks: List[Callable[[any], None]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._pcap_writer: Optional[PcapWriter] = None
        self.captured_count = 0

        if self.output_pcap and PcapWriter:
            self._pcap_writer = PcapWriter(self.output_pcap, append=True, sync=True)

    def add_callback(self, callback: Callable[[DissectedPacket], None]):
        """Register a callback for each dissected packet."""
        self._callbacks.append(callback)

    def add_raw_callback(self, callback: Callable[[any], None]):
        """Register a callback for raw scapy packets."""
        self._raw_callbacks.append(callback)

    def _packet_handler(self, scapy_pkt):
        """Internal callback invoked for each captured packet."""
        if self._stop_event.is_set():
            return

        self.captured_count += 1

        # Write to PCAP file if writer configured
        if self._pcap_writer:
            try:
                self._pcap_writer.write(scapy_pkt)
            except Exception:
                pass

        # Dissect packet
        dissected = PacketParser.parse(scapy_pkt)

        # Notify callbacks
        for cb in self._callbacks:
            try:
                cb(dissected)
            except Exception:
                pass

        for raw_cb in self._raw_callbacks:
            try:
                raw_cb(scapy_pkt)
            except Exception:
                pass

        # Check packet count termination
        if 0 < self.packet_count <= self.captured_count:
            self._stop_event.set()

    def start(self, blocking: bool = False):
        """Start packet sniffing either asynchronously or blocking."""
        self._stop_event.clear()
        self.captured_count = 0

        if blocking:
            self._run_sniff()
        else:
            self._thread = threading.Thread(target=self._run_sniff, daemon=True)
            self._thread.start()

    def _run_sniff(self):
        """Sniffer execution loop."""
        sniff_kwargs = {
            "prn": self._packet_handler,
            "stop_filter": lambda _: self._stop_event.is_set(),
            "store": False
        }

        if self.interface:
            sniff_kwargs["iface"] = self.interface
        if self.bpf_filter:
            sniff_kwargs["filter"] = self.bpf_filter
        if self.packet_count > 0:
            sniff_kwargs["count"] = self.packet_count

        try:
            sniff(**sniff_kwargs)
        except PermissionError:
            raise PermissionError(
                "Packet sniffing requires elevated privileges. "
                "On Linux run with 'sudo', or on Windows ensure Npcap is installed and run as Administrator."
            )
        except Exception as e:
            raise RuntimeError(f"Sniffing error: {str(e)}")
        finally:
            self.close()

    def stop(self):
        """Signal sniffer to stop capturing."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.close()

    def is_running(self) -> bool:
        """Check if sniffing is active."""
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def close(self):
        """Close open file handles."""
        if self._pcap_writer:
            try:
                self._pcap_writer.close()
            except Exception:
                pass
            self._pcap_writer = None

    @staticmethod
    def get_interfaces() -> List[str]:
        """List available network interfaces."""
        if conf and hasattr(conf, "ifaces"):
            return [str(iface) for iface in conf.ifaces.values()]
        return []
