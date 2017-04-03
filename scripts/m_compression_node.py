from argparse import ArgumentParser

from mflow_nodes.script_tools.helpers import add_default_arguments, setup_console_logging, start_stream_node_helper
from mflow_processor.lz4_compressor import LZ4CompressionProcessor


def run(input_args, parameters=None):
    start_stream_node_helper(LZ4CompressionProcessor(), input_args, parameters)


if __name__ == "__main__":
    setup_console_logging()

    parser = ArgumentParser()
    add_default_arguments(parser, binding_argument=True)
    parser.add_argument("--block_size", type=int, default=2048, help="LZ4 block size.")

    run(parser.parse_args())
