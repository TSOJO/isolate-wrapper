import subprocess
from os import path
import os

from .config import *
from .verdict import *

class IsolateSandbox:
    def __init__(self) -> None:
        self.create()     

    def create(self):
        # Initialize sandbox and return path.
        # Find next available box.
        for id in range(0, MAX_BOX):
            proc = subprocess.run(['isolate',
                                '--box-id', f'{id}',
                                '--init'],
                                    capture_output=True)
            if proc.returncode != 0:
                # Box already in use.
                continue
            self.box_path = proc.stdout.decode('utf-8')[:-1] + '/box' # usually /var/local/lib/isolate/{box-id}/box
            self.id = id
            return
        raise Exception('All boxes full')

    def cleanup(self):
        subprocess.run(['isolate',
                        '--box-id', f'{self.id}',
                        '--cleanup'])

    # def run_file(self, file_name: str):
    #     box_path = self.create()
    #     subprocess.run(['cp',
    #                     file_name,
    #                     box_path])
    #     if file_name.endswith('.py'):
    #         subprocess.run(['isolate',
    #                         '--box-id', f'{self.id}',
    #                         '--run', PYTHON_PATH, file_name])
    #     elif file_name.endswith('.cpp'):
    #         pass
    #     self.cleanup()

    # TODO: Make code a class, representing different languages.
    def run_code(self, code: str, testcases, restrictions):
        # Return `verdict` given code and test cases.
        code_path = path.join(self.box_path, 'code.py')
        
        # Write code to `code.py`.
        subprocess.run(['touch', code_path])
        subprocess.run(['echo', code,], stdout=open(code_path, 'w'))
        
        verdicts = []
        metadata_path = f'metadata_paths/{self.id}.txt'
        # TODO: For non-python code, we need to compile it first, return CE if compilation fails.
        # if compilation fails
        #   return Verdict.CE, [Verdict.CE for _ in range(len(testcases))]
        for testcase in testcases:
            proc = subprocess.run(['isolate',
                            '--box-id', f'{self.id}',
                            '-M', metadata_path,
                            '-t', f"{restrictions['time_limit']}",
                            '-w', '10',
                            '-m', f"{restrictions['memory_limit']}",
                            '--run', PYTHON_PATH, 'code.py'],
                            input=testcase['input'].encode('utf-8'),
                            capture_output=True)
            
            # Judge.
            verdict: Verdict = None
            if proc.returncode != 0:
                # TLE, MLE, RE, SE.
                metadata = {}
                with open(metadata_path, 'r') as f:
                    for line in f.readlines():
                        key, value = line.split(':', maxsplit=1)
                        metadata[key] = value.strip()
                if metadata['status'] == 'RE':
                    verdict = Verdict.RE
                elif metadata['status'] == 'TO':
                    verdict = Verdict.TLE
                elif metadata['status'] == 'SG' or metadata['status'] == 'XX':
                    verdict = Verdict.SE
            else:
                # AC, WA.
                verdict = Verdict.AC
                output_lines = proc.stdout.decode('utf-8').splitlines()
                answer_lines = testcase['answer'].splitlines()
                if len(output_lines) != len(answer_lines):
                    verdict = Verdict.WA
                else:
                    for output_line, answer_line in zip(output_lines, answer_lines):
                        if output_line.rstrip() != answer_line.rstrip():
                            verdict = Verdict.WA
                            break
                for line in proc.stdout.decode('utf-8').splitlines():
                    if line.rstrip() != testcase['answer'].rstrip():
                        verdict = Verdict.WA
                        break
            verdicts.append(verdict)

        # Determine final verdict.
        final_verdict = None
        # priority: SE > WA > RE > TLE > AC.
        if Verdict.SE in verdicts:
            final_verdict = Verdict.SE
        elif Verdict.WA in verdicts:
            final_verdict = Verdict.WA
        elif Verdict.RE in verdicts:
            final_verdict = Verdict.RE
        elif Verdict.TLE in verdicts:
            final_verdict = Verdict.TLE
        else:
            final_verdict = Verdict.AC
            
        self.cleanup()
        return (final_verdict, verdicts)
