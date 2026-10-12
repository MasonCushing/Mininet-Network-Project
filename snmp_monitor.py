import os, re, threading 

SNMP_DIR = '/tmp/mn_snmp' #where agent confics and log files go so the nodes read and write here Tmp make data cleaned on end
COMMUNITY = "public" # password to agents they wont lisen to request unless this is provided

OID_TABLE = {
    '2': 'name', '6': 'mac', '8': 'status',
    '10': 'bytes_in', '11': 'packets_in', '14': 'errors_in',
    '16': 'bytes_out', '17': 'packets_out', '20': 'errors_out',
} # numbers represent the columns from oid address it determines which statistic


def start_agents(net):
    os.makedirs(SNMP_DIR, exist_ok=True) #makes a dir to store data without it we have nowhere to store agent info 
    for nodes in net.hosts:

def stop_agents(net):
    for nodes in net.hosts:

def walk():


def get():


def get_node_stats(); 

