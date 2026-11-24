// ==========================================
// GLOBAL VARIABLES
// ==========================================

let cy = null;
let selectedNode = null;
let selectedEdge = null;
let statsTimer = null;

let performanceChart = null;
let performanceHistory = [];

let availableHosts = [];
let previousPair = null;
let monitoringActive = false;
let monitoringTimer = null;
let automaticTestRunning = false;

const PERFORMANCE_INTERVAL = 30000;


// ==========================================
// PAGE INITIALIZATION
// ==========================================

document.addEventListener('DOMContentLoaded', () => {

    loadTopology().catch(error => {
        console.error(error);

        const status = document.getElementById('network-status');

        if (status) {
            status.textContent =
                'Failed to load topology: ' + error.message;
        }
    });

    loadNetworkSummary();

    // Traffic generator controls
    document.querySelectorAll('.traffic-btn[data-profile]')
        .forEach(btn => {
            btn.addEventListener('click', () => {
                const profile = btn.dataset.profile;

                sendTraffic(
                    '/api/traffic/' + encodeURIComponent(profile),
                    profile + ' traffic running'
                );
            });
        });

    const stopButton = document.getElementById('traffic-stop');

    if (stopButton) {
        stopButton.addEventListener('click', () => {
            sendTraffic('/api/traffic/stop', 'Traffic stopped');
        });
    }

    // Performance history controls
    const metricSelector = document.getElementById(
        'performance-metric'
    );

    if (metricSelector) {
        metricSelector.addEventListener(
            'change',
            updatePerformanceChart
        );
    }

    const testButton = document.getElementById(
        'run-performance-test'
    );

    if (testButton) {
        testButton.addEventListener('click', async () => {

            testButton.disabled = true;
            testButton.textContent = 'Testing...';

            try {
                await runPerformanceTest('h1', 'h2');
            } finally {
                testButton.disabled = false;
                testButton.textContent = 'Run New Performance Test';
            }
        });
    }

    // Start monitoring
    document.getElementById('start-monitoring')
        .addEventListener('click', startAutomaticMonitoring);

    // Stop monitoring
    document.getElementById('stop-monitoring')
        .addEventListener('click', stopAutomaticMonitoring);

    // Reset history
    document.getElementById('reset-history')
        .addEventListener('click', resetPerformanceHistory);

    // Set initial button states
    updateMonitoringButtons();

    // Load previous measurements.
    // This does NOT run a new performance test.
    loadPerformance();

});


// ==========================================
// NETWORK TOPOLOGY
// ==========================================

async function loadTopology() {

    const response = await fetch('/api/topology');

    if (!response.ok) {
        throw new Error('Could not load network topology');
    }

    const topology = await response.json();

    cy = cytoscape({

        container: document.getElementById('network'),

        elements: [
            ...topology.nodes,
            ...topology.edges
        ],

        style: [

            {
                selector: 'node',

                style: {
                    'label': 'data(label)',
                    'text-valign': 'bottom',
                    'text-margin-y': 8,
                    'width': 38,
                    'height': 38,
                    'background-color': '#64748b',
                    'color': 'white',
                    'font-size': 12
                }
            },

            {
                selector: 'node[type="host"]',

                style: {
                    'shape': 'ellipse',
                    'background-color': '#3b82f6'
                }
            },

            {
                selector: 'node[type="switch"]',

                style: {
                    'shape': 'round-rectangle',
                    'background-color': '#10b981'
                }
            },

            {
                selector: 'node[type="router"]',

                style: {
                    'shape': 'diamond',
                    'background-color': '#f59e0b'
                }
            },

            {
                selector: 'edge',

                style: {
                    'width': 2,
                    'line-color': '#94a3b8',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'none'
                }
            }

        ],

        layout: {
            name: 'cose',
            animate: false,
            padding: 35
        }

    });

    setupEvents();

    const networkStatus = document.getElementById(
        'network-status'
    );

    if (networkStatus) {
        networkStatus.textContent =
            'Network loaded successfully';
    }
}


// ==========================================
// NODE SELECTION AND SNMP STATISTICS
// ==========================================

