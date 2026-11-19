from flask import Flask, jsonify, render_template, send_from_directory, redirect, request, session, url_for
import os
from Topology import myNetwork
from mininet.log import setLogLevel
import re
import snmp_monitor
import traffic_controller 
from network_performance import ( measure_ping, measure_throughput)
import threading 
performance_lock = threading.Lock()
from routing import (shortest_path, least_cost_path, apply_route)
current_routing_algorithm = 'shortest_path'  

app = Flask(__name__, template_folder='Gui', static_folder='Styling')
app.secret_key = os.environ.get('NETWORK_MONITOR_SECRET_KEY', os.urandom(32))

net = None

@app.before_request
def require_login_for_api():
    if request.path.startswith('/api/') and 'authenticated' not in session:
        return jsonify({'error': 'Authentication required'}), 401

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
    if 'authenticated' not in session:
        return render_template('Login-Design/login.html')
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        credentials = request.get_json(silent=True) or request.form
        if credentials.get('username') == 'admin' and credentials.get('password') == '1234':
            session['authenticated'] = True
            return jsonify({'authenticated': True, 'redirect': url_for('index')})
        return jsonify({'authenticated': False, 'message': 'Invalid username or password.'}), 401

    if 'authenticated' in session:
        return redirect(url_for('index'))
    return render_template('Login-Design/login.html')

@app.route('/qos')
def qos_page():
    if 'authenticated' not in session:
        return redirect(url_for('index'))
    return render_template('Qos-Config/Qos.html')

@app.route('/traffic')
def traffic_page():
    if 'authenticated' not in session:
        return redirect(url_for('index'))
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
    traffic_controller.stop_traffic(net)
    return jsonify({'status': 'stopped'})

@app.route('/api/traffic/active')
def traffic_active():
    return jsonify({'flows': traffic_controller.get_active_flows(net)})

@app.route('/api/traffic/random', methods=['POST'])
def traffic_random():
    traffic_controller.start_random_traffic(net)
    return jsonify({'status': 'started', 'profile': 'random'})

@app.route('/api/traffic/custom', methods=['POST'])
def traffic_custom():
    data = request.get_json(silent=True) or {}
    source = data.get('source')
    target = data.get('target')
    profile = data.get('profile')
    rate = data.get('rate') or None
    duration = data.get('duration') or None

    if not isinstance(source, str) or not isinstance(target, str):
        return jsonify({'error': 'Source and destination must be host names'}), 400
    if source not in net.nameToNode or target not in net.nameToNode:
        return jsonify({'error': 'Unknown source or destination host'}), 400
    if source not in {host.name for host in net.hosts} or target not in {host.name for host in net.hosts}:
        return jsonify({'error': 'Source and destination must be hosts'}), 400
    if source == target:
        return jsonify({'error': 'Source and destination must be different hosts'}), 400
    if profile not in traffic_controller.TRAFFIC_PROFILES:
        return jsonify({'error': 'Unknown traffic profile'}), 400

    try:
        rate = float(rate) if rate is not None else None
        duration = int(duration) if duration is not None else None
    except (TypeError, ValueError):
        return jsonify({'error': 'Rate and duration must be numeric'}), 400
    if rate is not None and not 0 < rate <= 1000:
        return jsonify({'error': 'Rate must be greater than 0 and no more than 1000 Mbps'}), 400
    if duration is not None and not 1 <= duration <= 3600:
        return jsonify({'error': 'Duration must be between 1 and 3600 seconds'}), 400

    try:
        traffic_controller.start_custom_flow(
            net,
            source,
            target,
            profile,
            rate=rate,
            duration=duration
        )
    except Exception as e:
        return jsonify({'error': 'Failed to start traffic', 'details': repr(e)}), 500

    return jsonify({'status': 'started', 'source': source, 'target': target, 'profile': profile})

@app.route('/api/traffic/<profile>', methods=['POST'])
def traffic_start(profile):
    if profile not in traffic_controller.TRAFFIC_PROFILES:
        return jsonify({'error': 'unknown traffic profile'}), 400
    traffic_controller.start_traffic(net, profile)
    return jsonify({'status': 'started', 'profile': profile})

@app.route('/api/route', methods=['GET', 'POST'])
def route():
    request_data = request.get_json(silent=True) or request.args
    source = request_data.get('source', 'h1')
    target = request_data.get('target', 'h54')
    mode = request_data.get('mode', 'shortest')

    if source not in net.nameToNode or target not in net.nameToNode:
        return jsonify({'error': 'Unknown source or target node'}), 400

    try:
        shortest = shortest_path(net, source, target)
    except Exception as e:
        shortest = []
        print('Error calculating shortest path:', repr(e))
    try:
        least_traffic = least_cost_path(net, source, target)
    except Exception as e:
        least_traffic = []
        print('Error calculating least traffic path:', repr(e))

    if not shortest:
        return jsonify({'error': 'No route found', 'source': source, 'target': target}), 404

    selected_path = shortest if mode != 'least-cost' else (least_traffic or shortest)
    installed = []
    if request.method == 'POST':
        try:
            installed = apply_route(net, source, target, selected_path)
        except Exception as e:
            return jsonify({'error': 'Failed to install route', 'details': repr(e)}), 500

    return jsonify({
        "algorithms": ["BFS", "Dijkstra"],
        "source": source,
        "target": target,
        "shortest_path": shortest,
        "shortest_hops": max(0, len(shortest) - 1),
        "least_traffic_path": least_traffic,
        "least_traffic_hops": max(0, len(least_traffic) - 1),
        "selected_path": selected_path,
        "mode": mode,
        "installed_routes": installed,
        "routing_applied": request.method == 'POST'
    })

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
    net = None
    try:
        net = myNetwork()
        snmp_monitor.start_agents(net)
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        if net is not None:
            with traffic_controller.traffic_lock:
                try:
                    snmp_monitor.stop_agents(net)
                finally:
                    net.stop()

        