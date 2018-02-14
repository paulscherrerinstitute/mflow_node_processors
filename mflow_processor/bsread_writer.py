from logging import getLogger
from threading import Event, Thread
from collections import deque

from mflow import mflow
from mflow_nodes.processors.base import BaseProcessor
from mflow_processor.utils.h5_utils import create_folder_if_does_not_exist
from bsread import dispatcher, writer, SUB
from bsread.handlers import compact

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
        self.start_pulse_id = None
        self.end_pulse_id = None

        # Parameters with default value.
        self.receive_timeout = 1000

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

        if not self.output_file:
            error_message += "Parameter 'output_file' not set.\n"

        if not self.channels:
            error_message += "No channels specified.\n"

        if error_message:
            self._logger.error(error_message)
            raise ValueError(error_message)

    def receive_messages(self, connect_address):
        _logger = getLogger("bsread_receive_message")
        _logger.info("Connecting to stream '%s'.", connect_address)

        try:
            handler = compact.Handler()
            receiver = mflow.connect(connect_address, receive_timeout=self.receive_timeout, mode=SUB)

            self._running_event.set()

            while self._running_event.is_set():
                message_data = receiver.receive(handler=handler.receive)

                # In case you set a receive timeout, the returned message can be None.
                if message_data is None:
                    continue

                self._buffer.append(message_data)
                print(message_data.data.pulse_id, len(self._buffer), self.start_pulse_id)
                # launch an hdf5 writing thread upon start_pulse setup
                if self.start_pulse_id:
                    self._writing_thread = Thread(target=self.write_messages, args=(self.start_pulse_id,))
                    self._writing_thread.start()
                    self.start_pulse_id = None

        except:
            _logger.exception("Error while receiving bsread stream.")

        finally:
            self._running_event.clear()

        _logger.debug("Stopping bsread h5 thread.")

    def write_messages(self, start_pulse_id):
        from time import sleep
        _logger = getLogger("bsread_write_message")

        h5_writer = None
        _logger.info("Writing channels to output_file '%s'.", self.output_file)

        try:
            h5_writer = writer.Writer()
            h5_writer.open_file(self.output_file)
            first_iteration = True

            if start_pulse_id < self._buffer[0].data.pulse_id:
                _logger.warning("start_pulse_id < oldest buffered message pulse_id")

            while self._running_event.is_set():
                if len(self._buffer) == 0:
                    continue  # wait for more messages being buffered

                # process the oldest buffered message
                next_msg = self._buffer.popleft()
                msg_pulse_id = next_msg.data.pulse_id

                if self.end_pulse_id and self.end_pulse_id < msg_pulse_id:
                    # no more messages to write
                    end_pulse_id = self.end_pulse_id
                    self.end_pulse_id = None

                    # finilize hdf5 file
                    if end_pulse_id < msg_pulse_id:
                        # TODO: prune data on disk
                        print('prunning from', msg_pulse_id, 'to', end_pulse_id)

                    break

                if msg_pulse_id < start_pulse_id:
                    print('discarding', msg_pulse_id)
                    continue  # discard the message

                # TODO: save messages to hdf5 file
                first_iteration = False
                print('processing', msg_pulse_id, start_pulse_id)
                sleep(0.01)

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

        self._logger.info("Requesting channels from dispatching layer: %s", self.channels)
        address = dispatcher.request_stream(self.channels)

        create_folder_if_does_not_exist(self.output_file)

        self._running_event.clear()

        self._receiving_thread = Thread(target=self.receive_messages, args=(address, ))
        self._receiving_thread.start()

        if not self._running_event.wait(BSREAD_START_TIMEOUT):
            raise ValueError("Cannot start bsread writing process in time.")

    def stop(self):
        self._logger.debug("Writer stopped.")

        self._running_event.clear()

        if self._receiving_thread:
            self._receiving_thread.join()

        if self._writing_thread:
            self._writing_thread.join()
