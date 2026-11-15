"""
Anomaly & Threat Detection Heuristic Rules
==========================================
Engineered rules detecting SYN floods, ARP spoofing, stealth port scans,
DNS tunneling exfiltration, illegal TCP flag combinations, and payload injection patterns.
"""

import math
from collections import defaultdict, deque
from typing import List, Dict, Any, Optional
from netpulse.core.parser import DissectedPacket
from netpulse.detector.alerts import ThreatAlert, Severity


def shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string to detect encrypted or tunneled data."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    counts = {}
    for char in data:
        counts[char] = counts.get(char, 0) + 1
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


class SynFloodRule:
    """Detects TCP SYN Flood denial-of-service patterns."""

    def __init__(self, threshold: int = 15, window_seconds: float = 3.0):
        self.threshold = threshold
        self.window = window_seconds
        self.syn_history: Dict[str, deque] = defaultdict(deque)
        self.ack_counts: Dict[str, int] = defaultdict(int)
        self.cooldown: Dict[str, float] = {}

    def evaluate(self, pkt: DissectedPacket) -> Optional[ThreatAlert]:
        if pkt.protocol != "TCP" or not pkt.tcp_flags:
            return None

        src = pkt.src_ip
        ts = pkt.timestamp

        # Track ACK/FIN responses
        if pkt.tcp_flags.get("ACK", False) or pkt.tcp_flags.get("FIN", False):
            self.ack_counts[src] += 1

        # Track SYN without ACK
        if pkt.tcp_flags.get("SYN", False) and not pkt.tcp_flags.get("ACK", False):
            history = self.syn_history[src]
            history.append(ts)

            # Purge expired
            cutoff = ts - self.window
            while history and history[0] < cutoff:
                history.popleft()

            # Cooldown check (alert max once every 5 seconds per source)
            if src in self.cooldown and ts - self.cooldown[src] < 5.0:
                return None

            if len(history) >= self.threshold:
                self.cooldown[src] = ts
                return ThreatAlert(
                    rule_name="SYN Flood DoS Attack",
                    severity=Severity.CRITICAL,
                    source=src,
                    target=f"{pkt.dst_ip}:{pkt.dst_port}",
                    description=f"High-frequency SYN flood detected: {len(history)} SYN packets within {self.window}s with no handshake completion.",
                    recommendation="Enable TCP SYN Cookies ('sysctl -w net.ipv4.tcp_syncookies=1') and apply iptables rate-limiting rules.",
                    evidence={"syn_count": len(history), "window_seconds": self.window, "dst_port": pkt.dst_port}
                )
        return None


class PortScanRule:
    """Detects vertical, horizontal, and TCP flag anomaly scans (XMAS, NULL, FIN)."""

    def __init__(self, port_threshold: int = 8, window_seconds: float = 4.0):
        self.port_threshold = port_threshold
        self.window = window_seconds
        self.scanned_ports: Dict[str, Dict[int, float]] = defaultdict(dict)
        self.cooldown: Dict[str, float] = {}

    def evaluate(self, pkt: DissectedPacket) -> Optional[ThreatAlert]:
        if pkt.protocol != "TCP" or not pkt.src_ip or not pkt.dst_port:
            return None

        src = pkt.src_ip
        dst = pkt.dst_ip
        ts = pkt.timestamp
        flags = pkt.tcp_flags

        # 1. Illegal TCP flag combinations (Stealth Scans)
        # NULL Scan: No flags set
        is_null = flags and not any(flags.values())
        if is_null:
            return ThreatAlert(
                rule_name="TCP NULL Stealth Scan",
                severity=Severity.HIGH,
                source=src,
                target=f"{dst}:{pkt.dst_port}",
                description="TCP packet received with zero control flags set (characteristic of Nmap NULL scan).",
                recommendation="Drop invalid TCP flag packets at the firewall: iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP",
                evidence={"flags": flags, "probe_port": pkt.dst_port}
            )

        # XMAS Scan: FIN, PSH, and URG all set
        is_xmas = flags.get("FIN") and flags.get("PSH") and flags.get("URG")
        if is_xmas:
            return ThreatAlert(
                rule_name="TCP XMAS Stealth Scan",
                severity=Severity.HIGH,
                source=src,
                target=f"{dst}:{pkt.dst_port}",
                description="TCP packet received with FIN, PSH, and URG flags set simultaneously (characteristic of Nmap XMAS scan).",
                recommendation="Drop Xmas packets: iptables -A INPUT -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP",
                evidence={"flags": flags, "probe_port": pkt.dst_port}
            )

        # 2. Vertical Port Scanning (Single target, many ports)
        if flags.get("SYN") and not flags.get("ACK"):
            ports = self.scanned_ports[src]
            ports[pkt.dst_port] = ts

            # Purge old probes
            cutoff = ts - self.window
            expired = [p for p, t in ports.items() if t < cutoff]
            for p in expired:
                del ports[p]

            if src in self.cooldown and ts - self.cooldown[src] < 5.0:
                return None

            if len(ports) >= self.port_threshold:
                self.cooldown[src] = ts
                return ThreatAlert(
                    rule_name="Vertical Port Scan",
                    severity=Severity.HIGH,
                    source=src,
                    target=dst,
                    description=f"Rapid probe of {len(ports)} distinct ports within {self.window}s from single source IP.",
                    recommendation="Blacklist offending host via iptables or block suspicious subnets using fail2ban.",
                    evidence={"scanned_ports": sorted(list(ports.keys())), "window_seconds": self.window}
                )
        return None


