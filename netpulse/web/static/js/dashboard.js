/* ==========================================================================
   NetPulse SOC Dashboard - Interactive Telemetry & Chart Engine
   ========================================================================== */

let throughputChart = null;
let protocolChart = null;
let throughputHistory = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
let throughputLabels = Array(10).fill('');
let currentSimulationState = false;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  fetchOverview();
  setInterval(fetchOverview, 1500);
});

// Initialize Chart.js Graphs
function initCharts() {
  const ctxT = document.getElementById("chart-throughput");
  if (ctxT) {
    throughputChart = new Chart(ctxT.getContext("2d"), {
      type: "line",
      data: {
        labels: throughputLabels,
        datasets: [{
          label: "Packets / Sec",
          data: throughputHistory,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.1)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { display: false },
          y: {
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#94a3b8", font: { family: "JetBrains Mono", size: 10 } },
            beginAtZero: true
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  const ctxP = document.getElementById("chart-protocols");
  if (ctxP) {
    protocolChart = new Chart(ctxP.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: ["TCP", "UDP", "DNS", "HTTP", "ICMP", "ARP"],
        datasets: [{
          data: [1, 1, 1, 1, 1, 1],
          backgroundColor: [
            "#06b6d4",
            "#8b5cf6",
            "#10b981",
            "#3b82f6",
            "#f59e0b",
            "#ec4899"
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#94a3b8", font: { family: "Inter", size: 11 }, boxWidth: 12 }
          }
        },
        cutout: "65%"
      }
    });
  }
}

// Switch Active Tab
function switchTab(tabId) {
  document.querySelectorAll(".tab-pane").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

  const targetPane = document.getElementById(`tab-${tabId}`);
  if (targetPane) {
    targetPane.classList.add("active");
  }

  const activeBtn = Array.from(document.querySelectorAll(".tab-btn")).find(b => b.getAttribute("onclick").includes(tabId));
  if (activeBtn) {
    activeBtn.classList.add("active");
  }
}

// Fetch Overview Telemetry
async function fetchOverview() {
  try {
    const res = await fetch("/api/overview");
    if (!res.ok) return;
    const data = await res.json();

    const m = data.metrics;
    document.getElementById("val-total-pkts").innerText = m.total_packets.toLocaleString();
    document.getElementById("val-total-bytes").innerText = `${(m.total_bytes / 1024).toFixed(1)} KB total volume`;
    document.getElementById("val-pps").innerHTML = `${m.current_pps} <span style="font-size:14px;color:var(--text-muted)">pps</span>`;
    document.getElementById("val-bandwidth").innerText = `${m.average_bandwidth_kbps} Kbps average`;
    document.getElementById("val-threats").innerText = m.total_threats;
    document.getElementById("val-threat-sub").innerText = `${m.critical_threats} Critical, ${m.high_threats} High`;

    // Health Score
    if (m.critical_threats > 0) {
      document.getElementById("val-health-score").innerText = "45%";
      document.getElementById("val-health-score").style.color = "var(--accent-rose)";
      document.getElementById("val-health-verdict").innerText = "Under Active Threat";
    } else if (m.high_threats > 0) {
      document.getElementById("val-health-score").innerText = "75%";
      document.getElementById("val-health-score").style.color = "var(--accent-amber)";
      document.getElementById("val-health-verdict").innerText = "Anomalies Detected";
    } else {
      document.getElementById("val-health-score").innerText = "100%";
      document.getElementById("val-health-score").style.color = "var(--accent-green)";
      document.getElementById("val-health-verdict").innerText = "Optimal Performance";
    }

    // Update Simulation Button
    currentSimulationState = data.simulation_running;
    const simBtn = document.getElementById("btn-toggle-sim");
    if (simBtn) {
      if (currentSimulationState) {
        simBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Simulation';
        simBtn.classList.add("btn-primary");
        simBtn.classList.remove("btn-outline");
      } else {
        simBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Live Simulation';
        simBtn.classList.add("btn-outline");
        simBtn.classList.remove("btn-primary");
      }
    }

    // Update Throughput Chart
    if (throughputChart) {
      throughputHistory.push(m.current_pps);
      if (throughputHistory.length > 20) throughputHistory.shift();
      throughputChart.data.labels = Array(throughputHistory.length).fill('');
      throughputChart.data.datasets[0].data = throughputHistory;
      throughputChart.update("none");
    }

    // Update Protocol Chart
    if (protocolChart && data.protocol_breakdown) {
      const p = data.protocol_breakdown;
      const labels = Object.keys(p);
      const values = Object.values(p);
      if (labels.length > 0) {
        protocolChart.data.labels = labels;
        protocolChart.data.datasets[0].data = values;
        protocolChart.update("none");
      }
    }

    // Update Top Talkers Table
    renderTalkersTable(data.top_sources, data.top_destinations);

    // Update Recent Alerts Feed
    renderRecentAlerts(data.recent_alerts);

    // Update Packets Table
    if (data.recent_packets) {
      renderPacketsTable(data.recent_packets);
    }

  } catch (err) {
    console.error("Telemetry fetch error:", err);
  }
}

// Render Top Talkers
function renderTalkersTable(sources, dests) {
  const tbody = document.querySelector("#table-talkers tbody");
  if (!tbody) return;

  if (!sources || sources.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-dim)">No traffic data accumulated yet.</td></tr>';
    return;
  }

  let html = '';
  const rows = Math.max(sources.length, dests.length);
  for (let i = 0; i < Math.min(rows, 5); i++) {
    const s = sources[i] || { ip: '-', packets: '-' };
    const d = dests[i] || { ip: '-', packets: '-' };
    html += `
      <tr>
        <td style="color:var(--accent-cyan)">${s.ip}</td>
        <td>${s.packets}</td>
        <td style="color:var(--accent-amber)">${d.ip}</td>
        <td>${d.packets}</td>
      </tr>
    `;
  }
  tbody.innerHTML = html;
}

// Render Recent Alerts
function renderRecentAlerts(alerts) {
  const container = document.getElementById("feed-recent-threats");
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-dim);padding:30px 0;">No active threats detected. Network is clean.</div>';
    return;
  }

  let html = '';
  alerts.slice(0, 4).forEach(a => {
    const sevClass = a.severity === 'CRITICAL' ? 'badge-critical' : (a.severity === 'HIGH' ? 'badge-high' : 'badge-medium');
    html += `
      <div class="threat-card">
        <div class="threat-header">
          <span class="threat-title">${a.rule_name}</span>
          <span class="badge ${sevClass}">${a.severity}</span>
        </div>
        <div class="threat-desc">${a.description}</div>
        <div style="font-size:11px;color:var(--text-dim);margin-bottom:4px;">Src: ${a.source} &rarr; Dst: ${a.target}</div>
        <div class="threat-remediation"><i class="fa-solid fa-wrench"></i> ${a.recommendation}</div>
      </div>
    `;
  });
  container.innerHTML = html;

  // Also update full threats tab
  const fullContainer = document.getElementById("threats-full-list");
  if (fullContainer) {
    let fullHtml = '';
    alerts.forEach(a => {
      const sevClass = a.severity === 'CRITICAL' ? 'badge-critical' : (a.severity === 'HIGH' ? 'badge-high' : 'badge-medium');
      fullHtml += `
        <div class="threat-card" style="margin-bottom:14px;">
          <div class="threat-header">
            <div>
              <span class="threat-title" style="font-size:16px;">${a.rule_name}</span>
              <span class="badge ${sevClass}" style="margin-left:8px;">${a.severity}</span>
            </div>
            <span style="font-size:12px;color:var(--text-dim);font-family:var(--font-mono);">${a.formatted_time || 'Just now'}</span>
          </div>
          <div class="threat-desc" style="font-size:13px;margin:8px 0;">${a.description}</div>
          <div style="font-family:var(--font-mono);font-size:12px;color:var(--accent-cyan);margin-bottom:6px;">
            <b>Path:</b> ${a.source} &rarr; ${a.target}
          </div>
          <div class="threat-remediation" style="font-size:13px;">
            <i class="fa-solid fa-shield-check"></i> <b>Remediation:</b> ${a.recommendation}
          </div>
        </div>
      `;
    });
    fullContainer.innerHTML = fullHtml;
  }
}

// Render Packets Table
function renderPacketsTable(packets) {
  const tbody = document.querySelector("#table-packets tbody");
  if (!tbody) return;

  if (!packets || packets.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-dim)">Awaiting packets...</td></tr>';
    return;
  }

  let html = '';
  packets.forEach(p => {
    const protoLower = (p.protocol || 'other').toLowerCase();
    const badgeClass = `badge-${protoLower}`;
    const src = p.src_port ? `${p.src_ip}:${p.src_port}` : p.src_ip;
    const dst = p.dst_port ? `${p.dst_ip}:${p.dst_port}` : p.dst_ip;

    html += `
      <tr>
        <td style="color:var(--text-dim)">${p.formatted_time}</td>
        <td><span class="badge ${badgeClass}">${p.protocol}</span></td>
        <td style="color:var(--text-main)">${src}</td>
        <td style="color:var(--text-main)">${dst}</td>
        <td style="color:var(--accent-amber)">${p.tcp_flags_str || '-'}</td>
        <td style="color:var(--text-dim)">${p.length}B</td>
        <td style="color:#cbd5e1">${p.summary}</td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

// Instant Filter Packet Table
function filterPacketTable() {
  const query = document.getElementById("pkt-filter").value.toLowerCase();
  const rows = document.querySelectorAll("#table-packets tbody tr");
  rows.forEach(r => {
    r.style.display = r.innerText.toLowerCase().includes(query) ? '' : 'none';
  });
}

// Toggle Live Simulation Stream
async function toggleSimulation() {
  try {
    const res = await fetch("/api/simulate_toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enable: !currentSimulationState })
    });
    const data = await res.json();
    currentSimulationState = data.simulation_running;
    fetchOverview();
  } catch (e) {
    console.error(e);
  }
}

// Ingest Demo PCAP
async function loadSamplePcap() {
  try {
    const res = await fetch("/api/analyze_sample", { method: "POST" });
    const rep = await res.json();
    fetchOverview();

    // Render Forensics Pane
    const fBody = document.getElementById("forensics-body");
    if (fBody) {
      const f = rep.file_info;
      const m = rep.metrics;
      fBody.innerHTML = `
        <div class="metrics-grid" style="margin-bottom:20px;">
          <div class="glass-panel metric-card">
            <div class="metric-label">Capture File</div>
            <div class="metric-value" style="font-size:18px;">${f.file_name}</div>
            <div class="metric-sub">${f.file_size_formatted}</div>
          </div>
          <div class="glass-panel metric-card">
            <div class="metric-label">Total Packets</div>
            <div class="metric-value">${f.analyzed_packets}</div>
            <div class="metric-sub">${f.duration_seconds}s duration</div>
          </div>
          <div class="glass-panel metric-card">
            <div class="metric-label">Throughput</div>
            <div class="metric-value">${m.average_bandwidth_kbps} <span style="font-size:12px;">Kbps</span></div>
            <div class="metric-sub">${m.average_pps} pkts/sec</div>
          </div>
          <div class="glass-panel metric-card threat">
            <div class="metric-label">Threats In Capture</div>
            <div class="metric-value" style="color:var(--accent-rose)">${rep.anomalies_detected}</div>
            <div class="metric-sub">Heuristic IDS rules matched</div>
          </div>
        </div>
        <p style="color:var(--accent-green);font-weight:600;margin-bottom:12px;">
          <i class="fa-solid fa-check"></i> Deep Forensic Inspection Complete. All sessions parsed and correlated.
        </p>
      `;
    }

    alert(`[✓] Successfully ingested demo PCAP (${rep.file_info.analyzed_packets} packets, ${rep.anomalies_detected} threats detected).`);
  } catch (e) {
    console.error(e);
  }
}

// Trigger Multi-Threaded Port Scan
async function triggerPortScan() {
  const target = document.getElementById("scan-target").value;
  const ports = document.getElementById("scan-ports").value;
  const btn = document.getElementById("btn-scan");

  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';
  btn.disabled = true;

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target, ports })
    });
    const data = await res.json();

    document.getElementById("scan-results-title").innerText = `Scan Results: ${data.target} (${data.open_ports_count} Open Ports Found in ${data.scan_duration_seconds}s)`;

    const tbody = document.querySelector("#table-scan-results tbody");
    if (!data.open_ports || data.open_ports.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-dim)">No open ports discovered in target range.</td></tr>';
    } else {
      let html = '';
      data.open_ports.forEach(p => {
        html += `
          <tr>
            <td style="color:var(--accent-cyan);font-weight:700;">${p.port}</td>
            <td><span class="badge" style="background:rgba(16,185,129,0.15);color:var(--accent-green)">${p.state}</span></td>
            <td style="color:var(--accent-amber)">${p.service}</td>
            <td style="color:var(--text-dim)">${p.rtt_ms} ms</td>
            <td style="color:#cbd5e1;font-family:var(--font-mono)">${p.banner || '[No Banner Captured]'}</td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    }
  } catch (err) {
    alert("Port scan failed: " + err);
  } finally {
    btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Launch Port Scan';
    btn.disabled = false;
  }
}

// Trigger Health Diagnostics
async function triggerHealthCheck() {
  const target = document.getElementById("health-target").value;
  const count = document.getElementById("health-count").value;
  const box = document.getElementById("health-verdict-box");

  box.innerHTML = '<div style="text-align:center;color:var(--accent-cyan);padding:30px 0;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><br><br>Probing latency, jitter & dropouts...</div>';

  try {
    const res = await fetch("/api/health", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target, count })
    });
    const data = await res.json();
    const m = data.metrics;

    const vColor = data.verdict.includes("HEALTHY") ? "var(--accent-green)" : (data.verdict.includes("DEGRADED") ? "var(--accent-amber)" : "var(--accent-rose)");

    box.innerHTML = `
      <div style="border-left:4px solid ${vColor};padding-left:14px;margin-bottom:16px;">
        <div style="font-size:18px;font-weight:800;color:${vColor}">${data.verdict}</div>
        <div style="font-size:12px;color:var(--text-dim);margin-top:2px;">Target: ${data.target}:${data.port} | Probes: ${m.total_probes}</div>
      </div>
      <div class="metrics-grid" style="grid-template-columns: repeat(2, 1fr); gap:10px; margin-bottom:14px;">
        <div style="background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;">
          <small style="color:var(--text-muted)">Avg Latency</small>
          <div style="font-size:18px;font-weight:700;color:#fff">${m.avg_rtt_ms} ms</div>
        </div>
        <div style="background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;">
          <small style="color:var(--text-muted)">RFC-Compliant Jitter</small>
          <div style="font-size:18px;font-weight:700;color:var(--accent-cyan)">${m.jitter_ms} ms</div>
        </div>
        <div style="background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;">
          <small style="color:var(--text-muted)">Packet Loss</small>
          <div style="font-size:18px;font-weight:700;color:${m.packet_loss_pct > 0 ? 'var(--accent-rose)' : 'var(--accent-green)'}">${m.packet_loss_pct}%</div>
        </div>
        <div style="background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;">
          <small style="color:var(--text-muted)">Dropouts Recorded</small>
          <div style="font-size:18px;font-weight:700;color:${m.dropouts_count > 0 ? 'var(--accent-rose)' : 'var(--accent-green)'}">${m.dropouts_count}</div>
        </div>
      </div>
      <div>
        <b style="font-size:12px;color:var(--text-muted);display:block;margin-bottom:6px;">Recommendations:</b>
        ${data.recommendations.map(r => `<div style="font-size:12px;color:#cbd5e1;margin-bottom:4px;"><i class="fa-solid fa-chevron-right" style="color:var(--accent-green);font-size:10px;"></i> ${r}</div>`).join('')}
      </div>
    `;

    // Telemetry probe table
    document.getElementById("diag-detail-title").innerText = "Probe History (RTT Milliseconds)";
    const dBody = document.getElementById("diag-detail-body");
    let probeHtml = '<table class="custom-table"><thead><tr><th>Seq</th><th>Status</th><th>RTT</th></tr></thead><tbody>';
    data.probe_history.forEach(p => {
      probeHtml += `
        <tr>
          <td>#${p.seq}</td>
          <td><span class="badge" style="background:rgba(${p.success ? '16,185,129' : '244,63,94'},0.15);color:${p.success ? 'var(--accent-green)' : 'var(--accent-rose)'}">${p.status}</span></td>
          <td style="color:var(--accent-cyan)">${p.rtt_ms ? p.rtt_ms + ' ms' : 'TIMEOUT'}</td>
        </tr>
      `;
    });
    probeHtml += '</tbody></table>';
    dBody.innerHTML = probeHtml;

  } catch (err) {
    box.innerHTML = `<div style="color:var(--accent-rose)">Health check failed: ${err}</div>`;
  }
}

