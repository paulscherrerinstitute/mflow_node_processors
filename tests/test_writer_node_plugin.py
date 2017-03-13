import unittest
from time import sleep

import h5py
import numpy as np

from mflow_nodes.test_tools.m_generate_test_stream import generate_test_array_stream
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor
from mflow_processor.utils import writer_plugins
from tests.helpers import setup_writer, cleanup_writer, default_frame_shape, \
    default_number_of_frames, default_output_file

frame_index_dataset_name = "group1/group2/dataset"


class PluginTransferTest(unittest.TestCase):
    def setUp(self):
        plugins = [writer_plugins.write_frame_index_to_dataset(frame_index_dataset_name)]
        self.receiver_node = setup_writer(processor=HDF5ChunkedWriterProcessor(plugins=plugins))

    def tearDown(self):
        cleanup_writer(self.receiver_node)

    def test_plugin(self):
        """
        Test if the plugin functionality of the writer works as expected.
        """
        # Transfer the data and wait a bit for the writer to finish.
        generate_test_array_stream(frame_shape=default_frame_shape, number_of_frames=default_number_of_frames)

        # Wait for the stream to complete transfer.
        sleep(0.5)

        self.receiver_node.stop()
        # Wait for the file to be written.
        sleep(0.5)

        file = h5py.File(default_output_file, 'r')
        frame_index_dataset = file[frame_index_dataset_name]

        # Check if the index dataset contains all frame numbers.
        self.assertTrue((frame_index_dataset.value == np.arange(0, default_number_of_frames)).all(),
                        "Plugin did not populate frame number correctly.")


if __name__ == '__main__':
    unittest.main()
