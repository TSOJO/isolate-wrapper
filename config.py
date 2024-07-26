"""Store configuration for wrapper."""
from os import environ

# Path to Python.
if environ.get('DEV') == '1':
    PYTHON_PATH = '/usr/bin/python3'
else:
    PYTHON_PATH = environ.get('PYTHON_PATH')

# Path to AQA Assembly Interpreter.
AQAASM_PATH = 'AQA_Assembly_Interpreter/aqaasm.py'

# Compilation flags for C++.
CPP_COMPILE_FLAGS = '-static -std=c++2a -s -O2'

# Maximum number of concurrent sandboxes.
MAX_BOX = 1000

# Folder to store metadata, which will be read to infer verdict.
METADATA_FOLDER = 'metadata'