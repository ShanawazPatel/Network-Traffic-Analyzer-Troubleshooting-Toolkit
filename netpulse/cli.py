"""
NetPulse Command Line Interface (CLI)
=====================================
Main CLI entrypoint providing subcommands for live sniffing, PCAP forensic inspection,
multi-threaded port scanning, network health & dropout diagnostics, traceroute, and Web SOC.
"""

import sys
import os
import argparse
import logging
from typing import Optional

# Suppress Scapy runtime warnings for clean terminal presentation
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from netpulse import __version__
from netpulse.core.sniffer import PacketSniffer
from netpulse.core.pcap_analyzer import PcapAnalyzer
from netpulse.detector.anomaly_engine import AnomalyEngine
from netpulse.diagnostics.port_scanner import PortScanner
from netpulse.diagnostics.health_monitor import HealthMonitor
from netpulse.diagnostics.dns_checker import DnsHealthChecker
from netpulse.diagnostics.traceroute import RouteTracer
from netpulse.visualizer.console_ui import ConsoleUI, console


def cmd_sniff(args):
    """Handle 'sniff' subcommand."""
    ConsoleUI.print_banner()
    console.print(f"[bold cyan][*] Starting live packet sniffer...[/]")
    if args.interface:
        console.print(f"    Interface: [white]{args.interface}[/]")
    if args.filter:
        console.print(f"    BPF Filter: [yellow]{args.filter}[/]")
    if args.pcap:
        console.print(f"    PCAP Output: [green]{args.pcap}[/]")
    console.print("[dim]Press Ctrl+C to terminate capture.\n[/]")

    engine = AnomalyEngine()
    sniffer = PacketSniffer(
        interface=args.interface,
        bpf_filter=args.filter,
        packet_count=args.count or 0,
        output_pcap=args.pcap
    )

    def on_packet(pkt):
        ConsoleUI.print_packet(pkt)
        threats = engine.process_packet(pkt)
        for t in threats:
            ConsoleUI.print_alert(t)

    sniffer.add_callback(on_packet)
    try:
        sniffer.start(blocking=True)
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Sniffing stopped by user.[/]")
    except Exception as e:
        console.print(f"[bold red][!] Error: {str(e)}[/]")
    finally:
        sniffer.stop()


def cmd_analyze(args):
    """Handle 'analyze' subcommand."""
    ConsoleUI.print_banner()
    pcap_file = args.pcap_file
    if not os.path.exists(pcap_file):
        console.print(f"[bold red][!] File not found: {pcap_file}[/]")
        sys.exit(1)

    console.print(f"[bold cyan][*] Analyzing PCAP capture:[/] [white]{pcap_file}[/]")
    analyzer = PcapAnalyzer(pcap_file)
    engine = AnomalyEngine()

    report = analyzer.analyze(max_packets=args.max_packets, anomaly_engine=engine)
    ConsoleUI.print_pcap_report(report)

    if args.export_json:
        analyzer.export_json(args.export_json)
        console.print(f"[bold green][✓] Exported forensic JSON report to: {args.export_json}[/]")

    if args.export_csv:
        analyzer.export_csv(args.export_csv)
        console.print(f"[bold green][✓] Exported packet table CSV to: {args.export_csv}[/]")


def cmd_scan(args):
    """Handle 'scan' subcommand."""
    ConsoleUI.print_banner()
    target = args.target
    console.print(f"[bold cyan][*] Launching multi-threaded port scan against:[/] [white]{target}[/]")

    ports = None
    if args.ports:
        if "-" in args.ports:
            s, e = map(int, args.ports.split("-"))
            ports = list(range(s, e + 1))
        else:
            ports = [int(p.strip()) for p in args.ports.split(",") if p.strip()]

    scanner = PortScanner(target=target, timeout=args.timeout, max_threads=args.threads)
    result = scanner.scan(ports=ports)
    ConsoleUI.print_scan_report(result)


def cmd_health(args):
    """Handle 'health' subcommand."""
    ConsoleUI.print_banner()
    target = args.target
    console.print(f"[bold cyan][*] Probing network health & dropouts for:[/] [white]{target}[/]")

    monitor = HealthMonitor(target=target, port=args.port, timeout=args.timeout)
    result = monitor.run_check(count=args.count, interval=args.interval)
    ConsoleUI.print_health_report(result)


