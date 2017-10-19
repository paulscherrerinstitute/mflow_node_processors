from argparse import ArgumentParser

import os

import h5py
import zmq
from mflow_nodes.stream_tools.mflow_message import get_raw_mflow_message

from mflow import Stream, mflow

IO_THREADS = 1
RECEIVE_TIMEOUT = 1
QUEUE_SIZE = 1000
FRAME_SIZE = [1536, 1024]
DTYPE = "uint16"


def run(connection_address, output_file, process_uid):
    os.setgid(process_uid)
    os.setuid(process_uid)

    # Setup the ZMQ listener and the stream mflow_processor.
    context = zmq.Context(io_threads=IO_THREADS)

    stream = Stream()
    stream.connect(address=connection_address,
                   conn_type=mflow.CONNECT,
                   mode=mflow.PULL,
                   receive_timeout=RECEIVE_TIMEOUT,
                   queue_size=QUEUE_SIZE,
                   context=context)

    file = h5py.File(output_file, "w")
    dataset = file.create_dataset(name="data",
                                  shape=[10000] + FRAME_SIZE,
                                  maxshape=[None] + FRAME_SIZE,
                                  chunks=tuple([1] + FRAME_SIZE),
                                  dtype=DTYPE)

    try:
        # The running event is used to signal that mflow has successfully started.
        while True:
            message = get_raw_mflow_message(stream.receive_raw())
            frame_index = message.get_frame_index()

            # Process only valid messages.
            if message is not None:
                bytes_to_write = message.get_data()
                dataset.id.write_direct_chunk((frame_index, 0, 0), bytes_to_write)

    except KeyboardInterrupt:
        stream.disconnect()
        file.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("connection_address", type=str, help="Address to connect to.")
    parser.add_argument("output_file", type=str, help="File to write to.")
    parser.add_argument("process_uid", type=str, help="Which user to write as.")
    arguments = parser.parse_args()

    run(arguments.connection_address, arguments.output_file, arguments.process_uid)
