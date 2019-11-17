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
    self.addMiIP = {}

  def _handle_PacketIn(self, event):
    """
    Esta funcion es llamada cada vez que el switch recibe un paquete
    y no encuentra en su tabla una regla para rutearlo
    """
    #print self.__dict__
    packet = event.parsed


    #si viene de un host q no tengo anotado lo agrego a la lista de hosts alcanzables
    #print(event.port)
    #print(self.linkTo)
    if (event.port not in self.linkTo.values()):
        self.clientes[packet.src] = event.port




    #descarto ip6
    if packet.type != packet.IP_TYPE:
        return

    log.info("Packet arrived to switch %s from %s to %s", self.dpid, packet.src, packet.dst)
    #La idea era si tenia la coneccion. Mandarlo por ese puerto.
	#Pero el puerto no se esta guardando como un INT. Sino como un EthAddr
    #if (packet.dst in self.linkTo.keys()):
      #print "lo tengo"
      #puerto = self.linkTo[packet.dst]
      #self.sendPacketThourgh(packet,puerto)
      #return

    #ask4help
    self.boss_controler.helpSwitchSendMsg(self, event)


  def addLinkFromPortTo(self,port,dpid):
      self.linkTo[dpid] = port

  def getVecinos(self):
      return self.linkTo.keys()


  def sendPacketThourgh(self,msg2,out_port):
    print ("quiero mandarlo por")
    print (out_port)
    msg = of.ofp_packet_out(in_port=of.OFPP_NONE)
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

  def agregarValorHotsFT(self,packet,puerto_sal):
      #print("Agregando Valor Hots")
      #print(packet)
      msg = of.ofp_flow_mod()
      msg.command = of.OFPFC_ADD
      msg.match.dl_dst = packet.src
      msg.match.nw_dst = packet.payload.srcip
      msg.actions.append(of.ofp_action_output(port = puerto_sal))

      #print(msg)
      self.connection.send(msg);



  def agregarValorFT(self,packet,puerto_sal):
      print("Agregando Valor")
      #print(packet)
      msg = of.ofp_flow_mod()
      msg.command = of.OFPFC_ADD
      #msg.match.dl_type = packet.type
      #msg.match.dl_src = packet.src
      #msg.match.dl_dst = packet.dst
      #msg.match.nw_src= packet.payload.srcip
      #msg.match.nw_dst = packet.payload.dstip
      msg.actions.append(of.ofp_action_output(port = puerto_sal))

      #msg.data = packet.ofp
      #msg.match.in_port = in_port
      #msg.match.nw_proto = packet.payload.protocol
      #if (packet.payload.protocol == packet.payload.TCP_PROTOCOL or
        #packet.payload.protocol == packet.payload.UDP_PROTOCOL):
        #msg.match.tp_src = packet.payload.srcport
        #msg.match.tp_dst = packet.payload.dstport

      #print(msg)
      self.connection.send(msg);

  def setFWT(self, in_port, exit_port,packet,event):
    msg = of.ofp_flow_mod()

    msg.data = event.ofp
    msg.command = of.OFPFC_ADD
    msg.match.dl_dst = packet.dst
    msg.match.dl_src = packet.src
    msg.match.in_port = in_port
    msg.match.dl_type = packet.type
    msg.match.nw_src = packet.payload.srcip
    msg.match.nw_dst = packet.payload.dstip
    msg.match.nw_proto = packet.payload.protocol

    msg.actions.append(of.ofp_action_output(port = exit_port))
    log.info("Sending to switch: %s from %s to %s port in: %s out: %s.", self.dpid, packet.src, packet.dst, in_port, exit_port)
    self.connection.send(msg)
