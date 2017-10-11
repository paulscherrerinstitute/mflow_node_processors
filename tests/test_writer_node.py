import os
import unittest
from time import sleep

import h5py

from mflow_nodes.test_tools.m_generate_test_stream import generate_test_array_stream
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor
from tests.helpers import setup_writer, default_output_file, default_dataset_name, \
    default_number_of_frames, default_frame_shape


class TransferTest(unittest.TestCase):

    def test_transfer(self):
        """
        Check if the message pipeline works - from receiving to writing the message down in H5 format.
        """
        receiver_node = setup_writer(processor=HDF5ChunkedWriterProcessor())

        generate_test_array_stream(frame_shape=default_frame_shape, number_of_frames=default_number_of_frames)

        # Wait for the stream to complete transfer.
        sleep(0.5)

        receiver_node.stop()
        # Wait for file to be written to disk.
        sleep(0.5)

        # Collect statistics.
        statistics = receiver_node.get_statistics()

        # Count the total number of received frames.
        self.assertEqual(statistics["messages_received"], default_number_of_frames, "Not all frames were transferred.")

        # Check if the output file was written.
        self.assertTrue(os.path.exists(default_output_file), "Output file does not exist.")
        file = h5py.File(default_output_file, 'r')

        # Check if the dataset groups were correctly constructed.
        self.assertTrue(default_dataset_name in file, "Required dataset not present in output file.")

        # Check if the shrink procedure worked correctly.
        dataset = file[default_dataset_name]


if __name__ == '__main__':
    unittest.main()
