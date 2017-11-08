import os
import unittest
from time import sleep

import h5py

from mflow_nodes.test_tools.m_generate_test_stream import generate_test_array_stream, generate_frame_data
from mflow_processor.h5_nx_writer import HDF5FormatWriterProcessor
from mflow_processor.utils.schemas.csax_nxsas import csax_nxsas_schema, csax_nxsas_values
from tests.helpers import setup_writer, cleanup_writer, default_output_file, default_dataset_name, \
    default_number_of_frames, default_frame_shape


class TransferTest(unittest.TestCase):
    def setUp(self):
        self.receiver_node = setup_writer(processor=HDF5FormatWriterProcessor(h5_schema=csax_nxsas_schema,
                                                                              h5_values=csax_nxsas_values))

    def tearDown(self):
        cleanup_writer(self.receiver_node)

    def test_transfer(self):
        h5_nx_values = {
            "scan": "test",
            "date": "test",
            "curr": "test",
            "idgap": "test",
            "harmonic": "test",
            "sl0wh": "test",
            "sl0ch": "test",
            "sl1wh": "test",
            "sl1wv": "test",
            "sl1ch": "test",
            "sl1cv": "test",
            "mokev": 1,
            "moth1": "test",
            "temp_mono_cryst_1": "test",
            "temp_mono_cryst_2": "test",
            "mobd": "test",
            "sec": "test",
            "bpm4_saturation_value": "test",
            "bpm4_gain_setting": "test",
            "bpm4s": "test",
            "bpm4x": "test",
            "bpm4y": "test",
            "bpm4z": "test",
            "mith": "test",
            "mirror_coating": "test",
            "mibd": "test",
            "bpm5_gain_setting": "test",
            "bpm5s": "test",
            "bpm5_saturation_value": "test",
            "bpm5x": "test",
            "bpm5y": "test",
            "bpm5z": "test",
            "sl2wh": "test",
            "sl2wv": "test",
            "sl2ch": "test",
            "sl2cv": "test",
            "bpm6_gain_setting": "test",
            "bpm6s": "test",
            "bpm6_saturation_value": "test",
            "bpm6x": "test",
            "bpm6y": "test",
            "bpm6z": "test",
            "sl3wh": "test",
            "sl3wv": "test",
            "sl3ch": "test",
            "sl3cv": "test",
            "fil_comb_description": "test",
            "sl4wh": "test",
            "sl4wv": "test",
            "sl4ch": "test",
            "sl4cv": "test",
            "bs1x": "test",
            "bs1y": "test",
            "bs1_det_dist": "test",
            "bs1_status": "test",
            "bs2x": "test",
            "bs2y": "test",
            "bs2_det_dist": "test",
            "bs2_status": "test",
            "diode": "test",
            "sample_name": "test",
            "sample_description": "test",
            "samx": "test",
            "samy": "test",
            "samz": 1,
            "temp": "test",
            "ftrans": 1
        }

        self.receiver_node.set_parameters({"h5_nx_values": h5_nx_values})

        generate_test_array_stream(frame_shape=default_frame_shape, number_of_frames=default_number_of_frames)

        # Wait for the stream to complete transfer.
        sleep(0.5)
        self.receiver_node.stop()
        # Wait for file to be written to disk.
        sleep(0.5)

        # Collect statistics.
        statistics = self.receiver_node.get_statistics()

        # Count the total number of received frames.
        self.assertEqual(statistics["messages_received"], default_number_of_frames, "Not all frames were transferred.")

        # Check if the output file was written.
        self.assertTrue(os.path.exists(default_output_file), "Output file does not exist.")
        file = h5py.File(default_output_file, 'r')

        # Check if the dataset groups were correctly constructed.
        self.assertTrue(default_dataset_name in file, "Required dataset not present in output file.")

        # Check if the shrink procedure worked correctly.
        dataset = file[default_dataset_name]
        self.assertEqual(dataset.shape, (default_number_of_frames,) + default_frame_shape, "Dataset of incorrect size.")

        # Check if all the frames are correct.
        for frame_number in range(default_number_of_frames):
            self.assertTrue((dataset.value[frame_number] ==
                             generate_frame_data(default_frame_shape, frame_number)).all(),
                            "Dataset data does not match original data for frame %d." % frame_number)

        # TODO: Check if the file format is correct.


if __name__ == '__main__':
    unittest.main()
