import os, re, threading

SNMP_DIR = '/tmp/mn_snmp' #where agent confics and log files go so the nodes read and write here Tmp make data cleaned on end
COMMUNITY = "public" # password to agents they wont lisen to request unless this is provided
BASE_OID = '1.3.6.1.2.1.2.2.1' # the interface table, every column in OID_TABLE hangs off of this
_lock = threading.Lock() # only one snmp command at a time since mininet's cmd() isnt safe to call from many threads at once
OID_TABLE = {
    '2': 'interfaces', '6': 'mac', '8': 'status',
    '10': 'bytes_in', '11': 'packets_in', '14': 'errors_in',
    '16': 'bytes_out', '17': 'packets_out', '20': 'errors_out',
} # numbers represent the columns from oid address it determines which statistic


def start_agents(net):
    os.makedirs(SNMP_DIR, exist_ok=True) #makes a dir to store data without it we have nowhere to store agent info
    for node in net.hosts: # every node gets its own config/pid/log file, nodes share one filesystem so they cant share a pid file
        conf = f'{SNMP_DIR}/{node.name}.conf'
        with open(conf, 'w') as f:
            f.write('agentaddress udp:127.0.0.1:161\n') # only listen inside the nodes own namespace
            f.write(f'rocommunity {COMMUNITY} 127.0.0.1\n') # read only access with our passwor
        node.cmd(f"snmpd -C -c {conf} -p {SNMP_DIR}/{node.name}.pid -Lf {SNMP_DIR}/{node.name}.log")


def stop_agents(net):
    for node in net.hosts:
        node.cmd(f"[ -f {SNMP_DIR}/{node.name}.pid ] && kill $(cat {SNMP_DIR}/{node.name}.pid)")


def walk(node, oid):
    with _lock:
        result = node.cmd(f"snmpwalk -v2c -c {COMMUNITY} -t 1 -r 1 " f"127.0.0.1 {oid}") # runs snmp walk
    return result


def get(node, oid):
    with _lock: #makes sure only the one runs at a time
        result = node.cmd( f"snmpget -v2c -c {COMMUNITY} -t 1 -r 1 " f"127.0.0.1 {oid}" ) #runs snmp get script
    return result.strip()


def get_node_stats(node):
    stats = {
        'name': node.name,
        'type': 'router' if re.fullmatch(r'r\d+', node.name) else 'host'
    }

    columns = {}

    for column, field in OID_TABLE.items():
        output = walk(node, f'{BASE_OID}.{column}')

        values = []

        for line in output.splitlines():
            if '=' in line:
                value = line.split('=', 1)[1].strip()

                if ': ' in value:
                    value = value.split(': ', 1)[1]

                values.append(value.strip('"'))

        columns[field] = values

    keep = [i for i, name in enumerate(columns['interfaces']) if name != 'lo']

    for field, values in columns.items():
        values = [values[i] for i in keep if i < len(values)]

        if field in ('interfaces', 'mac', 'status'):
            stats[field] = values
        else:
            stats[field] = sum(
                int(value) for value in values if value.isdigit()
            )

    return stats