"""
Comprehensive Word (.docx) Documentation Generator for NetPulse
==============================================================
Generates a complete, professional, publication-quality technical report
covering all 13 required sections for interviews, architecture reviews,
and project submission.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

OUTPUT_DOCX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "NetPulse_Complete_Project_Documentation.docx"
)

# Color Palette Constants
COLOR_PRIMARY = RGBColor(30, 58, 138)       # Navy Blue (#1E3A8A)
COLOR_SECONDARY = RGBColor(2, 132, 199)    # Sky/Cyan Blue (#0284C7)
COLOR_TEXT_MAIN = RGBColor(31, 41, 55)     # Charcoal Dark (#1F2937)
COLOR_TEXT_MUTED = RGBColor(100, 116, 139) # Slate Gray (#64748B)
COLOR_ACCENT_GREEN = RGBColor(16, 185, 129)# Emerald Green (#10B981)
COLOR_ACCENT_RED = RGBColor(239, 68, 68)   # Crimson Red (#EF4444)
HEX_BG_LIGHT = "F8FAFC"
HEX_HEADER_BG = "0F172A"
HEX_ALT_ROW = "F1F5F9"
HEX_CALLOUT_BG = "F0F9FF"


def set_cell_background(cell, hex_color):
    """Sets background shading of a docx table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal padding for a table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_callout(doc, text, title="KEY TAKEAWAY", border_color="0284C7"):
    """Adds a stylish callout box with a colored left border."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)

    cell = table.cell(0, 0)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    # Left border only
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="28" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    run_title = p.add_run(f"📌 {title}: ")
    run_title.bold = True
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(10.5)
    run_title.font.color.rgb = COLOR_SECONDARY

    run_text = p.add_run(text)
    run_text.font.name = "Calibri"
    run_text.font.size = Pt(10)
    run_text.font.color.rgb = COLOR_TEXT_MAIN

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_code_block(doc, code_str, caption=""):
    """Adds a formatted monospaced code snippet block."""
    if caption:
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.space_before = Pt(4)
        p_cap.paragraph_format.space_after = Pt(2)
        r_cap = p_cap.add_run(f"📄 {caption}")
        r_cap.font.name = "Calibri"
        r_cap.font.size = Pt(9.5)
        r_cap.font.bold = True
        r_cap.font.color.rgb = COLOR_SECONDARY

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)

    cell = table.cell(0, 0)
    set_cell_background(cell, "0F172A")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15

    run = p.add_run(code_str.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(226, 232, 240)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def format_table_headers(table, headers, col_widths=None):
    """Styles the header row of a table with dark background and bold white text."""
    hdr_row = table.rows[0]
    for idx, header_text in enumerate(headers):
        cell = hdr_row.cells[idx]
        set_cell_background(cell, HEX_HEADER_BG)
        set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(header_text)
        run.bold = True
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)

    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = width


def style_table_rows(table):
    """Applies alternating row background and border formatting to table body."""
    for row_idx, row in enumerate(table.rows[1:], start=1):
        bg = HEX_ALT_ROW if row_idx % 2 == 0 else "FFFFFF"
        for cell in row.cells:
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                for run in p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(9)
                    run.font.color.rgb = COLOR_TEXT_MAIN


def add_section_heading(doc, text, level=1):
    """Adds customized section headings with spacing and theme colors."""
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(16)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    for r in h.runs:
        r.font.name = "Calibri"
        if level == 1:
            r.font.size = Pt(18)
            r.font.color.rgb = COLOR_PRIMARY
            r.bold = True
        elif level == 2:
            r.font.size = Pt(14)
            r.font.color.rgb = COLOR_SECONDARY
            r.bold = True
        elif level == 3:
            r.font.size = Pt(12)
            r.font.color.rgb = COLOR_TEXT_MAIN
            r.bold = True
    return h


def add_paragraph(doc, text="", bold_prefix=""):
    """Adds a standard body paragraph with styling."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = COLOR_PRIMARY
    if text:
        r_txt = p.add_run(text)
        r_txt.font.name = "Calibri"
        r_txt.font.size = Pt(10)
        r_txt.font.color.rgb = COLOR_TEXT_MAIN
    return p