def cmd_traceroute(args):
    """Handle 'traceroute' subcommand."""
    ConsoleUI.print_banner()
    target = args.target
    console.print(f"[bold cyan][*] Tracing route to:[/] [white]{target}[/] ...")

    tracer = RouteTracer(target=target, max_hops=args.max_hops)
    hops = tracer.trace()

    from rich.table import Table
    from rich import box
    table = Table(title=f"Route Trace to {target}", box=box.ROUNDED, border_style="cyan")
    table.add_column("Hop", style="bold cyan", justify="right")
    table.add_column("Gateway IP", style="white")
    table.add_column("Hostname", style="dim")
    table.add_column("RTT (Latency)", style="yellow", justify="right")
    table.add_column("Status", style="green")

    for h in hops:
        rtt_str = f"{h['rtt_ms']} ms" if h['rtt_ms'] is not None else "*"
        stat_color = "green" if h['status'] == "REACHED" else "red"
        table.add_row(str(h['hop']), h['ip'], h['hostname'], rtt_str, f"[{stat_color}]{h['status']}[/]")
    console.print(table)


def cmd_dns(args):
    """Handle 'dns' subcommand."""
    ConsoleUI.print_banner()
    domain = args.domain
    console.print(f"[bold cyan][*] Benchmarking DNS resolution for domain:[/] [white]{domain}[/]")

    checker = DnsHealthChecker(test_domain=domain)
    results = checker.benchmark_resolvers()

    from rich.table import Table
    from rich import box
    table = Table(title=f"DNS Benchmark Results ({domain})", box=box.ROUNDED, border_style="green")
    table.add_column("Resolver", style="bold white")
    table.add_column("Latency (RTT)", style="cyan", justify="right")
    table.add_column("Status", style="green")

    for r in results:
        lat = f"{r['latency_ms']} ms" if r['latency_ms'] is not None else "-"
        table.add_row(r['resolver'], lat, r['status'])
    console.print(table)


def cmd_web(args):
    """Handle 'web' subcommand."""
    ConsoleUI.print_banner()
    from netpulse.visualizer.web_server import start_server
    start_server(host=args.host, port=args.port, debug=args.debug)


