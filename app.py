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
from routing import (shortest_path, least_cost_path)
current_routing_algorithm = 'shortest_path'  
import database

app = Flask(__name__, template_folder='Gui', static_folder='Styling')
database.initialize_database()
secret_key = os.environ.get('NETWORK_MONITOR_SECRET_KEY')

if not secret_key:
    raise RuntimeError(
        "Set NETWORK_MONITOR_SECRET_KEY before starting the application"
    )

app.secret_key = secret_key

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
    if net is None:
        return jsonify({
            'error': 'Network is not running'
        }), 503

    return jsonify(get_topology())

@app.route('/api/stats/<name>')
def node_stats(name):
    if net is None:
        return jsonify({
            'error': 'Network is not running'
        }), 503

    node = net.nameToNode.get(name)

    if node is None or node not in net.hosts:
        return jsonify({
            'error': f'No SNMP agent on {name}'
        }), 404

    try:
        return jsonify(snmp_monitor.get_node_stats(node))
    except Exception:
        app.logger.exception(
            "SNMP statistics retrieval failed"
        )
        return jsonify({
            'error': 'Unable to retrieve node statistics'
        }), 500

@app.route('/api/traffic/stop', methods=['POST'])
def traffic_stop():
    traffic_controller.stop_traffic(net)
    return jsonify({'status': 'stopped'})

@app.route('/api/traffic/random', methods=['POST'])
def traffic_random():
    traffic_controller.start_random_traffic(net)
    return jsonify({'status': 'started', 'profile': 'random'})

@app.route('/api/traffic/<profile>', methods=['POST'])
def traffic_start(profile):
    if profile not in traffic_controller.TRAFFIC_PROFILES:
        return jsonify({'error': 'unknown traffic profile'}), 400
    traffic_controller.start_traffic(net, profile)
    return jsonify({'status': 'started', 'profile': profile})



@app.route('/api/route', methods=['GET', 'POST'])
def route():
    if net is None:
        return jsonify({
            'error': 'Network is not running'
        }), 503

    data = request.get_json(silent=True) or {}

    source = data.get(
        'source', request.args.get('source', 'h1')
    )

    target = data.get(
        'target', request.args.get('target', 'h54')
    )

    algorithm = data.get(
        'algorithm',
        request.args.get('algorithm', 'both')
    )

    hosts = {host.name for host in net.hosts}

    if source not in hosts or target not in hosts:
        return jsonify({
            'error': 'Invalid source or destination'
        }), 400

    if source == target:
        return jsonify({
            'error': 'Source and destination must differ'
        }), 400

    if algorithm not in ('bfs', 'dijkstra', 'both'):
        return jsonify({
            'error': 'Invalid routing algorithm'
        }), 400

    try:
        results = {
            'source': source,
            'target': target,
            'algorithm': algorithm
        }

        if algorithm in ('bfs', 'both'):
            path = shortest_path(net, source, target)

            results['shortest_path'] = path
            results['shortest_hops'] = (
                len(path) - 1 if path else None
            )

        if algorithm in ('dijkstra', 'both'):
            path = least_cost_path(net, source, target)

            results['least_cost_path'] = path
            results['least_cost_hops'] = (
                len(path) - 1 if path else None
            )

        database.add_event(
            severity='INFO',
            event_type='ROUTING',
            message=(
                f'{algorithm.upper()} route calculated: '
                f'{source} -> {target}'
            )
        )

        return jsonify(results)

    except Exception:
        app.logger.exception(
            "Routing calculation failed"
        )

        return jsonify({
            'error': 'Unable to calculate route'
        }), 500


