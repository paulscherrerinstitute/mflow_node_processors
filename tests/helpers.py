import os

from mflow_nodes.stream_node import get_processor_function, get_receiver_function
from mflow_nodes.node_manager import ExternalProcessWrapper

default_frame_shape = (4, 4)
default_number_of_frames = 16
default_output_file = "ignore_test_output.h5"
default_dataset_name = "entry/dataset/data"


def setup_writer(processor, parameters=None, connect_address="tcp://127.0.0.1:40000"):
    """
    Setup and start the receiver with default values, mainly for testing purposes.
    To be used in the setUp test method.
    :param processor: Processor instance.
    :param parameters: Processor parameters. Defaults (dataset_name, output_file) provided.
    :param connect_address: Connection address. Default "tcp://127.0.0.1:40000".
    :return: instance of ExternalProcessorWrapper.
    """

    # Setup the parameters for the processor.
    process_parameters = {"dataset_name": default_dataset_name,
                          "output_file": default_output_file}
    process_parameters.update(parameters or {})

    receiver_node = ExternalProcessWrapper(processor_function=get_processor_function(processor=processor),
                                           receiver_function=get_receiver_function(connection_address=connect_address,
                                                                                   receive_raw=True),
                                           initial_parameters=process_parameters,
                                           processor_instance=processor)

    receiver_node.start()

    return receiver_node


def cleanup_writer(receiver_node, files_to_cleanup=None):
    """
    Stop the receiver and delete the temporary files.
    To be used in the tearDown test method.
    :param receiver_node: ExternalProcessWrapper to cleanup.
    :param files_to_cleanup: Temporary files to delete (default already provided).
    """
    if receiver_node.is_running():
        receiver_node.stop()

    files_to_cleanup = files_to_cleanup or []
    files_to_cleanup.append(default_output_file)

    for file in files_to_cleanup:
        if os.path.exists(file):
            os.remove(file)
