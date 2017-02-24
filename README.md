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

### Running nodes
The scripts for running the existing nodes are located under the **scripts/** folder. To start a node, execute the 
script with the required parameters (which parameters you need to provide depends on the node type).

The currently available scripts are:

- **Proxy node** (proxy_node.py): Outputs the stream to the console and forwards it to the next node.
- **Compression node** (compression_node.py): Compresses the stream using the bitshuffle LZ4 algorithm.
- **Writer node** (writer_node.py): Writes the stream to a H5 file.
- **NXMX node** (nxmx_node.py): Creates the master H5 file in the NXMX standard and forwards the stream.
- **Jungfrau node** (write_jungfrau_node.py): H5 writer node with an additional plugin for the Jungfrau detector.

The documentation for each node should be located at the end of this document (chapter **Processors documentation**), 
but some help if also available if you run the scripts with the '-h' parameter.

## Run a sample node chain

**WARNING**: Due to a bug in the mflow forward function raw messages cannot be forwarded by the proxy.
Consequently this example will not work.

In order to better illustrate how nodes are supposed to be used, we are going to generate a test mflow stream, output 
its content to the console, compress the stream, output the compressed stream to the console, and finally write it into 
a H5 file.

Once you have installed the library, run the following commands, each in a separate terminal to execute the example:
```bash
# Start a proxy node:
#   - name the node 'proxy'
#   - listen on localhost port 40000
#   - forward the stream to localhost port 40001
#   - start the web interface on port 8080
proxy_node.py proxy tcp://127.0.0.1:40000 tcp://127.0.0.1:40001 --rest_port 8080
```

```bash
# Start a compression node:
#   - name the node 'compress'
#   - listen on localhost port 40001
#   - forward the stream to localhost port 40002
#   - start the web interface on port 8081
compression_node.py compress tcp://127.0.0.1:40001 tcp://127.0.0.1:40002 --rest_port 8081
```

```bash
# Start a proxy node:
#   - name the node 'proxy2'
#   - listen on localhost port 40002
#   - forward the stream to localhost port 40003
#   - start the web interface on port 8082
#   - receive messages in raw format, because the stream is compressed, and it cannot
#     be automatically reinterpreted as an array.
proxy_node.py proxy2 tcp://127.0.0.1:40002 tcp://127.0.0.1:40003 --rest_port 8082 --raw
```
```bash
# Start a writer node:
#   - name the node 'write'
#   - listen on localhost port 40003
#   - save the stream to file sample_output.h5
#   - start the web interface on port 8083
#   - receive message in raw format, because the stream is compressed, and it cannot
#     be automatically reinterpreted as an array.
write_node.py write tcp://127.0.0.1:40003 --output_file sample_output.h5 --rest_port 8083 --raw
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
#   - Send the stream to tcp://127.0.0.1:40000, the first node in the chain.
mflow_generate_test_stream.py tcp://127.0.0.1:40000

# Stop the writer:
curl -X DELETE 0.0.0.0:8083/api/v1/write/
```

Inspect the output of each terminal. The default logging level is DEBUG - what is happening in the nodes should 
be self explanatory.

When you no longer need the nodes terminate them by pressing **CTRL+C** in each terminal.

## Nodes documentation
This chapter is not yet ready.

### Proxy node

### Compression node

### Write node

### Write Jungfrau node

### NXMX node