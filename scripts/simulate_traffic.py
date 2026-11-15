#!/usr/bin/env python3
"""
Synthetic Network Traffic Stream Simulator
==========================================
Streams realistic synthetic packets (TCP handshakes, DNS queries, HTTP GETs,
and periodic anomaly probes) to test live sniffers, pipelines, or Web dashboards.
"""

import sys
import os
import time
import random
import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

from scapy.all import Ether, IP, TCP, UDP, ICMP, DNS, DNSQR, Raw


def simulate_stream(duration_seconds: int = 30, delay: float = 0.2):
    print(f"[*] Streaming synthetic traffic for {duration_seconds} seconds (delay: {delay}s)...")
    start = time.time()
    count = 0

    while time.time() - start < duration_seconds:
        r = random.random()
        t = time.time()

        if r < 0.4:
            # HTTP Web Packet
            pkt = Ether(src="00:11:22:33:44:55", dst="aa:bb:cc:dd:ee:ff") / \
                  IP(src="192.168.1.50", dst="93.184.216.34") / \
                  TCP(sport=random.randint(40000, 60000), dport=80, flags="PA") / \
                  Raw(load=b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n")
        elif r < 0.7:
            # DNS Query
            pkt = Ether(src="00:11:22:33:44:55", dst="aa:bb:cc:dd:ee:ff") / \
                  IP(src="192.168.1.50", dst="8.8.8.8") / \
                  UDP(sport=random.randint(50000, 60000), dport=53) / \
                  DNS(rd=1, qd=DNSQR(qname=f"host{random.randint(1,100)}.example.org"))
        elif r < 0.9:
            # ICMP Ping
            pkt = Ether(src="00:11:22:33:44:55", dst="aa:bb:cc:dd:ee:ff") / \
                  IP(src="192.168.1.50", dst="192.168.1.1") / \
                  ICMP(type=8, code=0, id=100, seq=count)
        else:
            # Stealth or Attack Probe
            pkt = Ether(src="de:ad:be:ef:13:37", dst="aa:bb:cc:dd:ee:ff") / \
                  IP(src="192.168.1.99", dst="192.168.1.100") / \
                  TCP(sport=55000 + (count % 100), dport=random.choice([22, 80, 443, 3306]), flags="S")

        pkt.time = t
        count += 1
        if count % 10 == 0:
            print(f"  [+] Streamed {count} packets...")
        time.sleep(delay)

    print(f"[✓] Simulation complete: {count} packets generated in {round(time.time() - start, 2)}s.")


if __name__ == "__main__":
    dur = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    simulate_stream(duration_seconds=dur)
