import logging
import sys
from argparse import ArgumentParser

from mflow_nodes.stream_node import start_stream_node
from mflow_processor.lz4_compressor import LZ4CompressionProcessor

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logging.getLogger("mflow.mflow").setLevel(logging.ERROR)
logging.getLogger("ThroughputStatistics").setLevel(logging.ERROR)

parser = ArgumentParser()
parser.add_argument("instance_name", type=str, help="Name of the node instance. Should be unique.")
parser.add_argument("connect_address", type=str, help="Connect address for mflow.\n"
                                                      "Example: tcp://127.0.0.1:40000")
parser.add_argument("binding_address", type=str, help="Binding address for mflow forwarding.\n"
                                                      "Example: tcp://127.0.0.1:40001")
parser.add_argument("--rest_port", type=int, default=41000, help="Port for web interface.")
parser.add_argument("--block_size", type=int, default=2048, help="LZ4 block size.")
input_args = parser.parse_args()

start_stream_node(instance_name=input_args.instance_name,
                  processor=LZ4CompressionProcessor(),
                  processor_parameters={"binding_address": input_args.binding_address},
                  connection_address=input_args.connect_address,
                  control_port=input_args.rest_port)
