#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, Host, Node, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink


def myNetwork():
# All of this topology was created via minedit a software that comes with the mininet package it exports the network topology as a python file none of this was written by us 
    net = Mininet(
        topo=None,
        build=False,
        ipBase='10.0.0.0/8',
        controller=None,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=False
    )

    info('*** Adding Ryu controller\n')

    c0 = net.addController(
        name='c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )

    info('*** Adding routers\n')

    r1 = net.addHost('r1', cls=Node, ip='0.0.0.0')
    r2 = net.addHost('r2', cls=Node, ip='0.0.0.0')
    r3 = net.addHost('r3', cls=Node, ip='0.0.0.0')

    info('*** Adding switches\n')

    s4 = net.addSwitch('s4', cls=OVSSwitch)
    s5 = net.addSwitch('s5', cls=OVSSwitch)
    s6 = net.addSwitch('s6', cls=OVSSwitch)
    s7 = net.addSwitch('s7', cls=OVSSwitch)
    s8 = net.addSwitch('s8', cls=OVSSwitch)
    s9 = net.addSwitch('s9', cls=OVSSwitch)
    s10 = net.addSwitch('s10', cls=OVSSwitch)
    s11 = net.addSwitch('s11', cls=OVSSwitch)
    s12 = net.addSwitch('s12', cls=OVSSwitch)

    info('*** Adding hosts\n')

    hosts = {}

    for i in range(1, 55):
        hosts[f'h{i}'] = net.addHost(
            f'h{i}',
            cls=Host,
            ip=f'10.0.0.{i}/8',
            defaultRoute=None
        )

    info('*** Adding links\n')

    net.addLink(r1, s4)
    net.addLink(r1, s5)
    net.addLink(r1, s6)

    for host_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        net.addLink(s4, hosts[host_name])

    for host_name in ['h7', 'h8', 'h9', 'h10', 'h11', 'h12']:
        net.addLink(s5, hosts[host_name])

    for host_name in ['h13', 'h14', 'h15', 'h18', 'h19', 'h20']:
        net.addLink(s6, hosts[host_name])

    net.addLink(r2, s7)
    net.addLink(r2, s8)
    net.addLink(r2, s9)

    for host_name in ['h16', 'h17', 'h21', 'h22', 'h23', 'h24']:
        net.addLink(s7, hosts[host_name])

    for host_name in ['h25', 'h26', 'h27', 'h28', 'h29', 'h30']:
        net.addLink(s8, hosts[host_name])

    for host_name in ['h31', 'h32', 'h33', 'h34', 'h35', 'h36']:
        net.addLink(s9, hosts[host_name])

    net.addLink(r3, s10)
    net.addLink(r3, s11)
    net.addLink(r3, s12)

    for host_name in ['h37', 'h38', 'h39', 'h40', 'h41', 'h42']:
        net.addLink(s10, hosts[host_name])

    for host_name in ['h43', 'h44', 'h45', 'h46', 'h47', 'h48']:
        net.addLink(s11, hosts[host_name])

    for host_name in ['h49', 'h50', 'h51', 'h52', 'h53', 'h54']:
        net.addLink(s12, hosts[host_name])

    net.addLink(r2, r1)
    net.addLink(r2, r3)

    info('*** Building network\n')
    net.build()

    info('*** Configuring routers\n')

    for router in [r1, r2, r3]:
        router.cmd('sysctl -w net.ipv4.ip_forward=1')

    info('*** Initializing Open vSwitch\n')
    OVSSwitch.setup()

    info('*** Starting controller\n')
    c0.start()

    info('*** Starting switches\n')

    for switch in net.switches:
        switch.start([c0])

    info('*** Starting hosts\n')

    for host in net.hosts:
        host.configDefault()

    info('*** Network startup complete\n')

    return net


if __name__ == '__main__':
    setLogLevel('info')

    net = myNetwork()

    try:
        CLI(net)
    finally:
        net.stop()