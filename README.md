# Python client and module for Lacus

Use this module to interact with a [Lacus](https://github.com/ail-project/lacus) instance.

## Installation

```bash
pip install pylacus
```

## Usage

### Command line

You can use the `pylacus` command:

```bash
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

```

### Library

See [API Reference](https://pylacus.readthedocs.io/en/latest/api_reference.html)
