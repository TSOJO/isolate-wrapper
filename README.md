# isolate-wrapper
Wrapper for ioi-isolate

# Requirements
- `sudo apt update`
Python
- `sudo apt install python3`
C++
- `sudo apt install build-essential gdb`


## Installation
Install [isolate](https://github.com/ioi/isolate):
- In home directory, run `git clone https://github.com/ioi/isolate`
- `cd isolate`
- `sudo apt install libcap-dev`
- `sudo make`
- `sudo make install`
- If you see an error saying a2x is required, you can ignore it, as it is only for the docs
Install python, then update the PYTHON_PATH in config.py