class ArpSpoofRule:
    """Detects ARP cache poisoning / Man-In-The-Middle attempts."""

    def __init__(self):
        self.ip_to_mac: Dict[str, str] = {}
        self.cooldown: Dict[str, float] = {}

    def evaluate(self, pkt: DissectedPacket) -> Optional[ThreatAlert]:
        if pkt.protocol != "ARP" or pkt.src_ip == "N/A" or pkt.src_mac == "N/A":
            return None

        ip = pkt.src_ip
        mac = pkt.src_mac.lower()
        ts = pkt.timestamp

        if ip in self.ip_to_mac:
            previous_mac = self.ip_to_mac[ip]
            if previous_mac != mac:
                # MAC changed for known IP!
                if ip in self.cooldown and ts - self.cooldown[ip] < 5.0:
                    return None

                self.cooldown[ip] = ts
                return ThreatAlert(
                    rule_name="ARP Spoofing / Poisoning",
                    severity=Severity.CRITICAL,
                    source=f"{mac} (claiming {ip})",
                    target=pkt.dst_ip,
                    description=f"ARP cache conflict detected! IP {ip} was previously bound to {previous_mac}, now claimed by {mac}.",
                    recommendation="Inspect network segment for rogue hosts, enable Dynamic ARP Inspection (DAI) on switches, or configure static ARP entries.",
                    evidence={"ip": ip, "original_mac": previous_mac, "spoofed_mac": mac}
                )
        else:
            self.ip_to_mac[ip] = mac

        return None


class DnsTunnelRule:
    """Detects DNS exfiltration and tunneling through abnormally long or high-entropy queries."""

    def __init__(self, length_threshold: int = 45, entropy_threshold: float = 3.6):
        self.length_threshold = length_threshold
        self.entropy_threshold = entropy_threshold
        self.cooldown: Dict[str, float] = {}

    def evaluate(self, pkt: DissectedPacket) -> Optional[ThreatAlert]:
        if pkt.protocol != "DNS" or not pkt.dns_query:
            return None

        query = pkt.dns_query
        domain_parts = query.split(".")
        subdomain = domain_parts[0] if domain_parts else query

        ts = pkt.timestamp
        length = len(subdomain)
        entropy = round(shannon_entropy(subdomain), 2)

        if length >= self.length_threshold or (length > 25 and entropy >= self.entropy_threshold):
            key = f"{pkt.src_ip}:{query}"
            if key in self.cooldown and ts - self.cooldown[key] < 10.0:
                return None

            self.cooldown[key] = ts
            return ThreatAlert(
                rule_name="DNS Tunneling / Exfiltration",
                severity=Severity.HIGH,
                source=pkt.src_ip,
                target=f"{pkt.dst_ip}:53",
                description=f"Suspicious DNS query '{query}' exhibits high Shannon entropy ({entropy}) and length ({length} chars), typical of base64/hex data exfiltration.",
                recommendation="Inspect endpoints for covert DNS tunneling malware (e.g. dnscat2, iodine) and enforce DNS filtering via internal recursive resolvers.",
                evidence={"query": query, "subdomain_length": length, "shannon_entropy": entropy}
            )
        return None


