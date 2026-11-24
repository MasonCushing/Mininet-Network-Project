
#!/usr/bin/env python3

import re
import time
import json

from mininet_command_lock import mininet_command_lock



def measure_ping(h1, h2, count=10):
    """Measure latency, RTT variation and packet loss."""

    if not isinstance(count, int) or not 1 <= count <= 30:
        raise ValueError("Ping count must be between 1 and 30")

    with mininet_command_lock:
        result = h1.cmd(
            f"ping -c {count} -W 2 {h2.IP()}"
        )

    latency = None
    jitter = None
    packet_loss = 100.0

    for line in result.splitlines():

        loss_match = re.search(
            r'([\d.]+)% packet loss',
            line
        )

        if loss_match:
            packet_loss = float(loss_match.group(1))

        rtt_match = re.search(
            r'rtt min/avg/max/(?:mdev|stddev) = '
            r'([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)',
            line
        )

        if rtt_match:
            latency = float(rtt_match.group(2))
            jitter = float(rtt_match.group(4))

    return latency, jitter, packet_loss


def measure_throughput(h1, h2, duration=3):
    """
    Measure throughput using iPerf3 JSON output.
    Returns throughput in Mbps.
    """

    if not isinstance(duration, int) or not 1 <= duration <= 30:
        raise ValueError(
            "Duration must be between 1 and 30 seconds"
        )

    server_started = False

    with mininet_command_lock:
        try:
            # Remove any stale iPerf3 server in the destination host.
            h2.cmd(
                "pkill -x iperf3 >/dev/null 2>&1 || true"
            )

            # Start a one-off iPerf3 server.
            h2.cmd("iperf3 -s -1 -D")

            time.sleep(1)

            # Verify the server started.
            server_check = h2.cmd("pgrep -x iperf3")

            if not server_check.strip():
                raise RuntimeError(
                    "iPerf3 server failed to start"
                )

            server_started = True

            # Run client and request JSON output.
            result = h1.cmd(
                f"iperf3 -c {h2.IP()} -t {duration} -J"
            )

            # Parse JSON output.
            try:
                data = json.loads(result)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid iPerf3 JSON output: {result[:500]}"
                ) from exc

            if data.get("error"):
                raise RuntimeError(
                    f"iPerf3 error: {data['error']}"
                )

            end_data = data.get("end", {})

            # Prefer receiver throughput.
            summary = (
                end_data.get("sum_received")
                or end_data.get("sum_sent")
                or end_data.get("sum")
            )

            if not summary:
                raise RuntimeError(
                    "No throughput summary found in iPerf3 output"
                )

            bits_per_second = summary.get(
                "bits_per_second"
            )

            if bits_per_second is None:
                raise RuntimeError(
                    "Missing bits_per_second in iPerf3 output"
                )

            # Convert bits/sec to megabits/sec.
            throughput_mbps = bits_per_second / 1_000_000

            return round(throughput_mbps, 2)

        finally:
            # Always clean up the server.
            if server_started:
                h2.cmd(
                    "pkill -x iperf3 >/dev/null 2>&1 || true"
                )


def measure_link_utilization(
    snmp_before,
    snmp_after,
    interval
):
    """Calculate average link utilization in Mbps."""

    if interval <= 0:
        raise ValueError("Interval must be positive")

    delta_bytes = (
        (snmp_after["bytes_in"] - snmp_before["bytes_in"])
        +
        (snmp_after["bytes_out"] - snmp_before["bytes_out"])
    )

    if delta_bytes < 0:
        raise ValueError(
            "SNMP counters decreased; possible counter reset"
        )

    mbps = (
        delta_bytes * 8
    ) / (
        interval * 1_000_000
    )

    return round(mbps, 2)
