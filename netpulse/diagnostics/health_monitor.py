"""
Network Health Monitor & Connectivity Dropouts Diagnostic Engine
================================================================
Monitors round-trip latency, RFC-compliant jitter, packet loss percentage,
and tracks connectivity dropouts and latency spikes with automated diagnostic verdicts.
"""

import socket
import time
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable


@dataclass
class HealthProbe:
    """Individual network probe measurement."""
    timestamp: float
    seq: int
    rtt_ms: Optional[float]
    success: bool
    status: str


@dataclass
class DropoutEvent:
    """Recorded connectivity dropout window."""
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: float = 0.0
    failed_probes: int = 0

    @property
    def formatted_start(self) -> str:
        return datetime.fromtimestamp(self.start_time).strftime("%H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time,
            "formatted_start": self.formatted_start,
            "end_time": self.end_time,
            "duration_seconds": round(self.duration_seconds, 2),
            "failed_probes": self.failed_probes
        }


class HealthMonitor:
    """Automated network health, latency, jitter, and dropout diagnostic tool."""

    def __init__(
        self,
        target: str = "8.8.8.8",
        port: int = 53,
        timeout: float = 1.0,
        latency_spike_threshold_ms: float = 120.0,
        jitter_threshold_ms: float = 25.0,
        loss_threshold_pct: float = 5.0
    ):
        self.target = target
        self.port = port
        self.timeout = timeout
        self.latency_spike_threshold = latency_spike_threshold_ms
        self.jitter_threshold = jitter_threshold_ms
        self.loss_threshold = loss_threshold_pct

        self.probes: List[HealthProbe] = []
        self.dropouts: List[DropoutEvent] = []
        self.current_dropout: Optional[DropoutEvent] = None
        self.consecutive_fails = 0

    def probe_once(self, seq: int = 1) -> HealthProbe:
        """Perform a single TCP connect latency probe."""
        start = time.perf_counter()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)

        ts = datetime.now().timestamp()
        try:
            s.connect((self.target, self.port))
            rtt = (time.perf_counter() - start) * 1000.0
            probe = HealthProbe(timestamp=ts, seq=seq, rtt_ms=rtt, success=True, status="OK")

            # Check if recovering from a dropout
            if self.current_dropout:
                self.current_dropout.end_time = ts
                self.current_dropout.duration_seconds = ts - self.current_dropout.start_time
                self.dropouts.append(self.current_dropout)
                self.current_dropout = None
            self.consecutive_fails = 0

        except (socket.timeout, socket.error):
            probe = HealthProbe(timestamp=ts, seq=seq, rtt_ms=None, success=False, status="TIMEOUT")
            self.consecutive_fails += 1

            # Dropout tracking
            if self.consecutive_fails >= 2:
                if not self.current_dropout:
                    self.current_dropout = DropoutEvent(start_time=ts, failed_probes=self.consecutive_fails)
                else:
                    self.current_dropout.failed_probes = self.consecutive_fails
        finally:
            s.close()

        self.probes.append(probe)
        return probe

    def run_check(
        self,
        count: int = 10,
        interval: float = 0.5,
        callback: Optional[Callable[[HealthProbe], None]] = None
    ) -> Dict[str, Any]:
        """Run batch health check over specified number of iterations."""
        self.probes.clear()
        self.dropouts.clear()
        self.current_dropout = None
        self.consecutive_fails = 0

        for i in range(1, count + 1):
            probe = self.probe_once(seq=i)
            if callback:
                callback(probe)
            if i < count:
                time.sleep(interval)

        if self.current_dropout:
            self.current_dropout.end_time = datetime.now().timestamp()
            self.current_dropout.duration_seconds = self.current_dropout.end_time - self.current_dropout.start_time
            self.dropouts.append(self.current_dropout)
            self.current_dropout = None

        return self.get_report()

    def get_report(self) -> Dict[str, Any]:
        """Compute metrics, verdicts, and recommendations."""
        total_probes = len(self.probes)
        if total_probes == 0:
            return {"status": "NO_DATA"}

        successful = [p for p in self.probes if p.success and p.rtt_ms is not None]
        failed_count = total_probes - len(successful)
        packet_loss_pct = round((failed_count / total_probes) * 100.0, 1)

        rtts = [p.rtt_ms for p in successful]
        min_rtt = round(min(rtts), 2) if rtts else 0.0
        max_rtt = round(max(rtts), 2) if rtts else 0.0
        avg_rtt = round(statistics.mean(rtts), 2) if rtts else 0.0
        median_rtt = round(statistics.median(rtts), 2) if rtts else 0.0

        # Calculate RFC-style Jitter: mean absolute successive difference
        jitter = 0.0
        if len(rtts) > 1:
            diffs = [abs(rtts[i + 1] - rtts[i]) for i in range(len(rtts) - 1)]
            jitter = round(statistics.mean(diffs), 2)

        # Count spikes
        spikes = [p for p in successful if p.rtt_ms >= self.latency_spike_threshold]
        spike_count = len(spikes)

        # Health verdict determination
        verdict = "HEALTHY"
        issues = []

        if packet_loss_pct >= self.loss_threshold:
            verdict = "CRITICAL - PACKET LOSS"
            issues.append(f"High packet loss ({packet_loss_pct}% >= {self.loss_threshold}%)")
        elif len(self.dropouts) > 0:
            verdict = "WARNING - CONNECTIVITY DROPOUT"
            issues.append(f"{len(self.dropouts)} dropouts recorded")
        elif avg_rtt >= self.latency_spike_threshold or spike_count > 0:
            verdict = "DEGRADED - LATENCY SPIKES"
            issues.append(f"{spike_count} latency spikes exceeded {self.latency_spike_threshold}ms")
        elif jitter >= self.jitter_threshold:
            verdict = "DEGRADED - HIGH JITTER"
            issues.append(f"Network jitter ({jitter}ms >= {self.jitter_threshold}ms)")

        # Remediation recommendations
        recommendations = []
        if packet_loss_pct > 0:
            recommendations.append("Inspect intermediate router queues, MTU fragmentation, and wireless interference.")
        if spike_count > 0 or jitter >= self.jitter_threshold:
            recommendations.append("Check for bufferbloat on gateway router; implement FQ-CoDel or CAKE traffic shaping.")
        if len(self.dropouts) > 0:
            recommendations.append("Check physical link integrity, DHCP lease renewals, or upstream ISP flapping.")
        if not recommendations:
            recommendations.append("Network operating within optimal performance thresholds.")

        return {
            "target": self.target,
            "port": self.port,
            "verdict": verdict,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": {
                "total_probes": total_probes,
                "successful_probes": len(successful),
                "failed_probes": failed_count,
                "packet_loss_pct": packet_loss_pct,
                "min_rtt_ms": min_rtt,
                "avg_rtt_ms": avg_rtt,
                "max_rtt_ms": max_rtt,
                "median_rtt_ms": median_rtt,
                "jitter_ms": jitter,
                "latency_spikes_count": spike_count,
                "dropouts_count": len(self.dropouts)
            },
            "dropouts": [d.to_dict() for d in self.dropouts],
            "probe_history": [
                {
                    "seq": p.seq,
                    "rtt_ms": round(p.rtt_ms, 2) if p.rtt_ms else None,
                    "success": p.success,
                    "status": p.status
                }
                for p in self.probes
            ]
        }