// Trigger DNS Benchmark
async function triggerDnsCheck() {
  const dBody = document.getElementById("diag-detail-body");
  document.getElementById("diag-detail-title").innerText = "Multi-Resolver DNS Latency Benchmark";
  dBody.innerHTML = '<div style="text-align:center;color:var(--accent-cyan);padding:20px 0;"><i class="fa-solid fa-spinner fa-spin"></i> Benchmarking resolvers...</div>';

  try {
    const res = await fetch("/api/dns", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ domain: "example.com" }) });
    const data = await res.json();

    let html = '<table class="custom-table"><thead><tr><th>Resolver</th><th>Latency (ms)</th><th>Status</th></tr></thead><tbody>';
    data.resolvers.forEach(r => {
      html += `
        <tr>
          <td style="color:var(--text-main)">${r.resolver}</td>
          <td style="color:var(--accent-cyan);font-weight:700;">${r.latency_ms ? r.latency_ms + ' ms' : '-'}</td>
          <td><span class="badge" style="background:rgba(16,185,129,0.15);color:var(--accent-green)">${r.status}</span></td>
        </tr>
      `;
    });
    html += '</tbody></table>';
    dBody.innerHTML = html;
  } catch (e) {
    dBody.innerHTML = `<div style="color:var(--accent-rose)">DNS benchmark failed: ${e}</div>`;
  }
}

