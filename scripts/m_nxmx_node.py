import json
import logging
import sys
from argparse import ArgumentParser

from mflow_nodes.stream_node import start_stream_node
from mflow_processor.h5_nxmx_writer import HDF5nxmxWriter

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("mflow.mflow").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("ThroughputStatistics").setLevel(logging.ERROR)

parser = ArgumentParser()
parser.add_argument("instance_name", type=str, help="Name of the node instance. Should be unique.")
parser.add_argument("connect_address", type=str, help="Connect address for mflow.\n"
                                                      "Example: tcp://127.0.0.1:40000")
parser.add_argument("writer_binding_address", type=str, help="Binding address for mflow forwarding.\n"
                                                             "Example: tcp://127.0.0.1:40001")
parser.add_argument("writer_control_address", type=str, help="URL of the H5 writer node REST Api.\n"
                                                             "Example: http://127.0.0.1:41001")
parser.add_argument("writer_instance_name", type=str, help="Name of the writer instance name.")
parser.add_argument("--config_file", type=str, help="Config file with the detector properties.")
parser.add_argument("--rest_port", type=int, default=41000, help="Port for web interface.")
input_args = parser.parse_args()

# Read the processor parameters if provided.
parameters = {"filename": "~/tmp/ignore_experiment_master.h5",
              "frames_per_file": 100,
              "h5_datasets": {
                  "/entry/instrument/detector/bit_depth_image": 32,
                  "/entry/instrument/detector/detectorSpecific/compression": "bslz4",
                  "/entry/instrument/detector/detectorSpecific/countrate_correction_count_cutoff": 245916,
                  "/entry/instrument/detector/detectorSpecific/eiger_fw_version": "eiger-1.6.5-224.gitc9fbb9a.release",
                  "/entry/instrument/detector/detectorSpecific/flatfield": [9.999],
                  "/entry/instrument/detector/detectorSpecific/module_bandwidth": 590,
                  "/entry/instrument/detector/detectorSpecific/nsequences": 1,
                  "/entry/instrument/detector/detectorSpecific/pixel_mask": [9999],
                  "/entry/instrument/detector/detectorSpecific/roi_mode": "disabled",
                  "/entry/instrument/detector/detectorSpecific/test_mode": 0}
              }

if input_args.config_file:
    with open(input_args.config_file) as config_file:
        parameters.update(json.load(config_file))

start_stream_node(instance_name=input_args.instance_name,
                  processor=HDF5nxmxWriter(h5_writer_stream_address=input_args.writer_binding_address,
                                           h5_writer_control_address=input_args.writer_control_address,
                                           h5_writer_instance_name=input_args.writer_instance_name),
                  processor_parameters=parameters,
                  connection_address=input_args.connect_address,
                  control_port=input_args.rest_port)
