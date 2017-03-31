from devp2p.service import WiredService
from handshake_protocol import HandshakeProtocol
import random
import gevent

from ethereum import slogging

log = slogging.get_logger('handshake')

class HandshakeService(WiredService):

    name = 'hs'
    default_config = dict(
        handshake=dict(
            network_id=0,
        )
    )

    # required by WiredService
    wire_protocol = HandshakeProtocol  # create for each peer

    def __init__(self, app):
        log.warning("Handshake service init")
        cfg = app.config['handshake']
        super(HandshakeService, self).__init__(app)

    def on_wire_protocol_start(self, proto):
        log.warning('on_wire_protocol_start', proto=proto)
        assert isinstance(proto, self.wire_protocol)
        # register callbacks
        proto.receive_challenge_callbacks.append(self.on_receive_challenge)
        proto.receive_response_callbacks.append(self.on_receive_response)
        proto.challenge = random.randint(1, 100000000)
        self.verified = False
        apply_after(10, self.check_verification, proto)
        proto.send_challenge(proto.challenge)

    def on_wire_protocol_stop(self, proto):
        assert isinstance(proto, self.wire_protocol)
        log.info('on_wire_protocol_stop', proto=proto)

    def on_receive_challenge(self, proto, challenge):
        log.warning('on_receive_challenge', proto=proto)
        response = challenge * 2
        proto.send_response(response)

    def on_receive_response(self, proto, response):
        if response == proto.challenge * 2:
            self.verified = True
            log.warning('validated!', proto=proto)
        else:
            log.warning('failed!', proto=proto)
            proto.peer.stop()

    def check_verification(self, proto):
        if not self.verified:
            log.error('timeouted!', proto=proto)
            proto.peer.stop()


def apply_after(delay, func, *args, **kw_args):
    gevent.spawn_later(delay, func, *args, **kw_args)
