import rlp
from devp2p.protocol import BaseProtocol
from ethereum import slogging

log = slogging.get_logger('protocol.bhs')

class HandshakeProtocol(BaseProtocol):
    protocol_id = 9863
    network_id = 0
    max_cmd_id = 3
    name = 'bhs'
    version = 1

    def __init__(self, peer, service):
        # required by P2PProtocol
        self.config = peer.config
        BaseProtocol.__init__(self, peer, service)

    class challenge(BaseProtocol.command):
        cmd_id = 0
        structure = [
            ('challenge', rlp.sedes.big_endian_int)
        ]

    class response(BaseProtocol.command):
        cmd_id = 1
        structure = [
            ("response", rlp.sedes.big_endian_int)
        ]
