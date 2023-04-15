from mininet.topo import Topo
from mininet.link import TCLink


class CustomTopo (Topo):
    def __init__(self, num_hosts, loss_percent):
        # Initialize topology
        Topo.__init__(self)
        # Create hosts
        hosts = []
        for i in range(0, num_hosts + 1):
            host_name = 'h{}'.format(i)
            host = self.addHost(host_name)
            hosts.append(host)

        # Add links between server and other hosts (h0 is the server)
        for i in range(1, num_hosts + 1):
            self.addLink(hosts[0], hosts[i], cls=TCLink, loss=loss_percent)


topos = {'customTopo': CustomTopo}