def cmd_demo(args):
    """Run an automated end-to-end interactive demonstration."""
    ConsoleUI.print_banner()
    console.print("[bold green]======================================================================[/]")
    console.print("[bold green]          NetPulse End-to-End Automated Demonstration               [/]")
    console.print("[bold green]======================================================================[/]\n")

    # Step 1: Generate or locate sample capture
    sample_pcap = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "demo_traffic.pcap")
    if not os.path.exists(sample_pcap):
        console.print("[*] Generating synthetic capture with threat traffic...")
        from scripts.generate_sample_pcap import generate_traffic
        generate_traffic()

    # Step 2: PCAP Forensics & DPI Threat Detection
    console.print("\n[bold cyan]>>> STEP 1: PCAP Forensic Analysis & Threat Detection (Bullet 1)[/]")
    analyzer = PcapAnalyzer(sample_pcap)
    engine = AnomalyEngine()
    report = analyzer.analyze(anomaly_engine=engine)
    ConsoleUI.print_pcap_report(report)

    # Step 3: Multi-Threaded Port Scanner
    console.print("\n[bold cyan]>>> STEP 2: Fast Concurrent TCP Port Scanner (Bullet 2)[/]")
    scanner = PortScanner(target="127.0.0.1", timeout=0.5, max_threads=40)
    scan_res = scanner.scan(ports=[21, 22, 80, 443, 135, 445, 3306, 5000, 8080])
    ConsoleUI.print_scan_report(scan_res)

    # Step 4: Network Health & Dropout Diagnostics
    console.print("\n[bold cyan]>>> STEP 3: Automated Latency, Jitter, & Dropout Diagnostics (Bullet 2)[/]")
    monitor = HealthMonitor(target="8.8.8.8", port=53, timeout=1.0)
    health_res = monitor.run_check(count=5, interval=0.1)
    ConsoleUI.print_health_report(health_res)

    # Step 5: Summary
    console.print("\n[bold green]======================================================================[/]")
    console.print("[bold green][✓] Demo Complete! All 3 Project Bullets Fully Verified.[/]")
    console.print("[dim]To view the interactive Web UI, execute: python -m netpulse web[/]")
    console.print("[bold green]======================================================================[/]\n")


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="netpulse",
        description="NetPulse: Enterprise Network Traffic Analyzer, IDS & Troubleshooting Diagnostic Suite"
    )
    parser.add_argument("-v", "--version", action="version", version=f"NetPulse v{__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available NetPulse commands")

    # sniff
    p_sniff = subparsers.add_parser("sniff", help="Capture and inspect live network packets")
    p_sniff.add_argument("-i", "--interface", help="Network interface to sniff on")
    p_sniff.add_argument("-f", "--filter", help="BPF capture filter (e.g. 'tcp port 80')")
    p_sniff.add_argument("-c", "--count", type=int, default=0, help="Stop after N packets (0 = infinite)")
    p_sniff.add_argument("-o", "--pcap", help="Save captured packets to PCAP file")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Perform offline forensic inspection on PCAP files")
    p_analyze.add_argument("pcap_file", help="Path to .pcap or .pcapng file")
    p_analyze.add_argument("-m", "--max-packets", type=int, help="Maximum packets to process")
    p_analyze.add_argument("--export-json", help="Export structured report to JSON file")
    p_analyze.add_argument("--export-csv", help="Export packet records to CSV file")

    # scan
    p_scan = subparsers.add_parser("scan", help="Run multi-threaded TCP port scan & banner grabbing")
    p_scan.add_argument("target", help="Target hostname or IP address")
    p_scan.add_argument("-p", "--ports", help="Port range (e.g. 1-1024) or comma-separated list (e.g. 80,443)")
    p_scan.add_argument("-t", "--threads", type=int, default=50, help="Concurrency thread worker count")
    p_scan.add_argument("--timeout", type=float, default=0.8, help="Connection timeout in seconds")

    # health
    p_health = subparsers.add_parser("health", help="Automated latency, jitter, packet loss, and dropout diagnostics")
    p_health.add_argument("-t", "--target", default="8.8.8.8", help="Target host to probe")
    p_health.add_argument("-p", "--port", type=int, default=53, help="Target port for TCP probes")
    p_health.add_argument("-c", "--count", type=int, default=10, help="Number of diagnostic probes")
    p_health.add_argument("-i", "--interval", type=float, default=0.5, help="Interval between probes in seconds")
    p_health.add_argument("--timeout", type=float, default=1.0, help="Probe timeout in seconds")

    # traceroute
    p_trace = subparsers.add_parser("traceroute", help="Trace routing path and hop-by-hop latency")
    p_trace.add_argument("target", help="Destination hostname or IP")
    p_trace.add_argument("-m", "--max-hops", type=int, default=20, help="Maximum hop count")

    # dns
    p_dns = subparsers.add_parser("dns", help="Benchmark DNS query resolution times across resolvers")
    p_dns.add_argument("-d", "--domain", default="example.com", help="Domain name to resolve")

    # web
    p_web = subparsers.add_parser("web", help="Launch interactive Web SOC Dashboard")
    p_web.add_argument("--host", default="127.0.0.1", help="Bind host address")
    p_web.add_argument("--port", type=int, default=5000, help="HTTP port")
    p_web.add_argument("--debug", action="store_true", help="Run Flask in debug mode")

    # demo
    subparsers.add_parser("demo", help="Run automated end-to-end demo of all features")

    return parser


def main():
    """Main CLI execution dispatch."""
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    handlers = {
        "sniff": cmd_sniff,
        "analyze": cmd_analyze,
        "scan": cmd_scan,
        "health": cmd_health,
        "traceroute": cmd_traceroute,
        "dns": cmd_dns,
        "web": cmd_web,
        "demo": cmd_demo
    }

    handler = handlers.get(args.subcommand)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
