# mflow node processors
An mflow node processor is a standalone processes that receive, process, and maybe forward an mflow stream.
To accomplish this it uses the **mflow_nodes** library, which provides a set of tools to easily develop, control, 
and test processors.

## Conda setup
If you use conda, you can create an environment with the mflow_nodes library by running:

```bash
conda create -c paulscherrerinstitute --name <env_name> mflow_node_processors
```

After that you can just source you newly created environment and start using the library.

## Local build
You can build the library by running the setup script in the root folder of the project:

```bash
python setup.py install
```

or by using the conda also from the root folder of the project:

```bash
conda build conda-recipe
conda install --use-local mflow_node_processors
```

### Requirements
The library relies on the following packages:

- numpy
- hdf5 ==1.8.17
- h5py >=2.7.*
- bitshuffle ==0.2.4
- mflow_nodes >=0.0.3

In case you are using conda to install the packages, you might need to add the **paulscherrerinstitute** channel to 
your conda config:

```
conda config --add channels paulscherrerinstitute
```

If you do not want to install the packages manually you can use the **conda-recipe/conda_env.txt** file to create 
the conda environment with the packages used for developemnt:

```bash
conda create --name <env> --file conda-recipe/conda_env.txt
```

## Web interface
Each node starts a web interface on **0.0.0.0** using the port provided at the node startup (default port is **8080**).
Navigate your browser to **0.0.0.0:8080** (or corresponding port) to view the interface.

For more information on how to interact with the web interface check the **mflow_nodes** documentation.

## Using existing nodes
There are already several processors and the scripts to run them in this library. All the 
running scripts should be automatically added to your path, so you should be able to run 
them from anywhere.

All mflow related executables start with the prefix **m\_** so you can use the autocomplete functionality in bash 
(by writing in the console "m_" and pressing TAB) to discover the available scripts.

