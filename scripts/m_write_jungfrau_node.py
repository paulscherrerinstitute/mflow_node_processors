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

    parameters["dataset_name"] = input_args.group + "/" + input_args.dataset

    if "compression" in input_args and input_args.compression:
        compression_arguments = compression_data.get(input_args.compression, {})
        parameters.update(compression_arguments)

    if "output_file" in input_args and input_args.output_file:
        parameters["output_file"] = input_args.output_file

    plugins = [writer_plugins.write_header_parameters_to_dataset(input_args.group)]

    start_stream_node_helper(HDF5ChunkedWriterProcessor(plugins=plugins), input_args, parameters)


if __name__ == "__main__":
    parser = ArgumentParser()
    add_default_arguments(parser)
    parser.add_argument("--output_file", type=str, help="Name of output h5 file to write.")
    parser.add_argument("--compression", default=None, choices=['lz4'], help="Incoming stream compression.")
    parser.add_argument("--dataset", type=str, default="data", help="Name of the dataset tot store the frames into.")
    parser.add_argument("--group", type=str, default="jungfrau", help="Name of the group to store "
                                                                                       "the datasets into.")
    arguments = parser.parse_args()

    setup_logging(arguments.log_level)

    run(arguments)
