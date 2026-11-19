import random
from Topology import ROUTER_SWITCHES, SWITCH_HOST_IDS
from mininet_command_lock import mininet_command_lock
from routing import shortest_path

traffic_lock = mininet_command_lock
CONTINUOUS_DURATION = 2147483647

TRAFFIC_PROFILES = {
    'voice': {
        'transport': 'udp',
        'bitrate': '64K',
        'packet_length': 160,
        'duration': 60,
        'tos': '0xb8',  # DSCP EF (46)
        'description': 'Voice-like UDP stream'
    },
    'video': {
        'transport': 'udp',
        'bitrate': '4M',
        'packet_length': 1200,
        'duration': 60,
        'tos': '0x88',  # DSCP AF41 (34)
        'description': 'Video-like UDP stream'
    },
    'web': {
        'transport': 'tcp',
        'transfer_size': '2M',
        'tos': '0x00',  # Best effort
        'description': 'Short web-like TCP transfer'
    },
    'bulk': {
        'transport': 'tcp',
        'duration': 60,
        'tos': '0x20',  # DSCP CS1 (8)
        'description': 'Long-lived background TCP transfer'
    },
    'gaming': {
        'transport': 'udp',
        'bitrate': '128K',
        'packet_length': 128,
        'duration': 60,
        'tos': '0xa0',  # DSCP CS5 (40)
        'description': 'Low-rate, small-packet gaming-like UDP stream'
    },
    'streaming': {
        'transport': 'tcp',
        'duration': 60,
        'tos': '0x68',  # DSCP AF31 (26)
        'description': 'Sustained TCP video-streaming approximation'
    }
}

ROUTER_GROUPS = [
    [list(SWITCH_HOST_IDS[switch]) for switch in switches]
    for switches in ROUTER_SWITCHES.values()
]
SWITCH_GROUPS = [
    group for router_groups in ROUTER_GROUPS for group in router_groups
]

# Creates client server pair on the same switch 
def build_pairs(count):
    pairs = []
    for i in range(3):
        for group in SWITCH_GROUPS:
            pairs.append((group[i * 2], group[i * 2 + 1]))  # groups pairs and loops 3 times for each group and puts 2 of each into a tuple
    return pairs[:count]

PROFILE_PAIRS = dict(zip(TRAFFIC_PROFILES, build_pairs(len(TRAFFIC_PROFILES))))


def stop_traffic(net):
    with traffic_lock:
        _stop_all_traffic(net)


def _stop_all_traffic(net):
    for host in net.hosts:
        host.cmd('pkill -x iperf')
<<<<<<< Updated upstream
=======
    _active_flows.clear()


def _record_flow(client, server, profile, port, route_path=None, routing_mode=None):
    _active_flows[(client.name, port)] = {
        'source': client.name,
        'target': server.name,
        'profile': profile,
        'port': port,
        'started_at': time.time(),
        'routing_mode': routing_mode or 'default',
        'route_path': route_path or []
    }


def get_active_flows(net):
    with traffic_lock:
        if not _active_flows:
            return []

        active = []
        for key, flow in list(_active_flows.items()):
            target_ip = net.get(flow['target']).IP()
            signature = f'iperf -c {target_ip} -p {flow["port"]}'
            process_list = net.get(flow['source']).cmd('ps -C iperf -o args=')
            if any(signature in line for line in process_list.splitlines()):
                active.append(dict(flow))
            else:
                _active_flows.pop(key, None)
        return active
>>>>>>> Stashed changes


def _start_flow(net, profile, client_id, server_id, port, duration=None):
    settings = TRAFFIC_PROFILES[profile]
    client = net.get(f'h{client_id}')
    server = net.get(f'h{server_id}')

    udp_args = ' -u' if settings['transport'] == 'udp' else ''
    server.cmd(
        f"iperf -s{udp_args} -p {port} > /dev/null 2>&1 & sleep 0.1"
    )

    if 'transfer_size' in settings and duration is None:
        client_args = f"-n {settings['transfer_size']}"
    elif settings['transport'] == 'tcp':
        client_args = f"-t {duration or settings['duration']}"
    else:
        client_args = (
            f"-u -b {settings['bitrate']} "
            f"-l {settings['packet_length']} "
            f"-t {duration or settings['duration']}"
        )

    client.cmd(
        f"iperf -c {server.IP()} -p {port} {client_args} "
        f"-S {settings['tos']} > /dev/null 2>&1 &"
    )
<<<<<<< Updated upstream
=======
    _record_flow(
        client,
        server,
        profile,
        port,
        route_path=shortest_path(net, client.name, server.name)
    )
>>>>>>> Stashed changes


def start_traffic(net, profile):
    client_id, server_id = PROFILE_PAIRS[profile]
    client = net.get(f'h{client_id}')
    server = net.get(f'h{server_id}')
    port = 5201 + list(TRAFFIC_PROFILES).index(profile)

    with traffic_lock:
        client.cmd('pkill -x iperf')
        server.cmd('pkill -x iperf')
        _start_flow(net, profile, client_id, server_id, port)


<<<<<<< Updated upstream
=======
def start_custom_flow(
    net, source_name, target_name, profile, rate=None, duration=None,
    route_path=None, routing_mode=None
):
    global _next_custom_port

    if profile not in TRAFFIC_PROFILES:
        raise ValueError('Unknown traffic profile')

    source = net.get(source_name)
    target = net.get(target_name)
    settings = TRAFFIC_PROFILES[profile]

    with traffic_lock:
        udp_args = ' -u' if settings['transport'] == 'udp' else ''
        port = _next_custom_port
        _next_custom_port += 1
        if _next_custom_port > 65000:
            _next_custom_port = 5300
        target.cmd(f"iperf -s{udp_args} -p {port} > /dev/null 2>&1 & sleep 0.1")

        if settings['transport'] == 'udp':
            bitrate = f"{rate}M" if rate else settings['bitrate']
            client_args = (
                f"-u -b {bitrate} -l {settings['packet_length']} "
                f"-t {duration or settings['duration']}"
            )
        else:
            transfer_duration = duration or settings.get('duration', 60)
            client_args = f"-t {transfer_duration}"

        source.cmd(
            f"iperf -c {target.IP()} -p {port} {client_args} "
            f"-S {settings['tos']} > /dev/null 2>&1 &"
        )
        _record_flow(
            source, target, profile, port,
            route_path=route_path,
            routing_mode=routing_mode
        )


>>>>>>> Stashed changes
def start_random_traffic(net):
    profiles = list(TRAFFIC_PROFILES)
    flows = []

    for router_index, source_groups in enumerate(ROUTER_GROUPS):
        destination_groups = ROUTER_GROUPS[
            (router_index + 1) % len(ROUTER_GROUPS)
        ]
        for source_group, destination_group in zip(
            random.sample(source_groups, len(source_groups)),
            random.sample(destination_groups, len(destination_groups))
        ):
            flows.append((
                random.choice(source_group),
                random.choice(destination_group)
            ))

    assigned_profiles = random.sample(profiles, len(profiles))
    assigned_profiles.extend(
        random.choice(profiles)
        for _ in range(len(flows) - len(assigned_profiles))
    )
    random.shuffle(assigned_profiles)

    with traffic_lock:
        _stop_all_traffic(net)
        for flow_index, (profile, (client_id, server_id)) in enumerate(
            zip(assigned_profiles, flows)
        ):
            _start_flow(
                net, profile, client_id, server_id, 5201 + flow_index,
                duration=CONTINUOUS_DURATION
            )
