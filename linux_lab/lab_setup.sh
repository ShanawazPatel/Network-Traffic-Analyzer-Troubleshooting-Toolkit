#!/usr/bin/env bash
# ==============================================================================
# NetPulse - Virtualized Local Network Setup (Linux Network Namespaces)
# ==============================================================================
# Creates an isolated multi-node virtual network topology using Linux network
# namespaces (netns) and virtual ethernet pairs (veth) to simulate real-world
# routing, stateful firewalls, client workstations, servers, and rogue hosts.
# ==============================================================================

set -euo pipefail

# Ensure script is run with root privileges
if [[ $EUID -ne 0 ]]; then
   echo "[!] Error: This script must be run as root (sudo)."
   exit 1
fi

echo "======================================================================"
echo "    NetPulse: Initializing Virtual Network Namespaces Topology       "
echo "======================================================================"

# 1. Clean up any existing namespaces
ip netns del ns-client 2>/dev/null || true
ip netns del ns-router 2>/dev/null || true
ip netns del ns-server 2>/dev/null || true
ip netns del ns-attacker 2>/dev/null || true

# 2. Create Network Namespaces
echo "[+] Creating network namespaces: ns-client, ns-router, ns-server, ns-attacker..."
ip netns add ns-client
ip netns add ns-router
ip netns add ns-server
ip netns add ns-attacker

# 3. Create Virtual Ethernet (veth) Pairs
echo "[+] Establishing virtual link pairs..."
# Client <-> Router (Subnet 10.10.1.0/24)
ip link add veth-c-node type veth peer name veth-c-rtr
ip link set veth-c-node netns ns-client
ip link set veth-c-rtr netns ns-router

# Attacker <-> Router (Subnet 10.10.1.0/24 via bridge or dedicated link)
ip link add veth-a-node type veth peer name veth-a-rtr
ip link set veth-a-node netns ns-attacker
ip link set veth-a-rtr netns ns-router

# Server <-> Router (Subnet 10.10.2.0/24)
ip link add veth-s-node type veth peer name veth-s-rtr
ip link set veth-s-node netns ns-server
ip link set veth-s-rtr netns ns-router

# 4. Configure Router Interfaces & IP Forwarding
echo "[+] Configuring router interfaces and enabling kernel IP forwarding..."
ip netns exec ns-router ip link set lo up
ip netns exec ns-router ip link set veth-c-rtr up
ip netns exec ns-router ip addr add 10.10.1.1/24 dev veth-c-rtr

ip netns exec ns-router ip link set veth-a-rtr up
ip netns exec ns-router ip addr add 10.10.1.254/24 dev veth-a-rtr

ip netns exec ns-router ip link set veth-s-rtr up
ip netns exec ns-router ip addr add 10.10.2.1/24 dev veth-s-rtr

# Enable IPv4 forwarding on router
ip netns exec ns-router sysctl -w net.ipv4.ip_forward=1 >/dev/null

# 5. Configure Client Node
echo "[+] Configuring client node (10.10.1.10)..."
ip netns exec ns-client ip link set lo up
ip netns exec ns-client ip link set veth-c-node up
ip netns exec ns-client ip addr add 10.10.1.10/24 dev veth-c-node
ip netns exec ns-client ip route add default via 10.10.1.1

# 6. Configure Attacker Node
echo "[+] Configuring attacker node (10.10.1.99)..."
ip netns exec ns-attacker ip link set lo up
ip netns exec ns-attacker ip link set veth-a-node up
ip netns exec ns-attacker ip addr add 10.10.1.99/24 dev veth-a-node
ip netns exec ns-attacker ip route add default via 10.10.1.254

# 7. Configure Server Node
echo "[+] Configuring server node (10.10.2.80)..."
ip netns exec ns-server ip link set lo up
ip netns exec ns-server ip link set veth-s-node up
ip netns exec ns-server ip addr add 10.10.2.80/24 dev veth-s-node
ip netns exec ns-server ip route add default via 10.2.1.1 2>/dev/null || ip netns exec ns-server ip route add default via 10.10.2.1

echo "======================================================================"
echo "    Network Topology Setup Successfully Deployed!                     "
echo "======================================================================"
cat << 'EOF'

   +--------------------------+          +--------------------------+
   |   ns-client              |          |   ns-attacker            |
   |   IP: 10.10.1.10/24      |          |   IP: 10.10.1.99/24      |
   +-------------+------------+          +-------------+------------+
                 | (veth-c-node)                       | (veth-a-node)
                 |                                     |
                 | (veth-c-rtr)                        | (veth-a-rtr)
   +-------------+-------------------------------------+------------+
   |                        ns-router                               |
   |   Gateway 1: 10.10.1.1/24       Gateway 2: 10.10.2.1/24        |
   |   Stateful Firewall / Routing Engine / Packet Filter          |
   +------------------------------+---------------------------------+
                                  | (veth-s-rtr)
                                  |
                                  | (veth-s-node)
                   +--------------+---------------+
                   |   ns-server                  |
                   |   IP: 10.10.2.80/24          |
                   |   Web Services (HTTP/API)    |
                   +------------------------------+

EOF
echo "[*] Next step: Run './firewall_rules.sh' to enforce firewall security policies."
