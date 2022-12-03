import subprocess

from .config import *

class IsolateSandbox:
    def __init__(self, id) -> None:
        self.id = id

    # Initialize sandbox and return path.
    def create(self):
        proc = subprocess.run(["isolate",
                               "--box-id", f"{self.id}",
                               "--init"], capture_output=True)
        return proc.stdout[:-1].decode("utf-8") + "/box"

    def cleanup(self):
        subprocess.run(["isolate",
                        "--box-id", f"{self.id}",
                        "--cleanup"])

    def run_file(self, file_name: str):
        path = self.create()
        subprocess.run(['cp',
                        file_name,
                        path])
        if file_name.endswith(".py"):
            subprocess.run(["isolate",
                            "--box-id", f"{self.id}",
                            "--run", PYTHON_PATH, file_name])
        elif file_name.endswith(".cpp"):
            pass
        self.cleanup()

    # Return `verdict` given code and test cases.
    def run_code(self, code: str):
        path = self.create()
        subprocess.run(['touch',
                        path + "/code.py"])
        subprocess.run(['echo',
                        code,], stdout=open(path + "/code.py", "w"))
        proc = subprocess.run(["isolate",
                        "--box-id", f"{self.id}",
                        "--run", PYTHON_PATH, "code.py"])
        
        self.cleanup()

if __name__ == '__main__':
    sandbox = IsolateSandbox(0)
    # sandbox.run_file("test.py")
    sandbox.run_code('print("Hello World")')
