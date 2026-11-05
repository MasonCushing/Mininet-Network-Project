import threading 
traffic_lock = threading.Lock() 

TRAFFIC_TYPES = {
    'low': {'pairs': 5, 'bw': '1M', 'duration': 60},
    'medium': {'pairs': 10, 'bw': '5M', 'duration': 60},
    'high': {'pairs': 20, 'bw': '10M', 'duration': 60}
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

#traffic stopper
def stop_traffic(net):
    net.hosts[0].cmd('pkill -f iperf') #kills all proccesses going on host
    

#traffic Starter
def start_traffic(net, level):
    dict_level = TRAFFIC_TYPES[level]
    with traffic_lock:
        stop_traffic(net)
        for client_id, server_id in build_pairs(dict_level['pairs']): #grabs the pairs and seperates them into client and server
            client = net.get(f'h{client_id}') #the gets turn them into servers and clients 
            server = net.get(f'h{server_id}')
            server.cmd('iperf -s -u > /dev/null 2>&1 &')
            client.cmd(f"iperf -c {server.IP()} -u -b {dict_level['bw']} " f"-t {dict_level['duration']} > /dev/null 2>&1 &") # runs command to create server and throws away outputs
