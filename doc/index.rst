.. VOPaaS documentation master file, created by
   sphinx-quickstart on Mon Nov  2 08:36:02 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to VOPaaS's documentation!
==================================

Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Generate metadata
-----------------

Use the script **make_vopaas_metadata.py** to generate frontend metadata for the VOPaaS proxy.
The script takes the proxy config file as parameter. The script will generate one metadata file for each target OP/IDP.

Example::

   python3 make_vopaas_metadata.py proxy_config.yaml

