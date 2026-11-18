#!/usr/bin/env python3

import time
import re
from mininet_command_lock import mininet_command_lock

def measure_ping(h1, h2, count=5):
    with mininet_command_lock:
        result = h1.cmd(f"ping -c {count} {h2.IP()}")
    latency = 0
    packet_loss = 100
    for line in result.splitlines():
        match = re.search(r'(\d+(?:\.\d+)?)% packet loss', line)
        if match:
            packet_loss = float(match.group(1))
        if "rtt min/avg/max/mdev" in line:
            parts = line.split('=')[1].strip().split('/')
            latency = float(parts[1])
    return latency, packet_loss

   


def measure_throughput(h1, h2, duration=3):
    with mininet_command_lock:
        try:
            h1.cmd("pkill -f iperf3")
            h2.cmd("pkill -f iperf3")
            time.sleep(1)
            h2.cmd("iperf3 -s -D")
            time.sleep(2)
            result = h1.cmd(f"iperf3 -c {h2.IP()} -t {duration}")
            h2.cmd("pkill -f iperf3")
            match = re.search(r'(\d+(?:\.\d+)?) Mbits/sec', result)
            if match:
                return float(match.group(1))
        except Exception as e:
            print(f"throughput error:", repr(e))

    return 0


def measure_link_utilization(snmp_before, snmp_after, interval):
    
    delta_bytes = (
        (snmp_after["bytes_in"] - snmp_before["bytes_in"]) +
        (snmp_after["bytes_out"] - snmp_before["bytes_out"])
    )
    # Convert
    mbps = (delta_bytes * 8) / (interval * 1_000_000)
    return round(mbps, 2)