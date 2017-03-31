import signal
import sys
from logging import StreamHandler

import click
import gevent
from gevent.event import Event

import ethereum.slogging as slogging
from ethereum.utils import encode_hex, decode_hex, sha3, privtopub
from handshake_service import HandshakeService
from devp2p.app import BaseApp
from devp2p.discovery import NodeDiscovery
from devp2p.peermanager import PeerManager
from devp2p.service import BaseService

slogging.PRINT_FORMAT = '%(asctime)s %(name)s:%(levelname).1s\t%(message)s'
log = slogging.get_logger('app')

services = [NodeDiscovery, PeerManager, HandshakeService]

privkeys = [encode_hex(sha3(i)) for i in range(100, 200)]
pubkeys = [encode_hex(privtopub(decode_hex(k))[1:]) for k in privkeys]

class SimpleHandshake(BaseApp):
    client_name = 'simplehandshake'
    default_config = dict(BaseApp.default_config)


@click.group(help='Welcome to Buggy message passing')
@click.option('-l', '--log_config', multiple=False, type=str, default=":info",
              help='log_config string: e.g. ":info,eth:debug', show_default=True)
@click.pass_context
def app(ctx, log_config):
    slogging.configure(log_config)
    ctx.obj = {
        'log_config': log_config,
        'config': {
            'node': {
            },
            'handshake': {
                'network_id': 0
            },
            'discovery': {
                'listen_host': '0.0.0.0',
                'listen_port': 20170,
                'bootstrap_nodes': [
                    'enode://%s@127.0.0.1:20170' % pubkeys[0]
                ]
            },
            'p2p': {
                'listen_host': '0.0.0.0',
                'listen_port': 20170,
                'min_peers': 4,
                'max_peers': 60
            }
        }
    }


@app.command()
@click.argument('node_id', type=click.IntRange(0,100))
@click.pass_context
def run(ctx, node_id):
    """Start the daemon"""
    config = ctx.obj['config']
    config['node']['privkey_hex'] = privkeys[node_id]
    config['discovery']['listen_port'] += node_id
    config['p2p']['listen_port'] += node_id
    log.info("starting", config=config)

    app = SimpleHandshake(config)

    for service in services:
        assert issubclass(service, BaseService)
        assert service.name not in app.services
        service.register_with_app(app)
        assert hasattr(app.services, service.name)

    # start app
    log.info('starting')
    app.start()

    # wait for interrupt
    evt = Event()
    gevent.signal(signal.SIGQUIT, evt.set)
    gevent.signal(signal.SIGTERM, evt.set)
    evt.wait()

    # finally stop
    app.stop()


if __name__ == '__main__':
    app()
