import os
import unittest
from time import sleep

import h5py
from bitshuffle.h5 import H5_COMPRESS_LZ4, H5FILTER

from mflow_nodes.node_manager import NodeManager
from mflow_nodes.stream_node import get_processor_function, get_receiver_function
from mflow_nodes.test_tools.m_generate_test_stream import generate_test_array_stream, generate_frame_data
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor
from mflow_processor.lz4_compressor import LZ4CompressionProcessor
from tests.helpers import setup_writer, cleanup_writer, default_frame_shape, default_number_of_frames, \
    default_output_file, default_dataset_name

STREAM_CONNECT_ADDRESS = "tcp://127.0.0.1:40000"
WRITER_ADDRESS = "tcp://127.0.0.1:40001"


class CompressionTest(unittest.TestCase):
    def setUp(self):
        self.writer_node = setup_writer(processor=HDF5ChunkedWriterProcessor(),
                                        connect_address=WRITER_ADDRESS,
                                        parameters={"compression": 32008,
                                                    "compression_opts": (2048, H5_COMPRESS_LZ4)})

        # Start the compressor.s
        compressor_procesor = LZ4CompressionProcessor()
        self.compression_node = NodeManager(
            processor_function=get_processor_function(processor=LZ4CompressionProcessor(),
                                                      connection_address=STREAM_CONNECT_ADDRESS),
            receiver_function=get_receiver_function(connection_address=STREAM_CONNECT_ADDRESS),
            processor_instance=compressor_procesor,
            initial_parameters={"binding_address": WRITER_ADDRESS})

        self.compression_node.start()

    def tearDown(self):
        cleanup_writer(self.writer_node)

        if self.compression_node.is_running():
            self.compression_node.stop()

    def test_compression(self):
        # Generate a plain stream and send it to the compression node.
        generate_test_array_stream(binding_address=STREAM_CONNECT_ADDRESS,
                                   frame_shape=default_frame_shape,
                                   number_of_frames=default_number_of_frames)

        # Wait for the stream to complete transfer.
        sleep(0.5)

        self.writer_node.stop()
        # Wait for the file to be written.
        sleep(0.5)

        # Check if the output file was written.
        self.assertTrue(os.path.exists(default_output_file), "Output file does not exist.")
        file = h5py.File(default_output_file, 'r')

        # Check if the compression procedure worked correctly.
        dataset = file[default_dataset_name]
        self.assertEqual(dataset.shape, (default_number_of_frames,) + default_frame_shape, "Dataset of incorrect size.")

        self.assertTrue(str(H5FILTER) in dataset._filters.keys(), "H5 file is not encoded.")

        # Check if all the frames are correct.
        for frame_number in range(default_number_of_frames):
            self.assertTrue((dataset.value[frame_number] ==
                             generate_frame_data(default_frame_shape, frame_number)).all(),
                            "Dataset data does not match original data for frame %d." % frame_number)
