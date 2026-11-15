# NetPulse Linux Virtualized Lab & Firewall Benchmark Sandbox

This directory contains the automation scripts, routing definitions, stateful firewall policies, and benchmark testing utilities configured for Linux environments.

---

## 📐 Virtual Network Architecture

NetPulse configures an isolated multi-subnet topology using Linux **Network Namespaces (`ip netns`)** and **Virtual Ethernet (`veth`)** pairs:

```
   +-----------------------------+          +-----------------------------+
   |   ns-client                 |          |   ns-attacker               |
   |   IP: 10.10.1.10/24         |          |   IP: 10.10.1.99/24         |
   |   Workstation Subnet        |          |   Rogue / Attacker Node     |
   +--------------+--------------+          +--------------+--------------+
                  | (veth-c-node)                          | (veth-a-node)
                  |                                        |
                  | (veth-c-rtr)                           | (veth-a-rtr)
   +--------------+----------------------------------------+--------------+
   |                           ns-router                                  |
   |   Gateway 1: 10.10.1.1/24 (Client Subnet)                            |
   |   Gateway 2: 10.10.2.1/24 (Server Subnet)                            |
   |   Kernel IP Forwarding | Stateful iptables | SYN Cookie Defense      |
   +------------------------------+---------------------------------------+
                                  | (veth-s-rtr)
                                  |
                                  | (veth-s-node)
                   +--------------+---------------+
                   |   ns-server                  |
                   |   IP: 10.10.2.80/24          |
                   |   Protected Web Services     |
                   +------------------------------+
```

---

## 🚀 Lab Automation Scripts

| Script | Purpose | Execution |
| :--- | :--- | :--- |
| `lab_setup.sh` | Deploys virtual namespaces, veth links, IP addressing, and kernel IP forwarding | `sudo bash lab_setup.sh` |
| `firewall_rules.sh` | Enforces stateful inspection, SYN flood mitigation, stealth scan drops, and service whitelists | `sudo bash firewall_rules.sh` |
| `test_routing_firewall.sh` | Automated compliance suite verifying routing policies and firewall rule enforcement | `sudo bash test_routing_firewall.sh` |
| `benchmark_rules.sh` | Benchmarks packet filtering latency overhead and drop throughput under high traffic volume | `sudo bash benchmark_rules.sh` |
| `lab_teardown.sh` | Safely destroys virtual namespaces, veth interfaces, and restores host state | `sudo bash lab_teardown.sh` |

---

## 🛡️ Firewall Policy Breakdown

1. **Default Deny**: `iptables -P FORWARD DROP` blocks all inter-subnet routing by default.
2. **Stateful Connection Tracking**:
   ```bash
   iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
   iptables -A FORWARD -m state --state INVALID -j DROP
   ```
3. **TCP SYN Cookie Protection**:
   ```bash
   sysctl -w net.ipv4.tcp_syncookies=1
   ```
4. **Stealth Scan Detection**:
   ```bash
   # Drop NULL Scans
   iptables -A FORWARD -p tcp --tcp-flags ALL NONE -j DROP
   # Drop XMAS Scans
   iptables -A FORWARD -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP
   ```
5. **Rate Limiting & SYN Flood Defense**:
   ```bash
   iptables -A FORWARD -p tcp --syn -m limit --limit 25/s --limit-burst 50 -j ACCEPT
   iptables -A FORWARD -p tcp --syn -j DROP
   ```
6. **Rogue Node Quarantine**:
   ```bash
   iptables -I FORWARD 1 -s 10.10.1.99 -j DROP
   ```

---

## ⚡ Running on Non-Linux Systems (Docker)

If you are running Windows or macOS, you can deploy this exact virtual topology with a single command via Docker Compose:

```bash
docker compose up --build
```
