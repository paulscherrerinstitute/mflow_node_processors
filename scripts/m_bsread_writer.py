from argparse import ArgumentParser

from mflow_nodes.script_tools.helpers import setup_logging, add_default_arguments, start_stream_node_helper
from mflow_processor.bsread_writer import BsreadWriter


def run(input_args, parameters=None):
    parameters = parameters or {}

    start_stream_node_helper(BsreadWriter(), input_args, parameters)


if __name__ == "__main__":
    parser = ArgumentParser()
    add_default_arguments(parser)
    arguments = parser.parse_args()

    setup_logging(arguments.log_level)

    run(arguments)
