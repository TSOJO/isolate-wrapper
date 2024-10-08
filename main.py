import subprocess
import logging
import os
from typing import List, Tuple, Dict, Generator, Optional

from .config import PYTHON_PATH, MAX_BOX, METADATA_FOLDER
from .constants import COMPILATION_ERROR_RETURN_CODE, NO_OUTPUT_FILE_RETURN_CODE
from .custom_types import Verdict, Result, Testcase
from .source_code import SourceCode


class IsolateSandbox:
    """Sandbox for running code.
    Wraps `isolate` (see https://github.com/ioi/isolate).

    Attributes:
        box_id (int): ID of box.
        box_path (str): Path to box.

    """

    def __init__(self) -> None:
        """Try to initialise by assigning to an available box."""
        os.makedirs(METADATA_FOLDER, exist_ok=True)
        self.ensure_isolate_installed()
        self.create()

    @staticmethod
    def ensure_isolate_installed() -> None:
        """Ensures isolate is installed."""
        try:
            proc = subprocess.run(
                ['isolate', '--version'], capture_output=True, check=True
            )
        except:
            raise Exception('Isolate is not installed.')

    @staticmethod
    def cleanup_all() -> None:
        """Clean up all boxes."""
        for box_id in os.listdir('/var/local/lib/isolate'):
            subprocess.run(
                ['isolate', '--box-id', f'{box_id}', '--cleanup'], check=False
            )

    def create(self):
        """Try assign to an available box.

        Also, initialise class attributes if box found successfully.

        Raises:
            Exception: If no boxes are available.

        """

        logging.info('Creating sandbox...')
        for id_ in range(0, MAX_BOX):
            proc = subprocess.run(
                ['isolate', '--box-id', f'{id_}', '--init'],
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                # Box already in use.
                logging.info('Box %d in use. Trying next...', id_)
                continue

            # Usually /var/local/lib/isolate/{box-id}/box
            self.box_path = proc.stdout.decode('utf-8')[:-1] + '/box'
            self.box_id = id_

            logging.info(
                'Box %d available. Created box at %s', self.box_id, self.box_path
            )
            return

        raise Exception('All boxes full')

    def cleanup(self):
        """Clean up the box.

        Note:
            If this method isn't eventually called (e.g., some error stopped program flow),
            then box will continue to be occupied. Manual cleanup is then needed.

        """
        subprocess.run(
            ['isolate', '--box-id', f'{self.box_id}', '--cleanup'], check=False
        )
        logging.info('Cleaned up box %d.', self.box_id)

    def judge(
        self,
        source_code: SourceCode,
        testcases: List[Testcase],
        time_limit: int,
        memory_limit: int,
        grader_source_code: Optional[SourceCode] = None,
        file_in: Optional[str] = None,
        file_out: Optional[str] = None
    ) -> Generator[Result, None, None]:
        """Judges code and returns verdict.

        Args:
            source_code (SourceCode): The SourceCode object that stores the source code.
            testcases (List[Testcase]): Testcase objects.
            time_limit (int): Time limit in milliseconds.
            memory_limit (int): Memory limit in KB.
            grader_source_code (Optional[SourceCode]): Optional argument that gives the SourceCode object of the grader if used.
            file_in (Optional[str]): The file to write the input to.
            file_out (Optional[str]): The file to read the output from.

        Returns:
            Generator[Result, None, None]: Generator of all Result objects.

        """
        logging.info('Judging code...')
        if grader_source_code is not None:
            grader_source_code.file_name = 'grader'
        
        try:
            for testcase in testcases:
                output, error, metadata, return_code = self.run_code(
                    source_code, testcase.input, time_limit, memory_limit,
                    file_in=file_in, file_out=file_out
                )
                message = ''
                if return_code == COMPILATION_ERROR_RETURN_CODE:
                    verdict = Verdict.CE
                    message = error
                elif return_code == NO_OUTPUT_FILE_RETURN_CODE:
                    verdict = Verdict.NOF
                elif return_code != 0:
                    verdict = IsolateSandbox.decide_RE_verdict(metadata, memory_limit)
                    message = error
                else:
                    if grader_source_code is not None:
                        # ? should grader use the same time limit / memory limit as the code?
                        grader_input = testcase.input + '\n' + output
                        grader_output, grader_error, _, grader_return_code = self.run_code(grader_source_code, grader_input, time_limit, memory_limit)
                        if grader_return_code != 0:
                            verdict = Verdict.SE
                            logging.warn(f'Grader returned non-zero exit code with error: {grader_error}')
                        else:
                            if self.check_output(grader_output, 'AC'):
                                verdict = Verdict.AC
                            elif self.check_output(grader_output, 'WA'):
                                verdict = Verdict.WA
                            else:
                                verdict = Verdict.SE
                                logging.warn(f'Grader returned unexpected output: {grader_output}')
                    else:
                        if not self.check_output(output, testcase.answer):
                            verdict = Verdict.WA
                        else:
                            verdict = Verdict.AC

                result = Result(
                    verdict=verdict,
                    time=int(float(metadata['time']) *
                            1000) if 'time' in metadata else -1,
                    memory=int(metadata['max-rss']
                            ) if 'max-rss' in metadata else -1,
                    message=message
                )
                yield result
        finally:
            # By using `finally`, this code is executed even when the calling loop uses `break`.
            logging.info('Finished judging code.')
            self.cleanup()

    def get_outputs(
        self,
        source_code: SourceCode,
        inputs: List[str],
        time_limit: int,
        memory_limit: int,
        file_in: Optional[str] = None,
        file_out: Optional[str] = None
    ) -> Generator[Tuple[str, Result], None, None]:
        """Gets the outputs of a code given inputs.

        Args:
            source_code (SourceCode): SourceCode object that stores the source code.
            inputs (List[str]): List of inputs.
            time_limit (int): The time limit.
            memory_limit (int): The memory limit.
            file_in (Optional[str]): The file to write the input to.
            file_out (Optional[str]): The file to read the output from.

        Yields:
            Generator[Tuple[str, Result], None, None]: A Generator of tuples of the output and the Result. The Verdict AC means code ran successfully without errors.
        """
        logging.info('Generating outputs...')
        
        try:
            for input in inputs:
                output, error, metadata, return_code = self.run_code(source_code, input, time_limit, memory_limit, file_in=file_in, file_out=file_out)
                message = ''
                if return_code == COMPILATION_ERROR_RETURN_CODE:
                    verdict = Verdict.CE
                    message = error
                elif return_code == NO_OUTPUT_FILE_RETURN_CODE:
                    verdict = Verdict.NOF
                elif return_code != 0:
                    verdict = IsolateSandbox.decide_RE_verdict(metadata, memory_limit)
                    message = error
                else:
                    verdict = Verdict.AC
                result = Result(verdict=verdict,
                                time=int(float(metadata['time']) * 1000) if 'time' in metadata else -1,
                                memory=int(metadata['max-rss']) if 'max-rss' in metadata else -1,
                                message=message)
                yield (output, result)
        finally:
            # By using `finally`, this code is executed even when the calling loop uses `break`.
            logging.info('Finished generating outputs.')
            self.cleanup()

    def run_code(
        self,
        source_code: SourceCode,
        input: str,
        time_limit: int,
        memory_limit: int,
        file_in: Optional[str] = None,
        file_out: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, str], int]:
        """Runs the code and return the output, error, metadata, and return code.

        Args:
            source_code (SourceCode): SoureCode object that stores the source code.
            input (str): The input.
            time_limit (int): The time limit.
            memory_limit (int): The memory limit.
            file_in (Optional[str]): The file to write the input to.
            file_out (Optional[str]): The file to read the output from.

        Returns:
            Tuple[str, str, Dict[str, str], int]: A tuple of (the output, error message, metadata Dict, return code).
        """
        metadata_path = os.path.join(METADATA_FOLDER, f'{self.box_id}.txt')

        source_code.box_path = self.box_path
        compile_message = source_code.prepare_if_needed()
        if compile_message:
            logging.info('Compilation failed.')
            return ('', compile_message, {}, COMPILATION_ERROR_RETURN_CODE)
        
        if file_in is not None:
            with open(os.path.join(self.box_path, file_in), 'w', encoding='utf-8') as f:
                f.write(input)
            input = ''

        output, error, return_code = source_code.run(
            box_id=self.box_id,
            metadata_path=metadata_path,
            time_limit=time_limit,
            memory_limit=memory_limit,
            input=input,
        )

        if file_out is not None:
            try:
                with open(os.path.join(self.box_path, file_out), 'r', encoding='utf-8') as f:
                    output = f.read()
            except FileNotFoundError:
                logging.error(f'User code does not produce output file: {file_out}')
                return ('', '', {}, NO_OUTPUT_FILE_RETURN_CODE)

        if error:
            logging.info(f'User code gave error: {error}')
        metadata = self.read_metadata(metadata_path)
        return (output, error, metadata, return_code)

    def read_metadata(self, metadata_path: str) -> Dict[str, str]:
        """Reads metadata file and returns a dictionary of metadata.

        Args:
            metadata_path (str): Path to metadata file.

        Returns:
            dict[str, str]: Metadata dictionary.

        """
        metadata = {}
        with open(metadata_path, 'r', encoding='utf-8') as metadata_file:
            for line in metadata_file.readlines():
                key, value = line.split(':', maxsplit=1)
                metadata[key] = value.strip()
        return metadata

    @staticmethod
    def check_output(output: str, answer: str) -> bool:
        """Compare `output` and `answer`, and return whether `output` is correct.

        Args:
            output (str): Output from user's code.
            answer (str): Testcase answer.

        Returns:
            bool: True if `output` is correct; False otherwise.

        """
        output_lines = output.splitlines()
        answer_lines = answer.splitlines()
        if len(output_lines) != len(answer_lines):
            return False
        for output_line, answer_line in zip(output_lines, answer_lines):
            if output_line.rstrip() != answer_line.rstrip():
                return False
        return True

    @staticmethod
    def decide_final_verdict(verdicts: List[Verdict]) -> Verdict:
        """Decide overall verdict based on list of verdicts.

        Args:
            verdicts (List[Verdict]): List of verdicts.

        Returns:
            Verdict: Overall verdict.

        """
        verdict_importance_order = [
            Verdict.WJ,
            Verdict.SE,
            Verdict.CE,
            Verdict.NOF,
            Verdict.WA,
            Verdict.RE,
            Verdict.TLE,
            Verdict.MLE,
        ]
        for verdict in verdict_importance_order:
            if verdict in verdicts:
                return verdict
        return Verdict.AC

    @staticmethod
    def decide_RE_verdict(metadata: Dict[str, str], memory_limit: int) -> Verdict:
        """Decide verdict based on metadata and memory limit if the return code is non-zero.

        Args:
            metadata (Dict[str, str]): Metadata.
            memory_limit (int): Memory limit.

        Returns:
            Verdict: Verdict.
        
        """
        if metadata['status'] == 'XX':
            return Verdict.SE
        if metadata['status'] == 'TO':
            return Verdict.TLE
        if metadata['status'] in ('RE', 'SG'):
            if 'max-rss' in metadata and float(metadata['max-rss']) > memory_limit * 0.8:
                return Verdict.MLE
            return Verdict.RE
        if metadata['status'] == 'OK': # This should not happen, since status would not be 'OK' if the return code is non-zero.
            return Verdict.AC
        raise Exception('Unexpected metadata status.')