import subprocess
from .config import PYTHON_PATH, CPP_COMPILE_FLAGS
from .custom_types import Language
import os


class SourceCode:
    def __init__(self, code: str, language: Language, box_path: str=None) -> None:
        self.code = code
        self.language = language
        self.run_args = None

        self._box_path = box_path
        self.file_name = 'code'

    @property
    def box_path(self):
        if self._box_path is None:
            raise Exception('Box path has not yet been set')
        return self._box_path

    @box_path.setter
    def box_path(self, value):
        self._box_path = value

    def compile_if_needed(self):
        if self.run_args is not None:
            if self.run_args == []:
                return 'See error details in the first testcase.'
            return ''
        if self.language == Language.PYTHON:
            code_path = os.path.join(self.box_path, f'{self.file_name}.py')
            subprocess.run(['touch', code_path], check=False)
            subprocess.run(
                ['echo', self.code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
            )
            self.run_args = [PYTHON_PATH, f'{self.file_name}.py']
        elif self.language == Language.CPLUSPLUS:
            code_path = os.path.join(self.box_path, f'{self.file_name}.cpp')
            exe_path = os.path.join(self.box_path, self.file_name)
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
                self.run_args = []
                return error
        return ''

    def run(self, box_id: int, metadata_path: str, time_limit: int, memory_limit: int, input: str):
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
            input=input.encode('utf-8'),
            capture_output=True,
            check=False,
        )
        output = proc.stdout.decode('utf-8')
        error_raw = '\n'.join(proc.stderr.decode('utf-8').split('\n')[:-2])
        if self.language.file_extension == 'py':
            error = error_raw[error_raw.rfind('Traceback (most recent call last):'):]
        else:
            error = ''
        return_code = proc.returncode
        return output, error, return_code
    
    def cast_to_document(self):
        return {
            'code': self.code,
            'language': self.language.name,
        }
    
    @classmethod
    def cast_from_document(cls, document):
        return SourceCode(
            code=document['code'],
            language=Language[document['language']],
        )
