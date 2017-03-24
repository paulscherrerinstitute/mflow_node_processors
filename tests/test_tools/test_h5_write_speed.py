from argparse import ArgumentParser

from mflow import mflow
from mflow.tools import StreamStatisticsPrinter

from mflow_nodes.stream_tools.mflow_message import get_mflow_message
from mflow_nodes.test_tools.m_generate_test_stream import generate_frame_data
from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor


def test_h5_write_speed(output_file, frame_size, n_frames, sampling_interval):
    writer = HDF5ChunkedWriterProcessor()
    writer.dataset_name = "data"
    writer.output_file = output_file

    receiver_statistics = mflow.Statistics()

    # Constructed message will be the same for each frame - do not waste CPU time on this.
    frame_shape = [frame_size, frame_size]
    frame_data = generate_frame_data(frame_shape, 0).tobytes()
    message_data = {'header': {"htype": "raw-1.0",
                               "type": "int32",
                               "shape": frame_shape},
                    'data': [frame_data]}
    message = get_mflow_message(mflow.Message(receiver_statistics, message_data))

    # We have only 1 data block, and we can specify it explicitly to avoid performance overhead.
    message.get_data = lambda: frame_data

    # Writer statistics.
    statistics = StreamStatisticsPrinter(sampling_interval)

    try:
        for i in range(n_frames):
            # Set data for current frame.
            message_data["header"]["frame"] = i
            receiver_statistics.messages_received += 1
            receiver_statistics.total_bytes_received += len(frame_data)

            # Write data to disk.
            writer.process_message(message)

            # Process the statistics.
            statistics.process_statistics(receiver_statistics)

    except KeyboardInterrupt:
        print("Terminated by user.")

    writer.stop()
    statistics.print_summary()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("output_file", type=str, help="Path to the output file.")
    parser.add_argument("--frame_size", type=int, default=2048, help="Number of pixels in each frame dimension.")
    parser.add_argument("--n_frames", type=int, default=100, help="Number of frames to write.")
    parser.add_argument("--sampling_interval", type=float, default=0.2, help="Write sampling interval in seconds."
                                                                             "If zero, each message will be measured "
                                                                             "separately.")
    input_args = parser.parse_args()

    test_h5_write_speed(input_args.output_file,
                        input_args.frame_size,
                        input_args.n_frames,
                        input_args.sampling_interval)
