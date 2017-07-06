from argparse import ArgumentParser
from bitshuffle.h5 import H5_COMPRESS_LZ4

from mflow_nodes.script_tools.helpers import setup_logging, add_default_arguments, start_stream_node_helper
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor

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

    start_stream_node_helper(HDF5ChunkedWriterProcessor(), input_args, parameters)


if __name__ == "__main__":
    parser = ArgumentParser()
    add_default_arguments(parser)
    parser.add_argument("--output_file", type=str, help="Name of output h5 file to write.")
    parser.add_argument("--compression", default=None, choices=['lz4'], help="Incoming stream compression.")
    arguments = parser.parse_args()

    setup_logging(arguments.log_level)

    run(arguments)
