from argparse import ArgumentParser
from logging import getLogger

from mflow_nodes.processors.proxy import ProxyProcessor
from mflow_nodes.script_tools.helpers import setup_logging, add_default_arguments, start_stream_node_helper

_logger = getLogger("ProxyMessage")


def run(input_args, parameters=None):
    def print_function(message):
        _logger.debug("============= Frame %i =============" % message.get_frame_index())
        _logger.debug(message.get_header())
        _logger.debug(message.get_data())
        _logger.debug("====================================")
        return True

    start_stream_node_helper(ProxyProcessor(proxy_function=print_function), input_args, parameters)

if __name__ == "__main__":
    parser = ArgumentParser()
    add_default_arguments(parser, binding_argument=True)
    arguments = parser.parse_args()

    setup_logging(arguments.log_level)

    run(arguments)