// Trigger Traceroute
async function triggerTraceroute() {
  const target = document.getElementById("health-target").value;
  const dBody = document.getElementById("diag-detail-body");
  document.getElementById("diag-detail-title").innerText = `Hop-by-Hop Route Trace &rarr; ${target}`;
  dBody.innerHTML = '<div style="text-align:center;color:var(--accent-cyan);padding:20px 0;"><i class="fa-solid fa-spinner fa-spin"></i> Tracing network hops...</div>';

  try {
    const res = await fetch("/api/traceroute", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target }) });
    const data = await res.json();

    let html = '<table class="custom-table"><thead><tr><th>Hop</th><th>Gateway / Node IP</th><th>RTT Latency</th><th>Status</th></tr></thead><tbody>';
    data.hops.forEach(h => {
      html += `
        <tr>
          <td style="color:var(--accent-cyan);font-weight:700;">${h.hop}</td>
          <td style="color:var(--text-main)">${h.ip} (${h.hostname})</td>
          <td style="color:var(--accent-amber)">${h.rtt_ms ? h.rtt_ms + ' ms' : '*'}</td>
          <td><span class="badge" style="background:rgba(16,185,129,0.15);color:var(--accent-green)">${h.status}</span></td>
        </tr>
      `;
    });
    html += '</tbody></table>';
    dBody.innerHTML = html;
  } catch (e) {
    dBody.innerHTML = `<div style="color:var(--accent-rose)">Traceroute failed: ${e}</div>`;
  }
}

function clearPackets() {
  document.querySelector("#table-packets tbody").innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-dim)">Packets cleared.</td></tr>';
}
