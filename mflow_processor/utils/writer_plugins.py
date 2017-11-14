def write_frame_index_to_dataset(target_dataset):
    """
    Create a separate dataset with the list of frame indexes.
    :param target_dataset: Dataset to store the frame indexes into.
    :return: Function to pass to the writer as a plugin.
    """
    def plugin(writer, message):
        # Append the frame index to the specified dataset.
        writer.h5_datasets.setdefault(target_dataset, []).append(message.get_frame_index())

    return plugin


def write_header_parameter_to_dataset(header_parameter, target_dataset):
    """
    Create a separate dataset with frame indexes for each (upper, lower) part of the image.
    :param header_parameter: Header parameter to write to the target dataset.
    :param target_dataset: Dataset to store the frame indexes into.
    :return: Function to pass to the writer as a plugin.
    """
    def plugin(writer, message):
        # Append the frame index to the specified dataset.
        data = message.get_header()[header_parameter]
        writer.h5_datasets.setdefault(target_dataset, []).append(data)

    return plugin


def write_header_parameters_to_dataset(root_dataset):
    """
    Create a separate dataset with frame indexes for each parameter in the header, beside the
    standard array ones ["shape", "type", "htype"].
    :param root_dataset: group where to write metadata
    :return: Function to pass to the writer as a plugin.
    """
    def plugin(writer, message):
        # Append the frame index to the specified dataset.
        for header_parameter, data in message.get_header().items():
            if header_parameter in ["shape", "type", "htype"]:
                continue
            writer.h5_datasets.setdefault(root_dataset + "/" + header_parameter, []).append(data)

    return plugin
