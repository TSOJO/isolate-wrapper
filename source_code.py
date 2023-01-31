import subprocess
from .config import *
import os


class SourceCode:
    def __init__(self, box_path: str, code: str, language: str) -> None:
        self.code = code
        self.language = language
        self.box_path = box_path

        
    def compile_if_needed(self):
        if self.language == 'py':
            code_path = os.path.join(self.box_path, 'code.py')
            subprocess.run(['touch', code_path], check=False)
            subprocess.run(
                ['echo', self.code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
            )
            self.run_args = [PYTHON_PATH, 'code.py']
        elif self.language == 'cpp':
            code_path = os.path.join(self.box_path, 'code.cpp')
            exe_path = os.path.join(self.box_path, 'code')
            subprocess.run(['touch', code_path], check=False)
            subprocess.run(
                ['echo', self.code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
            )
            compile_proc = subprocess.run(
                ['g++', *CPP_COMPILE_FLAGS.split(), '-o', exe_path, code_path],
                check=False, capture_output=True
            )
            self.run_args = ['./code']
            error = compile_proc.stderr.decode('utf-8')
            if error:
                return error
        else:
            raise ValueError(f'Language {self.language} is not supported.')
        return ''

    def run(self, box_id: int, metadata_path: str, time_limit: int, memory_limit: int, input_: str):
        args = [
            'isolate',
            '--box-id', f'{box_id}',
            '-M', metadata_path,
            '-t', f'{time_limit}',
            '-w', f'{time_limit+1}',
            '-m', f'{memory_limit}',
            '--run', *self.run_args,
        ]
        proc = subprocess.run(
            args,
            input=input_.encode('utf-8'),
            capture_output=True,
            check=False,
        )
        output = proc.stdout.decode('utf-8')
        error_raw = '\n'.join(proc.stderr.decode('utf-8').split('\n')[:-2])
        if self.language == 'py':
            error = error_raw[error_raw.rfind('Traceback (most recent call last):'):]
        else:
            error = ''
        return_code = proc.returncode
        return output, error, return_code