function setupEvents() {

    // Node selection
    cy.on('tap', 'node', evt => {

        selectedNode = evt.target.id();
        selectedEdge = null;

        showNodeStats(selectedNode);

        clearInterval(statsTimer);

        statsTimer = setInterval(() => {

            if (selectedNode) {
                showNodeStats(selectedNode);
            }

        }, 2000);

    });


    // Edge selection
    cy.on('tap', 'edge', evt => {

        selectedEdge = evt.target.id();
        selectedNode = null;

        clearInterval(statsTimer);

    });


    // Background selection
    cy.on('tap', evt => {

        if (evt.target === cy) {

            selectedNode = null;
            selectedEdge = null;

            clearInterval(statsTimer);

        }

    });

}


// Display node SNMP statistics
async function showNodeStats(id) {

    const panel = document.getElementById('stats-panel');

    try {

        const response = await fetch(
            '/api/stats/' + encodeURIComponent(id)
        );

        if (!response.ok) {
            panel.textContent = id + ': No SNMP agent available';
            return;
        }

        const s = await response.json();

        // Build the panel without inserting API data as HTML.
        panel.replaceChildren();

        const heading = document.createElement('h3');
        heading.textContent = `${s.name} (${s.type})`;

        const details = [
            `Interfaces: ${(s.interfaces || []).join(', ')}`,
            `Bytes in/out: ${s.bytes_in} / ${s.bytes_out}`,
            `Packets in/out: ${s.packets_in} / ${s.packets_out}`,
            `Errors in/out: ${s.errors_in} / ${s.errors_out}`
        ];

        panel.appendChild(heading);

        details.forEach(detail => {

            const paragraph = document.createElement('p');
            paragraph.textContent = detail;

            panel.appendChild(paragraph);

        });

    } catch (error) {

        console.error('SNMP statistics error:', error);

        panel.textContent = 'Unable to retrieve node statistics';

    }

}


// ==========================================
// TRAFFIC GENERATOR
// ==========================================

async function sendTraffic(url, label) {

    const status = document.getElementById('traffic-status');

    status.textContent = 'Working...';

    try {

        const response = await fetch(url, {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || 'HTTP ' + response.status
            );
        }

        status.textContent = label;

    } catch (error) {

        console.error(error);

        status.textContent = 'Failed: ' + error.message;

    }

}


// ==========================================
// AUTOMATIC RANDOMIZED MONITORING
// ==========================================

// Retrieve available Mininet hosts.
async function loadAvailableHosts() {

    const response = await fetch('/api/devices');

    if (!response.ok) {
        throw new Error('Unable to retrieve network devices');
    }

    const data = await response.json();

    availableHosts = data.devices
        .filter(device => device.type === 'host')
        .map(device => device.name);

    if (availableHosts.length < 2) {
        throw new Error('Not enough hosts available for testing');
    }
}


// Select two different random hosts.
// Avoid repeating the immediately previous pair.
function selectRandomPair() {

    let source;
    let target;

    let attempts = 0;

    do {

        source = availableHosts[
            Math.floor(Math.random() * availableHosts.length)
        ];

        target = availableHosts[
            Math.floor(Math.random() * availableHosts.length)
        ];

        attempts++;

        if (attempts > 100) {
            break;
        }

    } while (
        source === target ||
        (
            previousPair &&
            source === previousPair.source &&
            target === previousPair.target
        )
    );

    previousPair = {
        source,
        target
    };

    return {
        source,
        target
    };
}


// Run one automatic test.
async function runAutomaticPerformanceTest() {

    if (automaticTestRunning || !monitoringActive) {
        return;
    }

    if (document.visibilityState !== 'visible') {
        return;
    }

    automaticTestRunning = true;

    const status = document.getElementById(
        'next-test-status'
    );

    try {

        if (availableHosts.length < 2) {
            await loadAvailableHosts();
        }

        const pair = selectRandomPair();

        status.textContent =
            `Testing ${pair.source} → ${pair.target}`;

        const success = await runPerformanceTest(
            pair.source,
            pair.target
        );

        if (success) {
            status.textContent =
                `Last test: ${pair.source} → ${pair.target}`;
        } else {
            status.textContent = 'Performance test failed';
        }

    } catch (error) {

        console.error(error);

        status.textContent = 'Test error: ' + error.message;

    } finally {

        automaticTestRunning = false;

    }

}


