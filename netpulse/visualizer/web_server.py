"""
NetPulse Web Dashboard & SOC Server
===================================
Hosts the interactive glassmorphic web dashboard, exposes REST APIs for live
packet stream telemetry, threat detection feed, port scans, and health diagnostics.
"""

import os
import sys
import time
import threading
from typing import Dict, Any, List
from flask import Flask, render_template, jsonify, request
from netpulse.core.parser import PacketParser, DissectedPacket
from netpulse.core.statistics import TrafficStatistics
from netpulse.core.pcap_analyzer import PcapAnalyzer
from netpulse.detector.anomaly_engine import AnomalyEngine
from netpulse.diagnostics.port_scanner import PortScanner
from netpulse.diagnostics.health_monitor import HealthMonitor
from netpulse.diagnostics.dns_checker import DnsHealthChecker
from netpulse.diagnostics.traceroute import RouteTracer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
SAMPLE_PCAP = os.path.join(os.path.dirname(BASE_DIR), "samples", "demo_traffic.pcap")

app = Flask(
    __name__,
    template_folder=os.path.join(WEB_DIR, "templates"),
    static_folder=os.path.join(WEB_DIR, "static")
)

# Global in-memory state
traffic_stats = TrafficStatistics()
anomaly_engine = AnomalyEngine()
recent_packets: List[Dict[str, Any]] = []
MAX_PACKETS = 150

simulation_running = False
sim_thread: threading.Thread = None


def ingest_packet(pkt: DissectedPacket):
    """Process packet through statistics and IDS engine."""
    traffic_stats.update(pkt)
    anomaly_engine.process_packet(pkt)
    recent_packets.insert(0, pkt.to_dict())
    if len(recent_packets) > MAX_PACKETS:
        recent_packets.pop()


def run_simulation_loop():
    """Simulates realistic traffic stream for interactive dashboard demonstration."""
    global simulation_running
    if not os.path.exists(SAMPLE_PCAP):
        try:
            from scripts.generate_sample_pcap import generate_traffic
            generate_traffic()
        except Exception:
            pass

    if not os.path.exists(SAMPLE_PCAP):
        return

    from scapy.all import PcapReader
    while simulation_running:
        try:
            with PcapReader(SAMPLE_PCAP) as reader:
                for scapy_pkt in reader:
                    if not simulation_running:
                        break
                    pkt = PacketParser.parse(scapy_pkt)
                    pkt.timestamp = time.time()
                    ingest_packet(pkt)
                    time.sleep(0.3)
        except Exception:
            time.sleep(1.0)


@app.route("/")
def index():
    """Render main SOC dashboard."""
    return render_template("index.html")


@app.route("/api/overview")
def get_overview():
    """Return dashboard summary metrics, protocols, recent alerts and packets."""
    stats = traffic_stats.get_summary()
    threat_sum = anomaly_engine.get_summary()

    return jsonify({
        "status": "ONLINE",
        "simulation_running": simulation_running,
        "metrics": {
            "total_packets": stats["total_packets"],
            "total_bytes": stats["total_bytes"],
            "current_pps": stats["current_pps"],
            "current_bandwidth_kbps": stats["current_bandwidth_kbps"],
            "average_bandwidth_kbps": stats["average_bandwidth_kbps"],
            "duration_seconds": stats["duration_seconds"],
            "total_threats": threat_sum["total_alerts"],
            "critical_threats": threat_sum["by_severity"].get("CRITICAL", 0),
            "high_threats": threat_sum["by_severity"].get("HIGH", 0)
        },
        "protocol_breakdown": stats["protocol_counts"],
        "top_sources": stats["top_sources"],
        "top_destinations": stats["top_destinations"],
        "top_ports": stats["top_ports"],
        "recent_alerts": threat_sum["recent_alerts"][:8],
        "recent_packets": recent_packets[:30]
    })


@app.route("/api/packets")
def get_packets():
    """Return recent packet list."""
    return jsonify({"packets": recent_packets})


@app.route("/api/alerts")
def get_alerts():
    """Return all detected threat alerts."""
    return jsonify({
        "total": len(anomaly_engine.alerts),
        "alerts": [a.to_dict() for a in anomaly_engine.alerts]
    })


@app.route("/api/scan", methods=["POST"])
def run_scan():
    """Execute multi-threaded TCP port scan."""
    data = request.get_json() or {}
    target = data.get("target", "127.0.0.1")
    ports_str = data.get("ports", "")

    ports = None
    if ports_str:
        try:
            if "-" in ports_str:
                start, end = map(int, ports_str.split("-"))
                ports = list(range(start, min(65535, end + 1)))
            else:
                ports = [int(p.strip()) for p in ports_str.split(",") if p.strip()]
        except Exception:
            ports = None

    scanner = PortScanner(target=target, timeout=0.6, max_threads=60)
    result = scanner.scan(ports=ports)
    return jsonify(result)


@app.route("/api/health", methods=["POST"])
def run_health():
    """Execute network latency, jitter, and dropout diagnostic check."""
    data = request.get_json() or {}
    target = data.get("target", "8.8.8.8")
    count = int(data.get("count", 10))

    monitor = HealthMonitor(target=target)
    result = monitor.run_check(count=min(25, count), interval=0.2)
    return jsonify(result)


@app.route("/api/dns", methods=["POST"])
def run_dns_bench():
    """Benchmark DNS query latency across resolvers."""
    data = request.get_json() or {}
    domain = data.get("domain", "example.com")
    checker = DnsHealthChecker(test_domain=domain)
    benchmarks = checker.benchmark_resolvers()
    return jsonify({"domain": domain, "resolvers": benchmarks})


@app.route("/api/traceroute", methods=["POST"])
def run_trace():
    """Execute route traceroute."""
    data = request.get_json() or {}
    target = data.get("target", "8.8.8.8")
    tracer = RouteTracer(target=target, max_hops=15)
    hops = tracer.trace()
    return jsonify({"target": target, "hops": hops})


@app.route("/api/analyze_sample", methods=["POST"])
def analyze_sample():
    """Analyze sample PCAP and inject results into engine."""
    if not os.path.exists(SAMPLE_PCAP):
        from scripts.generate_sample_pcap import generate_traffic
        generate_traffic()

    analyzer = PcapAnalyzer(SAMPLE_PCAP)
    anomaly_engine.clear()
    traffic_stats.__init__()
    recent_packets.clear()

    report = analyzer.analyze(anomaly_engine=anomaly_engine)
    for p in analyzer.packets[-MAX_PACKETS:]:
        recent_packets.append(p.to_dict())

    # Update traffic stats
    traffic_stats.total_packets = report["file_info"]["analyzed_packets"]
    traffic_stats.total_bytes = report["metrics"]["total_bytes"]
    traffic_stats.protocol_counts.update(report["protocol_breakdown"])

    return jsonify(report)


@app.route("/api/simulate_toggle", methods=["POST"])
def toggle_simulation():
    """Start or stop synthetic live traffic stream generator."""
    global simulation_running, sim_thread
    data = request.get_json() or {}
    enable = data.get("enable", not simulation_running)

    if enable and not simulation_running:
        simulation_running = True
        sim_thread = threading.Thread(target=run_simulation_loop, daemon=True)
        sim_thread.start()
    elif not enable:
        simulation_running = False

    return jsonify({"simulation_running": simulation_running})


def start_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Start web dashboard server."""
    print(f"\n[+] NetPulse Web SOC Dashboard running at: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_server()
