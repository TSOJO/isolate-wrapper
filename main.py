import subprocess
from os import path

from .config import *

class IsolateSandbox:
    def __init__(self, id) -> None:
        self.id = id

    # Initialize sandbox and return path.
    def create(self):
        proc = subprocess.run(['isolate',
                               '--box-id', f'{self.id}',
                               '--init'],
                               capture_output=True)
        return proc.stdout[:-1].decode('utf-8') + '/box'

    def cleanup(self):
        subprocess.run(['isolate',
                        '--box-id', f'{self.id}',
                        '--cleanup'])

    def run_file(self, file_name: str):
        box_path = self.create()
        subprocess.run(['cp',
                        file_name,
                        box_path])
        if file_name.endswith(".py"):
            subprocess.run(["isolate",
                            "--box-id", f"{self.id}",
                            "--run", PYTHON_PATH, file_name])
        elif file_name.endswith(".cpp"):
            pass
        self.cleanup()

    # Return `verdict` given code and test cases.
    def run_code(self, code: str, testcases):
        box_path = self.create()
        code_path = path.join(box_path, 'code.py')
        
        # Create code file.
        subprocess.run(['touch', code_path])
        subprocess.run(['echo', code], stdout=open(code_path, 'w'))
        
        # Judge.
        correct = 0
        for testcase in testcases:
            # Write input into `/input.txt`.
            subprocess.run(['echo', testcase['input']], stdout=open(box_path + '/input.txt', 'w'))
            
            # Run code, redirect output to `/output.txt`.
            subprocess.run(['isolate',
                            '--box-id', f'{self.id}',
                            '--stdin=input.txt',
                            '--run', PYTHON_PATH, 'code.py'],
                            stdout=open(box_path + '/output.txt', 'w'))
            
            # Compare answer and output.
            with open(box_path + '/output.txt', 'r') as output:
                # TODO: Compare multi-line answers. Maybe separate comparison into another function.
                if output.readline().strip() == testcase['answer']:
                    correct += 1

        self.cleanup()
        return str(correct)


if __name__ == '__main__':
    sandbox = IsolateSandbox(0)
    # sandbox.run_file("test.py")
    sandbox.run_code('print("Hello World")')
