"""Store configuration for wrapper."""
from os import environ
from .custom_types import Language

# Path to Python.
if environ.get('DEV') == '1':
    PYTHON_PATH = '/usr/bin/python3'
else:
    PYTHON_PATH = environ.get('PYTHON_PATH')

CPP_COMPILE_FLAGS = '-static -std=c++2a -s -O2'

# Maximum number of concurrent sandboxes.
MAX_BOX = 1000

# Folder to store metadata, which will be read to infer verdict.
METADATA_FOLDER = 'metadata'

SUPPORTED_LANGUAGES = {
    'cpp': Language(
        file_extension='cpp',
        ace_mode='c_cpp',
    ),
    'py': Language(
        file_extension='py',
        ace_mode='python',
    ),
}
