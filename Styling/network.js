let cy; //Variables
let selectedNode = null; 
let selectedEdge = null;
let statsTimer = null;

async function loadTopology() { // Creates and loads the topoloy by retreiving it from Topology.py 
    const response = await fetch('/api/topology');

    if (!response.ok) {
        throw new Error('Could not load network topology');
    }

    const topology = await response.json(); //await makes something finish before moving on

    cy = cytoscape({
        container: document.getElementById('network'),

        elements: [
            ...topology.nodes,
            ...topology.edges
        ],

        style: [ //anything in this section is just for looks ajust if you like 
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
                style: { 'shape': 'ellipse', 'background-color': '#3b82f6' }
            },
            {
                selector: 'node[type="switch"]',
                style: { 'shape': 'round-rectangle', 'background-color': '#10b981' }
            },
            {
                selector: 'node[type="router"]',
                style: { 'shape': 'diamond', 'background-color': '#f59e0b' }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#94a3b8',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'none'
                }
            },
            {
                selector: 'node.route-highlight',
                style: {
                    'border-width': 4,
                    'border-color': '#facc15',
                    'border-opacity': 1
                }
            },
            {
                selector: 'edge.route-highlight',
                style: {
                    'width': 5,
                    'line-color': '#facc15',
                    'target-arrow-shape': 'none'
                }
            }
        ],

        layout: {
            name: 'cose',
            animate: false,
            padding: 35
        } // end of styling 
    });

    setupEvents(); //event grabber running so when you click things nodes and edges id are saved i think

    const networkStatus=document.getElementById('network-status');
    if (networkStatus) {
        networkStatus.textContent = 'network loaded successfully';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadTopology().catch((error) => {
        console.error(error);
        const networkStatus=document.getElementById('network-status');
        if (networkStatus) {
            networkStatus.textContent = 'Failed to load network topology: ' + error.message;
        }
    });

});

async function showNodeStats(id) {
    const panel = document.getElementById('stats-panel');
    const response = await fetch('/api/stats/' + id);
    if (!response.ok) { panel.textContent = id + ': no SNMP agent'; return; }
    const s = await response.json();
    panel.innerHTML = '<b>' + s.name + '</b> (' + s.type + ')<br>' +
        'Interfaces: ' + s.interfaces.join(', ') + '<br>' +
        'Bytes in/out: ' + s.bytes_in + ' / ' + s.bytes_out + '<br>' +
        'Packets in/out: ' + s.packets_in + ' / ' + s.packets_out + '<br>' +
        'Errors in/out: ' + s.errors_in + ' / ' + s.errors_out;
}

function setupEvents(){
        /* Saves node on click for dynamic on click stuff*/ 
        cy.on('tap', 'node', evt => {  /* when a node is clicked it runs the function */
            selectedNode = evt.target.id(); /*gets a nodes id puts it in a string selected nodes*/
            selectedEdge = null; /*Removes the edge if previously picked so were not saving multiple points at once */
            console.log('node', selectedNode);
            showNodeStats(selectedNode); 
           
            clearInterval(statsTimer); // allows me to refresh node stats fixes a bug where my node details didnt function properly
            statsTimer = setInterval(() => {
                if (selectedNode) {
                    showNodeStats(selectedNode);
                }
            }, 2000);

        }); 
    
        cy.on('tap', 'edge', evt => {
            selectedEdge = evt.target.id(); //basically the same idea as the one above this one 
            selectedNode = null;  
            console.log(selectedEdge)
            clearInterval(statsTimer);
        }); 

        cy.on('tap', evt => {
            if (evt.target === cy) {
                selectedNode = null; // removes saved varibales on click on anything other then a node and edge
                selectedEdge = null;
                clearInterval(statsTimer);
            }
        });

}

// traffic handler front end link ai generated for testing purposes
async function sendTraffic(url, label) { 
    const status = document.getElementById('traffic-status');
    status.textContent = 'Working...';
    try {
        const response = await fetch(url, { method: 'POST' });
        if (!response.ok) throw new Error('HTTP ' + response.status);
        status.textContent = label;
    } catch (error) {
        console.error(error);
        status.textContent = 'Failed: ' + error.message;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.traffic-btn[data-profile]').forEach(btn => {
        btn.addEventListener('click', () => {
            const profile = btn.dataset.profile;
            sendTraffic('/api/traffic/' + profile, profile + ' traffic running');
        });
    });

    document.getElementById('traffic-stop').addEventListener('click', () => {
        sendTraffic('/api/traffic/stop', 'Traffic stopped');
    });
    document.getElementById('find-route').addEventListener('click', findRoute);
    document.getElementById('route-target').addEventListener('keydown', event => {
        if (event.key === 'Enter') findRoute();
    });
    loadPerformance();
    setInterval(loadPerformance, 5000);
});
async function findRoute() {
    const source = document.getElementById('route-source').value.trim();
    const target = document.getElementById('route-target').value.trim();
    const status = document.getElementById('route-status');
    const results = document.getElementById('route-results');

    if (!source || !target) {
        status.textContent = 'Enter both a source and target.';
        return;
    }

    status.textContent = 'Calculating routes...';
    results.textContent = '';

    try {
        const response = await fetch('/api/route?source=' + encodeURIComponent(source) + '&target=' + encodeURIComponent(target));
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Route calculation failed');

        status.textContent = 'Routes calculated for ' + data.source + ' to ' + data.target;
        results.innerHTML =
            '<div class="route-result"><strong>BFS shortest path</strong><span> — ' + data.shortest_hops + ' hops</span>' +
            '<code>' + data.shortest_path.join(' → ') + '</code></div>' +
            '<div class="route-result"><strong>Dijkstra least-traffic path</strong><span> — ' + data.least_traffic_hops + ' hops</span>' +
            '<code>' + (data.least_traffic_path.length ? data.least_traffic_path.join(' → ') : 'Unavailable') + '</code></div>';

        highlightRoute(data.shortest_path, data.least_traffic_path);
    } catch (error) {
        status.textContent = 'Route failed: ' + error.message;
        clearRouteHighlight();
    }
}

function clearRouteHighlight() {
    if (!cy) return;
    cy.nodes().removeClass('route-highlight');
    cy.edges().removeClass('route-highlight');
}

function highlightRoute(shortestPath, leastTrafficPath) {
    if (!cy) return;
    clearRouteHighlight();

    const paths = [shortestPath, leastTrafficPath].filter(path => path.length);
    paths.forEach(path => {
        path.forEach(nodeId => cy.$id(nodeId).addClass('route-highlight'));

        for (let i = 0; i < path.length - 1; i++) {
            cy.edges().forEach(edge => {
                const source = edge.source().id();
                const target = edge.target().id();
                if ((source === path[i] && target === path[i + 1]) ||
                    (target === path[i] && source === path[i + 1])) {
                    edge.addClass('route-highlight');
                }
            });
        }
    });
}

async function loadPerformance(){
    try{
        const response= await fetch('/api/performance');
        if(!response.ok){
            throw new Error(
                'could not load performance matrics'
            );
        }
        const data = await response.json();
        document.getElementById('latency').textContent= data.latency+'ms';
        document.getElementById('packet-loss').textContent=data['packet-loss']+'%';
        document.getElementById('throughput').textContent= data.throughput+'Mbps';
        
    }
    catch (error){
        console.error(error);
    }
}
