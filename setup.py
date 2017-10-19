#!/usr/bin/env python
from setuptools import setup

setup(
    name='mflow_node_processors',
    version="1.2.6",
    description="mflow stream node processors",
    author='Paul Scherrer Institute',
    author_email='andrej.babic@psi.ch',
    requires=["mflow_nodes", "h5py", "numpy", "bitshuffle"],

    scripts=['scripts/m_write_node.py',
             'scripts/m_write_jungfrau_node.py',
             'scripts/m_write_csax_nxsas_node.py',
             'scripts/m_write_px_node.py',
             'scripts/m_proxy_node.py',
             "scripts/m_compression_node.py",
             "scripts/m_nxmx_node.py",
             "scripts/m_dummy_writer.py"],

    package_dir={"mflow_processor.scripts": 'scripts'},

    packages=['mflow_processor',
              'mflow_processor.utils',
              'mflow_processor.scripts'],

    include_package_data=True
)