class SuspiciousPayloadRule:
    """Detects plaintext credentials, SQL injection, and directory traversal signatures."""

    SQLI_PATTERNS = ["' or '1'='1", "union select", "waitfor delay", "exec(", "benchmark("]
    TRAVERSAL_PATTERNS = ["../..", "/etc/passwd", "win.ini", "boot.ini"]
    CRED_PATTERNS = ["password=", "passwd=", "auth_token=", "bearer "]

    def evaluate(self, pkt: DissectedPacket) -> Optional[ThreatAlert]:
        if not pkt.payload_preview or pkt.payload_len == 0:
            return None

        preview_lower = pkt.payload_preview.lower()

        for pattern in self.SQLI_PATTERNS:
            if pattern in preview_lower:
                return ThreatAlert(
                    rule_name="SQL Injection Attempt",
                    severity=Severity.HIGH,
                    source=pkt.src_ip,
                    target=f"{pkt.dst_ip}:{pkt.dst_port}",
                    description=f"Inbound payload matches SQL injection signature: '{pattern}'.",
                    recommendation="Deploy Web Application Firewall (WAF) rule and sanitize SQL input queries with parameterized statements.",
                    evidence={"matched_signature": pattern, "preview": pkt.payload_preview[:60]}
                )

        for pattern in self.TRAVERSAL_PATTERNS:
            if pattern in preview_lower:
                return ThreatAlert(
                    rule_name="Path Traversal Attempt",
                    severity=Severity.HIGH,
                    source=pkt.src_ip,
                    target=f"{pkt.dst_ip}:{pkt.dst_port}",
                    description=f"Payload contains directory traversal signature: '{pattern}'.",
                    recommendation="Validate and restrict file system paths within web server root directory.",
                    evidence={"matched_signature": pattern, "preview": pkt.payload_preview[:60]}
                )

        for pattern in self.CRED_PATTERNS:
            if pattern in preview_lower and pkt.dst_port == 80:
                return ThreatAlert(
                    rule_name="Cleartext Credential Transmission",
                    severity=Severity.MEDIUM,
                    source=pkt.src_ip,
                    target=f"{pkt.dst_ip}:{pkt.dst_port}",
                    description=f"Unencrypted credentials transmitted over HTTP port 80 ('{pattern}').",
                    recommendation="Enforce HTTPS/TLS 1.3 across all authentication endpoints and redirect HTTP traffic to HTTPS.",
                    evidence={"matched_signature": pattern}
                )
        return None


class VolumetricSpikeRule:
    """Detects sudden traffic volume surges exceeding baseline thresholds."""

    def __init__(self, pps_threshold: int = 150):
        self.pps_threshold = pps_threshold
        self.timestamps: deque = deque()
        self.last_alert: float = 0.0

    def evaluate(self, pkt: DissectedPacket) -> Optional[ThreatAlert]:
        ts = pkt.timestamp
        self.timestamps.append(ts)

        cutoff = ts - 1.0
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

        pps = len(self.timestamps)
        if pps >= self.pps_threshold and (ts - self.last_alert > 5.0):
            self.last_alert = ts
            return ThreatAlert(
                rule_name="Volumetric Traffic Spike",
                severity=Severity.MEDIUM,
                source="Multiple Hosts / Aggregate",
                target=pkt.dst_ip,
                description=f"Traffic surge detected: {pps} packets/sec exceeds baseline threshold ({self.pps_threshold} pps).",
                recommendation="Investigate traffic destination; apply traffic policing or upstream rate-limiting if DDoS is suspected.",
                evidence={"current_pps": pps, "threshold_pps": self.pps_threshold}
            )
        return None
