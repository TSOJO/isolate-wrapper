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
    def run_code(self, code: str, testcases):
        path = self.create()
        subprocess.run(['touch',
                        path + "/code.py"])
        subprocess.run(['echo',
                        code,], stdout=open(path + "/code.py", "w"))
        correct = 0
        for testcase in testcases:
            subprocess.run([
                'echo', f'{testcase["input"]}'
            ], stdout=open(path + "/input.txt", "w"))
            proc = subprocess.run(["isolate",
                            "--box-id", f"{self.id}", "--stdin=input.txt",
                            "--run", PYTHON_PATH, "code.py"], stdout=open(path + '/output.txt', 'w'))
            with open(path + '/output.txt', 'r') as output:
                # TODO: Compare multi-line answers.
                if output.readline().strip() == testcase['answer']:
                    correct += 1

        self.cleanup()
        return str(correct)

if __name__ == '__main__':
    sandbox = IsolateSandbox(0)
    # sandbox.run_file("test.py")
    sandbox.run_code('print("Hello World")')
