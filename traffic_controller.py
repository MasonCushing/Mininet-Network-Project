import random
from Topology import ROUTER_SWITCHES, SWITCH_HOST_IDS
from mininet_command_lock import mininet_command_lock

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


def start_traffic(net, profile):
    client_id, server_id = PROFILE_PAIRS[profile]
    client = net.get(f'h{client_id}')
    server = net.get(f'h{server_id}')
    port = 5201 + list(TRAFFIC_PROFILES).index(profile)

    with traffic_lock:
        client.cmd('pkill -x iperf')
        server.cmd('pkill -x iperf')
        _start_flow(net, profile, client_id, server_id, port)


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
