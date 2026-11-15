#!/usr/bin/env bash
# ==============================================================================
# NetPulse - Virtual Network Lab Teardown & Clean Up
# ==============================================================================
# Safely tears down virtual network namespaces and restores host networking.
# ==============================================================================

set -uo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "[!] Error: Must run as root (sudo)."
   exit 1
fi

echo "[*] Tearing down NetPulse virtual network namespaces..."
ip netns del ns-client 2>/dev/null || true
ip netns del ns-router 2>/dev/null || true
ip netns del ns-server 2>/dev/null || true
ip netns del ns-attacker 2>/dev/null || true

echo "[*] Cleaning up orphaned virtual interfaces..."
ip link del veth-c-rtr 2>/dev/null || true
ip link del veth-s-rtr 2>/dev/null || true
ip link del veth-a-rtr 2>/dev/null || true

echo "[✓] Virtual network lab cleanly dismantled. Host system restored."
