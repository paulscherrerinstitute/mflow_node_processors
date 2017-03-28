import logging
import sys
from argparse import ArgumentParser

from bitshuffle.h5 import H5_COMPRESS_LZ4
from mflow_nodes.stream_node import start_stream_node
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("mflow.mflow").setLevel(logging.ERROR)
logging.getLogger("ThroughputStatistics").setLevel(logging.ERROR)

parser = ArgumentParser()
parser.add_argument("instance_name", type=str, help="Name of the node instance. Should be unique.")
parser.add_argument("connect_address", type=str, help="Connect address for mflow.\n"
                                                      "Example: tcp://127.0.0.1:40000")
parser.add_argument("--output_file", type=str, help="Name of output h5 file to write.")
parser.add_argument("--rest_port", type=int, default=41001, help="Port for web interface.")
parser.add_argument("--raw", action='store_true', help="Receive the mflow messages in raw mode.")
parser.add_argument("--compression", default=None, choices=['lz4'], help="Incoming stream compression.")
input_args = parser.parse_args()

compression_data = {
    "lz4": {"compression": 32008,
            "compression_opts": (2048, H5_COMPRESS_LZ4)}
}

parameters = {"dataset_name": "data"}

if input_args.compression:
    compression_arguments = compression_data.get(input_args.compression, {})
    # noinspection PyTypeChecker
    parameters.update(compression_arguments)

if input_args.output_file:
    parameters["output_file"] = input_args.output_file

start_stream_node(instance_name=input_args.instance_name,
                  processor=HDF5ChunkedWriterProcessor(),
                  processor_parameters=parameters,
                  connection_address=input_args.connect_address,
                  control_port=input_args.rest_port,
                  receive_raw=input_args.raw)
