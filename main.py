import subprocess

from constants import *

class IsolateSandbox:
    def __init__(self, id) -> None:
        self.id = id
        self.path = None

    def create(self):
        proc = subprocess.run(["isolate",
                               "--box-id", f"{self.id}",
                               "--init"], capture_output=True)
        self.path = proc.stdout[:-1].decode("utf-8") + "/box"

    def cleanup(self):
        subprocess.run(["isolate",
                        "--box-id", f"{self.id}",
                        "--cleanup"])

    def run_file(self, file_name : str):
        self.create()
        subprocess.run(['cp',
                        file_name,
                        self.path])
        if file_name.endswith(".py"):
            subprocess.run(["isolate",
                            "--box-id", f"{self.id}",
                            "--run", PYTHON_PATH, file_name])
        elif file_name.endswith(".cpp"):
            pass
        self.cleanup()

    def run_code(self, code :str):
        self.create()
        subprocess.run(['touch',
                        self.path + "/code.py"])
        subprocess.run(['echo',
                        code,], stdout=open(self.path + "/code.py", "w"))
        proc = subprocess.run(["isolate",
                        "--box-id", f"{self.id}",
                        "--run", PYTHON_PATH, "code.py"])
        self.cleanup()

if __name__ == '__main__':
    sandbox = IsolateSandbox(0)
    # sandbox.run_file("test.py")
    sandbox.run_code('print("Hello World")')
