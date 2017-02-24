#!/usr/bin/env python
from setuptools import setup

setup(
    name='mflow_node_processors',
    version="0.0.1",
    description="mflow stream node processors",
    author='Paul Scherrer Institute',
    author_email='andrej.babic@psi.ch',
    requires=["mflow", "h5py", "numpy", "bitshuffle", 'requests'],

    scripts=['scripts/write_node.py',
             'scripts/write_jungfrau_node.py',
             'scripts/proxy_node.py',
             "scripts/compression_node.py",
             "scripts/nxmx_node.py"],

    packages=['mflow_processor',
              'mflow_processor.utils'],

    include_package_data=True
)
