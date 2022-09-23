Welcome to PyLacus's documentation!
=============================================

This is the client API for `Lacus <https://github.com/ail-project/Lacus>`_:

  A capturing system using playwright, as a web service. `


Installation
------------

The package is available on PyPi, so you can install it with::

  pip install pylacus


Usage
-----

You can use `pylacus` as a python script::

    $ pylacus -h
    usage: pylacus [-h] --url-instance URL_INSTANCE [--redis_up] {enqueue,status,result} ...

    Query a Lacus instance.

    positional arguments:
      {enqueue,status,result}
                            Available commands
        enqueue             Enqueue a url for capture
        status              Get status of a capture
        result              Get result of a capture.

    options:
      -h, --help            show this help message and exit
      --url-instance URL_INSTANCE
                            URL of the instance.
      --redis_up            Check if redis is up.


Or as a library:

.. toctree::
   :glob:

   api_reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
