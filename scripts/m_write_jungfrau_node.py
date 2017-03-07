import logging
import sys
from argparse import ArgumentParser

from mflow_nodes.stream_node import start_stream_node
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor
from mflow_processor.utils import writer_plugins

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("mflow.mflow").setLevel(logging.ERROR)

parser = ArgumentParser()
parser.add_argument("instance_name", type=str, help="Name of the node instance. Should be unique.")
parser.add_argument("connect_address", type=str, help="Connect address for mflow.\n"
                                                      "Example: tcp://127.0.0.1:40000")
parser.add_argument("--output_file", type=str, help="Name of output h5 file to write.")
parser.add_argument("--rest_port", type=int, default=41001, help="Port for web interface.")
parser.add_argument("--frame_index_dataset", type=str, default="frame_index", help="Name of the dataset to store "
                                                                                   "the frame indexes into.")
input_args = parser.parse_args()

parameters = {"dataset_name": "data",
              "output_file": "ignore_jungfrau.h5"}

if input_args.output_file:
    parameters["output_file"] = input_args.output_file


plugins = [writer_plugins.write_frame_index_to_dataset(input_args.frame_index_dataset)]

start_stream_node(instance_name=input_args.instance_name,
                  processor=HDF5ChunkedWriterProcessor(plugins=plugins),
                  processor_parameters=parameters,
                  connection_address=input_args.connect_address,
                  control_port=input_args.rest_port,
                  receive_raw=input_args.raw)
