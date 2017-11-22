from logging import getLogger
from threading import Event, Thread

from bsread.h5 import process_message
from mflow import mflow

from bsread import dispatcher, writer
from bsread.handlers import extended
from mflow_nodes.processors.base import BaseProcessor


class BsreadWriter(BaseProcessor):
    """
    H5 chunked writer

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

        # Parameters with default value.
        self.receive_timeout = 200

        self._receiving_thread = None
        self._stop_event = Event()

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
    def receive_messages(stop_event, connect_address, output_file, receive_timeout):
        _logger = getLogger("bsread_receive_message")
        _logger.info("Writing channels to output_file '%s'.", output_file)
        _logger.info("Connecting to stream '%s'.", connect_address)

        h5_writer = None

        try:
            handler = extended.Handler()
            receiver = mflow.connect(connect_address, receive_timeout=receive_timeout)

            h5_writer = writer.Writer()
            h5_writer.open_file(output_file)

            first_iteration = True

            while not stop_event.is_set():

                success = process_message(handler, receiver, h5_writer, first_iteration)

                if success:
                    first_iteration = False

        except:
            _logger.exception("Error while receiving bsread stream.")

        finally:
            if h5_writer:
                h5_writer.close_file()

        _logger.debug("Stopping bsread h5 thread.")

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

        self._stop_event.clear()
        self._receiving_thread = Thread(target=self.receive_messages, args=(self._stop_event,
                                                                            address,
                                                                            self.output_file,
                                                                            self.receive_timeout))
        self._receiving_thread.start()

    def stop(self):
        self._logger.debug("Writer stopped.")

        self._stop_event.set()

        if self._receiving_thread:
            self._receiving_thread.join()

