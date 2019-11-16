from pox.core import core
import pox.openflow.discovery
import pox.openflow.spanning_tree
import pox.forwarding.l2_learning
from pox.lib.util import dpid_to_str
from extensions.switchFirstTry import SwitchController
from collections import deque

log = core.getLogger()


class Controller:
  def __init__ (self):
    self.connections = set()
    self.switches = {}
    self.links = {}
    self.numberOfLinks = 0

    # Esperando que los modulos openflow y openflow_discovery esten listos
    core.call_when_ready(self.startup, ('openflow', 'openflow_discovery'))

  def startup(self):
    #print("\n Inicio")
    """
    Esta funcion se encarga de inicializar el controller
    Agrega el controller como event handler para los eventos de
    openflow y openflow_discovery
    """
    core.openflow.addListeners(self)
    core.openflow_discovery.addListeners(self)
    log.info('Controller initialized')

  def _handle_ConnectionUp(self, event):
    """
    Esta funcion es llamada cada vez que un nuevo switch establece conexion
    Se encarga de crear un nuevo switch controller para manejar los eventos de cada switch
    """
    log.info("Switch %s has come up.", dpid_to_str(event.dpid))
    if (event.connection not in self.connections):
      self.connections.add(event.connection)
      sw = SwitchController(event.dpid, event.connection,self)
      self.switches[event.dpid] = sw
      #print("\n Swith concetado")
      #print(event.dpid)

  def _handle_LinkEvent(self, event):
    """
    Esta funcion es llamada cada vez que openflow_discovery descubre un nuevo enlace
    """
    link = event.link
    #print("\n Cargando Link")
    #print("link es")
    #print(link)
    self.switches[link.dpid1].addLinkFromPortTo(link.port1,link.dpid2)
    self.switches[link.dpid2].addLinkFromPortTo(link.port2,link.dpid1)

    #print("resultados")
    #print(self.switches[link.dpid1].getHostsConectados())
    #print(self.switches[link.dpid2].getHostsConectados())


    #log.info("Link has been discovered from %s,%s to %s,%s", dpid_to_str(link.dpid1), link.port1, dpid_to_str(link.dpid2), link.port2)


  def helpSwitchSendMsg(self,switchControllerSrc, packet):
    if ( packet.type != packet.IP_TYPE ) :
        return
    #print("\n Buscando Ruta")
    #dijkstra
    #setup
    distancias = {}
    prevSwitch = {}
    switchesAVisitar = []
    for node in self.switches.keys():
        distancias[node] = 99999
        prevSwitch[node] = None
        switchesAVisitar.append(node)

    distancias[switchControllerSrc.dpid] = 0

    switchActual = switchControllerSrc.dpid
    while len(switchesAVisitar) > 0:
        switchActual = switchesAVisitar[0]
        for switch in switchesAVisitar:
            if distancias[switchActual] > distancias[switch]:
                switchActual = switch
        switchesAVisitar.remove(switchActual)

        vecinos = self.switches[switchActual].getVecinos()
        #mejora algun camino?
        for vecino in vecinos:
            distanciaNueva = distancias[switchActual] + 1
            if distanciaNueva < distancias[vecino]:
                print("ENTRE")
                distancias[vecino] = distanciaNueva
                prevSwitch[vecino] = switchActual

    print(prevSwitch)
    print ("SALI")
    switch_dst = None
    for switch in self.switches.values():
    	#print("Hots conectados:")
        #print(switch.getHostsConectados())
    	#print("Hots buscado:")
        #print(packet.dst)
        if packet.dst in switch.getHostsConectados():
            switch_dst = switch
            break
    if switch_dst == None:
        print("No se encontro el Hots")
        return

    camino = deque()
    switchActual = prevSwitch.keys()[-1]#switch_dst.dpid
    while prevSwitch[switchActual] is not None:
        print ("cargando a la tabla")
        switchAnterior = prevSwitch[switchActual]
        #port = self.switches[switchAnterior].getPortFor(switchActual)
        #self.switches[switchAnterior].agregarValorFT(packet,port)
        port = self.switches[switchActual].getPortFor(switchAnterior)
        self.switches[switchActual].agregarValorFT(packet,port)
        camino.appendleft(switchActual)
        switchActual = prevSwitch[switchActual]

    camino.appendleft(switchControllerSrc.dpid)
    print("El camino es")
    print camino
    switchControllerSrc.sendPacketThourgh(packet,2);

    #while camino:
    #    print("El paso uno")
        #switch = camino.popleft()
    #    print (switch)
    #    print (switch_dst.dpid)
    #    if switch == switch_dst.dpid:
    #        print ("cargando a la tabla")
    #        port = self.switches[switch].getPortFor(camino)
    #        self.switches[switch].agregarValorFT(packet,port)


    #IdSigueinteSwitch = camino[1].dpid

    #x ahora uso el primer camino en la lista x q no se como sacar el minimo camino del diccionaio //superbug
    #switchControllerSrc.sendPacketThourgh(packet,switchControllerSrc.getPortFor(IdSigueinteSwitch))



def launch():
  # Inicializando el modulo openflow_discovery
  pox.openflow.discovery.launch()

  # Registrando el Controller en pox.core para que sea ejecutado
  core.registerNew(Controller)

  """
  Corriendo Spanning Tree Protocol y el modulo l2_learning.
  No queremos correrlos para la resolucion del TP.
  Aqui lo hacemos a modo de ejemplo
  """
