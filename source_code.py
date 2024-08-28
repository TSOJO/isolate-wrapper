import subprocess
import os
from typing import Optional, List, Tuple

from .config import PYTHON_PATH, CPP_COMPILE_FLAGS, AQAASM_PATH
from .custom_types import Language


class SourceCode:
    """SourceCode object for storing, compiling, and running source code.
    """
    def __init__(self,
                 code: str,
                 language: Language,
                 box_path: Optional[str] = None,
                 aqaasm_inputs: Optional[List[str]] = None,
                 aqaasm_outputs: Optional[List[str]] = None,
                 python_ignore_prompts: bool = False) -> None:
        """Initialises a SourceCode object.

        Args:
            code (str): The raw code.
            language (Language): The Language,
            box_path (Optional[str], optional): Path to its sandbox. Defaults to None.
            aqaasm_inputs (Optional[List[str]], optional): Memory address locations for the inputs for when Language is AQAASM. Defaults to None.
            aqaasm_outputs (Optional[List[str]], optional): Memory address locations for the outputs for when Language is AQAASM. Defaults to None.
        """
        self.code = code
        self.language = language
        self.run_args = None
        self.aqaasm_inputs = [] if aqaasm_inputs is None else aqaasm_inputs
        self.aqaasm_outputs = [] if aqaasm_outputs is None else aqaasm_outputs
        self.python_ignore_prompts = python_ignore_prompts

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

    def prepare_if_needed(self) -> str:
        """Prepares the source code before running, if not already prepared.

        Returns:
            str: The error message is compilation failed; Otherwise an empty string is returned.
        """

        if self.run_args is not None: # This means the source code is already prepared in the box.
            if self.run_args == []: # This means compilation has failed (for compiled languages only) in the first testcase.
                # Directly return the following error message.
                return 'See error details in the first testcase.'
            # Otherwise, do nothing.
            return ''
        if self.language == Language.PYTHON:
            if self.python_ignore_prompts:
                self.code = 'TOPYC_INPUT = input; input = lambda _=0: TOPYC_INPUT()\n' + self.code
            # Create code file inside the box.
            code_path = os.path.join(self.box_path, f'{self.file_name}.py')
            subprocess.run(['touch', code_path], check=False)
            subprocess.run(
                ['echo', self.code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
            )
            self.run_args = [PYTHON_PATH, f'{self.file_name}.py']
        elif self.language == Language.CPLUSPLUS:
            # Create code file inside the box.
            code_path = os.path.join(self.box_path, f'{self.file_name}.cpp')
            exe_path = os.path.join(self.box_path, self.file_name)
            subprocess.run(['touch', code_path], check=False)
            subprocess.run(
                ['echo', self.code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
            )
            # Compile the code using g++ inside the box.
            compile_proc = subprocess.run(
                ['g++', *CPP_COMPILE_FLAGS.split(), '-o', exe_path, code_path],
                check=False, capture_output=True
            )
            self.run_args = [self.file_name]
            error = compile_proc.stderr.decode('utf-8')
            if error:
                self.run_args = []
                return error
        elif self.language == Language.AQAASM:
            # Create code and interpreter files inside the box.
            code_path = os.path.join(self.box_path, f'{self.file_name}.aqaasm')
            interpreter_path = os.path.join(self.box_path, 'aqaasm.py')
            subprocess.run(['touch', code_path], check=False)
            subprocess.run(
                ['echo', self.code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
            )
            subprocess.run(['touch', interpreter_path], check=False)
            subprocess.run(
                ['echo', open(AQAASM_PATH, 'r', encoding='utf-8').read()],
                stdout=open(interpreter_path, 'w', encoding='utf-8'),
                check=False
            )
            self.run_args = [PYTHON_PATH, 'aqaasm.py',
                             f'{self.file_name}.aqaasm',
                             '-i', *self.aqaasm_inputs,
                             '-o', *self.aqaasm_outputs]
        return ''

    def run(self, box_id: int, metadata_path: str, time_limit: int, memory_limit: int, input: str) -> Tuple[str, str, int]:
        """Runs the source code.

        Args:
            box_id (int): The box id to use.
            metadata_path (str): The path to metadata.
            time_limit (int): The time limit.
            memory_limit (int): The memory limit.
            input (str): The input.

        Returns:
            Tuple[str, str, int]: A tuple of (the output, error message, return code)
        """
        time_limit //= 1000 # Convert milliseconds to seconds.
        args = [
            'isolate',
            '--box-id', f'{box_id}',
            '-M', metadata_path,
            '-t', f'{time_limit}',
            '-w', f'{time_limit+1}',
            '-m', f'{memory_limit}',
            '--run', '--', *self.run_args,
        ]
        proc = subprocess.run(
            args,
            input=input.encode('utf-8'),
            capture_output=True,
            check=False,
        )
        output = proc.stdout.decode('utf-8')
        error_raw = '\n'.join(proc.stderr.decode('utf-8').split('\n')[:-2])
        if self.language == Language.PYTHON:
            error_start = error_raw.find('Traceback (most recent call last):')
            error = error_raw[error_start:] if error_start != -1 else error_raw
        elif self.language == Language.AQAASM:
            try:
                line_num = int(error_raw.split()[-1])
            except:
                error = error_raw
            else:
                newl = '\n'
                error = (
                    f'{error_raw[(error_raw.rfind("Exception: ")+11):]}\n'
                    f'  Line {line_num}:\n'
                    f'    {self.code.split(newl)[line_num-1]}'
                )
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