// ==========================================
// AUTOMATIC MONITORING CONTROLS
// ==========================================

function updateMonitoringButtons() {

    const startButton = document.getElementById(
        'start-monitoring'
    );

    const stopButton = document.getElementById(
        'stop-monitoring'
    );

    startButton.disabled = monitoringActive;
    stopButton.disabled = !monitoringActive;
}


// Start automatic monitoring.
async function startAutomaticMonitoring() {

    if (monitoringActive) {
        return;
    }

    monitoringActive = true;

    updateMonitoringButtons();

    const status = document.getElementById(
        'next-test-status'
    );

    status.textContent = 'Preparing network...';

    try {

        await loadAvailableHosts();

        if (!monitoringActive) {
            return;
        }

        status.textContent =
            `Monitoring ${availableHosts.length} hosts`;

        await runAutomaticPerformanceTest();

        if (monitoringActive) {
            scheduleNextTest();
        }

    } catch (error) {

        console.error(error);

        status.textContent =
            'Monitoring failed: ' + error.message;

        stopAutomaticMonitoring();

    }

}


// Schedule next measurement.
function scheduleNextTest() {

    clearTimeout(monitoringTimer);

    if (!monitoringActive) {
        return;
    }

    const status = document.getElementById(
        'next-test-status'
    );

    status.textContent =
        'Next test in 30 seconds';

    monitoringTimer = setTimeout(async () => {

        if (!monitoringActive) {
            return;
        }

        await runAutomaticPerformanceTest();

        if (monitoringActive) {
            scheduleNextTest();
        }

    }, PERFORMANCE_INTERVAL);

}


// Stop automatic monitoring.
function stopAutomaticMonitoring() {

    monitoringActive = false;

    clearTimeout(monitoringTimer);

    monitoringTimer = null;

    updateMonitoringButtons();

    const status = document.getElementById(
        'next-test-status'
    );

    status.textContent = automaticTestRunning
        ? 'Stopping after current test...'
        : 'Monitoring stopped';

}


// ==========================================
// RESET PERFORMANCE HISTORY
// ==========================================

async function resetPerformanceHistory() {

    const confirmed = window.confirm(
        'Are you sure you want to delete all saved performance measurements? This cannot be undone.'
    );

    if (!confirmed) {
        return;
    }

    const status = document.getElementById(
        'performance-chart-status'
    );

    const button = document.getElementById(
        'reset-history'
    );

    button.disabled = true;

    try {

        const response = await fetch(
            '/api/performance/history/reset',
            {
                method: 'POST'
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || 'Unable to reset history'
            );
        }

        // Clear frontend history.
        performanceHistory = [];

        // Clear latest performance values.
        updateLatestPerformance(null);

        // Clear chart.
        if (performanceChart) {
            performanceChart.destroy();
            performanceChart = null;
        }

        status.textContent =
            'Performance history successfully reset.';

    } catch (error) {

        console.error(error);

        status.textContent =
            'Reset failed: ' + error.message;

    } finally {

        button.disabled = false;

    }

}



// ==========================================
// NETWORK SUMMARY
// ==========================================

async function loadNetworkSummary() {

    try {

        const response = await fetch('/api/summary');

        if (!response.ok) {
            throw new Error('Unable to retrieve network summary');
        }

        const data = await response.json();

        document.getElementById('host-count').textContent =
            data.hosts;

        document.getElementById('router-count').textContent =
            data.routers;

        document.getElementById('switch-count').textContent =
            data.switches;

        document.getElementById('link-count').textContent =
            data.links;

    } catch (error) {

        console.error('Network summary error:', error);

    }

}


// ==========================================
// LOAD HISTORICAL PERFORMANCE
// ==========================================

// IMPORTANT:
// This function only retrieves saved results.
// It does NOT run ping or iPerf3.

