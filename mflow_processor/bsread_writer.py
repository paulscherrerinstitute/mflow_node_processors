from logging import getLogger
from threading import Event, Thread
from collections import deque

from mflow import mflow
from bsread import dispatcher, writer, SUB
from bsread.handlers import extended
from mflow_nodes.processors.base import BaseProcessor
from mflow_processor.utils.h5_utils import create_folder_if_does_not_exist

BSREAD_START_TIMEOUT = 2
BUFFER_SIZE = 100


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
        self.start_pulse = None
        self.end_pulse = None

        # Parameters with default value.
        self.receive_timeout = 200
        self.n_pulses = 0

        self._buffer = deque(maxlen=BUFFER_SIZE)

        self._receiving_thread = None
        self._writing_thread = None
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

    def receive_messages(self, running_event, connect_address, receive_timeout, n_pulses, start_event):
        _logger = getLogger("bsread_receive_message")
        _logger.info("Connecting to stream '%s'.", connect_address)

        try:
            current_pulse = 0

            handler = extended.Handler()
            receiver = mflow.connect(connect_address, receive_timeout=receive_timeout, mode=SUB)

            running_event.set()

            while running_event.is_set() and start_event.is_set():

                message_data = receiver.receive(handler=handler.receive)

                # In case you set a receive timeout, the returned message can be None.
                if message_data is None:
                    return False

                # TODO: message_data or message_data.data?
                self._buffer.append(message_data.data)

                current_pulse += 1

                if current_pulse == n_pulses:
                    running_event.clear()

        except:
            _logger.exception("Error while receiving bsread stream.")

        finally:
            running_event.clear()

        _logger.debug("Stopping bsread h5 thread.")

    def write_messages(self):
        _logger = getLogger("bsread_write_message")

        if self.start_pulse:
            start_pulse = self.start_pulse
            n_pulses = self.n_pulses
            self.start_pulse = None
            self.n_pulses = 0

            h5_writer = None
            _logger.info("Writing channels to output_file '%s'.", self.output_file)

            try:
                h5_writer = writer.Writer()
                h5_writer.open_file(self.output_file)

                while True:
                    next_msg = self._buffer.popleft()
                    pulse_id = next_msg['pulse_id']
                    # TODO: save messages to hdf5 file

            except:
                _logger.exception("Error while writing bsread stream.")

            finally:
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

        self._receiving_thread = Thread(target=self.receive_messages,
                                        args=(self._running_event, address, self.receive_timeout,
                                              self.n_pulses, start_event))

        self._writing_thread = Thread(target=self.write_messages)

        self._receiving_thread.start()
        self._writing_thread.start()

        if not self._running_event.wait(BSREAD_START_TIMEOUT):
            start_event.clear()
            raise ValueError("Cannot start bsread writing process in time.")

    def stop(self):
        self._logger.debug("Writer stopped.")

        self._running_event.clear()

        if self._receiving_thread:
            self._receiving_thread.join()

        if self._writing_thread:
            self._writing_thread.join()
