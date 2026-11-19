const options = [
    "H1","H2","H3","H4","H5",
    "H6","H7","H8","H9","H10",
    "H11","H12","H13","H14","H15",
    "H16","H17","H18","H19","H20",
    "H21","H22","H23","H24","H25",
    "H26","H27","H28","H29","H30",
    "H31","H32","H33","H34","H35",
    "H36","H37","H38","H39","H40",
    "H41","H42","H43","H44","H45",
    "H46","H47","H48","H49","H50",
    "H51","H52","H53","H54",
];

let selectedRouteMode = 'shortest';

function hostName(value) {
    return value.trim().toLowerCase();
}

async function calculateRoute(applyRoute = false) {
    const source = hostName(document.getElementById('source-host').value);
    const target = hostName(document.getElementById('target-host').value);
    const status = document.getElementById('route-status');
    const results = document.getElementById('route-results');

    if (!source || !target) {
        status.textContent = 'Enter both a source and destination host.';
        return null;
    }

    status.textContent = applyRoute ? 'Applying route...' : 'Calculating routes...';

    try {
        const url = applyRoute
            ? '/api/route'
            : '/api/route?source=' + encodeURIComponent(source) + '&target=' + encodeURIComponent(target) + '&mode=' + encodeURIComponent(selectedRouteMode);
        const response = await fetch(url, {
            method: applyRoute ? 'POST' : 'GET',
            headers: applyRoute ? {'Content-Type': 'application/json'} : undefined,
            body: applyRoute ? JSON.stringify({source, target, mode: selectedRouteMode}) : undefined
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Route calculation failed');

        status.textContent = applyRoute
            ? 'Route applied for ' + data.source + ' to ' + data.target
            : 'Routes calculated for ' + data.source + ' to ' + data.target;
        results.innerHTML =
            '<div class="route-result"><strong>BFS shortest path</strong> — ' + data.shortest_hops + ' hops' +
            '<code>' + data.shortest_path.join(' → ') + '</code></div>' +
            '<div class="route-result"><strong>Dijkstra least-traffic path</strong> — ' + data.least_traffic_hops + ' hops' +
            '<code>' + (data.least_traffic_path.length ? data.least_traffic_path.join(' → ') : 'Unavailable') + '</code></div>';
        return data;
    } catch (error) {
        status.textContent = 'Route failed: ' + error.message;
        results.textContent = '';
        return null;
    }
}

document.querySelectorAll(".dropdown-menu").forEach(menu => {
    const searchInput = menu.querySelector("input");
    const dropdown = menu.querySelector(".dropdown-list");
    if (!searchInput || !dropdown) return;

    function displayOptions(filteredOptions) {
        dropdown.innerHTML = "";

        if (filteredOptions.length === 0) {
            const emptyMessage = document.createElement("div");
            emptyMessage.className = "dropdown-empty";
            emptyMessage.textContent = "No matching hosts";
            dropdown.appendChild(emptyMessage);
            return;
        }

        filteredOptions.forEach(option => {
            const item = document.createElement("button");
            item.type = "button";
            item.textContent = option;
            item.addEventListener("click", () => {
                searchInput.value = option;
                dropdown.style.display = "none";
                calculateRoute(false);
            });
            dropdown.appendChild(item);
        });
    }

    function filterOptions() {
        const search = searchInput.value.toLowerCase();
        const filteredOptions = options.filter(option =>
            option.toLowerCase().includes(search)
        );

        displayOptions(filteredOptions);
        dropdown.style.display = "block";
    }

    searchInput.addEventListener("focus", filterOptions);
    searchInput.addEventListener("input", filterOptions);
});

document.addEventListener("click", function(event) {
    if (!event.target.closest(".dropdown-menu")) {
        document.querySelectorAll(".dropdown-list").forEach(dropdown => {
            dropdown.style.display = "none";
        });
    }
});

document.querySelectorAll('.route-mode').forEach(button => {
    button.addEventListener('click', () => {
        selectedRouteMode = button.dataset.mode;
        document.querySelectorAll('.route-mode').forEach(item => item.classList.remove('active'));
        button.classList.add('active');
        calculateRoute(false);
    });
});

document.getElementById('apply-route').addEventListener('click', () => calculateRoute(true));
document.getElementById('source-host').addEventListener('change', () => calculateRoute(false));
document.getElementById('target-host').addEventListener('change', () => calculateRoute(false));

async function loadActiveFlows() {
    const status = document.getElementById('active-flows-status');
    const tableBody = document.getElementById('active-flows-list');

    try {
        const response = await fetch('/api/traffic/active');
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Could not load active flows');

        tableBody.replaceChildren();
        if (!data.flows.length) {
            const row = tableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 5;
            cell.textContent = 'No active flows.';
        } else {
            data.flows.forEach(flow => {
                const row = tableBody.insertRow();
                [
                    flow.source,
                    flow.target,
                    flow.profile,
                    flow.port,
                    new Date(flow.started_at * 1000).toLocaleTimeString()
                ].forEach(value => {
                    row.insertCell().textContent = value;
                });
            });
        }
        status.textContent = data.flows.length
            ? data.flows.length + ' active flow(s)'
            : 'No active flows';
    } catch (error) {
        status.textContent = 'Unable to load flows: ' + error.message;
    }
}

document.getElementById('stop-all').addEventListener('click', async () => {
    const status = document.getElementById('route-status');
    status.textContent = 'Stopping traffic...';
    try {
        const response = await fetch('/api/traffic/stop', {method: 'POST'});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Could not stop traffic');
        status.textContent = 'All traffic stopped.';
        await loadActiveFlows();
    } catch (error) {
        status.textContent = 'Stop failed: ' + error.message;
    }
});

document.getElementById('start-flow').addEventListener('click', async () => {
    const status = document.getElementById('route-status');
    const route = await calculateRoute(true);
    if (!route) return;

    status.textContent = 'Starting traffic...';
    try {
        const source = hostName(document.getElementById('source-host').value);
        const target = hostName(document.getElementById('target-host').value);
        const profile = document.getElementById('traffic-profile').value;
        const rate = document.getElementById('Rate').value;
        const duration = document.getElementById('Duration').value;
        const response = await fetch('/api/traffic/custom', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({source, target, profile, rate, duration})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Could not start traffic');
        status.textContent = 'Traffic started: ' + data.source + ' to ' + data.target;
        await loadActiveFlows();
    } catch (error) {
        status.textContent = 'Start failed: ' + error.message;
    }
});

loadActiveFlows();
window.setInterval(loadActiveFlows, 2000);