from logging import getLogger

from mflow_processor.h5_chunked_writer import HDF5ChunkedWriterProcessor


class HDF5FormatWriterProcessor(HDF5ChunkedWriterProcessor):
    """
    H5 format writer

    Writes the received stream to a HDF5 file, taking into account the specified format.

    Writer commands:
        start                          Starts the writer, overwriting the output file if exists.
        stop                           Stop the writer, compact the dataset and close the file.

    Writer parameters:

        dataset_name                   Name of the dataset to write the data inside the H5 file.
        frame_size                     Size of a single frame in pixels.
        dtype                          Data type of the stream.
        output_file                    Location to write the H5 file to.

        compression                    Filter number to be used. None for no compression. None is default.
        compression_opts               Options to pass to the compression filter. None is default.

        h5_group_attributes            Attributes to add to the H5 file groups.
        h5_dataset_attributes          Attributes to add the the H5 datasets.
        h5_datasets                    Datasets to add to the H5 file.

        h5_nx_values                    Values to set in the H5 format.

        h5_dataset_direct_input_values       Mappings of direct value copy from h5_nx_values to the H5 file.
        h5_dataset_calculated_input_values   Mappings of calculated value from h5_nx_values to transfer in the H5 file.
    """
    _logger = getLogger(__name__)

    def __init__(self, name="H5 chunked writer", plugins=None, h5_schema=None, h5_values=None):
        """
        Initialize the chunked writer.
            :param name: Name of the writer.
            :param plugins: Write plugins to use.
            :param h5_schema: Schema specification for the h5 file format.
            :param h5_values: Values to be used in the h5 file format.
        """
        super().__init__(name=name, plugins=plugins)

        self.__name__ = name
        self.h5_group_attributes.update(h5_schema["h5_group_attributes"])
        self.h5_dataset_attributes.update(h5_schema["h5_dataset_attributes"])
        self.h5_datasets.update(h5_values["h5_dataset_fixed_values"])

        # Values mappings from outside.
        self.h5_dataset_input_values = h5_values["h5_dataset_direct_input_values"]
        self.h5_dataset_calculated_input_values = h5_values["h5_dataset_calculated_input_values"]

        self.h5_nx_values = {}

    def prepare_nx_data(self):
            # Process direct value copy datasets.
            for input_name, target_datasets in self.h5_dataset_input_values.items():

                try:

                    if input_name not in self.h5_nx_values:
                        self._logger.warning("h5_nx_values is missing value '%s' for attribute '%s'.",
                                             input_name, target_datasets)
                        # Skip any further processing for this name.
                        continue

                    dataset_value = self.h5_nx_values[input_name]
                    self._logger.debug("Setting value '%s' to dataset '%s'.", dataset_value, target_datasets)

                    # Target datasets can be a string (single target) or a list of strings (multiple targets).
                    if isinstance(target_datasets, list):
                        for dataset_name in target_datasets:
                            self.h5_datasets[dataset_name] = dataset_value
                    else:
                        self.h5_datasets[target_datasets] = dataset_value

                except:
                    self._logger.exception("Cannot get nx data for attribute '%s'.", target_datasets)

            # Process calculated value copy datasets.
            for target_dataset, function_definition in self.h5_dataset_calculated_input_values.items():

                if target_dataset == "/entry/instrument/slit_2/distance":
                    a = 1

                try:

                    input_parameter = function_definition[0]
                    value_function = function_definition[1]

                    if input_parameter not in self.h5_nx_values:
                        self._logger.warning("h5_nx_values is missing input_parameter '%s' for attribute '%s'.",
                                             input_parameter, target_dataset)
                        # Skip any further processing for this name.
                        continue

                    input_value = self.h5_nx_values[input_parameter]
                    self.h5_datasets[target_dataset] = value_function(input_value)

                except:
                    self._logger.exception("Cannot calculate nx data for attribute '%s'.", target_datasets)

    def stop(self):
        self.prepare_nx_data()
        super().stop()
