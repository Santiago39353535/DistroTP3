from pox.core import core
import pox.openflow.discovery
import pox.openflow.spanning_tree
import pox.forwarding.l2_learning
from pox.lib.util import dpid_to_str
from extensions.switchFirstTry import SwitchController
from collections import deque

log = core.getLogger()
pesoDeHop = 100000000
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
    #log.info("Switch %s has come up.", dpid_to_str(event.dpid))
    if (event.connection not in self.connections):
      self.connections.add(event.connection)
      sw = SwitchController(event.dpid, event.connection,self)
      sw.peso = 1
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


    #log.info("Guarde id: %s port: %s conx id: %s port: %s",
     #dpid_to_str(link.dpid1),
     #self.switches[link.dpid1].getPortFor(link.dpid2),
     #dpid_to_str(link.dpid2),
     #self.switches[link.dpid2].getPortFor(link.dpid1))


  def helpSwitchSendMsg(self,switchControllerSrc, event):
    packet = event.parsed

    if ( packet.type != packet.IP_TYPE ) :
        return

    #log.info("\n Buscando Ruta de %s, a %s, llamado por %s", packet.src, packet.dst,switchControllerSrc.dpid)
    #dijkstra
    #setup
    distancias = {}
    prevSwitch = {}
    switchesAVisitar = []
    for node in self.switches.keys():
        distancias[node] = 99999999999
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
            distanciaNueva = distancias[switchActual] + pesoDeHop + self.switches[switchActual].getPesoALink(vecino)
            if distanciaNueva < distancias[vecino]:
                #print("ENTRE")
                distancias[vecino] = distanciaNueva
                prevSwitch[vecino] = switchActual

    #print("prevSwitch")
    #print(prevSwitch)
    #print ("SALI")

    switch_dst = None
    for switch in self.switches.values():
        #log.info("Switch %s", dpid_to_str(switch.dpid))
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

    #if (packet.src in self.switches[switchActual].getHostsConectados()):
    #    port = self.switches[switchActual].getPortForHost(packet.src)
    #    self.switches[switchActual].agregarValorFT(packet,port)
    #print("prevSwitch")
    #print(prevSwitch)
    switchActual = switch_dst.dpid
    #print("switchActual")
    #print(switchActual)

    while prevSwitch[switchActual] is not None:
        switchAnterior = prevSwitch[switchActual]
        camino.appendleft(switchActual)
        switchActual = prevSwitch[switchActual]

    camino.appendleft(switchControllerSrc.dpid)
    #print("El camino es")
    #print camino



    #for i in range(0,len(camino)-1):

    if(len(camino)==1):
        self.switches[camino[0]].setFWT(
                event.port,
                self.switches[camino[0]].getPortForHost(packet.dst),
                packet,
                event)
    else:
        print(camino[1],camino[0])
        self.switches[camino[0]].increaseLinkWeight(camino[1])
        self.switches[camino[0]].setFWT(
                event.port,
                self.switches[camino[0]].getPortFor(camino[1]),
                packet,
                event)

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