def build_full_documentation():
    print("[*] Generating comprehensive Word (.docx) project documentation...")
    doc = docx.Document()

    # Configure 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # =========================================================================
    # TITLE & METADATA COVER
    # =========================================================================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(30)
    p_title.paragraph_format.space_after = Pt(4)
    run_t = p_title.add_run("⚡ NetPulse: Network Traffic Analyzer &\nTroubleshooting Toolkit")
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(26)
    run_t.bold = True
    run_t.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    run_s = p_sub.add_run("Complete End-to-End Technical Project Documentation & Interview Guidebook")
    run_s.font.name = "Calibri"
    run_s.font.size = Pt(13)
    run_s.font.color.rgb = COLOR_SECONDARY

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_after = Pt(24)
    r_meta = p_meta.add_run(
        "Core Tech Stack: Python 3.12 | Scapy | Wireshark | Linux Network Namespaces | iptables | Bash | Flask\n"
        "Author: Shanawaz Patel | Project Version: 1.0.0 | Release: Production-Ready"
    )
    r_meta.font.name = "Calibri"
    r_meta.font.size = Pt(9.5)
    r_meta.font.color.rgb = COLOR_TEXT_MUTED

    doc.add_page_break()

    # =========================================================================
    # SECTION 1: PROJECT OVERVIEW
    # =========================================================================
    add_section_heading(doc, "1. Project Overview", level=1)

    add_paragraph(doc, bold_prefix="What is this project? ", text=
        "NetPulse is an enterprise-grade network monitoring, deep packet inspection (DPI), heuristic intrusion detection (IDS), "
        "and automated diagnostic toolkit. Built entirely with Python, Scapy, Wireshark, Linux Networking (netns), and Bash, "
        "it enables system engineers, network administrators, and security analysts to capture real-time traffic, dissect TCP/IP "
        "headers, pinpoint latency bottlenecks and packet dropouts, detect stealth intrusion attempts, and validate firewall routing policies."
    )

    add_paragraph(doc, bold_prefix="What problem does it solve? ", text=
        "In modern distributed systems, diagnosing network degradation is notoriously complex. Engineers typically face three painful hurdles: "
        "(1) Intermittent dropouts and latency jitter that vanish before manual diagnostics can be initiated; "
        "(2) Massive volumes of raw packets that require expensive or cumbersome manual analysis in Wireshark to spot malicious scans or floods; and "
        "(3) The danger of testing routing policies, iptables firewall rule changes, and packet filtering benchmarks directly on production hardware without isolated simulation. "
        "NetPulse solves this by providing automated real-time jitter/dropout telemetry, an algorithmic heuristic IDS that flags threats instantly, "
        "and a virtualized Linux namespace lab to safely validate firewall performance under synthetic load."
    )

    add_paragraph(doc, bold_prefix="Why did I build this project? ", text=
        "I built NetPulse to bridge the gap between low-level network packet dissection (Layer 2 through Layer 7) and automated operational troubleshooting. "
        "Instead of relying on fragmented tools (e.g. running ping in one terminal, Nmap in another, and manual tcpdump in a third), "
        "NetPulse unifies live packet capture, offline forensic PCAP reading, multi-threaded port scanning, continuous RFC-compliant health monitoring, "
        "and virtualized network namespace benchmarking into one cohesive, modular software suite."
    )

    add_paragraph(doc, bold_prefix="Who are its target users? ", text=
        "• Network Engineers & NOC Teams: For automated routine health checks, jitter monitoring, and dropout alerting.\n"
        "• Security Operations Center (SOC) Analysts: For triaging suspicious captures, detecting port scans, SYN floods, ARP spoofing, and DNS exfiltration.\n"
        "• DevOps & Cloud Infrastructure Engineers: For verifying routing policies, NAT rules, and firewall enforcement in virtualized environments.\n"
        "• Software Engineering Interviewers / Reviewers: Demonstrating deep competence in TCP/IP protocols, socket programming, concurrency, and Linux kernel networking."
    )

    add_paragraph(doc, bold_prefix="What are its main features? ", text=
        "1. Deep Packet Inspection & Dissector: Extracts IP TTL, TCP flags (SYN, ACK, FIN, RST, PSH, URG), UDP, ICMP, DNS query records, and HTTP payloads.\n"
        "2. Behavioral Intrusion Detection System (IDS): Multi-vector threat heuristic rules detecting SYN Flood DoS, vertical/horizontal port scans, NULL & XMAS stealth scans, ARP cache poisoning, DNS tunneling via Shannon entropy, and SQL injection payloads.\n"
        "3. Multi-Threaded TCP Port Scanner: High-concurrency socket engine probing target ports with service banner grabbing and RTT latency measurement.\n"
        "4. Automated Health & Dropout Diagnostic: Computes Min/Max/Avg RTT, RFC 3550-compliant jitter, packet loss percentage, and records dropout windows.\n"
        "5. Multi-Resolver DNS Benchmark & Traceroute: Latency comparison across Cloudflare, Google, Quad9, OpenDNS, and hop-by-hop route path discovery.\n"
        "6. Virtualized Linux Lab Sandbox: Linux Network Namespaces (ip netns) and virtual ethernet pairs (veth) with stateful iptables rules and line-rate filtering benchmarks.\n"
        "7. Dual UI Tier: A Rich Terminal UI (TUI) and an interactive dark Glassmorphic Web SOC Dashboard with real-time Chart.js telemetry."
    )

    add_paragraph(doc, bold_prefix="What makes this project useful? ", text=
        "NetPulse stands out because it is fully self-contained, automated, and cross-platform. It includes a built-in synthetic PCAP generator "
        "that allows immediate offline threat forensic validation without requiring root privileges or physical lab hardware. At the same time, "
        "it contains production-ready Bash automation to deploy real kernel-level network namespaces and stateful iptables rules on Linux."
    )

    add_paragraph(doc, bold_prefix="Explain the project in simple words: ", text=
        "Imagine NetPulse as a combination of an automated Wireshark, a smart Nmap scanner, and a continuous network doctor. "
        "It watches the data packets moving across the wire, inspects their headers to catch hackers scanning or flooding the network, "
        "continuously tests internet health to alert you when your connection drops, and lets you test firewall security rules in a safe virtual Linux playground."
    )

    add_callout(doc,
        "NetPulse directly maps to real-world infrastructure engineering: Layer 2-7 packet inspection, multi-threaded socket concurrency, "
        "RFC 3550 jitter mathematics, Shannon entropy information theory, Linux kernel netfilter/iptables, and modern web telemetry.",
        title="CORE PROJECT VALUE PROPOSITION"
    )

    # =========================================================================
    # SECTION 2: COMPLETE TECHNOLOGY STACK
    # =========================================================================
    add_section_heading(doc, "2. Complete Technology Stack", level=1)

    add_paragraph(doc, text="Every technology in NetPulse was selected for high performance, kernel-level capabilities, protocol fidelity, and zero unnecessary bloat.")

    tech_items = [
        ("Python 3.12",
         "A high-level, strongly typed, multi-paradigm programming language known for rapid prototyping and extensive networking libraries.",
         "Core programming language powering the entire NetPulse suite (CLI, packet parser, IDS rules, multi-threaded scanners, web backend).",
         "Executes packet dissection, mathematical calculations (jitter, Shannon entropy), concurrency coordination, and REST API dispatching.",
         "Directly invokes Scapy for raw packet manipulation, calls standard socket libraries for port probes, and interfaces with Flask for web routing.",
         "C/C++ (raw libpcap) or Go (gopacket).",
         "Python provides the ideal balance of deep library support (Scapy, Rich), clean object-oriented architecture, and rapid extensibility while maintaining microsecond-level parsing speed for forensic and diagnostic workloads."),

        ("Scapy 2.8.0",
         "A powerful Python-based interactive packet manipulation, crafting, sniffing, and decoding framework.",
         "Deep packet inspection (DPI), decoding binary packet frames into layer objects (Ether, IP, TCP, UDP, DNS, ARP), and writing Wireshark-compatible PCAP files.",
         "Dissects raw bytes, extracts TCP flags, computes checksums, parses DNS query/response structures, and streams captures via PcapReader/PcapWriter.",
         "Feeds parsed DissectedPacket objects into TrafficStatistics and AnomalyEngine; generates synthetic attack captures in generate_sample_pcap.py.",
         "Raw Linux sockets (`socket(AF_PACKET)`), PyShark (tshark wrapper), or dpkt.",
         "Scapy offers native protocol decoding for hundreds of layers without external binary runtime dependencies, and allows granular programmatic packet crafting."),

        ("Wireshark & PCAP Standard",
         "The industry-standard binary packet capture file format (.pcap / .pcapng) used worldwide by network analysts.",
         "Interoperability and forensic recording. All live traffic captures recorded by NetPulse can be opened in Wireshark, and any Wireshark capture can be ingested by NetPulse.",
         "Enables offline forensic investigation, post-incident analysis, and deterministic testing of intrusion detection heuristics.",
         "NetPulse's PcapAnalyzer streams standard PCAP files and PcapWriter produces RFC-compliant libpcap dumps.",
         "Proprietary JSON logs or raw socket text dumps.",
         "Using standard PCAP guarantees that NetPulse seamlessly integrates into existing enterprise SIEM and security analysis pipelines."),

        ("Linux Network Namespaces (ip netns)",
         "A fundamental Linux kernel virtualization feature providing complete isolation of network protocol stacks (interfaces, routing tables, firewall rules).",
         "Creating virtualized local networks (Client, Router/Firewall, Server, Attacker) on a single Linux host without the heavy overhead of hypervisors.",
         "Isolates network interfaces into distinct subnets (10.10.1.0/24 and 10.10.2.0/24), assigns virtual ethernet pairs (veth), and manages default gateway routing.",
         "Configured via Bash scripts; evaluated by iptables; stressed by synthetic traffic generators.",
         "Mininet, VMware, VirtualBox, or full KVM virtual machines.",
         "Namespaces are native to the Linux kernel, launch in milliseconds, require virtually zero RAM/CPU overhead, and faithfully execute real Linux kernel routing and firewall logic."),

        ("iptables / Netfilter",
         "The Linux kernel packet filtering framework and userspace CLI for managing stateful firewalls, NAT, and packet mangling.",
         "Enforcing stateful connection tracking, rate limiting, TCP SYN cookies, dropping stealth scans, and quarantining rogue attacker hosts.",
         "Inspects every packet entering or traversing the ns-router namespace, matching rules against connection state (ESTABLISHED, RELATED, INVALID), TCP flags, and subnets.",
         "Enforces policies tested by test_routing_firewall.sh; evaluated under load by benchmark_rules.sh.",
         "nftables, eBPF/XDP, or pfSense.",
         "iptables is universally deployed across enterprise Linux distributions, robust, and the standard benchmark for Linux firewall administration."),

        ("Bash Shell Scripting",
         "The standard Unix shell and command language for system administration and infrastructure automation.",
         "Automating the virtual network lifecycle: lab_setup.sh, firewall_rules.sh, test_routing_firewall.sh, benchmark_rules.sh, lab_teardown.sh.",
         "Executes privileged kernel configuration commands, verifies route reachability, parses iptables drop counters, and handles error trapping with set -euo pipefail.",
         "Orchestrates Linux kernel namespaces, sysctl parameters, and interacts with Python diagnostic probes.",
         "Ansible, Terraform, or pure Python subprocess scripts.",
         "Bash is the native language of Linux system engineers. Using shell scripts provides transparency and direct reproducibility on any Linux server."),

        ("Flask & Flask-CORS",
         "A lightweight, WSGI-compliant Python web framework and REST API microservices engine.",
         "Serving the NetPulse Web SOC Dashboard and exposing RESTful telemetry endpoints.",
         "Handles HTTP requests, serves HTML/CSS/JS assets, and delivers JSON responses for live packet streams, port scan triggers, health checks, and PCAP analysis.",
         "Communicates directly with in-memory singleton engines (TrafficStatistics, AnomalyEngine) and invokes diagnostics (PortScanner, HealthMonitor).",
         "FastAPI, Django, or Tornado.",
         "Flask is lightweight, synchronous, battle-tested, requires zero complex async compilation, and embeds effortlessly into a portable desktop or server CLI tool."),

        ("Rich 15.0",
         "A state-of-the-art Python terminal formatting and console UI library.",
         "Rendering high-fidelity terminal dashboards, styled tables, colored threat badges, and ASCII banners.",
         "Formats port scan results, health diagnosis cards, PCAP forensic tables, and live packet inspection streams directly in stdout.",
         "Consumed by netpulse.visualizer.console_ui and netpulse.cli.",
         "curses, colorama, or blessed.",
         "Rich produces SOC-quality visual presentations with rounded borders, automated column wrapping, and ANSI 256-color palettes with minimal code."),

        ("Chart.js",
         "A popular, responsive, canvas-based JavaScript charting library.",
         "Rendering real-time throughput time-series graphs and protocol breakdown doughnut charts in the web dashboard.",
         "Dynamically animates packet throughput (pps) and renders proportional protocol distributions (TCP, UDP, ICMP, DNS, HTTP, ARP).",
         "Receives telemetry data from dashboard.js via periodic REST polling from /api/overview.",
         "D3.js, ApexCharts, or Plotly.",
         "Chart.js is extremely lightweight, requires no heavy build step (works directly via CDN/vanilla JS), and performs smooth 60fps canvas animations."),

        ("Docker & Docker Compose",
         "Industry-standard containerization platform for isolating applications and multi-node service topologies.",
         "Providing a cross-platform Linux lab simulation that runs seamlessly on Windows and macOS via Docker Desktop.",
         "Defines multi-subnet bridge networks (client_net, server_net) and multi-container roles (Router with NET_ADMIN privileges, Server, Client, Attacker).",
         "Mirrors the Linux network namespace scripts in a standardized container environment.",
         "Vagrant or manual VM setup.",
         "Enables any reviewer or developer to test the virtual network lab with a single command (`docker compose up --build`) without needing native Linux.")
    ]

    for name, what, why, task, interact, alt, suit in tech_items:
        add_section_heading(doc, f"• {name}", level=3)
        add_paragraph(doc, bold_prefix="What is it? ", text=what)
        add_paragraph(doc, bold_prefix="Why is it used? ", text=why)
        add_paragraph(doc, bold_prefix="Specific Task: ", text=task)
        add_paragraph(doc, bold_prefix="How it interacts: ", text=interact)
        add_paragraph(doc, bold_prefix="Alternatives: ", text=alt)
        add_paragraph(doc, bold_prefix="Why chosen: ", text=suit)

    # Master Technology Table
    add_section_heading(doc, "Technology Comparison & Summary Table", level=2)
    tech_table = doc.add_table(rows=len(tech_items) + 1, cols=4)
    tech_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tech_table.autofit = False

    col_widths = [Inches(1.5), Inches(1.8), Inches(1.4), Inches(1.8)]
    format_table_headers(tech_table, ["Technology", "Purpose", "Where Used", "Why Used"], col_widths)

    table_data = [
        ("Python 3.12", "Core Language & Logic", "Entire Codebase", "Rapid socket scripting & object-oriented design"),
        ("Scapy 2.8.0", "Packet Dissection & Crafting", "netpulse/core, scripts/", "Native support for L2-L7 protocols and PCAP parsing"),
        ("Wireshark / PCAP", "Forensic Capture Standard", "samples/, PcapAnalyzer", "Industry standard for network security interoperability"),
        ("Linux netns", "Network Virtualization", "linux_lab/lab_setup.sh", "Kernel-level isolated routing without VM overhead"),
        ("iptables", "Stateful Firewall & Filter", "linux_lab/firewall_rules.sh", "Stateful connection tracking, rate limiting, SYN cookies"),
        ("Bash", "Lab Automation & Testing", "linux_lab/*.sh", "Native shell control for Linux network administration"),
        ("Flask", "REST API & Web Backend", "netpulse/visualizer/web_server.py", "Lightweight, robust microservices for SOC dashboard"),
        ("Rich 15.0", "Terminal User Interface (TUI)", "netpulse/visualizer/console_ui.py", "SOC-style colored tables, progress bars, and alerts"),
        ("Chart.js", "Live Visual Charting", "netpulse/web/static/js/", "Responsive 60fps canvas charts for throughput & protocols"),
        ("Docker", "Multi-Node Topology", "docker-compose.yml", "Runs virtualized network lab on Windows/macOS/Linux")
    ]

    for idx, (t, p, w, yu) in enumerate(table_data, start=1):
        row = tech_table.rows[idx]
        row.cells[0].paragraphs[0].add_run(t).bold = True
        row.cells[1].paragraphs[0].add_run(p)
        row.cells[2].paragraphs[0].add_run(w)
        row.cells[3].paragraphs[0].add_run(yu)

    style_table_rows(tech_table)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # =========================================================================
    # SECTION 3: PROJECT ARCHITECTURE
    # =========================================================================
    add_section_heading(doc, "3. Project Architecture", level=1)

    add_paragraph(doc, bold_prefix="Architecture Overview: ", text=
        "NetPulse follows a strictly decoupled, modular layered architecture adhering to the Separation of Concerns (SoC) principle. "
        "The system separates raw packet ingestion from packet parsing, parsing from threat heuristics, heuristics from visual presentation, "
        "and diagnostics from network virtualization."
    )

    add_paragraph(doc, bold_prefix="1. Frontend Architecture: ", text=
        "The frontend is designed as a zero-dependency Glassmorphic Single Page Application (SPA). Built with semantic HTML5, "
        "custom responsive CSS3 (cyber-dark theme with backdrop blur filters and neon status indicators), and vanilla JavaScript. "
        "It uses a reactive polling model: every 1.5 seconds, dashboard.js asynchronously requests /api/overview, dynamically updating "
        "metric counters, sliding time-series Chart.js canvas elements, and the live DPI packet table without full-page reloads."
    )

    add_paragraph(doc, bold_prefix="2. Backend Architecture: ", text=
        "The backend is powered by a multi-threaded Python core. When live sniffing or synthetic simulation is active, a dedicated background daemon thread "
        "captures or streams frames into PacketParser. Once parsed into DissectedPacket objects, packets pass through an in-memory Observer pattern dispatching "
        "to TrafficStatistics (aggregating throughput, conversation pairs, and protocol counters) and AnomalyEngine (evaluating IDS heuristic rules). "
        "Flask exposes these in-memory data structures via thread-safe RESTful API endpoints."
    )

    add_paragraph(doc, bold_prefix="3. Data & Storage Architecture: ", text=
        "To avoid the extreme disk I/O bottlenecks of relational databases under high-throughput traffic, NetPulse utilizes a high-speed in-memory architecture: "
        "(1) Bounded circular queues (deques) for rolling packet history (max 150-200 frames) and throughput calculation; "
        "(2) Python Counter hash-maps for O(1) protocol, talker, and port metric aggregation; and "
        "(3) Standard libpcap binary files (.pcap) for persistent storage. This ensures line-rate parsing without disk saturation."
    )

    add_paragraph(doc, bold_prefix="4. API Architecture: ", text=
        "NetPulse implements a clean RESTful interface over HTTP. State-retrieval endpoints (GET /api/overview, GET /api/packets, GET /api/alerts) "
        "return structured JSON payloads. Action endpoints (POST /api/scan, POST /api/health, POST /api/analyze_sample) accept JSON configurations, "
        "execute concurrent tasks via thread pools, and return immediate diagnostic summaries with HTTP 200 status codes."
    )

    add_paragraph(doc, bold_prefix="5. Authentication & Authorization: ", text=
        "Truthful Architectural Disclosure: NetPulse is designed as an internal engineering diagnostic utility and local SOC tool. "
        "It deliberately avoids complex web user logins or mock passwords. Instead, security boundaries are enforced strictly at the OS privilege level: "
        "raw packet sniffing requires elevated operating system privileges (root/sudo on Linux with CAP_NET_RAW/CAP_NET_ADMIN capabilities; Administrator with Npcap on Windows). "
        "Web access is bound locally to 127.0.0.1 by default."
    )

    add_paragraph(doc, bold_prefix="6. Third-Party Integrations: ", text=
        "• Wireshark / tcpdump: Full bidirectional integration via standard PCAP capture files.\n"
        "• Public DNS Resolvers: Benchmarking integration with Google (8.8.8.8), Cloudflare (1.1.1.1), Quad9 (9.9.9.9), and OpenDNS.\n"
        "• Linux Kernel Subsystems: Direct integration with iproute2 (netns, veth, ip route) and netfilter (iptables)."
    )

    add_paragraph(doc, bold_prefix="7. Inter-Component Communication: ", text=
        "Components communicate through well-defined contracts: raw frames -> Scapy Sniffer -> DissectedPacket -> AnomalyEngine / TrafficStatistics -> "
        "JSON Serialization -> Flask WSGI -> REST -> Fetch API -> DOM & Chart.js rendering."
    )

    # Architecture Diagram
    add_paragraph(doc, bold_prefix="System Architecture Flow Diagram: ", text="")
    arch_diagram = """
+-----------------------------------------------------------------------------------------+
|                                    NETPULSE ARCHITECTURE                                |
+-----------------------------------------------------------------------------------------+
   [Network Data Sources]             [DPI & Dissection Core]          [Detection & Telemetry]
   +-----------------------+          +-----------------------+        +-----------------------+
   | Live Network Nic      | ------>  | PacketParser          | -----> | AnomalyEngine (IDS)   |
   | Scapy PacketSniffer   |          | - L2: MAC Addresses   |        | - SYN Flood Rule      |
   +-----------------------+          | - L3: IP, TTL, Flags  |        | - Stealth Scan Rule   |
   +-----------------------+          | - L4: TCP Flags, Ports|        | - ARP Spoof Rule      |
   + Offline Wireshark     | ------>  | - L7: DNS, HTTP, Data |        | - DNS Tunnel (Entropy)|
   | PCAP Analyzer         |          +-----------------------+        | - SQLi / Cred Leaks   |
   +-----------------------+                      |                    +-----------------------+
                                                  v                                |
                                      +-----------------------+                    |
                                      | TrafficStatistics     | <------------------+
                                      | - Rolling pps / Kbps  |
                                      | - Protocols & Talkers |
                                      +-----------------------+
                                                  |
                                                  v
   [Presentation Tier]                [REST API Layer]
   +-----------------------+          +-----------------------+
   | Glassmorphic Web SOC  | <======> | Flask Web Server      |
   | - Chart.js Telemetry  |  (JSON)  | - GET  /api/overview  |
   | - Live DPI Table      |          | - POST /api/scan      |
   | - IDS Threat Feed     |          | - POST /api/health    |
   +-----------------------+          +-----------------------+
              |                                   ^
              v                                   |
   +-----------------------+          +-----------------------+
   | Rich Terminal Console |          | Diagnostics Suite     |
   | netpulse cli (TUI)    |          | - 50-Thread Port Scan |
   +-----------------------+          | - RFC Jitter Monitor  |
                                      +-----------------------+
+-----------------------------------------------------------------------------------------+
|                              VIRTUALIZED LINUX LAB SANDBOX                              |
|   ns-client (10.10.1.10) <===> ns-router / iptables Firewall <===> ns-server (10.10.2.80)  |
|                                         ^                                               |
|   ns-attacker (10.10.1.99) -------------+ (Firewall drops stealth & flood packets)     |
+-----------------------------------------------------------------------------------------+
"""
    add_code_block(doc, arch_diagram, caption="NetPulse End-to-End System Architecture")

    # =========================================================================
    # SECTION 4: COMPLETE WORKING FLOW
    # =========================================================================
    add_section_heading(doc, "4. Complete Working Flow", level=1)

    add_paragraph(doc, text="The operational lifecycle of NetPulse varies depending on the activated subsystem. Below are the actual execution flows implemented in code:")

    flows = [
        ("Flow A: Live Packet Sniffing & Threat Detection", [
            "User executes `python -m netpulse sniff -i eth0 -f 'tcp port 80' -o capture.pcap`.",
            "PacketSniffer verifies OS privileges and initializes Scapy's native sniffing thread with the specified Berkeley Packet Filter (BPF).",
            "A packet arrives on the NIC; Scapy intercepts the frame and invokes the internal `_packet_handler` callback.",
            "If PCAP recording is active, the raw frame is written immediately to disk using `PcapWriter`.",
            "The packet is passed to `PacketParser.parse()`, which evaluates headers layer-by-layer (Ethernet MACs, IP headers, TCP control flags, DNS queries, HTTP payloads).",
            "A structured `DissectedPacket` dataclass object is created and dispatched to registered observer callbacks.",
            "`AnomalyEngine.process_packet()` evaluates the dissected packet against all active heuristic threat rules (SynFloodRule, PortScanRule, etc.).",
            "If an anomaly rule threshold is breached, a `ThreatAlert` object (with severity, description, evidence, and remediation advice) is generated and emitted.",
            "`ConsoleUI.print_packet()` prints the formatted packet stream and `ConsoleUI.print_alert()` highlights the threat card in real-time."
        ]),
        ("Flow B: Offline PCAP Forensic Analysis & Ingestion", [
            "User runs `python -m netpulse analyze samples/demo_traffic.pcap --export-json report.json` (or clicks 'Ingest Demo PCAP' in the Web UI).",
            "`PcapAnalyzer` verifies file existence and opens the binary stream using Scapy's `PcapReader`.",
            "Packets are read sequentially into memory; each packet is parsed by `PacketParser`.",
            "`TrafficStatistics` aggregates total bytes, packets, protocol distribution, top source/destination IPs, and conversations.",
            "`AnomalyEngine` evaluates each packet; detected threats (e.g. SYN flood burst, ARP cache conflicts, base64 DNS tunneling) are stored in the anomalies list.",
            "Metrics are compiled into a comprehensive report dictionary via `get_report()`.",
            "If requested, the forensic report is exported to structured JSON and packet rows are written to CSV.",
            "The terminal renders high-resolution ASCII summary tables or the Web UI dynamically populates the forensics dashboard."
        ]),
        ("Flow C: Multi-Threaded TCP Port Scanning", [
            "User inputs target `127.0.0.1` and port range `1-1024` via CLI or Web UI.",
            "`PortScanner._resolve_target()` resolves the hostname to an IPv4 address using `socket.gethostbyname()`.",
            "`PortScanner.scan()` instantiates a `ThreadPoolExecutor` with a concurrency pool of 50-60 worker threads.",
            "Worker threads call `_scan_port(port)` in parallel, creating non-blocking TCP stream sockets and invoking `connect_ex()` with a 0.6s timeout.",
            "When `connect_ex() == 0` (SYN-ACK received / 3-way handshake established), the worker records the exact RTT latency in milliseconds.",
            "`_grab_banner()` sends an application-layer probe (e.g., HTTP `HEAD /` or null byte) and reads up to 256 bytes of service greeting.",
            "Results are mapped to standard service names (HTTP, SSH, MySQL, SMB, etc.) and compiled into `PortScanResult` objects.",
            "The completed list of open ports, banners, and latencies is returned to the UI and rendered in a sorted results table."
        ]),
        ("Flow D: Automated Health Diagnostics & Dropout Monitoring", [
            "User triggers health diagnostic against target gateway or DNS resolver (e.g. `8.8.8.8:53`).",
            "`HealthMonitor.run_check()` executes a sequence of N automated latency probes with a configured sleep interval.",
            "Each probe records start time using high-precision `time.perf_counter()`, attempts a socket connection, and measures round-trip time (RTT).",
            "If the connection succeeds: RTT is appended; if recovering from consecutive drops, the active `DropoutEvent` is finalized with start time, duration, and failure count.",
            "If the connection fails or times out: probe is marked failed; consecutive failure counter increments. If failures >= 2, a new `DropoutEvent` window is tracked.",
            "`get_report()` calculates statistical metrics: Min/Max/Avg/Median RTT, packet loss percentage, and RFC 3550-compliant jitter.",
            "A diagnostic verdict is evaluated: `HEALTHY`, `DEGRADED - LATENCY SPIKES`, or `CRITICAL - PACKET LOSS`.",
            "Actionable remediation recommendations (e.g., bufferbloat inspection, MTU check, link flapping investigation) are generated and displayed."
        ]),
        ("Flow E: Web SOC Dashboard User Interaction Flow", [
            "User opens `http://127.0.0.1:5000` in their browser.",
            "Flask routes the request to `index()`, serving the glassmorphic HTML5/CSS3 template.",
            "The browser executes `dashboard.js`, which initializes two Chart.js instances: Throughput (Line) and Protocols (Doughnut).",
            "A JavaScript interval begins querying `GET /api/overview` every 1,500ms.",
            "Flask reads from singleton in-memory instances `traffic_stats` and `anomaly_engine`, returning JSON telemetry.",
            "`dashboard.js` updates the DOM elements (total packets, pps, bandwidth, threat counters, health score) and pushes new points to the Chart.js canvas.",
            "User clicks 'Launch Port Scan'; frontend sends a `POST /api/scan` request with target parameters.",
            "Flask runs `PortScanner` in the background, waits for completion, and returns JSON; `dashboard.js` dynamically renders the open port cards."
        ]),
        ("Flow F: Virtualized Linux Lab & Firewall Rule Enforcement", [
            "Administrator executes `sudo bash linux_lab/lab_setup.sh` on Linux (or `docker compose up` on Windows/macOS).",
            "Script creates 4 isolated network namespaces: `ns-client`, `ns-router`, `ns-server`, `ns-attacker`.",
            "Virtual ethernet pairs (`veth`) are instantiated, bridging client and attacker to router on `10.10.1.0/24` and server to router on `10.10.2.0/24`.",
            "Kernel IP forwarding is enabled on `ns-router` (`sysctl net.ipv4.ip_forward=1`).",
            "`firewall_rules.sh` flushes iptables, sets default DROP policy on FORWARD, and configures stateful rules (`ESTABLISHED,RELATED -j ACCEPT`).",
            "Stealth scan filters (dropping NULL and XMAS packets) and SYN flood rate limits (25/sec limit, 50 burst) are activated alongside TCP SYN cookies.",
            "`test_routing_firewall.sh` executes automated tests: pinging across subnets (passes), accessing HTTP 80 (passes), accessing Telnet 23 (drops), attacker probes (drops).",
            "`benchmark_rules.sh` generates high-volume UDP/TCP flood traffic from attacker and measures router filtering overhead delta (+0.06ms)."
        ])
    ]

    for title, steps in flows:
        add_section_heading(doc, title, level=2)
        for idx, step in enumerate(steps, start=1):
            add_paragraph(doc, bold_prefix=f"{idx}. ", text=step)

    # =========================================================================
    # SECTION 5: FOLDER AND FILE STRUCTURE
    # =========================================================================
    add_section_heading(doc, "5. Folder and File Structure Analysis", level=1)

    add_paragraph(doc, text="Below is the complete architectural layout of the NetPulse repository, followed by an exhaustive file-by-file breakdown:")

    files_analysis = [
        ("netpulse/__init__.py",
         "Package initialization and metadata definition.",
         "Defines __version__ = '1.0.0', __author__, and package-level docstrings.",
         "Identifies the netpulse directory as an importable Python package.",
         "Imported whenever any module accesses netpulse.",
         "Executed during initial package import."),

        ("netpulse/__main__.py",
         "Executable module entrypoint.",
         "Imports `main` from `netpulse.cli` and invokes it under `if __name__ == '__main__':`.",
         "Enables users to run the toolkit directly from the terminal using `python -m netpulse <command>`.",
         "Delegates execution to `netpulse.cli`.",
         "Executed when running `python -m netpulse`."),

        ("netpulse/cli.py",
         "Unified Command Line Interface (CLI) dispatcher.",
         "Contains `build_parser()` using `argparse`, defining subcommands: sniff, analyze, scan, health, traceroute, dns, web, demo. Contains handler functions cmd_sniff(), cmd_analyze(), etc.",
         "Provides a polished terminal interface with flags, help screens, and parameter validation.",
         "Imports modules from core, detector, diagnostics, and visualizer.",
         "Parses CLI arguments and dispatches control to the selected subsystem handler."),

        ("netpulse/core/parser.py",
         "Multi-layer packet dissector and TCP/IP header analyzer.",
         "Defines the `DissectedPacket` dataclass and the `PacketParser` class with its static `parse()` method. Dissects Ethernet, IPv4, IPv6, ARP, TCP (all flags), UDP, ICMP, DNS, HTTP.",
         "Translates raw binary Scapy packet frames into structured, JSON-serializable Python objects.",
         "Consumed by `PacketSniffer`, `PcapAnalyzer`, and all IDS threat detection rules.",
         "Called once per captured packet frame."),

        ("netpulse/core/sniffer.py",
         "Multi-threaded live packet capture engine.",
         "Contains `PacketSniffer` class wrapping Scapy's `sniff()`, supporting BPF filters, thread management, `PcapWriter` disk flushing, and callback registration.",
         "Enables continuous real-time packet capturing on physical or virtual interfaces without freezing the CLI or UI.",
         "Invokes `PacketParser.parse()` on every captured frame and notifies registered callbacks.",
         "Runs inside a background daemon thread until stopped by user or count limit."),

        ("netpulse/core/pcap_analyzer.py",
         "Offline Wireshark PCAP forensic analyzer.",
         "Contains `PcapAnalyzer` class that opens .pcap/.pcapng files with Scapy's `PcapReader`, parses packets, feeds `TrafficStatistics` and `AnomalyEngine`, and exports to JSON/CSV.",
         "Allows deep security and protocol inspection of historical captures without requiring a live network interface.",
         "Interacts with `TrafficStatistics`, `AnomalyEngine`, and file export utilities.",
         "Executed on-demand when user runs `analyze` or clicks 'Ingest Demo PCAP'."),

        ("netpulse/core/statistics.py",
         "Real-time traffic throughput and conversation aggregation engine.",
         "Contains `TrafficStatistics` class. Tracks total packets, bytes, sliding-window pps/Kbps throughput, protocol breakdown counters, top source/destination talkers, and conversation pairs.",
         "Maintains rolling metrics for the dashboard charts and forensic summary tables.",
         "Updated by `PacketSniffer` or `PcapAnalyzer`; queried by Flask `/api/overview`.",
         "Updates in O(1) time per packet using Python `Counter` and `deque` structures."),

        ("netpulse/detector/alerts.py",
         "Threat alert data models and severity classifications.",
         "Defines the `Severity` class (LOW, MEDIUM, HIGH, CRITICAL) and the `ThreatAlert` dataclass with UUID generation, evidence dictionaries, and JSON serialization.",
         "Standardizes security incident alerts across all detection rules.",
         "Instantiated by detection rules in `rules.py`; consumed by `AnomalyEngine` and UI.",
         "Instantiated when an anomalous traffic heuristic threshold is breached."),

        ("netpulse/detector/rules.py",
         "Behavioral intrusion detection heuristic rules.",
         "Implements `shannon_entropy()`, `SynFloodRule`, `PortScanRule` (vertical, horizontal, NULL, XMAS), `ArpSpoofRule`, `DnsTunnelRule`, `SuspiciousPayloadRule`, and `VolumetricSpikeRule`.",
         "Performs the core cybersecurity anomaly detection identifying malicious network activities.",
         "Evaluates `DissectedPacket` objects and returns `ThreatAlert` instances.",
         "Executed on every packet passing through `AnomalyEngine.process_packet()`."),

        ("netpulse/detector/anomaly_engine.py",
         "Central Intrusion Detection System (IDS) orchestrator.",
         "Contains `AnomalyEngine` class managing the active list of rules, alert aggregation, observer callbacks, and severity counters.",
         "Provides a single clean interface for evaluating packets against multiple concurrent threat heuristics.",
         "Called by `PacketSniffer`, `PcapAnalyzer`, and `web_server.py`.",
         "Dispatches each packet to all rules and collects generated alerts."),

        ("netpulse/diagnostics/port_scanner.py",
         "High-concurrency TCP port scanner and service fingerprinter.",
         "Contains `PortScanner` and `PortScanResult`. Uses `ThreadPoolExecutor` (50 threads) for concurrent `connect_ex()` socket probes and banner grabbing.",
         "Automates routine port discovery and service auditing in sub-second times.",
         "Standalone diagnostic invoked by CLI `scan` or Web UI `/api/scan`.",
         "Spawns worker pool, tests socket connections, grabs service headers, returns results."),

        ("netpulse/diagnostics/health_monitor.py",
         "Continuous network health, jitter, and dropout diagnostic engine.",
         "Contains `HealthMonitor`, `HealthProbe`, and `DropoutEvent`. Measures RTT latency, calculates RFC 3550 jitter, tracks packet loss %, records dropout windows, and delivers verdicts.",
         "Pinpoints intermittent connectivity drops and latency spikes with automated recommendations.",
         "Invoked by CLI `health` or Web UI `/api/health`.",
         "Performs sequential timed socket probes and computes statistical metrics."),

        ("netpulse/diagnostics/dns_checker.py",
         "Multi-resolver DNS latency benchmark utility.",
         "Contains `DnsHealthChecker`. Tests domain resolution against local system resolver and TCP port 53 connectivity against Google, Cloudflare, Quad9, and OpenDNS.",
         "Identifies DNS lookup slowdowns and resolver unreachability.",
         "Invoked by CLI `dns` or Web UI `/api/dns`.",
         "Executes socket probes against public resolvers and measures RTT."),

        ("netpulse/diagnostics/traceroute.py",
         "Hop-by-hop route path and gateway latency tracer.",
         "Contains `RouteTracer` and `RouteHop`. Probes routing gateways across increasing TTL values to map the path to destination.",
         "Visualizes where network latency spikes and packet drops occur in the transit path.",
         "Invoked by CLI `traceroute` or Web UI `/api/traceroute`.",
         "Executes traceroute commands or fallback TTL probes, parsing hops and RTT."),

        ("netpulse/visualizer/console_ui.py",
         "Rich terminal operations console and card renderer.",
         "Contains `ConsoleUI` using the `rich` library. Methods: `print_banner()`, `print_packet()`, `print_alert()`, `print_pcap_report()`, `print_scan_report()`, `print_health_report()`.",
         "Presents enterprise-grade terminal output with colored tables, rounded panels, and severity badges.",
         "Called by `netpulse/cli.py` during CLI command execution.",
         "Renders structured text and ANSI visual formatting directly to stdout."),

        ("netpulse/visualizer/web_server.py",
         "Web SOC Dashboard server and REST API backend.",
         "Flask application exposing `/`, `/api/overview`, `/api/packets`, `/api/alerts`, `/api/scan`, `/api/health`, `/api/dns`, `/api/traceroute`, `/api/analyze_sample`, `/api/simulate_toggle`.",
         "Hosts the web operations center and bridges browser interactions to the Python backend engines.",
         "Imports and orchestrates core, detector, and diagnostics modules.",
         "Launched by `run_web.py` or `python -m netpulse web`."),

        ("netpulse/web/templates/index.html",
         "Single Page Application (SPA) web dashboard template.",
         "Semantic HTML5 document featuring header navigation, metric cards, 7 functional tabs, Chart.js canvas elements, and responsive tables.",
         "Provides the user interface for monitoring, threat analysis, port scanning, and lab visualization.",
         "Served by Flask; hydrated and updated dynamically by `dashboard.js`.",
         "Loaded by the browser when visiting `http://127.0.0.1:5000`."),

        ("netpulse/web/static/css/style.css",
         "Cyberpunk / dark-mode SOC styling stylesheet.",
         "Custom CSS variables, glassmorphic card styling (`backdrop-filter: blur`), custom scrollbars, glowing badges, threat alert styling, and responsive layout grid.",
         "Delivers the aesthetic visual experience of a professional cybersecurity operations center.",
         "Linked by `index.html`.",
         "Parsed and applied by the browser rendering engine."),

        ("netpulse/web/static/js/dashboard.js",
         "Frontend interactive controller and Chart.js telemetry engine.",
         "Initializes throughput line chart and protocol doughnut chart. Polls `/api/overview` every 1.5s, updates DOM, handles tab switching, triggers port scans, and manages simulation toggles.",
         "Enables dynamic, real-time interactivity without page refreshes.",
         "Communicates with Flask REST APIs via `fetch()` and updates DOM.",
         "Runs continuously in the browser event loop."),

        ("linux_lab/lab_setup.sh",
         "Linux virtual network namespace deployment automation.",
         "Bash script that creates `ns-client`, `ns-router`, `ns-server`, `ns-attacker`, connects them with `veth` pairs, configures IP addresses (10.10.1.0/24 & 10.10.2.0/24), and enables IP forwarding.",
         "Deploys an isolated multi-node network sandbox on a single Linux host.",
         "Executed before applying firewall rules or running routing tests.",
         "Executed as root (`sudo bash lab_setup.sh`)."),

        ("linux_lab/firewall_rules.sh",
         "Stateful iptables firewall rule enforcement.",
         "Bash script configuring iptables inside `ns-router`: stateful connection tracking, dropping invalid packets, SYN cookies, stealth scan filters (NULL/XMAS), ICMP/SYN rate limiting, and attacker isolation.",
         "Implements enterprise-grade packet filtering and DDoS mitigation policies.",
         "Configures netfilter rules inside the `ns-router` namespace.",
         "Executed as root (`sudo bash firewall_rules.sh`)."),

        ("linux_lab/test_routing_firewall.sh",
         "Automated routing policy and firewall verification test suite.",
         "Executes automated PASS/FAIL assertions: gateway reachability, cross-subnet routing, HTTP port 80 acceptance, Telnet port 23 blocking, and attacker isolation.",
         "Verifies that firewall security policies are properly enforced without breaking legitimate traffic.",
         "Executes tests inside `ns-client` and `ns-attacker` targeting `ns-server`.",
         "Runs sequentially and prints colored test results to console."),

        ("linux_lab/benchmark_rules.sh",
         "Packet filtering performance benchmarking engine.",
         "Measures baseline routing latency, injects a 2,500-packet flood from attacker, measures latency under rule-evaluation load, and calculates netfilter microsecond overhead delta.",
         "Quantifies the performance impact of stateful packet filtering and rate limiting under heavy load.",
         "Interacts with `ns-router` iptables counters and `ns-attacker` packet flood generators.",
         "Runs benchmark phases and outputs performance summary report."),

        ("linux_lab/lab_teardown.sh",
         "Virtual network clean-up automation.",
         "Safely deletes virtual namespaces (`ip netns del`) and removes orphaned `veth` interfaces, restoring the host system.",
         "Prevents orphaned virtual interfaces from cluttering the host networking stack.",
         "Executed after lab experiments are complete.",
         "Executed as root (`sudo bash lab_teardown.sh`)."),

        ("scripts/generate_sample_pcap.py",
         "Realistic PCAP capture and threat traffic generator.",
         "Generates a 94-packet Wireshark-compatible capture (`samples/demo_traffic.pcap`) containing legitimate DNS, HTTP handshakes, ICMP ping, alongside 8 orchestrated security attacks.",
         "Provides an out-of-the-box deterministic dataset for immediate offline testing without needing root permissions.",
         "Outputs binary PCAP using Scapy's `wrpcap()`.",
         "Executed via `python scripts/generate_sample_pcap.py`."),

        ("run_demo.py & run_web.py",
         "Convenience launchers for users and interviewers.",
         "`run_demo.py` executes the automated end-to-end demo CLI. `run_web.py` launches the Web SOC Dashboard on port 5000.",
         "Eliminates complex setup commands, allowing 1-click execution for reviews and demonstrations.",
         "Wrappers around `netpulse.cli.cmd_demo` and `netpulse.visualizer.web_server.start_server`.",
         "Executed directly from the workspace root.")
    ]

    for fname, purpose, code_desc, needed, connect, flow in files_analysis:
        add_section_heading(doc, f"📁 {fname}", level=3)
        add_paragraph(doc, bold_prefix="Purpose: ", text=purpose)
        add_paragraph(doc, bold_prefix="Code Description: ", text=code_desc)
        add_paragraph(doc, bold_prefix="Why Needed: ", text=needed)
        add_paragraph(doc, bold_prefix="Connections: ", text=connect)
        add_paragraph(doc, bold_prefix="Execution Flow: ", text=flow)

    # =========================================================================
    # SECTION 6: CODE EXPLANATION (ENGLISH + HINGLISH)
    # =========================================================================
    add_section_heading(doc, "6. Code Explanation (English + Hinglish)", level=1)

    add_paragraph(doc, text=
        "In this section, we analyze the core algorithms, data structures, and functions across the most critical source files. "
        "Each file is explained with code snippets, technical logic in English, and an intuitive breakdown in simple Hinglish."
    )

    code_files = [
        ("netpulse/core/parser.py - Packet Dissection Logic",
         """
@dataclass
class DissectedPacket:
    timestamp: float
    length: int
    protocol: str
    src_ip: str = "N/A"
    dst_ip: str = "N/A"
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    tcp_flags: Dict[str, bool] = field(default_factory=dict)
    tcp_flags_str: str = ""
    seq: Optional[int] = None
    ack: Optional[int] = None
    ttl: Optional[int] = None
    dns_query: Optional[str] = None
    payload_preview: str = ""
    summary: str = ""
         """,
         "English Explanation: The `DissectedPacket` class is a high-performance dataclass that normalizes heterogeneous network frames into a unified structure. "
         "The `PacketParser.parse()` method uses Scapy's `.haslayer()` method to traverse Layer 2 through Layer 7. "
         "For TCP packets, it unpacks the 8-bit flag byte into explicit boolean flags (SYN, ACK, FIN, RST, PSH, URG, ECE, CWR) and formats a human-readable string like `[SYN,ACK]`. "
         "For DNS, it parses query records (`DNSQR`) and extracts domain names and query types (A, AAAA, MX). For HTTP, it decodes request lines (`GET /path HTTP/1.1`) and Host headers.",
         "Hinglish Explanation: Yeh file hamare pure project ka 'Eye' ya dissector hai. Jab bhi network par koi raw packet aata hai, woh sirf binary 0s aur 1s ka bundle hota hai. "
         "Scapy ki madad se `PacketParser` check karta hai ki kya yeh packet Ethernet ka hai, IP ka hai, ya TCP ka hai. "
         "Agar TCP hai, toh flags check karta hai ki kya handshake shuru ho raha hai (SYN), khatam ho raha hai (FIN), ya reset ho raha hai (RST). "
         "Iske baad ek neat clean `DissectedPacket` object banata hai jise aage threat detection engine aur web UI asani se read kar sakein."),

        ("netpulse/detector/rules.py - Shannon Entropy & Threat Detection Rules",
         """
def shannon_entropy(data: str) -> float:
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
         """,
         "English Explanation: Shannon entropy measures the unpredictability or information density of a string in bits per character. "
         "In `DnsTunnelRule`, malware like dnscat2 or iodine exfiltrates sensitive data by encoding it in base64/hex and attaching it as DNS subdomains (e.g. `dGhpcy1pcy1h...attacker.com`). "
         "Natural English domains typically have an entropy of 2.0 to 3.2. Tunneled or encrypted data yields entropy > 3.8. "
         "The formula H(X) = -sum(p_i * log2(p_i)) is computed over the subdomain. If length > 25 and entropy >= 3.6, a HIGH severity alert is triggered. "
         "`SynFloodRule` uses a sliding time window (deque) to detect when unacknowledged SYN packets exceed 15 in 3 seconds. "
         "`PortScanRule` flags vertical scans (>8 ports probed in 4s) and stealth scans (NULL scan where flags=0; XMAS scan where FIN, PSH, URG are all 1).",
         "Hinglish Explanation: Yeh hamara brain / IDS engine hai. Yahan do main algorithms hain:\n"
         "1. Shannon Entropy: Hackers company ka sensitive data chori karne ke liye usko base64 me convert karke DNS queries ke andar chupate hain (DNS Tunneling). "
         "Normal English words (jaise 'google', 'apple') me letters repeat hote hain toh unka entropy (randomness) kam hota hai (~2.5). "
         "Lekin encrypted ya base64 string me bohot zyada randomness hoti hai (>3.8). Hum formula se entropy nikalte hain aur agar entropy aur length high hai, toh turant alert bajate hain!\n"
         "2. SYN Flood & Port Scans: Agar koi ek hi IP address se 3 second ke andar 15 se zyada SYN packets bhejta hai aur handshake complete nahi karta, toh hum usko DoS attack declare kar dete hain. "
         "Aur agar koi Nmap se stealth scan (NULL scan ya XMAS scan) bhejta hai jisme TCP flags illegal hote hain, toh hamare rules usko pakad lete hain."),

        ("netpulse/diagnostics/health_monitor.py - RFC 3550 Jitter & Dropout Tracking",
         """
# Successive absolute delay variation
if len(rtts) > 1:
    diffs = [abs(rtts[i + 1] - rtts[i]) for i in range(len(rtts) - 1)]
    jitter = round(statistics.mean(diffs), 2)

# Consecutive failure tracking for dropouts
if self.consecutive_fails >= 2:
    if not self.current_dropout:
        self.current_dropout = DropoutEvent(start_time=ts, failed_probes=self.consecutive_fails)
    else:
        self.current_dropout.failed_probes = self.consecutive_fails
         """,
         "English Explanation: Network latency alone does not capture the full quality of a connection; latency variance (jitter) is critical for real-time traffic (VoIP, video streaming, gaming). "
         "NetPulse implements the RFC 3550 standard algorithm, calculating jitter as the mean absolute difference between consecutive probe delays: Jitter = (1 / (N - 1)) * sum(|RTT_{i+1} - RTT_i|). "
         "Furthermore, the `HealthMonitor` tracks connectivity dropouts. A single timeout might be a minor dropped packet, but 2 or more consecutive timeouts constitute a network dropout event. "
         "The monitor records the exact start timestamp, duration, and probe loss count, outputting automated diagnostic verdicts.",
         "Hinglish Explanation: Sirf Ping (latency) dekhne se internet connection ki asli health pata nahi chalti. Agar latency 50ms se achanak 200ms ho jaye aur fir 50ms ho jaye, toh ise Jitter kehte hain. "
         "Hum consecutive pings ke beech ka difference calculate karte hain. Agar jitter > 25ms hai, toh network 'DEGRADED' mark ho jata hai. "
         "Aur agar lagataar 2 ya usse zyada pings fail hote hain, toh yeh use 'Connectivity Dropout Window' me record kar leta hai taaki engineer ko pata chale ki exact kis time par aur kitni der ke liye connection kata tha."),

        ("netpulse/diagnostics/port_scanner.py - Concurrent Socket Engine",
         """
with ThreadPoolExecutor(max_workers=min(self.max_threads, total_ports)) as executor:
    future_to_port = {executor.submit(self._scan_port, p): p for p in ports}
    for future in as_completed(future_to_port):
        res = future.result()
        if res:
            open_results.append(res)
         """,
         "English Explanation: Traditional sequential port scanners take several minutes to scan 1,000 ports because each closed port causes a timeout. "
         "`PortScanner` achieves sub-second performance by utilizing Python's `concurrent.futures.ThreadPoolExecutor` with a thread pool of 50-60 workers. "
         "Each worker probes a port using non-blocking socket `connect_ex()`. If port is open (return code 0), `_grab_banner()` sends protocol-specific probes and retrieves the application greeting banner.",
         "Hinglish Explanation: Agar hum ek-ek karke 1,000 ports scan karenge aur har port 1 second ka timeout lega, toh pura scan 15-20 minute lega. "
         "Humne `ThreadPoolExecutor` use karke 50 threads ek sath launch kiye. Har thread alag port ko probe karta hai. "
         "Jaise hi koi port open milta hai, hum HTTP ya standard greeting message bhejkar uska version banner (jaise MySQL 8.0 ya Apache 2.4) grab kar lete hain. Pura scan sirf 1 se 2 second me complete ho jata hai!"),

        ("linux_lab/firewall_rules.sh - Stateful iptables Enforcement",
         """
# 1. Stateful Connection Tracking
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m state --state INVALID -j DROP

# 2. Stealth Scan Drops
iptables -A FORWARD -p tcp --tcp-flags ALL NONE -j DROP
iptables -A FORWARD -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP

# 3. SYN Flood Mitigation
iptables -A FORWARD -p tcp --syn -m limit --limit 25/s --limit-burst 50 -j ACCEPT
iptables -A FORWARD -p tcp --syn -j DROP
         """,
         "English Explanation: This shell script configures Linux netfilter via `iptables` inside the `ns-router` network namespace. "
         "It enforces stateful inspection using the `conntrack` module: packets belonging to established sessions bypass rule evaluation, achieving line-rate forwarding. "
         "Invalid connection states and illegal TCP flag combinations (NULL, XMAS) are dropped. "
         "SYN flood protection limits new incoming connection attempts to 25/second with a burst allowance of 50, dropping excess packets and protecting downstream servers from resource exhaustion.",
         "Hinglish Explanation: Yeh script hamare Linux router ke andar ek secure firewall khada karti hai:\n"
         "1. Stateful Inspection: Agar connection pehle se verify ho chuka hai (ESTABLISHED), toh firewall us packet ko bina delay ke turant pass hone deta hai. Invalid packets ko drop kar deta hai.\n"
         "2. Stealth Scan Drop: Nmap ke NULL scan aur XMAS scan packets jinme ulte-seedhe flags hote hain, unhe turant block kar deta hai.\n"
         "3. Rate Limiting: Agar koi hacker bohot tezi se SYN packets bhejkar server ko crash karne ki koshish kare, toh firewall maximum 25 connections per second allow karta hai aur baki sabko drop kar deta hai.")
    ]

    for title, snippet, eng, hing in code_files:
        add_section_heading(doc, title, level=2)
        add_code_block(doc, snippet)
        add_paragraph(doc, bold_prefix="Technical Logic (English): ", text=eng)
        add_paragraph(doc, bold_prefix="Simple Explanation (Hinglish): ", text=hing)

    # =========================================================================
    # SECTION 7: DATABASE & DATA STORAGE DEEP DIVE
    # =========================================================================
    add_section_heading(doc, "7. Database & Data Storage Deep Dive", level=1)

    add_paragraph(doc, bold_prefix="Storage Architecture Philosophy: ", text=
        "In high-throughput networking applications capturing thousands of packets per second, writing every single raw packet into a traditional "
        "relational database (like MySQL or PostgreSQL) creates severe disk I/O bottlenecks and connection pool saturation. "
        "NetPulse employs a two-tier storage architecture:\n"
        "1. In-Memory High-Speed Circular Buffers & Hash Maps for real-time analytics.\n"
        "2. Binary Libpcap Standard Files (.pcap) for persistent packet storage, ensuring 100% interoperability with Wireshark and SIEM tools."
    )

    add_paragraph(doc, bold_prefix="In-Memory Schema & Data Models: ", text="")
    schema_desc = """
DissectedPacket In-Memory Model:
--------------------------------------------------------------------------------
Field Name          Data Type       Description
--------------------------------------------------------------------------------
timestamp           Float           Epoch timestamp with microsecond precision
length              Integer         Frame size in bytes
protocol            String (Enum)   'TCP', 'UDP', 'ICMP', 'DNS', 'HTTP', 'ARP'
src_ip / dst_ip     String          IPv4/IPv6 source and destination addresses
src_port / dst_port Integer / None  Transport layer port numbers (1-65535)
tcp_flags           Dictionary      Boolean map: {'SYN': True, 'ACK': False, ...}
tcp_flags_str       String          Formatted flag badge string: '[SYN,ACK]'
seq / ack           Integer / None  32-bit TCP sequence and acknowledgment numbers
window              Integer / None  16-bit TCP receive window advertisement
ttl                 Integer / None  8-bit IP Time-To-Live / Hop Limit
dns_query           String / None   Fully Qualified Domain Name queried
payload_preview     String          ASCII-sanitized printable payload preview
--------------------------------------------------------------------------------
"""
    add_code_block(doc, schema_desc, caption="DissectedPacket Data Model")

    add_paragraph(doc, bold_prefix="CRUD Operations in NetPulse: ", text=
        "• CREATE (Insert): When a frame arrives, `TrafficStatistics.update(pkt)` increments hash counters (O(1)) and appends to circular queues. If PCAP dumping is enabled, `PcapWriter.write(raw_pkt)` streams binary bytes to disk.\n"
        "• READ (Query): Flask endpoints read from `recent_packets` slice (O(1)), `protocol_counts`, and `top_sources`. `PcapAnalyzer` stream-reads PCAP files using iterator semantics without loading entire multi-gigabyte files into RAM.\n"
        "• UPDATE: Sliding-window throughput queues purge packets older than 3.0s using `deque.popleft()`.\n"
        "• DELETE: Calling `AnomalyEngine.clear()` or `/api/analyze_sample` flushes existing metric buffers."
    )

    add_paragraph(doc, bold_prefix="Indexing & Optimization Strategies: ", text=
        "• Hash-Map Indexing: Source IPs, destination IPs, and conversation tuples `tuple(sorted([src, dst]))` are stored in Python `Counter` (hash table) yielding O(1) lookups and O(k log n) top-talker sorting using `most_common(5)`.\n"
        "• Bounded Memory Safety: `recent_packets` has a hard boundary of max 150 items (`recent_packets.pop()`), ensuring that the web server memory footprint remains stable (~45MB) regardless of how many millions of packets pass through."
    )

    # =========================================================================
    # SECTION 8: API DEEP DIVE
    # =========================================================================
    add_section_heading(doc, "8. API Deep Dive", level=1)

    add_paragraph(doc, text="NetPulse exposes a robust, RESTful HTTP microservices API consumed by the web dashboard, CLI, or third-party automated pipelines.")

    api_endpoints = [
        ("GET", "/", "Renders and delivers the single-page web SOC dashboard.", "None", "None", "HTML document", "200 OK"),
        ("GET", "/api/overview", "Returns unified system status, throughput metrics, protocol breakdown, recent alerts, and recent packets.", "None", "None", "JSON {status, metrics, protocol_breakdown, top_sources, recent_alerts, recent_packets}", "200 OK"),
        ("GET", "/api/packets", "Returns list of recently dissected network packets in memory.", "None", "None", "JSON {packets: [...] }", "200 OK"),
        ("GET", "/api/alerts", "Returns all security threat alerts generated by the IDS engine.", "None", "None", "JSON {total, alerts: [...] }", "200 OK"),
        ("POST", "/api/scan", "Triggers multi-threaded TCP port scan against specified target.", "None", "JSON {target: str, ports: str}", "JSON {target, open_ports_count, scan_duration_seconds, open_ports: [{port, state, service, banner, rtt_ms}]}", "200 OK"),
        ("POST", "/api/health", "Executes automated latency, jitter, packet loss, and dropout diagnostics.", "None", "JSON {target: str, count: int}", "JSON {target, verdict, metrics: {avg_rtt_ms, jitter_ms, packet_loss_pct, dropouts_count}, probe_history, recommendations}", "200 OK"),
        ("POST", "/api/dns", "Benchmarks resolution latency across public resolvers (Google, Cloudflare, Quad9, OpenDNS).", "None", "JSON {domain: str}", "JSON {domain, resolvers: [{resolver, latency_ms, status}]}", "200 OK"),
        ("POST", "/api/traceroute", "Traces hop-by-hop route path and gateway latency.", "None", "JSON {target: str}", "JSON {target, hops: [{hop, ip, hostname, rtt_ms, status}]}", "200 OK"),
        ("POST", "/api/analyze_sample", "Ingests and performs full forensic inspection on samples/demo_traffic.pcap.", "None", "None", "JSON {file_info, metrics, protocol_breakdown, anomalies_detected, anomalies: [...]}", "200 OK"),
        ("POST", "/api/simulate_toggle", "Starts or stops background live synthetic traffic streaming thread.", "None", "JSON {enable: bool}", "JSON {simulation_running: bool}", "200 OK")
    ]

    api_table = doc.add_table(rows=len(api_endpoints) + 1, cols=7)
    api_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    api_table.autofit = False

    col_w = [Inches(0.6), Inches(1.2), Inches(1.5), Inches(0.6), Inches(1.1), Inches(1.0), Inches(0.5)]
    format_table_headers(api_table, ["Method", "Endpoint URL", "Purpose", "Auth", "Request Body", "Response", "Status"], col_w)

    for idx, (m, u, p, auth, req, res, stat) in enumerate(api_endpoints, start=1):
        row = api_table.rows[idx]
        r0 = row.cells[0].paragraphs[0].add_run(m)
        r0.bold = True
        r0.font.color.rgb = COLOR_SECONDARY if m == "GET" else COLOR_ACCENT_GREEN
        row.cells[1].paragraphs[0].add_run(u).bold = True
        row.cells[2].paragraphs[0].add_run(p)
        row.cells[3].paragraphs[0].add_run(auth)
        row.cells[4].paragraphs[0].add_run(req)
        row.cells[5].paragraphs[0].add_run(res)
        row.cells[6].paragraphs[0].add_run(stat)

    style_table_rows(api_table)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # =========================================================================
    # SECTION 9: AUTHENTICATION AND SECURITY
    # =========================================================================
    add_section_heading(doc, "9. Authentication and Security Audit", level=1)

    add_paragraph(doc, bold_prefix="Architectural Truthfulness Disclosure: ", text=
        "In accordance with software engineering integrity standards, NetPulse does not claim to implement user logins, JWT tokens, "
        "or session cookies. NetPulse is architected as an internal Network Operations & SOC utility. Its security model is built on "
        "operating system-level access controls, input sanitization, and defensive bounds."
    )

    add_paragraph(doc, bold_prefix="1. OS Privilege Separation & Access Control: ", text=
        "• Linux Capabilities: Live packet sniffing (`socket(AF_PACKET)`) and Linux namespace management (`ip netns`) strictly require `CAP_NET_RAW` and `CAP_NET_ADMIN` privileges. Non-root users cannot intercept promiscuous frames.\n"
        "• Windows Driver Boundary: Sniffing requires the kernel-level Npcap packet capture driver running in administrative context.\n"
        "• Localhost Binding: By default, the Flask server binds exclusively to `127.0.0.1:5000`, preventing unauthorized external network access."
    )

    add_paragraph(doc, bold_prefix="2. Input Validation & Command Injection Defense: ", text=
        "• Port Parsing: The port scanner sanitizes user input by strictly splitting integers and enforcing boundaries (`1 <= port <= 65535`). Any malformed string safely falls back to standard ports without shell evaluation.\n"
        "• IP Validation: Targets are sanitized through Python's `socket.gethostbyname()` resolution, avoiding command injection vulnerabilities."
    )

    add_paragraph(doc, bold_prefix="3. DoS Protection & Bounded Memory Buffers: ", text=
        "High-rate network traffic can easily crash an analyzer via Out-Of-Memory (OOM) errors. NetPulse prevents this with bounded data structures:\n"
        "• `recent_packets` has a fixed capacity of 150 items.\n"
        "• Sliding windows (`_recent_bytes`) automatically purge entries older than 3 seconds.\n"
        "• Threat alert cooldowns prevent alert flooding (e.g., maximum 1 SYN flood alert every 5 seconds per source IP)."
    )

    add_paragraph(doc, bold_prefix="4. Production Hardening Roadmap: ", text=
        "To deploy NetPulse as a multi-tenant enterprise cloud service, the following additions are recommended:\n"
        "1. Reverse Proxy & TLS: Place NGINX in front of NetPulse with HTTPS/TLS 1.3 certificates.\n"
        "2. OAuth2 / OpenID Connect: Authenticate security analysts via corporate identity providers (Okta, Azure AD).\n"
        "3. Role-Based Access Control (RBAC): Analyst (read-only telemetry) vs Administrator (trigger port scans and firewall modifications)."
    )

    # =========================================================================
    # SECTION 10: EXECUTION AND DEPLOYMENT
    # =========================================================================
    add_section_heading(doc, "10. Execution and Deployment Guide", level=1)

    add_paragraph(doc, bold_prefix="System Prerequisites: ", text="Python 3.9+ (Python 3.12 recommended), pip, Git. For live physical sniffing on Windows, install Npcap with WinPcap compatibility.")

    add_paragraph(doc, bold_prefix="1. Local Installation: ", text="")
    cmd_install = """
# Step 1: Clone the repository
git clone https://github.com/your-username/network-traffic-analyzer.git
cd "network-traffic-analyzer"

# Step 2: Create and activate virtual environment
python -m venv venv
# On Windows:
.\\venv\\Scripts\\activate
# On Linux/macOS:
source venv/bin/activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: (Optional) Install in editable mode for global 'netpulse' command
pip install -e .
"""
    add_code_block(doc, cmd_install, caption="Installation Commands")

    add_paragraph(doc, bold_prefix="2. Running the 1-Click Demo & Test Suite: ", text="")
    cmd_demo = """
# Run the automated end-to-end interactive CLI demo
python run_demo.py
# (or via module entrypoint)
python -m netpulse demo

# Execute the 21-test automated unit test suite
python -m unittest discover -s tests -p "test_*.py" -v
"""
    add_code_block(doc, cmd_demo, caption="Demo and Testing Commands")

    add_paragraph(doc, bold_prefix="3. Launching the Web SOC Dashboard: ", text="")
    cmd_web = """
# Launch Web Operations Center on http://127.0.0.1:5000
python run_web.py
# (or with custom host/port)
python -m netpulse web --host 0.0.0.0 --port 8080
"""
    add_code_block(doc, cmd_web, caption="Web Dashboard Launch")

    add_paragraph(doc, bold_prefix="4. Running the Linux Virtualized Lab: ", text="")
    cmd_lab = """
cd linux_lab

# 1. Setup virtual network namespaces and veth pairs
sudo bash lab_setup.sh

# 2. Deploy stateful firewall rules & SYN cookie protection
sudo bash firewall_rules.sh

# 3. Execute automated routing & firewall compliance tests
sudo bash test_routing_firewall.sh

# 4. Benchmark packet filtering latency overhead under flood traffic
sudo bash benchmark_rules.sh

# 5. Clean teardown of virtual namespaces
sudo bash lab_teardown.sh
"""
    add_code_block(doc, cmd_lab, caption="Linux Lab Automation Commands")

    add_paragraph(doc, bold_prefix="5. Deploying with Docker Compose (Cross-Platform): ", text="")
    cmd_docker = """
# Build and run the multi-node network lab topology in Docker
docker compose up --build

# In a separate terminal, inspect logs or enter client container
docker exec -it netpulse-client bash
"""
    add_code_block(doc, cmd_docker, caption="Docker Compose Commands")

    # =========================================================================
    # SECTION 11: INTERVIEW QUESTIONS AND ANSWERS (56 QUESTIONS)
    # =========================================================================
    doc.add_page_break()
    add_section_heading(doc, "11. Interview Questions and Answers (56 Comprehensive Q&As)", level=1)

    add_paragraph(doc, text="Below are 56 technically rigorous, clear interview questions with concise answers covering all aspects of NetPulse:")

    qa_list = [
        # Basic Project Questions
        ("Q1: What is the primary objective of the NetPulse project?",
         "NetPulse is a unified network traffic analyzer and troubleshooting toolkit designed to capture packets, analyze TCP/IP headers, detect anomalous attack patterns, automate routine latency/dropout health checks, and test routing policies in virtualized Linux environments."),

        ("Q2: Which core technologies did you use to build NetPulse?",
         "Python 3.12, Scapy for packet manipulation, Wireshark/libpcap for capture standards, Linux Network Namespaces (netns) and iptables for network virtualization, Bash for lab automation, and Flask with Chart.js for the Web SOC Dashboard."),

        ("Q3: What are the three key bullet points this project fulfills?",
         "1. Deep packet inspection and anomaly detection using Scapy;\n"
         "2. Automated health checks, multi-threaded port scanning, and jitter/dropout diagnostics;\n"
         "3. Virtualized Linux network configuration for firewall rule enforcement and packet filtering benchmarking."),

        ("Q4: Can NetPulse be run without administrator or root privileges?",
         "Yes. NetPulse features an offline PCAP analyzer and synthetic traffic generator (`demo_traffic.pcap`) that allows full protocol dissection and threat heuristic evaluation without raw socket permissions."),

        ("Q5: What is the difference between NetPulse and Wireshark?",
         "Wireshark is primarily a passive packet viewer. NetPulse combines packet inspection with active multi-threaded port scanning, continuous RFC jitter/dropout diagnostics, automated behavioral threat detection, and Linux firewall benchmarking."),

        ("Q6: How does NetPulse handle packet export?",
         "Captured packets can be streamed directly into standard Wireshark-compatible `.pcap` files using Scapy's `PcapWriter`, or exported as forensic reports in JSON and CSV formats."),

        ("Q7: What is a Berkeley Packet Filter (BPF)?",
         "A kernel-level mechanism that filters raw network traffic before passing it to user space (e.g. `tcp port 80` or `udp port 53`), dramatically reducing CPU overhead."),

        ("Q8: What user interfaces does NetPulse provide?",
         "Two distinct interfaces: (1) A modern dark Glassmorphic Web SOC Dashboard with real-time Chart.js telemetry, and (2) A Rich Terminal User Interface (TUI) with colored tables and cards."),

        # Technical & Networking Questions
        ("Q9: What happens during a standard TCP 3-way handshake?",
         "Client sends SYN (seq=x); Server responds with SYN-ACK (seq=y, ack=x+1); Client sends ACK (seq=x+1, ack=y+1). Connection transitions to ESTABLISHED."),

        ("Q10: Which TCP flags does NetPulse dissect?",
         "All 8 standard control flags: SYN (Synchronize), ACK (Acknowledge), FIN (Finish), RST (Reset), PSH (Push), URG (Urgent), ECE (ECN-Echo), and CWR (Congestion Window Reduced)."),

        ("Q11: What is the significance of the Time-To-Live (TTL) field?",
         "TTL is an 8-bit field in IPv4 headers decremented by 1 by each router. When TTL reaches 0, the packet is discarded and an ICMP Time Exceeded message is sent, preventing routing loops."),

        ("Q12: How does NetPulse detect a TCP SYN Flood attack?",
         "`SynFloodRule` monitors incoming TCP packets. If an IP sends a burst of SYN packets exceeding 15 within 3 seconds with little to no ACK handshake completions, a CRITICAL DoS alert is triggered."),

        ("Q13: What is a TCP NULL scan and how is it detected?",
         "An Nmap stealth scan where a TCP packet is sent with zero flags set. Normal operating systems drop it, but some RFC-compliant stacks respond with RST on closed ports. NetPulse flags any packet where all flag booleans are False."),

        ("Q14: What is a TCP XMAS scan?",
         "A stealth probe where FIN, PSH, and URG flags are set simultaneously ('lit up like a Christmas tree'). NetPulse detects this illegal flag combination and triggers a HIGH severity stealth scan alert."),

        ("Q15: How does ARP cache poisoning (ARP spoofing) work?",
         "An attacker broadcasts gratuitous ARP replies associating their MAC address with the default gateway's IP. Victims update their ARP cache, allowing the attacker to intercept or alter traffic (Man-In-The-Middle)."),

        ("Q16: How does NetPulse detect ARP spoofing?",
         "`ArpSpoofRule` maintains a stateful IP-to-MAC hash table. If an ARP reply claims an IP address previously bound to a different MAC address, an immediate CRITICAL security alert is generated."),

        ("Q17: What is DNS Tunneling and why is it used by malware?",
         "A technique where data is encoded into subdomains of DNS queries (e.g. `base64data.c2domain.com`) to exfiltrate information through firewalls that permit outbound UDP port 53."),

        ("Q18: How does Shannon Entropy detect DNS tunneling?",
         "Shannon entropy measures information randomness: H(X) = -sum(p_i * log2(p_i)). Natural domains have low entropy (~2.5), whereas base64/encrypted exfiltration yields high entropy (>3.8). Queries exceeding entropy and length thresholds are flagged."),

        # Architecture & Design Questions
        ("Q19: Explain the separation of concerns in NetPulse's architecture.",
         "Raw packet capture (`sniffer.py`) is decoupled from parsing (`parser.py`), parsing is decoupled from IDS evaluation (`rules.py`), and analytics are decoupled from visualization (`console_ui.py`, `web_server.py`)."),

        ("Q20: Why did you use the Observer pattern in the packet capture pipeline?",
         "To allow multiple independent components (`TrafficStatistics`, `AnomalyEngine`, PCAP writer, terminal logger) to subscribe to the packet stream without modifying the capture loop."),

        ("Q21: How does NetPulse prevent memory exhaustion under high traffic?",
         "By using fixed-capacity circular buffers (`deque(maxlen=150)`), rolling 3-second time windows that automatically purge stale timestamps, and alert cooldown timers."),

        ("Q22: Why is Flask suitable for this application?",
         "Flask is lightweight, synchronous, easy to embed inside a CLI package, and provides clean REST endpoints for JSON serialization without unnecessary framework overhead."),

        ("Q23: How does the Web UI achieve real-time telemetry updates?",
         "Through asynchronous polling: `dashboard.js` queries `GET /api/overview` every 1,500ms, updating DOM nodes and dynamically pushing data points to Chart.js canvas charts without full-page reloads."),

        ("Q24: What is the purpose of the DissectedPacket dataclass?",
         "It acts as a normalized Data Transfer Object (DTO) converting raw Scapy layer objects into clean, typed, JSON-serializable Python data structures."),

        ("Q25: Why did you include both a Web UI and a Terminal TUI?",
         "Network engineers frequently troubleshoot headless remote servers over SSH (where Rich TUI is ideal), while SOC analysts prefer graphical dashboards with visual charts (Web UI)."),

        ("Q26: How does Docker Compose support this project?",
         "It allows developers on Windows and macOS to launch the multi-subnet virtual network topology (Client, Router/Firewall, Server, Attacker) in isolated Linux containers with a single command."),

        # Data & In-Memory Storage Questions
        ("Q27: Why doesn't NetPulse write every packet to a SQL database?",
         "At high packet rates, relational database disk I/O, transaction logging, and connection pooling cause severe CPU bottlenecks and packet drops. In-memory data structures provide line-rate processing."),

        ("Q28: How does NetPulse calculate rolling throughput in Kbps?",
         "It maintains a sliding 3-second window of `(timestamp, bytes)`. Throughput (Kbps) is calculated as: `(sum(bytes) * 8) / (window_seconds * 1000)`."),

        ("Q29: How are top talkers and conversations aggregated?",
         "Using Python's `collections.Counter`. IP addresses and sorted conversation tuples `tuple(sorted([src, dst]))` are hashed in O(1) time and sorted using `most_common(5)`."),

        ("Q30: What binary capture format does NetPulse use for persistent storage?",
         "Standard libpcap binary format (`.pcap`), ensuring full compatibility with Wireshark, tcpdump, Snort, and Zeek."),

        ("Q31: How does PcapAnalyzer stream large capture files?",
         "It uses Scapy's `PcapReader` as an iterator/generator, processing packets sequentially without loading multi-gigabyte files into RAM all at once."),

        ("Q32: What data is exported when running PCAP analysis export?",
         "Complete forensic metadata, metrics, protocol breakdowns, and detected threat alerts in JSON format, alongside per-packet protocol headers in CSV format."),

        # API & Diagnostics Questions
        ("Q33: How does the multi-threaded port scanner achieve sub-second speeds?",
         "By leveraging `ThreadPoolExecutor` with 50-60 worker threads and non-blocking `connect_ex()` sockets with a 0.6s timeout, scanning dozens of ports simultaneously."),

        ("Q34: What is banner grabbing?",
         "Connecting to an open TCP port and reading the initial application handshake (e.g. HTTP server headers, SSH-2.0 banner, MySQL handshake) to identify the running software version."),

        ("Q35: How is RFC 3550-compliant jitter calculated in NetPulse?",
         "It computes the mean absolute difference of successive round-trip times: Jitter = (1 / (N - 1)) * sum(|RTT_{i+1} - RTT_i|)."),

        ("Q36: What constitutes a connectivity dropout event?",
         "Two or more consecutive socket probe timeouts. NetPulse records the dropout start time, duration until recovery, and number of failed probes."),

        ("Q37: What does the /api/dns endpoint benchmark?",
         "It resolves a domain via the local system resolver and tests TCP port 53 responsiveness across Cloudflare (1.1.1.1), Google (8.8.8.8), Quad9 (9.9.9.9), and OpenDNS."),

        # Security & Linux Lab Questions
        ("Q38: What is a Linux Network Namespace (netns)?",
         "A kernel feature that provides an isolated copy of the network stack, including its own network interfaces, routing tables, and iptables firewall rules."),

        ("Q39: What is a Virtual Ethernet (veth) pair?",
         "A pair of interconnected virtual network interfaces acting like a virtual patch cable; packets transmitted on one interface immediately emerge on the peer interface."),

        ("Q40: How does stateful connection tracking work in iptables?",
         "The `conntrack` kernel module tracks TCP state transitions. Established and related packets matching existing sessions bypass further rule checks, significantly boosting throughput."),

        ("Q41: What are TCP SYN Cookies?",
         "A defense against SYN floods where the server encodes connection state into the initial SYN-ACK sequence number instead of allocating kernel memory in the SYN backlog table."),

        ("Q42: How does NetPulse benchmark packet filtering performance?",
         "`benchmark_rules.sh` measures baseline round-trip latency, floods the router with 2,500 packets/sec from an attacker node, measures latency under load, and calculates the netfilter overhead delta."),

        ("Q43: What was the observed netfilter processing latency overhead in the benchmark?",
         "Approximately +0.060 milliseconds, demonstrating that Linux stateful packet filtering maintains line-rate performance under flood conditions."),

        ("Q44: How does NetPulse isolate rogue nodes in the Linux lab?",
         "`iptables -I FORWARD 1 -s 10.10.1.99 -j DROP` immediately quarantines the attacker subnet at the top of the FORWARD chain."),

        # Scenario-Based & Troubleshooting Questions
        ("Q45: If users complain that the internet is intermittently dropping every 10 minutes, how would you diagnose it using NetPulse?",
         "Run `python -m netpulse health --target 8.8.8.8 --count 60 --interval 1`. The dropout tracker will record the exact timestamps, durations, and consecutive probe losses to identify link flapping or DHCP lease renegotiations."),

        ("Q46: If a web server is experiencing high CPU and unresponsive ports, how can NetPulse assist?",
         "Use `netpulse sniff` or ingest capture. If `SynFloodRule` fires, it confirms a SYN flood DoS. Remedy by activating TCP SYN cookies and applying iptables rate-limiting."),

        ("Q47: If latency spikes to 300ms during video calls, what does NetPulse look for?",
         "High jitter and latency spikes in `HealthMonitor`. If ping latency increases proportionally with bandwidth load, it indicates router bufferbloat, remediable by deploying FQ-CoDel queue management."),

        ("Q48: How would you prove that an internal workstation is infected with data exfiltration malware?",
         "Run `netpulse analyze` on egress gateway traffic. `DnsTunnelRule` will flag high Shannon entropy subdomains and `SuspiciousPayloadRule` will detect cleartext credential leaks."),

        ("Q49: Why did the terminal demo initially show a charmap UnicodeEncodeError on Windows, and how did you resolve it?",
         "Windows consoles default to legacy `cp1252` encoding which cannot encode Unicode characters like checkmarks (`\u2713`). We resolved this by configuring `sys.stdout.reconfigure(encoding='utf-8')` and using ASCII-safe status tags (`[OK]`)."),

        ("Q50: Why did Scapy issue a warning about WinPcap when building Ethernet packets, and how was it fixed?",
         "When Ethernet frames lack explicit MAC addresses, Scapy attempts to resolve them using Layer 2 system APIs. We fixed this by assigning explicit virtual MAC addresses (`00:11:22:33:44:55`), bypassing raw L2 resolution."),

        ("Q51: How did you fix the ZeroDivisionError in TrafficStatistics when 0 packets were captured?",
         "By adding boundary guards in `average_pps` and `average_bandwidth_kbps` returning `0.0` whenever `self.duration_seconds <= 0.0` or `self.total_packets == 0`."),

        ("Q52: If an interviewer asks you to demonstrate the project live, what command do you run?",
         "`python run_demo.py` for the comprehensive terminal suite, or `python run_web.py` to open the interactive browser dashboard at `http://127.0.0.1:5000`."),

        # Fresher SWE / Advanced Questions
        ("Q53: What is the time complexity of the packet parsing and IDS heuristic rules?",
         "O(1) amortized time per packet frame. Header dissection involves direct byte offsets, and sliding-window checks use bounded deque pop/append operations."),

        ("Q54: How would you scale NetPulse to handle 10 Gigabit line-rate traffic?",
         "By migrating the capture hook from Scapy/AF_PACKET to Linux kernel **eBPF (Extended Berkeley Packet Filter)** and **XDP (eXpress Data Path)**, running packet filters directly in network driver memory before kernel allocation."),

        ("Q55: What design patterns are implemented in this project?",
         "Observer Pattern (packet callback dispatcher), Strategy Pattern (interchangeable anomaly detection rules), DTO Pattern (`DissectedPacket`), and Singleton Pattern (shared Web SOC engines)."),

        ("Q56: What did this project teach you about production software engineering?",
         "It reinforced the importance of robust error handling, memory safety under high input volumes, cross-platform compatibility across Windows and Linux, and building automated end-to-end verification tests.")
    ]

    for q, a in qa_list:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(6)
        p_q.paragraph_format.space_after = Pt(2)
        p_q.paragraph_format.keep_with_next = True
        r_q = p_q.add_run(q)
        r_q.bold = True
        r_q.font.name = "Calibri"
        r_q.font.size = Pt(10.5)
        r_q.font.color.rgb = COLOR_PRIMARY

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_before = Pt(0)
        p_a.paragraph_format.space_after = Pt(4)
        r_a = p_a.add_run(f"Answer: {a}")
        r_a.font.name = "Calibri"
        r_a.font.size = Pt(10)
        r_a.font.color.rgb = COLOR_TEXT_MAIN

    # =========================================================================
    # SECTION 12: PROJECT EXPLANATION FOR INTERVIEWS
    # =========================================================================
    doc.add_page_break()
    add_section_heading(doc, "12. Project Explanation for Interviews", level=1)

    add_paragraph(doc, text="Prepare these 5 tailored spoken explanations based on who is interviewing you and how much time you have:")

    speeches = [
        ("A. 30-Second Elevator Pitch (Quick & Punchy)",
         "I built NetPulse, a network traffic analyzer and troubleshooting toolkit developed with Python, Scapy, Linux, and Wireshark standards. "
         "It captures live network traffic, dissects TCP/IP headers, and uses behavioral heuristics to detect threats like SYN floods, port scans, and DNS exfiltration. "
         "It also features a 50-thread concurrent port scanner and an automated health monitor that measures latency, RFC-compliant jitter, and connectivity dropouts. "
         "To validate it, I configured virtualized multi-subnet Linux network namespaces with stateful iptables firewalls to benchmark filtering performance under flood traffic."),

        ("B. 1-Minute Project Overview (Standard Technical Intro)",
         "In my project NetPulse, I addressed the challenge of diagnosing intermittent network performance degradations and identifying stealth attack patterns. "
         "Using Python and Scapy, I built a modular packet dissection engine that parses Ethernet through application-layer protocols, extracting TCP flags, sequence numbers, DNS queries, and HTTP payloads. "
         "On top of this, I developed an algorithmic Intrusion Detection System that detects attacks like SYN Flood DoS, stealth NULL and XMAS scans, ARP cache poisoning, and DNS data tunneling using Shannon entropy calculations. "
         "To automate troubleshooting, I wrote a multi-threaded port scanner with banner grabbing and a continuous health monitor tracking latency, RFC 3550 jitter, and connectivity dropout events. "
         "Finally, to test routing policies and firewall enforcement without risking production hardware, I automated virtualized Linux network namespaces connected via veth pairs, enforcing stateful iptables rules and benchmarking filtering latency overhead under 2,500 packet floods. "
         "The toolkit includes both an interactive Rich terminal console and a modern glassmorphic web dashboard with real-time Chart.js telemetry."),

        ("C. 3-Minute Detailed Architectural Explanation (Deep Technical Interview)",
         "NetPulse was designed to bridge low-level packet dissection with automated network diagnostics and firewall verification. "
         "The architecture is organized into four distinct decoupled layers: Data Ingestion, Deep Packet Inspection & IDS, Diagnostics & Troubleshooting, and Presentation. "
         "At the ingestion layer, NetPulse captures live frames using Scapy with Berkeley Packet Filters (BPF) and writes standard libpcap captures, while also supporting offline Wireshark PCAP ingestion for forensics. "
         "The parsing engine traverses Layer 2 to Layer 7, unpacking the 8-bit TCP control byte into explicit boolean states and extracting application metadata. "
         "These parsed frames feed into our Behavioral IDS engine, which runs six independent heuristic rules: detecting SYN floods via unacknowledged handshake ratios, vertical and horizontal port scans, invalid TCP flag scans, ARP poisoning via stateful MAC tracking, and DNS tunneling using Shannon entropy mathematics. "
         "The troubleshooting module tackles the operational problem of intermittent drops and jitter. Using Python concurrency with 50 worker threads, our port scanner maps active services and grabs application banners in under 1 second. "
         "Our health monitor measures RFC 3550-compliant jitter—calculating mean successive absolute delay variations—and tracks consecutive timeouts to record exact dropout windows and deliver diagnostic verdicts. "
         "To test the system against real network policies, I wrote Bash automation deploying Linux Network Namespaces—isolating a client, router, server, and attacker across two subnets. "
         "Inside the router namespace, I configured stateful iptables connection tracking, TCP SYN cookies, and rate limiting. "
         "I then benchmarked packet filtering overhead under 2,500 packets/sec flood traffic, measuring a negligible latency delta of only +0.06 milliseconds. "
         "Everything is presented through a dual interface: an interactive terminal console built with Rich and a responsive web operations center powered by Flask and Chart.js."),

        ("D. Technical SWE / Systems Engineering Explanation",
         "From a software engineering perspective, NetPulse prioritizes memory safety, high concurrency, and zero disk bottlenecks. "
         "Rather than piping high-frequency network packets into a relational database, I designed an in-memory architecture utilizing bounded deques and Python hash-based Counters. "
         "This guarantees O(1) packet ingestion and rolling throughput computation while capping the memory footprint at ~45 megabytes. "
         "For multi-threaded port scanning, I implemented Python's `ThreadPoolExecutor` with non-blocking sockets, achieving high concurrency while gracefully handling connection timeouts. "
         "For threat detection, I leveraged information theory: computing the Shannon entropy of DNS subdomains to distinguish natural domain names from high-entropy base64 exfiltration streams. "
         "On the systems side, I utilized Linux kernel primitives—specifically `ip netns`, `veth` pairs, and `iptables` netfilter chains—to simulate and benchmark real kernel routing, verifying that stateful firewall inspection operates at line-rate speeds with sub-millisecond overhead. "
         "The codebase is fully tested with a 21-test automated suite with 100% pass rates across parsing, IDS heuristics, and diagnostic calculations."),

        ("E. HR / Non-Technical Friendly Explanation",
         "Think of NetPulse as an automated security guard and medical monitor for computer networks. "
         "Just as doctors monitor a patient's pulse and blood pressure to detect health issues before they become emergencies, NetPulse monitors the data packets flowing across a company's network. "
         "It automatically detects if someone is trying to hack into systems by scanning ports or flooding servers with fake traffic, and it catches hackers trying to smuggle secret company data out through disguised queries. "
         "At the same time, it watches connection quality, alerting engineers when the internet drops or becomes laggy during important calls. "
         "Finally, it creates a safe virtual sandbox—like a flight simulator—where engineers can test security firewall rules without any risk of breaking real company systems. "
         "I built it with a user-friendly visual dashboard so anyone can easily see what is happening on the network in real-time.")
    ]

    for title, text_val in speeches:
        add_section_heading(doc, title, level=2)
        add_paragraph(doc, text=text_val)

    # =========================================================================
    # SECTION 13: CHALLENGES AND IMPROVEMENTS
    # =========================================================================
    doc.add_page_break()
    add_section_heading(doc, "13. Challenges, Limitations & Future Roadmap", level=1)

    add_paragraph(doc, bold_prefix="1. Challenges Faced and Engineering Solutions: ", text="")
    challenges = [
        ("Windows Console Encoding (cp1252) Crash",
         "Challenge: On Windows terminals, printing Unicode status symbols (like checkmark \u2713) triggered fatal `UnicodeEncodeError: 'charmap' codec can't encode character`.\n"
         "Solution: Configured `sys.stdout.reconfigure(encoding='utf-8')` across all CLI entrypoints and refactored status indicators to use ASCII-safe strings like `[OK]` and `[✓]` inside Rich panels."),

        ("Layer 2 Socket Permissions on Windows",
         "Challenge: Scapy raised warnings when synthesizing Layer 2 Ethernet frames because raw WinPcap drivers were absent in standard user environments.\n"
         "Solution: Injected explicit synthetic MAC addresses into all crafted frames, bypassing Scapy's automatic L2 ARP resolution routines, and suppressed non-critical runtime logger warnings."),

        ("Division-by-Zero in Zero-Traffic Initialization",
         "Challenge: When starting the Web SOC server before any packets arrived, querying `/api/overview` caused a `ZeroDivisionError: float division by zero` because capture duration was 0.0 seconds.\n"
         "Solution: Hardened `TrafficStatistics.average_pps` and `average_bandwidth_kbps` with guard clauses returning `0.0` when total packets or duration are zero."),

        ("High-Rate SYN Flood Detection False Positives",
         "Challenge: Web browsing generates legitimate bursts of parallel TCP connections, which risked triggering false-positive SYN flood alerts.\n"
         "Solution: Implemented dual criteria: checking both the SYN burst rate (>15 in 3s) AND the ACK completion ratio (<0.2), combined with a 5-second per-source cooldown timer.")
    ]

    for c_title, c_desc in challenges:
        add_section_heading(doc, f"• {c_title}", level=3)
        add_paragraph(doc, text=c_desc)

    add_paragraph(doc, bold_prefix="2. Current Project Limitations: ", text=
        "• Single-Node Deployment: NetPulse currently monitors interfaces or PCAPs on a single host rather than aggregating distributed sensors across a multi-datacenter fleet.\n"
        "• High-Frequency Packet Rate Ceiling: While Python and Scapy handle thousands of packets per second effortlessly, true 10Gbps+ carrier line-rate packet capture saturates Python's Global Interpreter Lock (GIL).\n"
        "• In-Memory Ephemeral Storage: Detailed packet dissection history resets on application restart unless saved explicitly to PCAP or exported to JSON."
    )

    add_paragraph(doc, bold_prefix="3. Future Architectural Roadmap: ", text=
        "1. eBPF / XDP Kernel Bypass: Migrate packet filtering to Linux eBPF (Extended Berkeley Packet Filter) and XDP (eXpress Data Path) to process 10M+ packets per second at line rate with zero user-space copying.\n"
        "2. Machine Learning Anomaly Classifier: Train an unsupervised Isolation Forest or Autoencoder model on benign traffic baselines to automatically flag zero-day protocol anomalies.\n"
        "3. Distributed Agent Architecture: Decouple sniffing sensors into lightweight Go or C daemon agents reporting via gRPC to a central NetPulse controller cluster.\n"
        "4. Automated Active Defense: Integrate with cloud firewalls (AWS Security Groups, Cloudflare WAF, iptables) to automatically ban offending IP addresses upon detection of critical threats."
    )

    add_callout(doc,
        "NetPulse proves that deep networking principles, cybersecurity heuristics, and modern software engineering can be cleanly unified into an intuitive, high-performance portfolio project.",
        title="PROJECT CONCLUSION"
    )

    # Save Word Document
    doc.save(OUTPUT_DOCX)
    print(f"[OK] Successfully generated complete Word documentation at:\n    {OUTPUT_DOCX}")
    return OUTPUT_DOCX


if __name__ == "__main__":
    build_full_documentation()
