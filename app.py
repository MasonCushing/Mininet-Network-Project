from flask import Flask, jsonify, render_template
from Topology import myNetwork
from mininet.log import setLogLevel
import re

app = Flask(__name__, template_folder='Gui', static_folder='Styling')

net = None

# Displays the Topo and Gets it 

def get_node_type(name):
    if re.fullmatch(r'r\d+', name):
        return 'router'
    if re.fullmatch(r's\d+', name):
        return 'switch'
    if re.fullmatch(r'h\d+', name):
        return 'host'
    return 'other'


def get_topology():
    nodes = []
    edges = []

    for node in net.hosts + net.switches:
        nodes.append({
            'data': {
                'id': node.name,
                'label': node.name.upper(),
                'type': get_node_type(node.name)
            }
        })

    for link in net.links:
        edges.append({
            'data': {
                'id': f'{link.intf1.node.name}-{link.intf2.node.name}',
                'source': link.intf1.node.name,
                'target': link.intf2.node.name
            }
        })

    return {'nodes': nodes, 'edges': edges}

# End of diplaying the Topo


#Start Of Monitoring ps pretty sure this doesnt work

def read_host(h): 
    'data': { 
        'name': h.name,
        'ip': h.IP(),
        'Mac': h.MAC(),
    }

def read_switch(s):
    'data': {
        'name': s.name,
        'bytes' : s.dpctl('dump-ports'),

    }

def read_edges(e):
    'data':{
        'up/down': net.configLinkStatus('s1', 'h1', 'down');
        'dropS' : 	s.cmd('tc -s qdisc show dev s1-eth1')
    }

#Running
@app.route('/')
def index():
    return render_template('main.html')


@app.route('/api/topology')
def topology():
    return jsonify(get_topology())


if __name__ == '__main__':
    setLogLevel('info')
    net = myNetwork()

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        net.stop()

        