### Running nodes
The scripts for running the existing nodes are located under the **scripts/** folder. To start a node, execute the 
script with the required parameters (which parameters you need to provide depends on the node type).

The currently available scripts are:

- **Proxy node** (m_proxy_node.py): Outputs the stream to the console and forwards it to the next node.
- **Compression node** (m_compression_node.py): Compresses the stream using the bitshuffle LZ4 algorithm.
- **Writer node** (m_writer_node.py): Writes the stream to a H5 file.
- **NXMX node** (m_nxmx_node.py): Creates the master H5 file in the NXMX standard and forwards the stream.
- **Jungfrau node** (m_write_jungfrau_node.py): H5 writer node with an additional plugin for the Jungfrau detector.

The documentation for each node should be located at the end of this document (chapter **Processors documentation**), 
but some help if also available if you run the scripts with the '-h' parameter.

## Run a sample node chain

In order to better illustrate how nodes are supposed to be used, we are going to generate a test mflow stream, output 
its content to the console, compress the stream, output the compressed stream to the console, and finally write it into 
a H5 file.

Once you have installed the library, run the following commands, each in a separate terminal to execute the example:
```bash
# Start a proxy node:
#   - name the node 'proxy'
#   - connect to localhost port 40000
#   - bind the stream to localhost port 40001
#   - start the web interface on port 8080
m_proxy_node.py proxy tcp://127.0.0.1:40000 tcp://127.0.0.1:40001 --rest_port 8080
```

```bash
# Start a compression node:
#   - name the node 'compress'
#   - connect to localhost port 40001
#   - forward the stream to localhost port 40002
#   - start the web interface on port 8081
m_compression_node.py compress tcp://127.0.0.1:40001 tcp://127.0.0.1:40002 --rest_port 8081
```

```bash
# Start a proxy node:
#   - name the node 'proxy2'
#   - connect to localhost port 40002
#   - bind the stream to localhost port 40003
#   - start the web interface on port 8082
#   - receive messages in raw format, because the stream is compressed, and it cannot
#     be automatically reinterpreted as an array.
m_proxy_node.py proxy2 tcp://127.0.0.1:40002 tcp://127.0.0.1:40003 --rest_port 8082 --raw
```
```bash
# Start a writer node:
#   - name the node 'write'
#   - connect to localhost port 40003
#   - save the stream to file sample_output.h5
#   - start the web interface on port 8083
#   - receive message in raw format, because the stream is compressed, and it cannot
#     be automatically reinterpreted as an array.
m_write_node.py write tcp://127.0.0.1:40003 --output_file sample_output.h5 --rest_port 8083 --raw
```

Once you node chain is ready, you have to start each node and generate the test stream in yet another terminal. 
At the end close down the writer node (this will close the file handle) and try to get the statistics for this 
example from the compressor and the writer.

```bash
# Note: When calling the REST api you need to provide the instance name (the last part of the URL).

# Start the proxy:
curl -X PUT 0.0.0.0:8080/api/v1/proxy/

# Start the compressor:
curl -X PUT 0.0.0.0:8081/api/v1/compress/

# Start the other proxy:
curl -X PUT 0.0.0.0:8082/api/v1/proxy2/

# Start the writer:
curl -X PUT 0.0.0.0:8083/api/v1/write/

# Generate the test stream:
#   - Send the stream from tcp://127.0.0.1:40000, the first node in the chain.
m_generate_test_stream.py tcp://127.0.0.1:40000

# Stop the writer:
curl -X DELETE 0.0.0.0:8083/api/v1/write/
```

Inspect the output of each terminal. The default logging level is DEBUG - what is happening in the nodes should 
be self explanatory.

When you no longer need the nodes terminate them by pressing **CTRL+C** in each terminal.

## Nodes documentation
This are the nodes that come with the mflow_node_processors module. To develop your own nodes, you can see 
the implementations of the following ones for reference. They should cover most of basic scenarios. The 
nodes provided below are more of less general purpose and with some configuration can be adopet for many uses.

### Proxy node
class: **mflow\_nodes.processors.proxy.ProxyProcessor**

The proxy node allows for some processing to be done on the live stream, and than forward the stream to the next 
node without modifying it. The only was the proxy node can manipulate the stream is to decide with messages 
will continue to the next node (it is useful for online stream analysis and message filtering).

```bash
usage: m_proxy_node.py [-h] [--rest_port REST_PORT] [--raw]
                       instance_name connect_address binding_address

positional arguments:
  instance_name         Name of the node instance. Should be unique.
  connect_address       Connect address for mflow. Example:
                        tcp://127.0.0.1:40000
  binding_address       Binding address for mflow forwarding. Example:
                        tcp://127.0.0.1:40001

optional arguments:
  -h, --help            show this help message and exit
  --rest_port REST_PORT
                        Port for web interface.
  --raw                 Receive the mflow messages in raw mode.

```

#### Parameters

- **binding\_address**: Address to bind the forwarded stream to.

### Compression node
class: **mflow_processor.lz4_\compressor.LZ4CompressionProcessor**

The compression node takes an mflow stream, it compresses it with LZ4 Bitshuffle and forwards it to the next node.

```bash
usage: m_compression_node.py [-h] [--rest_port REST_PORT]
                             [--block_size BLOCK_SIZE]
                             instance_name connect_address binding_address

positional arguments:
  instance_name         Name of the node instance. Should be unique.
  connect_address       Connect address for mflow. Example:
                        tcp://127.0.0.1:40000
  binding_address       Binding address for mflow forwarding. Example:
                        tcp://127.0.0.1:40001

optional arguments:
  -h, --help            show this help message and exit
  --rest_port REST_PORT
                        Port for web interface.
  --block_size BLOCK_SIZE
                        LZ4 block size.
```

#### Parameters

- **binding\_address**: Address to bind the forwarded stream to.
- **block\_size**: Size of the block for LZ4 Bitshuffle compression (Default: 2048)

### Write node
class: **mflow_processor.h5_chunked_writer.HDF5ChunkedWriterProcessor**

The write node can write the provided stream to a H5 file. It can write all images in a single file, or use 
file roll over on a defined number of frames (for example 100 frames / file).

```bash
usage: m_write_node.py [-h] [--output_file OUTPUT_FILE]
                       [--rest_port REST_PORT] [--raw] [--compression {lz4}]
                       instance_name connect_address

positional arguments:
  instance_name         Name of the node instance. Should be unique.
  connect_address       Connect address for mflow. Example:
                        tcp://127.0.0.1:40000

optional arguments:
  -h, --help            show this help message and exit
  --output_file OUTPUT_FILE
                        Name of output h5 file to write.
  --rest_port REST_PORT
                        Port for web interface.
  --raw                 Receive the mflow messages in raw mode.
  --compression {lz4}   Incoming stream compression.
```

#### Parameters

- **output\_file**: Path to the output file to write. It can be a string template, but only if _frames\_per\_file_ 
is set.
- **dataset\_name**: Name of the dataset to write the data to.
- **frames\_per\_file**: Number of frames to write to a file. After the number has been reached, a new file is created. 
Use _None_ or _0_ to disable file roll over (Default: None).
- **compression**: H5 compression plugin value.
- **compression\_opts**: Compression options to pass to H5 library.
- **h5\_group\_attributes**: Attributes to set to H5 groups (used mainly for NXMX compliance).
- **h5\_dataset\_attributes**: Attributes to set to h5 datasets (used mainly for NXMX compliance).
- **h5\_datasets**: Additional datasets (apart from the data one) to set in the output H5 file.

### Write Jungfrau node
class: **mflow_processor.h5_chunked_writer.HDF5ChunkedWriterProcessor**

This node is a special case of the standard writer. In addition to the standard dataset written by the default writer, 
it provides an additional dataset with all the frame indexes. This is done via the plugin capability of the writer.

```bash
usage: m_write_jungfrau_node.py [-h] [--output_file OUTPUT_FILE]
                                [--rest_port REST_PORT]
                                [--frame_index_dataset FRAME_INDEX_DATASET]
                                instance_name connect_address

positional arguments:
  instance_name         Name of the node instance. Should be unique.
  connect_address       Connect address for mflow. Example:
                        tcp://127.0.0.1:40000

optional arguments:
  -h, --help            show this help message and exit
  --output_file OUTPUT_FILE
                        Name of output h5 file to write.
  --rest_port REST_PORT
                        Port for web interface.
  --frame_index_dataset FRAME_INDEX_DATASET
                        Name of the dataset to store the frame indexes into.
```

#### Parameters
Since it uses the same class, see **Write node** documentation for details.
 
### NXMX node
class: **mflow_processor.h5_nxmx_writer.HDF5nxmxWriter**

The NXMX node is basically a proxy node, that prepares the NXMX standard master file, while passing the stream on 
for a writer node to write the data files.

```bash
usage: m_nxmx_node.py [-h] [--config_file CONFIG_FILE] [--rest_port REST_PORT]
                      instance_name connect_address writer_binding_address
                      writer_control_address writer_instance_name

positional arguments:
  instance_name         Name of the node instance. Should be unique.
  connect_address       Connect address for mflow. Example:
                        tcp://127.0.0.1:40000
  writer_binding_address
                        Binding address for mflow forwarding. Example:
                        tcp://127.0.0.1:40001
  writer_control_address
                        URL of the H5 writer node REST Api. Example:
                        http://127.0.0.1:41001
  writer_instance_name  Name of the writer instance name.

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        Config file with the detector properties.
  --rest_port REST_PORT
                        Port for web interface.
```

#### Parameters
- **filename**: Path to the output master file to write. It must be in standard NXMX format: 
**<experiment_name>\_master.h5**
- **frames\_per\_file**: Number of frames to write to a data file.
- **h5\_group\_attributes**: Attributes to set to H5 groups.
- **h5\_dataset\_attributes**: Attributes to set to h5 datasets.
- **h5\_datasets**: Additional datasets (apart from the data one) to set in the output H5 file.

The H5 datasets are extrapolated from the stream produced by the detector, the H5 group and dataset 
attributes are passed as part of the config (--config_file argument).