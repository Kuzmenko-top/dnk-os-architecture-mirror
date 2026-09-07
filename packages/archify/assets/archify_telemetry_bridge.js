// --- DNK-MRH-HEADER ---
// mrh_id: "packages_archify_assets_archify_telemetry_bridge"
// purpose: "Live Mesh Telemetry Bridge for Archify Spatial Diagrams — connects to A2A WebSocket mesh and streams visual pulses along SVG edges and nodes"
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych Prime"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

(function () {
  'use strict';

  if (typeof window === 'undefined') return;

  const DEFAULT_WS_URL = (function () {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || 'localhost:8000';
    return `${proto}//${host}/ws/a2a`;
  })();

  class ArchifyTelemetryBridge {
    constructor(options = {}) {
      this.wsUrl = options.wsUrl || window.ARCHIFY_WS_URL || DEFAULT_WS_URL;
      this.socket = null;
      this.reconnectTimer = null;
      this.isConnected = false;
      this.pulseClass = 'archify-telemetry-pulse';
      this.activeEdges = new Set();
      this.initStyles();
      this.connect();
    }

    initStyles() {
      if (document.getElementById('archify-telemetry-styles')) return;
      const style = document.createElement('style');
      style.id = 'archify-telemetry-styles';
      style.textContent = `
        @keyframes archifyPulse {
          0% { filter: drop-shadow(0 0 2px #22d3ee); opacity: 0.8; }
          50% { filter: drop-shadow(0 0 12px #38bdf8) drop-shadow(0 0 20px #818cf8); opacity: 1; }
          100% { filter: drop-shadow(0 0 2px #22d3ee); opacity: 0.8; }
        }
        @keyframes archifyDash {
          to { stroke-dashoffset: -40; }
        }
        .archify-telemetry-active-node {
          animation: archifyPulse 1.5s infinite ease-in-out !important;
        }
        .archify-telemetry-active-edge {
          stroke: #22d3ee !important;
          stroke-width: 3px !important;
          stroke-dasharray: 6 4 !important;
          animation: archifyDash 1s linear infinite !important;
        }
        .archify-telemetry-indicator {
          position: fixed;
          bottom: 16px;
          right: 16px;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 9999px;
          background: rgba(13, 18, 31, 0.9);
          border: 1px solid rgba(56, 189, 248, 0.3);
          backdrop-filter: blur(12px);
          font-family: monospace;
          font-size: 11px;
          color: #94a3b8;
          z-index: 9999;
          box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
          user-select: none;
        }
        .archify-telemetry-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #10b981;
          box-shadow: 0 0 8px #10b981;
        }
        .archify-telemetry-dot.disconnected {
          background: #64748b;
          box-shadow: none;
        }
      `;
      document.head.appendChild(style);
      this.createIndicator();
    }

    createIndicator() {
      if (document.getElementById('archify-telemetry-indicator')) return;
      const indicator = document.createElement('div');
      indicator.id = 'archify-telemetry-indicator';
      indicator.className = 'archify-telemetry-indicator';
      indicator.innerHTML = `
        <span class="archify-telemetry-dot disconnected" id="archify-telemetry-dot"></span>
        <span id="archify-telemetry-label">A2A Mesh Telemetry: Offline</span>
      `;
      document.body.appendChild(indicator);
    }

    updateIndicator(connected, label) {
      const dot = document.getElementById('archify-telemetry-dot');
      const text = document.getElementById('archify-telemetry-label');
      if (dot && text) {
        if (connected) {
          dot.className = 'archify-telemetry-dot';
          text.textContent = label || 'A2A Mesh Telemetry: Live (Streaming)';
          text.style.color = '#38bdf8';
        } else {
          dot.className = 'archify-telemetry-dot disconnected';
          text.textContent = label || 'A2A Mesh Telemetry: Standalone / Demo';
          text.style.color = '#94a3b8';
        }
      }
    }

    connect() {
      try {
        this.socket = new WebSocket(this.wsUrl);

        this.socket.onopen = () => {
          this.isConnected = true;
          this.updateIndicator(true);
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMeshEvent(data);
          } catch (e) {
            // Raw text or non-json frame
          }
        };

        this.socket.onclose = () => {
          this.isConnected = false;
          this.updateIndicator(false);
          this.reconnectTimer = setTimeout(() => this.connect(), 5000);
        };

        this.socket.onerror = () => {
          this.isConnected = false;
          this.updateIndicator(false, 'A2A Mesh: Offline (Simulated)');
          this.startSimulation();
        };
      } catch (err) {
        this.updateIndicator(false, 'A2A Mesh: Offline (Simulated)');
        this.startSimulation();
      }
    }

    handleMeshEvent(event) {
      const { from, to, node_id, status } = event;

      if (node_id) {
        this.pulseNode(node_id);
      }
      if (from && to) {
        this.pulseConnection(from, to);
      }
    }

    pulseNode(nodeId) {
      const nodeEl =
        document.querySelector(`[data-node-id="${nodeId}"]`) ||
        document.querySelector(`[id*="${nodeId}"]`);
      if (nodeEl) {
        nodeEl.classList.add('archify-telemetry-active-node');
        setTimeout(() => {
          nodeEl.classList.remove('archify-telemetry-active-node');
        }, 1800);
      }
    }

    pulseConnection(fromId, toId) {
      const edgeEl =
        document.querySelector(`[data-from="${fromId}"][data-to="${toId}"]`) ||
        document.querySelector(`[id*="${fromId}"][id*="${toId}"]`);
      if (edgeEl) {
        edgeEl.classList.add('archify-telemetry-active-edge');
        setTimeout(() => {
          edgeEl.classList.remove('archify-telemetry-active-edge');
        }, 2200);
      }
    }

    startSimulation() {
      // Offline fallback: periodic heartbeat demonstration across discovered nodes
      if (this.simulationInterval) return;
      const demoNodes = ['node_triage', 'node_builder', 'node_dev', 'node_auditor', 'gateway', 'orchestrator'];
      this.simulationInterval = setInterval(() => {
        const randNode = demoNodes[Math.floor(Math.random() * demoNodes.length)];
        this.pulseNode(randNode);
      }, 3500);
    }
  }

  window.ArchifyTelemetryBridge = ArchifyTelemetryBridge;

  // Auto-init on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ArchifyTelemetryBridge());
  } else {
    new ArchifyTelemetryBridge();
  }
})();
