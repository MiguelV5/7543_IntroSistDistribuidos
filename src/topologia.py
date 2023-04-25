from mininet.topo import Topo
from mininet.link import TCLink


class CustomTopo (Topo):
    def __init__(self, num_clients, loss_percent):
        # Initialize topology
        Topo.__init__(self)
        # Create server host
        server = self.addHost('h0')

        # Create switch
        switch = self.addSwitch('s1')
        self.addLink(server, switch, cls=TCLink, loss=loss_percent)

        # Create other hosts
        for i in range(1, num_clients+1):
            host_name = 'h{}'.format(i)
            host = self.addHost(host_name)

            # Create links from server to other hosts
            self.addLink(switch, host, cls=TCLink, loss=loss_percent)


topos = {'customTopo': CustomTopo}
