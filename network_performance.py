#!/usr/bin/env python3

import time
import re

def measure_latency(h1, h2, count=5):
    
    result = h1.cmd(f"ping -c {count} {h2.IP()}")
    # Look for average
    for line in result.splitlines():
        if "rtt min/avg/max/mdev" in line:
            parts = line.split("=")[1].strip().split("/")
            avg = float(parts[1])
            return avg

    return None


def measure_packet_loss(h1, h2, count=10):
   
    result = h1.cmd(f"ping -c {count} {h2.IP()}")

    # Look for packet loss
    for line in result.splitlines():
        if "packet loss" in line:
            parts = line.split(",")
            loss_part = parts[2].strip() 
            loss_value = int(loss_part.split("%")[0])
            return loss_value

    return None


def measure_throughput(h1, h2, duration=5):
    
    # Start server on h2
    h2.cmd("iperf3 -s -D")
    # Run client on h1
    result = h1.cmd(f"iperf3 -c {h2.IP()} -t {duration}")
    # Kill server
    h2.cmd("pkill iperf3")
    # Look for Mbits/sec
    for line in result.splitlines():
        if "Mbits/sec" in line:
            parts = line.split()
            for p in parts:
                if "Mbits/sec" in p:
                    idx = parts.index(p)
                    value = float(parts[idx - 1])
                    return value

    return None


def measure_link_utilization(snmp_before, snmp_after, interval):
    
    delta_bytes = (
        (snmp_after["bytes_in"] - snmp_before["bytes_in"]) +
        (snmp_after["bytes_out"] - snmp_before["bytes_out"])
    )
    # Convert
    mbps = (delta_bytes * 8) / (interval * 1_000_000)
    return mbps

