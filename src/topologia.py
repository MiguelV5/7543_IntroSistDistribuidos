from mininet.topo import Topo
from mininet.link import TCLink, TCIntf


class CustomTopo (Topo):
    def __init__(self, num_hosts, loss_percent):
        # Initialize topology
        Topo.__init__(self)
        # Create server host
        server = self.addHost('h0')

        # Create other hosts
        for i in range(1, num_hosts+1):
            host_name = 'h{}'.format(i)
            host = self.addHost(host_name)

            # Create links from server to other hosts
            self.addLink(server, host, cls=TCLink,
                         intf=TCIntf, loss=loss_percent)


topos = {'customTopo': CustomTopo}