async function loadPerformance() {

    const status = document.getElementById(
        'performance-chart-status'
    );

    try {

        const response = await fetch(
            '/api/performance/history?limit=100'
        );

        if (!response.ok) {
            throw new Error('Unable to load performance history');
        }

        const data = await response.json();

        performanceHistory = data.results || [];

        if (performanceHistory.length === 0) {

            status.textContent =
                'No historical data yet. Run a performance test to get started.';

            updateLatestPerformance(null);
            updatePerformanceChart();

            return;
        }

        status.textContent =
            `Showing ${performanceHistory.length} saved performance tests.`;

        // Most recent result
        updateLatestPerformance(
            performanceHistory[performanceHistory.length - 1]
        );

        updatePerformanceChart();

    } catch (error) {

        console.error('Performance history error:', error);

        status.textContent =
            'Unable to retrieve performance history.';

    }

}


// ==========================================
// UPDATE PERFORMANCE CARDS
// ==========================================

function updateLatestPerformance(result) {

    const latency = document.getElementById('latency');
    const packetLoss = document.getElementById('packet-loss');
    const throughput = document.getElementById('throughput');
    const jitter = document.getElementById('jitter');

    if (!result) {

        latency.textContent = 'No data';
        jitter.textContent = 'No data';
        packetLoss.textContent = 'No data';
        throughput.textContent = 'No data';

        return;

    }

    latency.textContent =
        result.latency == null
            ? 'N/A'
            : `${Number(result.latency).toFixed(2)} ms`;

    packetLoss.textContent =
        result.packet_loss == null
            ? 'N/A'
            : `${Number(result.packet_loss).toFixed(2)}%`;

    throughput.textContent =
        result.throughput == null
            ? 'N/A'
            : `${Number(result.throughput).toFixed(2)} Mbps`;
    
    jitter.textContent =
    result.jitter == null
        ? 'N/A'
        : `${Number(result.jitter).toFixed(2)} ms`;

}


// ==========================================
// HISTORICAL PERFORMANCE CHART
// ==========================================

function updatePerformanceChart() {

    const canvas = document.getElementById(
        'performance-chart'
    );

    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    const metricSelector = document.getElementById(
        'performance-metric'
    );

    if (!metricSelector) {
        return;
    }

    const metric = metricSelector.value;

    const metricConfig = {

        throughput: {
            label: 'Throughput (Mbps)',
            color: '#3b82f6'
        },

        latency: {
            label: 'Latency (ms)',
            color: '#16a34a'
        },

        packet_loss: {
            label: 'Packet Loss (%)',
            color: '#ef4444'
        },

        jitter: {
            label: 'Jitter / RTT variation (ms)',
            color: '#f59e0b'
        },

    };

    const config = metricConfig[metric];

    if (!config) {
        return;
    }

    const labels = performanceHistory.map(item =>
        new Date(item.timestamp).toLocaleString()
    );

    const values = performanceHistory.map(item => {

        const value = item[metric];

        return value == null
            ? null
            : Number(value);

    });

    // Destroy previous chart before creating another.
    if (performanceChart) {
        performanceChart.destroy();
    }

    performanceChart = new Chart(canvas, {

        type: 'line',

        data: {

            labels: labels,

            datasets: [{

                label: config.label,

                data: values,

                borderColor: config.color,

                backgroundColor: config.color + '22',

                fill: true,

                tension: 0.3,

                spanGaps: false

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: true,

            interaction: {
                intersect: false,
                mode: 'index'
            },

            plugins: {

                legend: {
                    display: true
                }

            },

            scales: {

                x: {
                    title: {
                        display: true,
                        text: 'Test Date'
                    }
                },

                y: {

                    beginAtZero: true,

                    title: {
                        display: true,
                        text: config.label
                    }

                }

            }

        }

    });

}


// ==========================================
// RUN A NEW PERFORMANCE TEST
// ==========================================

// This is the ONLY function that runs a new test.

async function runPerformanceTest(source, target) {

    const status = document.getElementById(
        'performance-chart-status'
    );

    status.textContent =
        `Testing ${source} → ${target}...`;

    try {

        const response = await fetch('/api/performance', {
            method: 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({
                source,
                target,
                duration: 3
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Performance test failed');
        }

        await loadPerformance();

        return true;

    } catch (error) {

        console.error(error);

        status.textContent = error.message;

        return false;

    }
}
