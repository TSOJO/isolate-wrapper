"""Store configuration for wrapper."""
import shutil

# Path to Python, resolved from PATH.
PYTHON_PATH = shutil.which('python3') or shutil.which('python') or 'python3'

# Path to AQA Assembly Interpreter.
AQAASM_PATH = 'AQA_Assembly_Interpreter/aqaasm.py'

# Compilation flags for C++.
CPP_COMPILE_FLAGS = '-static -std=c++2a -s -O2'

# Maximum number of concurrent sandboxes.
MAX_BOX = 1000

# Folder to store metadata, which will be read to infer verdict.
METADATA_FOLDER = 'metadata'