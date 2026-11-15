"""
Packet Dissector & TCP/IP Header Parser
=======================================
Extracts detailed network and transport layer header attributes from raw or Scapy packets.
Analyzes TCP flags, IP TTL, ports, DNS queries, HTTP payloads, and ICMP diagnostics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import binascii

try:
    from scapy.all import IP, IPv6, TCP, UDP, ICMP, ARP, DNS, DNSQR, Raw, Ether
except ImportError:
    IP = IPv6 = TCP = UDP = ICMP = ARP = DNS = DNSQR = Raw = Ether = None


@dataclass
class DissectedPacket:
    """Structured representation of a dissected network packet."""
    timestamp: float
    length: int
    protocol: str
    src_ip: str = "N/A"
    dst_ip: str = "N/A"
    src_mac: str = "N/A"
    dst_mac: str = "N/A"
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    tcp_flags: Dict[str, bool] = field(default_factory=dict)
    tcp_flags_str: str = ""
    seq: Optional[int] = None
    ack: Optional[int] = None
    window: Optional[int] = None
    ttl: Optional[int] = None
    dns_query: Optional[str] = None
    dns_qtype: Optional[str] = None
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    http_host: Optional[str] = None
    payload_len: int = 0
    payload_preview: str = ""
    summary: str = ""
    raw_packet: Any = None

    @property
    def formatted_time(self) -> str:
        """Return human-readable time string (HH:MM:SS.microseconds)."""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%H:%M:%S.%f")[:-3]

    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to JSON-serializable dictionary."""
        return {
            "timestamp": self.timestamp,
            "formatted_time": self.formatted_time,
            "length": self.length,
            "protocol": self.protocol,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_mac": self.src_mac,
            "dst_mac": self.dst_mac,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "tcp_flags": self.tcp_flags,
            "tcp_flags_str": self.tcp_flags_str,
            "seq": self.seq,
            "ack": self.ack,
            "window": self.window,
            "ttl": self.ttl,
            "dns_query": self.dns_query,
            "dns_qtype": self.dns_qtype,
            "http_method": self.http_method,
            "http_path": self.http_path,
            "http_host": self.http_host,
            "payload_len": self.payload_len,
            "payload_preview": self.payload_preview,
            "summary": self.summary
        }


