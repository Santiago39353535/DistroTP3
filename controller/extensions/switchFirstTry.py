from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class SwitchController:
  def __init__(self, dpid, connection,boss_controler):
    self.dpid = dpid
    self.connection = connection
    self.boss_controler = boss_controler
    # El SwitchController se agrega como handler de los eventos del switch
    self.connection.addListeners(self)
    self.linkTo = {}
    self.clientes = {}

  def _handle_PacketIn(self, event):
    """
    Esta funcion es llamada cada vez que el switch recibe un paquete
    y no encuentra en su tabla una regla para rutearlo
    """
    packet = event.parsed

    #si viene de un host q no tengo anotado lo agrego a la lista de hosts alcanzables
    if (packet.src not in self.clientes):
      self.clientes[packet.src] = event.port

    #ask4help
    self.boss_controler.helpSwitchSendMsg(self,packet)
    log.info("Packet arrived to switch %s from %s to %s", self.dpid, packet.src, packet.dst)

  def addLinkFromPortTo(self,port,dpid):
    self.linkTo[dpid] = port

  def getVecinos(self):
      return self.linkTo.keys()


  def sendPacketThourgh(self,msg,out_port):
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)

  def getPortFor(self,dpid):
      return self.linkTo[dpid]

  def getHostsConectados(self):
      return self.clientes.keys()

  def getPortForHost(self,host):
      return self.clientes[host]
