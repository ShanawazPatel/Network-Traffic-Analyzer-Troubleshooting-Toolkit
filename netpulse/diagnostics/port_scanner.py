"""
Multi-Threaded TCP Port Scanner & Service Fingerprinter
======================================================
Executes high-concurrency TCP port scans with service identification,
banner grabbing, and round-trip response time (RTT) measurements.
"""

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPCBind", 135: "MSRPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1521: "Oracle", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",
    9000: "SonarQube", 27017: "MongoDB"
}


@dataclass
class PortScanResult:
    """Represents an open or responsive port probe result."""
    port: int
    state: str
    service: str
    banner: str = ""
    rtt_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "state": self.state,
            "service": self.service,
            "banner": self.banner,
            "rtt_ms": round(self.rtt_ms, 2)
        }


class PortScanner:
    """High-performance concurrent port scanner."""

    def __init__(self, target: str, timeout: float = 0.8, max_threads: int = 50):
        self.target = target
        self.timeout = timeout
        self.max_threads = max_threads
        self.target_ip = self._resolve_target(target)

    def _resolve_target(self, target: str) -> str:
        """Resolve target hostname to IP address."""
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            return target

    def _grab_banner(self, s: socket.socket, port: int) -> str:
        """Attempt to grab application banner from open port."""
        try:
            s.settimeout(0.6)
            # Send HTTP probe for web ports
            if port in (80, 8080, 8443):
                s.sendall(b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n")
            elif port in (21, 22, 25, 110):
                # Many services send greeting upon connect
                pass
            else:
                s.sendall(b"\r\n")

            data = s.recv(256)
            text = data.decode(errors="ignore").strip().split("\r\n")[0]
            return text[:60]
        except Exception:
            return ""

    def _scan_port(self, port: int) -> Optional[PortScanResult]:
        """Probe an individual TCP port."""
        start = time.perf_counter()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)

        try:
            result = s.connect_ex((self.target_ip, port))
            rtt = (time.perf_counter() - start) * 1000.0

            if result == 0:
                service = COMMON_PORTS.get(port, "Unknown")
                banner = self._grab_banner(s, port)
                return PortScanResult(
                    port=port,
                    state="open",
                    service=service,
                    banner=banner,
                    rtt_ms=rtt
                )
        except Exception:
            pass
        finally:
            s.close()

        return None

    def scan(
        self,
        ports: Optional[List[int]] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """Execute concurrent scan across specified ports."""
        if ports is None:
            ports = sorted(list(COMMON_PORTS.keys()))

        total_ports = len(ports)
        open_results: List[PortScanResult] = []
        completed = 0
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=min(self.max_threads, total_ports or 1)) as executor:
            future_to_port = {executor.submit(self._scan_port, p): p for p in ports}
            for future in as_completed(future_to_port):
                res = future.result()
                if res:
                    open_results.append(res)
                completed += 1
                if progress_cb:
                    progress_cb(completed, total_ports)

        duration = time.time() - start_time
        open_results.sort(key=lambda r: r.port)

        return {
            "target": self.target,
            "target_ip": self.target_ip,
            "scanned_ports_count": total_ports,
            "open_ports_count": len(open_results),
            "scan_duration_seconds": round(duration, 2),
            "open_ports": [r.to_dict() for r in open_results]
        }
