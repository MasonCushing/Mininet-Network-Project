let cy;
let selectedNode = null; 
let selectedEdge = null;

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
            }
        ],

        layout: {
            name: 'cose',
            animate: false,
            padding: 35
        }
    });

    document.getElementById('network-status').textContent = 'Network loaded';
}

document.addEventListener('DOMContentLoaded', () => {
    loadTopology().catch((error) => {
        console.error(error);
        document.getElementById('network-status').textContent =
            'Failed to load topology: ' + error.message;
    });

});

function setupEvents(){
        /* Saves node on click for dynamic on click stuff*/ 
        cy.on('tap', 'node', evt => {  /* when a node is clicked it runs the function */
            selectedNode = evt.target.id(); /*gets a nodes id puts it in a string selected nodes*/
            selectedEdge = null; /*Removes the edge if previously picked so were not saving multiple points at once */
            console.log('node', selectedNode);  /**/
        }); 
    
        cy.on('tap', 'edge', evt => {
            selectedEdge = evt.target.id();
            selectedNode = null; 
            console.log(selectedEdge)
        }); 

        cy.on('tap', evt => {
            if (evt.target === cy) {
                selectedNode = null; // removes saved varibales on click on anything other then a node and edge
                selectedEdge = null;
            }
        });

}
