import os, re, threading 

SNMP_DIR = '/tmp/mn_snmp' #where agent confics and log files go so the nodes read and write here Tmp make data cleaned on end
COMMUNITY = "public" # password to agents they wont lisen to request unless this is provided
_lock = threading.Lock()
OID_TABLE = {
    '2': 'name', '6': 'mac', '8': 'status',
    '10': 'bytes_in', '11': 'packets_in', '14': 'errors_in',
    '16': 'bytes_out', '17': 'packets_out', '20': 'errors_out',
} # numbers represent the columns from oid address it determines which statistic


def start_agents(net):
    os.makedirs(SNMP_DIR, exist_ok=True) #makes a dir to store data without it we have nowhere to store agent info 
    for nodes in net.hosts:
        nodes.cmd("mkdir -p /tmp/mn_snmp")
        nodes.cmd("snmpd -Lsd -Lf /dev/null -p /var/run/snmpd.pid -c /etc/snmp/snmpd.conf")

def stop_agents(net):
    for nodes in net.hosts:
        node.cmd("pkill -x snmpd")

def walk(nodes,old):
    result = nodes.cmd(f"snmpwalk -v2c -c {COMMUNITY} " f"127.0.0.1 {oid}")
    return result

def get():
    result = nodes.cmd( f"snmpget -v2c -c {COMMUNITY} " f"127.0.0.1 {oid}" )
    return result.strip()

def get_node_stats(); 

