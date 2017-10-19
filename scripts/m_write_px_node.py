from argparse import ArgumentParser

from bitshuffle.h5 import H5_COMPRESS_LZ4

from mflow_nodes.script_tools.helpers import start_stream_node_helper, setup_logging, add_default_arguments
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor
from mflow_processor.utils import writer_plugins


compression_data = {
    "lz4": {"compression": 32008,
            "compression_opts": (2048, H5_COMPRESS_LZ4)}
}


def run(input_args, parameters=None):
    parameters = parameters or {}

    if "compression" in input_args and input_args.compression:
        compression_arguments = compression_data.get(input_args.compression, {})
        parameters.update(compression_arguments)

    if "output_file" in input_args and input_args.output_file:
        parameters["output_file"] = input_args.output_file

    plugins = [writer_plugins.write_header_parameter_to_dataset("frame", "frame"),
               writer_plugins.write_header_parameter_to_dataset("daq_rec", "daq_rec"),
               writer_plugins.write_header_parameter_to_dataset("is_good_frame", "is_good_frame")]

    start_stream_node_helper(HDF5ChunkedWriterProcessor(plugins=plugins), input_args, parameters)


if __name__ == "__main__":
    parser = ArgumentParser()
    add_default_arguments(parser)
    parser.add_argument("--output_file", type=str, help="Name of output h5 file to write.")
    parser.add_argument("--compression", default=None, choices=['lz4'], help="Incoming stream compression.")
    parser.add_argument("--dataset", type=str, default="data", help="Name of the dataset tot store the frames into.")
    arguments = parser.parse_args()

    setup_logging(arguments.log_level)

    run(arguments, parameters={"dataset_name": arguments.dataset})