class PacketParser:
    """Dissects raw network packets into structured DissectedPacket objects."""

    @staticmethod
    def parse(packet: Any) -> DissectedPacket:
        """Parse a Scapy packet into a DissectedPacket object."""
        timestamp = float(getattr(packet, "time", datetime.now().timestamp()))
        length = len(packet)

        # Default properties
        protocol = "OTHER"
        src_ip = "N/A"
        dst_ip = "N/A"
        src_mac = "N/A"
        dst_mac = "N/A"
        src_port = None
        dst_port = None
        tcp_flags = {}
        tcp_flags_str = ""
        seq = None
        ack = None
        window = None
        ttl = None
        dns_query = None
        dns_qtype = None
        http_method = None
        http_path = None
        http_host = None
        payload_len = 0
        payload_preview = ""
        summary = ""

        # Layer 2: Ethernet
        if Ether and packet.haslayer(Ether):
            src_mac = packet[Ether].src
            dst_mac = packet[Ether].dst

        # Layer 3: ARP
        if ARP and packet.haslayer(ARP):
            protocol = "ARP"
            arp = packet[ARP]
            src_ip = arp.psrc
            dst_ip = arp.pdst
            src_mac = arp.hwsrc
            dst_mac = arp.hwdst
            op = "Request" if arp.op == 1 else "Reply"
            summary = f"ARP {op}: Who has {dst_ip}? Tell {src_ip}" if arp.op == 1 else f"ARP {op}: {src_ip} is at {src_mac}"

        # Layer 3: IPv4 / IPv6
        elif IP and packet.haslayer(IP):
            ip = packet[IP]
            src_ip = ip.src
            dst_ip = ip.dst
            ttl = ip.ttl
            protocol = "IP"

        elif IPv6 and packet.haslayer(IPv6):
            ip6 = packet[IPv6]
            src_ip = ip6.src
            dst_ip = ip6.dst
            ttl = ip6.hlim
            protocol = "IPv6"

        # Layer 4: TCP
        if TCP and packet.haslayer(TCP):
            tcp = packet[TCP]
            protocol = "TCP"
            src_port = tcp.sport
            dst_port = tcp.dport
            seq = tcp.seq
            ack = tcp.ack
            window = tcp.window

            # Parse TCP flags
            flag_chars = str(tcp.flags)
            tcp_flags = {
                "SYN": "S" in flag_chars,
                "ACK": "A" in flag_chars,
                "FIN": "F" in flag_chars,
                "RST": "R" in flag_chars,
                "PSH": "P" in flag_chars,
                "URG": "U" in flag_chars,
                "ECE": "E" in flag_chars,
                "CWR": "C" in flag_chars
            }
            active_flags = [k for k, v in tcp_flags.items() if v]
            tcp_flags_str = f"[{','.join(active_flags)}]" if active_flags else "[None]"

        # Layer 4: UDP
        elif UDP and packet.haslayer(UDP):
            udp = packet[UDP]
            protocol = "UDP"
            src_port = udp.sport
            dst_port = udp.dport

        # Layer 4: ICMP
        elif ICMP and packet.haslayer(ICMP):
            icmp = packet[ICMP]
            protocol = "ICMP"
            type_names = {0: "Echo Reply", 3: "Dest Unreachable", 8: "Echo Request", 11: "Time Exceeded"}
            summary = f"ICMP {type_names.get(icmp.type, f'Type {icmp.type}')} (Code {icmp.code})"

        # Layer 7: DNS
        if DNS and packet.haslayer(DNS):
            protocol = "DNS"
            dns = packet[DNS]
            if packet.haslayer(DNSQR) and dns.qd:
                try:
                    qname = dns.qd.qname
                    if isinstance(qname, bytes):
                        dns_query = qname.decode(errors="ignore").rstrip(".")
                    else:
                        dns_query = str(qname).rstrip(".")
                    qtypes = {1: "A", 28: "AAAA", 15: "MX", 16: "TXT", 5: "CNAME", 12: "PTR"}
                    dns_qtype = qtypes.get(dns.qd.qtype, f"TYPE{dns.qd.qtype}")
                except Exception:
                    dns_query = "Unknown"
            summary = f"DNS {'Query' if dns.qr == 0 else 'Response'} {dns_query or ''} ({dns_qtype or ''})"

        # Payload and Application layer inspection (HTTP / Plaintext)
        if Raw and packet.haslayer(Raw):
            raw_data = bytes(packet[Raw].load)
            payload_len = len(raw_data)

            # Check for HTTP methods
            http_methods = [b"GET ", b"POST ", b"PUT ", b"DELETE ", b"HEAD ", b"OPTIONS ", b"HTTP/1."]
            for method in http_methods:
                if raw_data.startswith(method):
                    protocol = "HTTP"
                    try:
                        lines = raw_data.decode(errors="ignore").split("\r\n")
                        req_line = lines[0].split(" ")
                        if len(req_line) >= 2:
                            http_method = req_line[0]
                            http_path = req_line[1]
                        for line in lines[1:]:
                            if line.lower().startswith("host:"):
                                http_host = line.split(":", 1)[1].strip()
                                break
                    except Exception:
                        pass
                    break

            # TLS handshake detection (port 443 or TLS record header 0x16 0x03)
            if (src_port == 443 or dst_port == 443) and len(raw_data) >= 3 and raw_data[0] == 0x16:
                protocol = "TLS"

            # Printable preview
            printable = "".join(chr(b) if 32 <= b <= 126 else "." for b in raw_data[:64])
            payload_preview = printable

        # Default summary if not set
        if not summary or protocol in ("TCP", "UDP", "HTTP", "TLS", "IP", "IPv6"):
            port_info = ""
            if src_port and dst_port:
                port_info = f":{src_port} -> :{dst_port}"
            flags_info = f" {tcp_flags_str}" if tcp_flags_str else ""
            summary = f"{protocol} {src_ip}{port_info} -> {dst_ip}{flags_info} (Len: {length}B)"

        return DissectedPacket(
            timestamp=timestamp,
            length=length,
            protocol=protocol,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_mac=src_mac,
            dst_mac=dst_mac,
            src_port=src_port,
            dst_port=dst_port,
            tcp_flags=tcp_flags,
            tcp_flags_str=tcp_flags_str,
            seq=seq,
            ack=ack,
            window=window,
            ttl=ttl,
            dns_query=dns_query,
            dns_qtype=dns_qtype,
            http_method=http_method,
            http_path=http_path,
            http_host=http_host,
            payload_len=payload_len,
            payload_preview=payload_preview,
            summary=summary,
            raw_packet=packet
        )
