#!/usr/bin/env bash
# ==============================================================================
# NetPulse - Stateful Firewall Rule Enforcement & Packet Filtering
# ==============================================================================
# Configures iptables / netfilter rules inside 'ns-router' to enforce strict
# routing policies, stateful connection tracking, SYN flood mitigation,
# stealth scan packet dropping, and rate limiting.
# ==============================================================================

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "[!] Error: Must run as root (sudo)."
   exit 1
fi

ROUTER_EXEC="ip netns exec ns-router"

echo "[+] Flushing existing iptables chains and rules inside ns-router..."
$ROUTER_EXEC iptables -F
$ROUTER_EXEC iptables -X
$ROUTER_EXEC iptables -t nat -F
$ROUTER_EXEC iptables -t nat -X
$ROUTER_EXEC iptables -t mangle -F
$ROUTER_EXEC iptables -t mangle -X

echo "[+] Setting default policies: DROP on FORWARD, ACCEPT on loopback..."
$ROUTER_EXEC iptables -P FORWARD DROP
$ROUTER_EXEC iptables -P INPUT DROP
$ROUTER_EXEC iptables -P OUTPUT ACCEPT

# Allow loopback interface traffic
$ROUTER_EXEC iptables -A INPUT -i lo -j ACCEPT

# 1. Stateful Connection Tracking (Allow Established & Related sessions)
echo "[+] Enabling stateful connection tracking (ESTABLISHED, RELATED)..."
$ROUTER_EXEC iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
$ROUTER_EXEC iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Drop Invalid Packets
$ROUTER_EXEC iptables -A FORWARD -m state --state INVALID -j DROP
$ROUTER_EXEC iptables -A INPUT -m state --state INVALID -j DROP

# 2. Kernel SYN Cookie Protection
echo "[+] Enabling TCP SYN Cookies in Linux kernel..."
$ROUTER_EXEC sysctl -w net.ipv4.tcp_syncookies=1 >/dev/null

# 3. Stealth Scan & Malformed Packet Filtering
echo "[+] Deploying stealth scan detection filters (NULL, XMAS, SYN-FIN)..."
# Drop NULL scans (No flags set)
$ROUTER_EXEC iptables -A FORWARD -p tcp --tcp-flags ALL NONE -m limit --limit 5/m -j LOG --log-prefix "[NETPULSE-FW-NULL-SCAN] "
$ROUTER_EXEC iptables -A FORWARD -p tcp --tcp-flags ALL NONE -j DROP

# Drop XMAS scans (FIN, PSH, URG)
$ROUTER_EXEC iptables -A FORWARD -p tcp --tcp-flags ALL FIN,PSH,URG -m limit --limit 5/m -j LOG --log-prefix "[NETPULSE-FW-XMAS-SCAN] "
$ROUTER_EXEC iptables -A FORWARD -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP

# Drop SYN-FIN scans
$ROUTER_EXEC iptables -A FORWARD -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP

# 4. SYN Flood Protection / Rate Limiting
echo "[+] Applying SYN flood rate-limiting (max 25 conn/sec with burst of 50)..."
$ROUTER_EXEC iptables -A FORWARD -p tcp --syn -m limit --limit 25/s --limit-burst 50 -j ACCEPT
$ROUTER_EXEC iptables -A FORWARD -p tcp --syn -m limit --limit 5/m -j LOG --log-prefix "[NETPULSE-FW-SYN-FLOOD-DROP] "
$ROUTER_EXEC iptables -A FORWARD -p tcp --syn -j DROP

# 5. ICMP Ping Rate Limiting (Prevent Ping of Death & Ping Floods)
echo "[+] Applying ICMP echo rate-limiting (max 5 pings/sec)..."
$ROUTER_EXEC iptables -A FORWARD -p icmp --icmp-type echo-request -m limit --limit 5/s --limit-burst 10 -j ACCEPT
$ROUTER_EXEC iptables -A FORWARD -p icmp --icmp-type echo-request -j DROP

# 6. Service Whitelisting Policies
echo "[+] Authorizing legitimate client traffic (HTTP 80/8080 and DNS 53 to Server)..."
# Client Subnet (10.10.1.0/24) can reach Server (10.10.2.80) on HTTP (80, 8080)
$ROUTER_EXEC iptables -A FORWARD -s 10.10.1.0/24 -d 10.10.2.80 -p tcp -m multiport --dports 80,8080 -m state --state NEW -j ACCEPT

# Allow DNS queries
$ROUTER_EXEC iptables -A FORWARD -s 10.10.1.0/24 -p udp --dport 53 -j ACCEPT

# 7. Block Rogue Attacker Node from Server Subnet Entirely
echo "[+] Enforcing isolation rule: Drop all traffic from rogue Attacker node (10.10.1.99)..."
$ROUTER_EXEC iptables -I FORWARD 1 -s 10.10.1.99 -m limit --limit 10/m -j LOG --log-prefix "[NETPULSE-FW-ATTACKER-BLOCKED] "
$ROUTER_EXEC iptables -I FORWARD 2 -s 10.10.1.99 -j DROP

# 8. Log and Drop Remaining Traffic
echo "[+] Logging and dropping all non-whitelisted packets..."
$ROUTER_EXEC iptables -A FORWARD -m limit --limit 10/m -j LOG --log-prefix "[NETPULSE-FW-DEFAULT-DROP] "
$ROUTER_EXEC iptables -A FORWARD -j DROP

echo "======================================================================"
echo "    Firewall Ruleset Successfully Activated!                         "
echo "======================================================================"
$ROUTER_EXEC iptables -L FORWARD -v -n --line-numbers
