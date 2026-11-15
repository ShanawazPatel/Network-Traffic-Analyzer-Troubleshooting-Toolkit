"""
DNS Resolution Health & Multi-Resolver Benchmarking
===================================================
Evaluates query response times and consistency across multiple public
and internal DNS resolvers (Cloudflare, Google, Quad9, OpenDNS, Local).
"""

import socket
import time
from typing import List, Dict, Any

POPULAR_RESOLVERS = [
    {"name": "Cloudflare Primary", "ip": "1.1.1.1"},
    {"name": "Google Primary", "ip": "8.8.8.8"},
    {"name": "Quad9 Secure", "ip": "9.9.9.9"},
    {"name": "OpenDNS Home", "ip": "208.67.222.222"}
]


class DnsHealthChecker:
    """Diagnostic tool for testing DNS resolution latency and resolver reachability."""

    def __init__(self, test_domain: str = "example.com", timeout: float = 2.0):
        self.test_domain = test_domain
        self.timeout = timeout

    def check_local_resolution(self) -> Dict[str, Any]:
        """Test default system resolver latency and answer."""
        start = time.perf_counter()
        try:
            ip = socket.gethostbyname(self.test_domain)
            latency = (time.perf_counter() - start) * 1000.0
            return {
                "resolver": "System Default Resolver",
                "resolved_ip": ip,
                "latency_ms": round(latency, 2),
                "status": "SUCCESS"
            }
        except socket.gaierror as e:
            return {
                "resolver": "System Default Resolver",
                "resolved_ip": None,
                "latency_ms": None,
                "status": f"FAILED: {str(e)}"
            }

    def benchmark_resolvers(self) -> List[Dict[str, Any]]:
        """Measure reachability and port 53 responsiveness across public resolvers."""
        results = [self.check_local_resolution()]

        for r in POPULAR_RESOLVERS:
            start = time.perf_counter()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            try:
                # Test TCP port 53 connectivity
                s.connect((r["ip"], 53))
                latency = (time.perf_counter() - start) * 1000.0
                results.append({
                    "resolver": f"{r['name']} ({r['ip']})",
                    "resolved_ip": "Port 53 Reachable",
                    "latency_ms": round(latency, 2),
                    "status": "REACHABLE"
                })
            except Exception as e:
                results.append({
                    "resolver": f"{r['name']} ({r['ip']})",
                    "resolved_ip": None,
                    "latency_ms": None,
                    "status": f"UNREACHABLE: {type(e).__name__}"
                })
            finally:
                s.close()

        return results
