import multiprocessing
import time
from logging import getLogger
from mflow import mflow
from .rest_interface import start_web_interface as start_web_interface

_logger = getLogger(__name__)


def start_node(processor, processor_parameters=None, listening_address="tcp://127.0.0.1:40000",
               control_host="0.0.0.0", control_port=8080,
               start_listener=True, receive_raw=False):
    """
    Start the ZMQ processing node.
    :param processor: Stream mflow_processor that does the actual work on the stream data.
    :type processor: StreamProcessor
    :param listening_address: Fully qualified ZMQ stream listening address. Default: "tcp://127.0.0.1:40000"
    :param control_host: Binding host for the control REST API. Default: "0.0.0.0"
    :param control_port: Binding port for the control REST API. Default: 8080
    :param start_listener: If true, the external mflow_processor will be started at node startup.
    :param processor_parameters: List of arguments to pass to the string mflow_processor start command.
    :param receive_raw: Pass the raw ZMQ messages to the mflow_processor.
    :return: None
    """
    _logger.debug("Node set to listen on '%s', with control address '%s:%s'." % (listening_address,
                                                                                 control_host,
                                                                                 control_port))

    # Start the ZMQ listener
    zmq_listener_process = ExternalProcessWrapper(get_zmq_listener(processor=processor,
                                                                   listening_address=listening_address,
                                                                   receive_raw=receive_raw),
                                                  initial_parameters=processor_parameters)

    if start_listener:
        zmq_listener_process.start()

    # Attach web interface
    start_web_interface(external_process=zmq_listener_process, host=control_host, port=control_port,
                        processor_instance=processor)


def get_zmq_listener(processor, listening_address, receive_timeout=1000, queue_size=32, receive_raw=False):
    """
    Generate and return the function for listening to the ZMQ stream and process it in the provider mflow_processor.
    :param processor: Stream mflow_processor to be used in this instance.
    :type processor: StreamProcessor
    :param listening_address: Fully qualified ZMQ stream listening address.
    :param receive_timeout: ZMQ read timeout. Default: 1000.
    :param queue_size: ZMQ queue size. Default: 10.
    :param receive_raw: Return the raw ZMQ message.
    :return: Function to be executed in an external process.
    """
    def zmq_listener(stop_event, statistics, parameter_queue):
        # Setup the ZMQ listener and the stream mflow_processor.
        stream = mflow.connect(address=listening_address,
                               conn_type=mflow.CONNECT,
                               mode=mflow.PULL,
                               receive_timeout=receive_timeout,
                               queue_size=queue_size)

        # Pass all the queued parameters before starting the mflow_processor.
        while not parameter_queue.empty():
            processor.set_parameter(parameter_queue.get())

        processor.start()

        # Setup the receive function according to the raw parameter.
        receive_function = stream.receive_raw if receive_raw else stream.receive

        while not stop_event.is_set():
            message = receive_function()

            # Process only valid messages.
            if message:
                processor.process_message(message)

            # If available, pass parameters to the mflow_processor.
            while not parameter_queue.empty():
                processor.set_parameter(parameter_queue.get())

        # Clean up after yourself.
        stop_event.clear()
        processor.stop()
        stream.disconnect()

    return zmq_listener


class ExternalProcessWrapper(object):
    """
    Wrap the processing function to allow for inter process communication.
    """

    def __init__(self, process_function, initial_parameters):
        """
        Constructor.
        :param process_function: Function to start in a new process.
        :param initial_parameters: Parameters to pass to the function at instantiation.
        """
        self.process_function = process_function
        self.process = None

        self.manager = multiprocessing.Manager()
        self.stop_event = multiprocessing.Event()
        self.statistics = self.manager.Namespace()
        self.parameter_queue = multiprocessing.Queue()

        self.current_parameters = initial_parameters or {}

    def is_running(self):
        """
        Return the status of the process function (running or not).
        :return: True if running, otherwise False.
        """
        return (self.process and self.process.is_alive()) or False

    def start(self):
        """
        Start the processing function in a new process.
        :return: None or Exception if the function is already running.
        """
        _logger.debug("Starting node.")

        if self.is_running():
            raise Exception("External process is already running.")

        self.process = multiprocessing.Process(target=self.process_function,
                                               args=(self.stop_event, self.statistics, self.parameter_queue))

        self._set_current_parameters()
        self.process.start()

    def stop(self):
        """
        Stop the processing function process.
        :return: None or Exception if the function is not running.
        """
        _logger.debug("Stopping node.")
        if not self.process:
            raise Exception("External process is already stopped.")

        self.stop_event.set()
        # Wait maximum of 10 seconds for process to stop
        for i in range(100):
            time.sleep(0.1)
            if not self.process.is_alive():
                break
        # Kill process - no-op in case process already terminated
        self.process.terminate()
        self.process = None

    def wait(self):
        self.process.join()

    def set_parameter(self, parameter):
        """
        Pass a parameter to the processing function. It needs to be in tuple format: (name, value).
        :param parameter: Tuple of (parameter_name, parameter_value).
        :return: None.
        """
        self.current_parameters[parameter[0]] = parameter[1]
        self.parameter_queue.put(parameter)

    def _set_current_parameters(self):
        for parameter in self.current_parameters.items():
            self.set_parameter(parameter)