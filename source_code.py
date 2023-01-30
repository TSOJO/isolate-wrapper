import subprocess
from .config import *
import os

class SourceCode:
    def __init__(self, box_path: str, code: str, language: str) -> None:
        self.code = code
        self.language = language
        self.box_path = box_path

        if self.language == 'py':
            code_path = os.path.join(self.box_path, 'code.py')
            subprocess.run(['touch', code_path], check=False)
            subprocess.run(
                ['echo', self.code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
        )
            self.run_args = [PYTHON_PATH, 'code.py']
        else:
            raise ValueError(f'Language {self.language} is not supported.')

    def run(self, box_id: int, metadata_path : str, time_limit: int, memory_limit: int, input_: str) -> subprocess.CompletedProcess:
        args = [
                    'isolate',
                    '--box-id', f'{box_id}',
                    '-M', metadata_path,
                    '-t', f'{time_limit}',
                    '-w', f'{time_limit+1}',
                    '-m', f'{memory_limit}',
                    '--run',
                ]
        if self.language == 'py':
            args += self.run_args
        else:
            raise ValueError(f'Language {self.language} is not supported.')
        return subprocess.run(
            args,
            input=input_.encode('utf-8'),
            capture_output=True,
            check=False,
        )