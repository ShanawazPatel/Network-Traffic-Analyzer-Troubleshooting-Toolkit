#!/usr/bin/env bash
# ==============================================================================
# NetPulse - Automated Routing Policy & Firewall Verification Test Suite
# ==============================================================================
# Executes automated compliance tests verifying routing path integrity,
# stateful session acceptance, unauthorized port blocking, and rogue host isolation.
# ==============================================================================

set -uo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "[!] Error: Must run as root (sudo)."
   exit 1
fi

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

run_test() {
    local test_name="$1"
    local command="$2"
    local expect_success="$3"

    echo -ne "  [TEST] ${test_name} ... "

    if eval "${command}" >/dev/null 2>&1; then
        res=0
    else
        res=1
    fi

    if [[ ($res -eq 0 && "$expect_success" == "true") || ($res -ne 0 && "$expect_success" == "false") ]]; then
        echo -e "${GREEN}PASS${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "\n${CYAN}======================================================================${NC}"
echo -e "${CYAN}    NetPulse: Routing Policy & Firewall Verification Suite           ${NC}"
echo -e "${CYAN}======================================================================${NC}\n"

# Start temporary mock web server in ns-server if not running
ip netns exec ns-server python3 -m http.server 80 >/dev/null 2>&1 &
SERVER_PID=$!
sleep 1

# TEST 1: Gateway Routing Reachability
run_test "Client to Gateway Reachability (Ping 10.10.1.1)" \
    "ip netns exec ns-client ping -c 2 -W 1 10.10.1.1" \
    "true"

# TEST 2: Cross-Subnet ICMP Routing to Server
run_test "Cross-Subnet ICMP Routing (Client -> Server 10.10.2.80)" \
    "ip netns exec ns-client ping -c 2 -W 1 10.10.2.80" \
    "true"

# TEST 3: Legitimate Authorized Port Traffic (HTTP 80)
run_test "Firewall Whitelist: Client -> Server HTTP Port 80" \
    "ip netns exec ns-client timeout 2 bash -c 'echo > /dev/tcp/10.10.2.80/80'" \
    "true"

# TEST 4: Unauthorized Port Blocking (Telnet 23)
run_test "Firewall Enforcement: Client -> Server Port 23 (DROP expected)" \
    "ip netns exec ns-client timeout 2 bash -c 'echo > /dev/tcp/10.10.2.80/23'" \
    "false"

# TEST 5: Unauthorized Port Blocking (SSH 22)
run_test "Firewall Enforcement: Client -> Server Port 22 (DROP expected)" \
    "ip netns exec ns-client timeout 2 bash -c 'echo > /dev/tcp/10.10.2.80/22'" \
    "false"

# TEST 6: Rogue Attacker Node Isolation
run_test "Firewall Isolation: Attacker (10.10.1.99) -> Server HTTP 80 (DROP expected)" \
    "ip netns exec ns-attacker timeout 2 bash -c 'echo > /dev/tcp/10.10.2.80/80'" \
    "false"

# TEST 7: Attacker Ping to Server Blocked
run_test "Firewall Isolation: Attacker Ping to Server (DROP expected)" \
    "ip netns exec ns-attacker ping -c 2 -W 1 10.10.2.80" \
    "false"

# Clean up background server
kill $SERVER_PID 2>/dev/null || true

echo -e "\n${CYAN}======================================================================${NC}"
echo -e "  Tests Completed: ${GREEN}${PASSED} Passed${NC}, ${RED}${FAILED} Failed${NC}"
if [[ $FAILED -eq 0 ]]; then
    echo -e "  ${GREEN}[✓] ALL ROUTING POLICIES & FIREWALL RULES FULLY ENFORCED!${NC}"
else
    echo -e "  ${RED}[!] POLICY VIOLATIONS DETECTED. Review iptables log: dmesg | grep NETPULSE${NC}"
fi
echo -e "${CYAN}======================================================================${NC}\n"
