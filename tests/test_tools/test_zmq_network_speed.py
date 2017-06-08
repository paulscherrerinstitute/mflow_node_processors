import argparse

import zmq


def test_zmq_network_speed(address, conn_type="connect", mode=zmq.PULL, queue_size=100):
    context = zmq.Context()

    # Start correct type of socket.
    if mode.lower() == "pull":
        socket = context.socket(zmq.PULL)
    elif mode.lower() == "sub":
        socket = context.socket(zmq.SUB)
        socket.setsockopt_string(zmq.SUBSCRIBE, '')
    else:
        raise ValueError("mode can be 'sub' or 'pull'")

    # Connect or bind.
    if conn_type.lower() == "connect":
        socket.connect(address)
    elif conn_type.lower() == "bind":
        socket.bind(address)
    else:
        raise ValueError("conn_type can be 'connect' or 'bind'")

    socket.set_hwm(queue_size)

    try:
        while True:
            socket.recv_multipart()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ZMQ network speed.')
    parser.add_argument('source', type=str, help='Source address - format "tcp://<address>:<port>"')
    parser.add_argument('-c', '--connection', default='connect', choices=['connect', 'bind'], type=str,
                        help='Connection type - either connect (default) or bind')
    parser.add_argument('-m', '--mode', default='pull', choices=['pull', 'sub'], type=str,
                        help='Communication mode - either pull (default) or sub')
    parser.add_argument('-q', '--queue_size', default=100, type=int, help='High water mark')
    arguments = parser.parse_args()

    test_zmq_network_speed(arguments.source, arguments.connection, arguments.mode, arguments.queue_size)
