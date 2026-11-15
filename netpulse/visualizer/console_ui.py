"""
Rich Terminal User Interface (TUI) & SOC Console
================================================
Renders high-fidelity animated dashboards, packet inspection tables,
threat alerts, port scan summaries, and health diagnostics in the terminal.
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box
from netpulse.core.parser import DissectedPacket
from netpulse.detector.alerts import ThreatAlert, Severity

console = Console()


class ConsoleUI:
    """Rich console renderer for terminal dashboards and command output."""

    @staticmethod
    def print_banner():
        """Render stylish ASCII header banner."""
        banner_text = Text(
            """
 ███╗   ██╗███████╗████████╗██████╗ ██╗   ██╗██╗     ███████╗███████╗
 ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
 ██╔██╗ ██║█████╗     ██║   ██████╔╝██║   ██║██║     ███████╗█████╗  
 ██║╚██╗██║██╔══╝     ██║   ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝  
 ██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝███████╗███████║███████╗
 ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝
       Network Traffic Analyzer & Troubleshooting Diagnostic Suite
            [ Python | Wireshark | Scapy | Linux | Bash ]
            """,
            style="bold cyan"
        )
        console.print(Panel(banner_text, border_style="bright_blue", box=box.ROUNDED))

    @staticmethod
    def print_packet(pkt: DissectedPacket):
        """Print single dissected packet summary line."""
        proto_colors = {
            "TCP": "cyan",
            "UDP": "magenta",
            "ICMP": "yellow",
            "ARP": "bright_blue",
            "DNS": "green",
            "HTTP": "bright_green",
            "TLS": "blue",
            "OTHER": "white"
        }
        color = proto_colors.get(pkt.protocol, "white")
        src = f"{pkt.src_ip}:{pkt.src_port}" if pkt.src_port else pkt.src_ip
        dst = f"{pkt.dst_ip}:{pkt.dst_port}" if pkt.dst_port else pkt.dst_ip

        flags = f" [bold yellow]{pkt.tcp_flags_str}[/]" if pkt.tcp_flags_str else ""
        console.print(
            f"[dim]{pkt.formatted_time}[/] | "
            f"[bold {color}]{pkt.protocol:<5}[/] | "
            f"[white]{src:<21}[/] -> [white]{dst:<21}[/]{flags} | "
            f"[dim]{pkt.length}B[/] | [italic]{pkt.summary}[/]"
        )

    @staticmethod
    def print_alert(alert: ThreatAlert):
        """Render a security threat alert card."""
        sev_styles = {
            Severity.CRITICAL: ("bold red", "CRITICAL THREAT"),
            Severity.HIGH: ("bold bright_red", "HIGH SEVERITY"),
            Severity.MEDIUM: ("bold yellow", "MEDIUM WARNING"),
            Severity.LOW: ("bold blue", "INFORMATIONAL")
        }
        color, badge = sev_styles.get(alert.severity, ("white", "ALERT"))

        content = Text()
        content.append(f"[{badge}] ", style=color)
        content.append(f"{alert.rule_name}\n", style="bold white")
        content.append(f"Timestamp:  {alert.formatted_time}\n", style="dim")
        content.append(f"Source:     {alert.source}  -->  Target: {alert.target}\n", style="cyan")
        content.append(f"Details:    {alert.description}\n", style="white")
        content.append(f"Remediation: {alert.recommendation}\n", style="italic green")

        console.print(Panel(content, border_style=color.split()[-1], box=box.ROUNDED))

    @staticmethod
    def print_pcap_report(report: Dict[str, Any]):
        """Render full PCAP forensic analysis report."""
        f_info = report["file_info"]
        metrics = report["metrics"]

        # 1. Capture Overview Table
        info_table = Table(title="Capture Forensic Metadata", box=box.ROUNDED, border_style="cyan")
        info_table.add_column("Property", style="bold white")
        info_table.add_column("Value", style="cyan")

        info_table.add_row("File Path", f_info["file_path"])
        info_table.add_row("File Size", f_info["file_size_formatted"])
        info_table.add_row("Total Packets Analyzed", str(f_info["analyzed_packets"]))
        info_table.add_row("Capture Duration", f"{f_info['duration_seconds']} seconds")
        info_table.add_row("Average Throughput", f"{metrics['average_bandwidth_kbps']} Kbps ({metrics['average_pps']} pkts/s)")
        info_table.add_row("Anomalies / Threats Detected", f"[bold red]{report['anomalies_detected']}[/]")
        console.print(info_table)
        console.print()

        # 2. Protocol Distribution Table
        proto_table = Table(title="Protocol Breakdown", box=box.ROUNDED, border_style="green")
        proto_table.add_column("Protocol", style="bold magenta")
        proto_table.add_column("Packets", style="green", justify="right")
        proto_table.add_column("Percentage", style="cyan", justify="right")

        total_pkts = max(1, f_info["analyzed_packets"])
        for proto, count in report["protocol_breakdown"].items():
            pct = round((count / total_pkts) * 100, 1)
            proto_table.add_row(proto, str(count), f"{pct}%")
        console.print(proto_table)
        console.print()

        # 3. Top Talkers Table
        talker_table = Table(title="Top Source & Destination Talkers", box=box.ROUNDED, border_style="blue")
        talker_table.add_column("Top Source IPs", style="cyan")
        talker_table.add_column("Pkts", style="dim", justify="right")
        talker_table.add_column("Top Destination IPs", style="yellow")
        talker_table.add_column("Pkts", style="dim", justify="right")

        sources = report["top_sources"]
        dests = report["top_destinations"]
        rows = max(len(sources), len(dests))
        for i in range(rows):
            src_ip = sources[i]["ip"] if i < len(sources) else ""
            src_pkts = str(sources[i]["packets"]) if i < len(sources) else ""
            dst_ip = dests[i]["ip"] if i < len(dests) else ""
            dst_pkts = str(dests[i]["packets"]) if i < len(dests) else ""
            talker_table.add_row(src_ip, src_pkts, dst_ip, dst_pkts)
        console.print(talker_table)
        console.print()

        # 4. Anomalies Table
        if report["anomalies_detected"] > 0:
            threat_table = Table(title="Detected Anomalies & Security Threats", box=box.ROUNDED, border_style="red")
            threat_table.add_column("Severity", style="bold", justify="center")
            threat_table.add_column("Threat Rule", style="bold white")
            threat_table.add_column("Source", style="cyan")
            threat_table.add_column("Target", style="yellow")
            threat_table.add_column("Remediation Action", style="italic green")

            sev_colors = {
                Severity.CRITICAL: "bold red",
                Severity.HIGH: "red",
                Severity.MEDIUM: "yellow",
                Severity.LOW: "blue"
            }
            for a in report["anomalies"]:
                col = sev_colors.get(a["severity"], "white")
                threat_table.add_row(
                    f"[{col}]{a['severity']}[/]",
                    a["rule_name"],
                    a["source"][:25],
                    a["target"][:25],
                    a["recommendation"][:45] + "..."
                )
            console.print(threat_table)
        else:
            console.print("[bold green][✓] Clean Capture: Zero anomalous patterns detected.[/]")

    @staticmethod
    def print_scan_report(report: Dict[str, Any]):
        """Render Port Scan Results Table."""
        console.print(f"[bold cyan]Port Scan Report for Target:[/] [white]{report['target']} ({report['target_ip']})[/]")
        console.print(f"[dim]Scanned {report['scanned_ports_count']} ports in {report['scan_duration_seconds']}s | Found {report['open_ports_count']} open ports[/]\n")

        table = Table(title=f"Open Port Services ({report['open_ports_count']} Active)", box=box.ROUNDED, border_style="cyan")
        table.add_column("Port", style="bold green", justify="right")
        table.add_column("State", style="green")
        table.add_column("Service", style="bold yellow")
        table.add_column("Latency (RTT)", style="cyan", justify="right")
        table.add_column("Banner / Fingerprint", style="dim italic")

        if not report["open_ports"]:
            table.add_row("-", "closed/filtered", "No open ports identified", "-", "-")
        else:
            for p in report["open_ports"]:
                table.add_row(
                    str(p["port"]),
                    p["state"],
                    p["service"],
                    f"{p['rtt_ms']} ms",
                    p["banner"] or "[no banner]"
                )
        console.print(table)

    @staticmethod
    def print_health_report(report: Dict[str, Any]):
        """Render Network Health & Dropout Diagnostics Table."""
        verdict = report["verdict"]
        v_color = "green" if "HEALTHY" in verdict else ("yellow" if "DEGRADED" in verdict else "red")

        m = report["metrics"]
        console.print(Panel(
            f"[bold {v_color}]DIAGNOSTIC VERDICT: {verdict}[/]\n"
            f"[white]Target: {report['target']}:{report['port']} | Probes: {m['total_probes']} | Loss: {m['packet_loss_pct']}%[/]\n"
            f"[dim]Latency: Avg {m['avg_rtt_ms']}ms (Min {m['min_rtt_ms']}ms / Max {m['max_rtt_ms']}ms) | Jitter: {m['jitter_ms']}ms[/]",
            title="Automated Network Health Diagnostic",
            border_style=v_color,
            box=box.ROUNDED
        ))

        if report["dropouts"]:
            drop_table = Table(title="Detected Connectivity Dropout Events", box=box.ROUNDED, border_style="red")
            drop_table.add_column("Start Time", style="cyan")
            drop_table.add_column("Duration", style="bold red")
            drop_table.add_column("Failed Probes", style="yellow")
            for d in report["dropouts"]:
                drop_table.add_row(d["formatted_start"], f"{d['duration_seconds']}s", str(d["failed_probes"]))
            console.print(drop_table)

        rec_table = Table(title="Diagnostic Recommendations", box=box.ROUNDED, border_style="green")
        rec_table.add_column("Remediation Step", style="white")
        for rec in report["recommendations"]:
            rec_table.add_row(f"[bold green]•[/] {rec}")
        console.print(rec_table)
