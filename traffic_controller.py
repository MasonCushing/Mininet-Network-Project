import threading 
traffic_lock = threading.Lock() 

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

SWITCH_GROUPS = [
    [1, 2, 3, 4, 5, 6],        # s4 host
    [7, 8, 9, 10, 11, 12],     # s5 host
    [13, 14, 15, 18, 19, 20],  # s6 host
    [16, 17, 21, 22, 23, 24],  # s7 host
    [25, 26, 27, 28, 29, 30],  # s8 host
    [31, 32, 33, 34, 35, 36],  # s9 host
    [37, 38, 39, 40, 41, 42],  # s10 host
    [43, 44, 45, 46, 47, 48],  # s11 host
    [49, 50, 51, 52, 53, 54],  # s12 host
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
        for host in net.hosts:
            host.cmd('pkill -x iperf')


def start_traffic(net, profile):
    settings = TRAFFIC_PROFILES[profile]
    client_id, server_id = PROFILE_PAIRS[profile]
    client = net.get(f'h{client_id}')
    server = net.get(f'h{server_id}')
    port = 5201 + list(TRAFFIC_PROFILES).index(profile)

    with traffic_lock:
        client.cmd('pkill -x iperf')
        server.cmd('pkill -x iperf')

        udp_args = ' -u' if settings['transport'] == 'udp' else ''
        server.cmd(
            f"iperf -s{udp_args} -p {port} > /dev/null 2>&1 &"
        )

        if 'transfer_size' in settings:
            client_args = f"-n {settings['transfer_size']}"
        elif settings['transport'] == 'tcp':
            client_args = f"-t {settings['duration']}"
        else:
            client_args = (
                f"-u -b {settings['bitrate']} "
                f"-l {settings['packet_length']} -t {settings['duration']}"
            )

        client.cmd(
            f"iperf -c {server.IP()} -p {port} {client_args} "
            f"-S {settings['tos']} > /dev/null 2>&1 &"
        )
