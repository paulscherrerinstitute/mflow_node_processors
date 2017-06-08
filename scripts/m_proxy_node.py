from argparse import ArgumentParser

from mflow_nodes.processors.proxy import ProxyProcessor
from mflow_nodes.script_tools.helpers import setup_logging, add_default_arguments, start_stream_node_helper


def run(input_args, parameters=None):
    def print_function(message):
        print("============= Frame %i =============" % message.get_frame_index())
        print(message.get_header())
        print(message.get_data())
        print("====================================")
        return True

    start_stream_node_helper(ProxyProcessor(proxy_function=print_function), input_args, parameters)

if __name__ == "__main__":
    parser = ArgumentParser()
    add_default_arguments(parser, binding_argument=True)
    arguments = parser.parse_args()

    setup_logging(arguments.log_config_file)

    run(arguments)
