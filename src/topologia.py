from mininet.topo import Topo
from mininet.link import TCLink
import sys


class CustomTopo (Topo):
    def __init__ (self, hosts, loss_percent):
        # Initialize topology
        Topo.__init__(self)
        # Create hosts
        for i in range(1, hosts + 1):
            host_name = 'h{}'.format(i)
            host = self.addHost(host_name)
            # Add links between hosts
            for j in range(i+1, hosts + 1):
                other_name = 'h{}'.format(j)
                other = self.addHost(other_name)
                self.addLink(host, other, cls = TCLink, loss = loss_percent)


topos = {  'customTopo' : CustomTopo }