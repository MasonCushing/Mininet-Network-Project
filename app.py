from flask import Flask, jsonify, render_template, send_from_directory
import os
from Topology import myNetwork
from mininet.log import setLogLevel
import re
import snmp_monitor
import traffic_controller 
from network_performance import ( measure_ping, measure_throughput)
import threading 
performance_lock = threading.Lock()


app = Flask(__name__, template_folder='Gui', static_folder='Styling')

net = None

# Displays the Topo and Gets it 

def get_node_type(name): #finds what each node type is 
    if re.fullmatch(r'r\d+', name):
        return 'router'
    if re.fullmatch(r's\d+', name):
        return 'switch'
    if re.fullmatch(r'h\d+', name):
        return 'host'
    return 'other'


def get_topology(): # converts mininet topo into the cytoscape form 
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

#Running
@app.route('/')
def index():
    return render_template('main.html')

@app.route('/login')
def login_page():
    return render_template('Login-Design/login.html')

@app.route('/qos')
def qos_page():
    return render_template('Qos-Config/Qos.html')

@app.route('/traffic')
def traffic_page():
    return render_template('Traffic-Controller/TrafficController.html')

@app.route('/gui-assets/<path:filename>')
def gui_asset(filename):
    return send_from_directory(os.path.join(app.root_path, app.template_folder), filename)


@app.route('/api/topology')
def topology():
    return jsonify(get_topology())

@app.route('/api/stats/<name>') 
def node_stats(name):
    node = net.nameToNode.get(name)
    if node is None or node not in net.hosts: # switches have no snmp agent
        return jsonify({'error': f'no snmp agent on {name}'}), 404
    return jsonify(snmp_monitor.get_node_stats(node))

@app.route('/api/traffic/stop', methods=['POST'])
def traffic_stop():
    with traffic_controller.traffic_lock:
        traffic_controller.stop_traffic(net)
    return jsonify({'status': 'stopped'})

@app.route('/api/traffic/<level>', methods=['POST'])
def traffic_start(level):
    if level not in traffic_controller.TRAFFIC_TYPES:
        return jsonify({'error': 'unknown level'}), 400
    traffic_controller.start_traffic(net, level)
    return jsonify({'status': 'started', 'level': level})
@app.route('/api/performance')
def get_performance():
  if not performance_lock.acquire(blocking=False):
    return jsonify({'latency': None, 'packet-loss': None, 'throughput': None, 'error': 'Performance measurement in progress'})
  try:
    h1 = net.get('h1')
    h2 = net.get('h2')
    latency, packet_loss = measure_ping(h1, h2)
    throughput = measure_throughput(h1, h2)
    return jsonify({
         'latency': latency,
         'packet-loss': packet_loss,
         'throughput': throughput
     })
  finally:
        performance_lock.release()

if __name__ == '__main__':
    setLogLevel('info')
    net = myNetwork()
    snmp_monitor.start_agents(net)

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        snmp_monitor.stop_agents(net)
        net.stop()

        