@app.route('/api/performance', methods=['GET', 'POST'])
def get_performance():
    if net is None:
        return jsonify({'error': 'Network is not running'}), 503

    data = request.get_json(silent=True) or {}

    source = data.get(
        'source', request.args.get('source', 'h1')
    )

    target = data.get(
        'target', request.args.get('target', 'h2')
    )

    duration = data.get('duration', 3)

    hosts = {host.name for host in net.hosts}

    if source not in hosts or target not in hosts:
        return jsonify({'error': 'Invalid host selection'}), 400

    if source == target:
        return jsonify({'error': 'Hosts must be different'}), 400

    if type(duration) is not int or not 1 <= duration <= 30:
        return jsonify({
            'error': 'Duration must be an integer between 1 and 30'
        }), 400

    if not performance_lock.acquire(blocking=False):
        return jsonify({
            'error': 'Performance measurement already running'
        }), 409

    try:
        host1 = net.get(source)
        host2 = net.get(target)

        latency, jitter, packet_loss = measure_ping(
            host1, host2, count=10
        )

        throughput = measure_throughput(
            host1, host2, duration=duration
        )

        database.add_performance(
            source=source,
            target=target,
            latency=latency,
            jitter=jitter,
            packet_loss=packet_loss,
            throughput=throughput,
            duration=duration
        )

        database.add_event(
            severity="INFO",
            event_type="PERFORMANCE",
            message=f"Performance test completed: {source} -> {target}"
        )

        return jsonify({
            'source': source,
            'target': target,

            'latency': latency,
            'jitter': jitter,
            'packet_loss': packet_loss,
            'throughput': throughput,

            'latency_unit': 'ms',
            'jitter_unit': 'ms',
            'packet_loss_unit': '%',
            'throughput_unit': 'Mbps',

            'duration': duration
        })

    except Exception:
        app.logger.exception("Performance test failed")
        return jsonify({'error': 'Performance test failed'}), 500

    finally:
        performance_lock.release()


@app.route('/api/performance/history')
def performance_history():
    limit = request.args.get(
        'limit', default=100, type=int
    )

    if limit is None or not 1 <= limit <= 1000:
        return jsonify({
            'error': 'Limit must be between 1 and 1000'
        }), 400

    try:
        history = database.get_performance_history(limit)

        return jsonify({
            'count': len(history),
            'results': history
        })

    except Exception:
        app.logger.exception(
            "Unable to retrieve performance history"
        )

        return jsonify({
            'error': 'Unable to retrieve performance history'
        }), 500

@app.route('/api/performance/history/reset', methods=['POST'])
def reset_performance_history():
    try:
        database.reset_performance_history()

        database.add_event(
            severity="INFO",
            event_type="PERFORMANCE",
            message="Performance history was reset"
        )

        return jsonify({
            'status': 'success',
            'message': 'Performance history reset successfully'
        })

    except Exception:
        app.logger.exception("History reset failed")

        return jsonify({
            'error': 'Unable to reset performance history'
        }), 500

@app.route('/api/summary')
def network_summary():
    if net is None:
        return jsonify({
            'error': 'Network is not running'
        }), 503

    hosts = net.hosts
    switches = net.switches
    routers = [
        node for node in hosts
        if get_node_type(node.name) == 'router'
    ]

    actual_hosts = [
        node for node in hosts
        if get_node_type(node.name) == 'host'
    ]

    return jsonify({
        'hosts': len(actual_hosts),
        'routers': len(routers),
        'switches': len(switches),
        'links': len(net.links)
    })


@app.route('/api/events')
def events():
    limit = request.args.get('limit', default=100, type=int)

    if limit is None or not 1 <= limit <= 500:
        return jsonify({'error': 'Limit must be between 1 and 500'}), 400

    return jsonify(database.get_events(limit))

@app.route('/api/devices')
def devices():
    if net is None:
        return jsonify({
            'error': 'Network is not running'
        }), 503

    results = []

    for node in net.hosts + net.switches:
        results.append({
            'name': node.name,
            'type': get_node_type(node.name),
            'status': 'configured'
        })

    return jsonify({
        'total': len(results),
        'devices': results
    })

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

        
