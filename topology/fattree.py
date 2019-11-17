from mininet.topo import Topo

class FatTree(Topo):
    my_switchs = []
    my_hosts = []
    def __init__( self, niveles = 2, **opts ):
        Topo.__init__(self, **opts)

        ###Crear switches
        prefijoSW = "sw"
        for lv in range(niveles):
            nivel = []
            for i in range(2**lv):
                sw = self.addSwitch(prefijoSW+'_'+str(lv)+str(i))

                nivel.append(sw)
            self.my_switchs.append(nivel)

        ###Creacion hosts
        prefijoHost = "h"
        for i in range((2**(niveles-1))+3):
            host = self.addHost(prefijoHost+'_'+str(i))
            self.my_hosts.append(host)

        ###Conexion de los hosts
        for i in range(3):
            host = self.my_hosts.pop(0)
            self.addLink(self.my_switchs[0][0], host)
        for switch in self.my_switchs[-1]:
            host = self.my_hosts.pop(0)
            self.addLink(switch, host)

        ###conexxion switches
        for lv in range(len(self.my_switchs)):
            if lv < (niveles-1):
                for switch1 in self.my_switchs[lv]:
                    for switch2 in self.my_switchs[lv+1]:
                        self.addLink(switch1, switch2)

#topos = FatTree(4)
topos = { 'fattree': FatTree }
