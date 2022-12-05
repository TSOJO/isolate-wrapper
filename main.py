import subprocess
from os import path
import logging
from typing import *

from .config import *
from .verdict import Verdict
from .result import Result
from .testcase import Testcase

class IsolateSandbox:
    def __init__(self) -> None:
        self.create()     

    def create(self):
        # Initialize sandbox and return path.
        # Find next available box.
        logging.info('Creating sandbox...')
        for id in range(0, MAX_BOX):
            proc = subprocess.run(['isolate',
                                '--box-id', f'{id}',
                                '--init'],
                                    capture_output=True)
            if proc.returncode != 0:
                # Box already in use.
                logging.info(f'Box {id} in use. Trying next...')
                continue
            self.box_path = proc.stdout.decode('utf-8')[:-1] + '/box' # usually /var/local/lib/isolate/{box-id}/box
            self.id = id
            logging.info(f'Box {id} available. Created box at {self.box_path}')
            return
        raise Exception('All boxes full')

    def cleanup(self):
        subprocess.run(['isolate',
                        '--box-id', f'{self.id}',
                        '--cleanup'])
        logging.info(f'Cleaned up box {self.id}.')

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
    def run_code(self, code: str, testcases : List[Testcase], restrictions):
        # Return `verdict` given code and test cases.
        logging.info('Begin running code...')
        code_path = path.join(self.box_path, 'code.py')
        
        # Write code to `code.py`.
        subprocess.run(['touch', code_path])
        subprocess.run(['echo', code,], stdout=open(code_path, 'w'))
        
        results = []
        metadata_path = path.join(METADATA_FOLDER, f'{self.id}.txt')
        # TODO: For non-python code, we need to compile it first, return CE if compilation fails.
        # if compilation fails
        #   return Verdict.CE, [Verdict.CE for _ in range(len(testcases))]
        for testcase in testcases:
            proc = subprocess.run(['isolate',
                            '--box-id', f'{self.id}',
                            '-M', metadata_path,
                            '-t', f"{restrictions['time_limit']}",
                            '-w', f"{restrictions['time_limit'] + 1}",
                            '-m', f"{restrictions['memory_limit']}",
                            '--run', PYTHON_PATH, 'code.py'],
                            input=testcase.input.encode('utf-8'),
                            capture_output=True)
            output = proc.stdout.decode('utf-8')
            
            # Judge.
            verdict = Verdict.AC
            metadata = {}
            with open(metadata_path, 'r') as f:
                for line in f.readlines():
                    key, value = line.split(':', maxsplit=1)
                    metadata[key] = value.strip()
                    
            if proc.returncode != 0:
                # TLE, MLE, RE, CE, SE.
                if metadata['status'] == 'RE' or metadata['status'] == 'SG':
                    verdict = Verdict.RE
                elif metadata['status'] == 'TO':
                    verdict = Verdict.TLE
                elif metadata['status'] == 'XX':
                    verdict = Verdict.SE
            else:
                # WA.
                output_lines = output.splitlines()
                answer_lines = testcase.answer.splitlines()
                if len(output_lines) != len(answer_lines):
                    verdict = Verdict.WA
                else:
                    for output_line, answer_line in zip(output_lines, answer_lines):
                        if output_line.rstrip() != answer_line.rstrip():
                            verdict = Verdict.WA
                            break
                    
            result = Result(verdict=verdict,
                            time=round(float(metadata['time']), 3),
                            memory=round(float(metadata['max-rss']) / 1024, 3))
            results.append(result)
        
        logging.info('Finished running.')
        
        final_verdict = None
        # Priority: SE > WA > RE > TLE > AC.
        verdicts = [r.verdict for r in results]
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
        return (final_verdict, results)
