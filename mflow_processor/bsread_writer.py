from logging import getLogger
from threading import Event, Thread

from bsread.h5 import process_message
from mflow import mflow

from bsread import dispatcher, writer, SUB
from bsread.handlers import extended
from mflow_nodes.processors.base import BaseProcessor
from mflow_processor.utils.h5_utils import create_folder_if_does_not_exist


BSREAD_START_TIMEOUT = 2


class BsreadWriter(BaseProcessor):
    """
    H5 bsread writer

    Writes the received stream to a HDF5 file.

    Writer commands:
        start                          Starts the writer, overwriting the output file if exists.
        stop                           Stop the writer, compact the dataset and close the file.

    Writer parameters:

        channels                       Channels to request from the dispatching layer.
        output_file                    File to write the stream to.
        receive_timeout                Timeout to use when receiving data from the dispatching layer.
        n_pulses                       How many pulses to collect before stopping the processor.

    """
    _logger = getLogger(__name__)

    def __init__(self, name="bsread writer"):
        """
        Initialize the bsread writer.
            :param name: Name of the writer.
        """
        self.__name__ = name

        # Parameters that need to be set.
        self.channels = None
        self.output_file = None

        # Parameters with default value.
        self.receive_timeout = 200
        self.n_pulses = 0

        self._receiving_thread = None
        self._running_event = Event()

    def _validate_parameters(self):
        """
        Check if all the needed parameters are set.
        :return: ValueError if any parameter is missing.
        """
        error_message = ""

        if not self.output_file and self.channels:
            error_message += "Parameter 'output_file' not set.\n"

        if error_message:
            self._logger.error(error_message)
            raise ValueError(error_message)

    @staticmethod
    def receive_messages(running_event, connect_address, output_file, receive_timeout, n_pulses, start_event):
        try:
            _logger = getLogger("bsread_receive_message")
            _logger.info("Writing channels to output_file '%s'.", output_file)
            _logger.info("Connecting to stream '%s'.", connect_address)

            h5_writer = None

            current_pulse = 0

            handler = extended.Handler()
            receiver = mflow.connect(connect_address, receive_timeout=receive_timeout, mode=SUB)

            h5_writer = writer.Writer()
            h5_writer.open_file(output_file)

            first_iteration = True

            running_event.set()

            while running_event.is_set() and start_event.is_set():

                success = process_message(handler, receiver, h5_writer, first_iteration)

                if success:
                    first_iteration = False
                    current_pulse += 1

                    if current_pulse == n_pulses:
                        running_event.clear()

        except:
            _logger.exception("Error while receiving bsread stream.")

        finally:
            running_event.clear()

            if h5_writer and h5_writer.file:
                h5_writer.close_file()

        _logger.debug("Stopping bsread h5 thread.")

    def is_running(self):
        return self._running_event.is_set()

    def start(self):
        self._logger.debug("Writer started.")
        # Check if all the needed input parameters are available.
        self._validate_parameters()
        self._logger.debug("Starting mflow_processor.")

        if not self.channels:
            self._logger.info("No channels specified. Not writing anything.")
            return

        self._logger.info("Requesting channels from dispatching layer: %s", self.channels)
        address = dispatcher.request_stream(self.channels)

        create_folder_if_does_not_exist(self.output_file)

        self._running_event.clear()

        start_event = Event()
        start_event.set()

        self._receiving_thread = Thread(target=self.receive_messages, args=(self._running_event,
                                                                            address,
                                                                            self.output_file,
                                                                            self.receive_timeout,
                                                                            self.n_pulses,
                                                                            start_event))

        self._receiving_thread.start()

        if not self._running_event.wait(BSREAD_START_TIMEOUT):
            start_event.clear()
            raise ValueError("Cannot start bsread writing process in time.")

    def stop(self):
        self._logger.debug("Writer stopped.")

        self._running_event.clear()

        if self._receiving_thread:
            self._receiving_thread.join()

