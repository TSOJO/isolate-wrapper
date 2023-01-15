import subprocess
import logging
import os
from typing import List, Tuple, Dict, Generator

from .config import PYTHON_PATH, MAX_BOX, METADATA_FOLDER
from .custom_types import Verdict, Result, Testcase


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

    def ensure_isolate_installed(self) -> None:
        """Ensures isolate is installed."""
        try:
            proc = subprocess.run(
                ['isolate', '--version'], capture_output=True, check=True
            )
        except:
            raise Exception('Isolate is not installed.')

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

    # TODO: Make code a class, representing different languages.
    # TODO: Fix docstring
    def judge(
        self,
        code: str,
        testcases: List[Testcase],
        time_limit: int,
        memory_limit: int,
    ) -> Tuple[Verdict, List[Result]]:
        """Judges code and returns verdict.

        Args:
            code (str): Source code.
            testcases (List[Testcase]): Testcase objects.
            time_limit (int): Time limit in milliseconds.
            memory_limit (int): Memory limit in KB.

        Returns:
            tuple[Verdict, List[Result]]: Tuple of final verdict and results.

        """
        results: List[Result] = []

        for (output, metadata, return_code, testcase) in self.run_code(
            code, testcases, time_limit, memory_limit
        ):
            if return_code != 0:
                # TLE, RE, CE, SE.
                if metadata['status'] in ('RE', 'SG'):
                    verdict = Verdict.RE
                    if 'max-rss' in metadata:
                        if float(metadata['max-rss']) > memory_limit * 0.8:
                            verdict = Verdict.MLE
                elif metadata['status'] == 'TO':
                    verdict = Verdict.TLE
                elif metadata['status'] == 'XX':
                    verdict = Verdict.SE
                else:
                    # This following code should be unreachable.
                    raise Exception('Unexpected metadata status.')
            else:
                # WA, AC.
                if not self.check_output(output, testcase.answer):
                    verdict = Verdict.WA
                else:
                    verdict = Verdict.AC

            result = Result(
                verdict=verdict,
                time=int(float(metadata['time']) * 1000),
                memory=int(metadata['max-rss']),
            )
            results.append(result)

            yield result

        # verdicts = [r.verdict for r in results]
        # final_verdict = self.decide_final_verdict(verdicts)

        self.cleanup()
        # return (final_verdict, results)

    def generate_answer(
        self,
        code: str,
        input: str,
        time_limit: int,
        memory_limit: int,
    ) -> Tuple[str, Verdict]:
        testcase = Testcase(input, '')
        for (output, metadata, return_code, testcase) in self.run_code(
            code, [testcase], time_limit, memory_limit
        ):

            if return_code != 0:
                # TLE, RE, SE.
                if metadata['status'] in ('RE', 'SG'):
                    verdict = Verdict.RE
                elif metadata['status'] == 'TO':
                    verdict = Verdict.TLE
                elif metadata['status'] == 'XX':
                    verdict = Verdict.SE
                else:
                    raise Exception('Unexpected metadata status.')
            else:
                # Faithfully executed code.
                testcase.answer = output
                verdict = Verdict.AC

        logging.info('Finished generating output.')
        self.cleanup()
        return (testcase.answer, verdict)

    # def generate_answers(
    #     self,
    #     code: str,
    #     testcases: List[Testcase],
    #     time_limit: int,
    #     memory_limit: int,
    # ) -> Tuple[Verdict, List[Testcase]]:
    #     # ! Maybe redundant...
    #     """Runs code, then set the answer of each testcase to the output.

    #     Returned verdict will be AC if code has run successfully.

    #     Args:
    #         code (str): Source code.
    #         testcases (List[Testcase]): Testcase objects.
    #         time_limit (int): Time limit in milliseconds.
    #         memory_limit (int): Memory limit in KB.

    #     Returns:
    #         Tuple[Verdict, List[Testcase]]: (Final verdict, modified testcases)

    #     """
    #     verdicts = []

    #     for (output, metadata, return_code, testcase) \
    #         in self.run_code(code, testcases, time_limit, memory_limit):

    #         if return_code != 0:
    #             # TLE, RE, SE.
    #             if metadata['status'] in ('RE', 'SG'):
    #                 verdict = Verdict.RE
    #             elif metadata['status'] == 'TO':
    #                 verdict = Verdict.TLE
    #             elif metadata['status'] == 'XX':
    #                 verdict = Verdict.SE
    #             else:
    #                 raise Exception('Unexpected metadata status.')
    #         else:
    #             # Faithfully executed code.
    #             testcase.answer = output
    #             verdict = Verdict.AC

    #         verdicts.append(verdict)

    #     logging.info('Finished generating output.')
    #     self.cleanup()
    #     return (self.decide_final_verdict(verdicts), testcases)

    def run_code(
        self,
        code: str,
        testcases: List[Testcase],
        time_limit: int,
        memory_limit: int,
    ) -> Generator[Tuple[str, Dict[str, str], int, Testcase], None, None]:
        """Iterate through the testcases and yield output.

        Args:
            code (str): Source code.
            testcases (List[Testcase]): Testcase objects.
            time_limit (int): Time limit in milliseconds.
            memory_limit (int): Memory limit in KB.

        Yields:
            Tuple[str, Dict[str, str], int, Testcase]: (Output, metadata, return code, current testcase)

        """
        logging.info('Begin running code...')
        code_path = os.path.join(self.box_path, 'code.py')
        metadata_path = os.path.join(METADATA_FOLDER, f'{self.box_id}.txt')

        # Write code to `code.py`.
        subprocess.run(['touch', code_path], check=False)
        subprocess.run(
            ['echo', code], stdout=open(code_path, 'w', encoding='utf-8'), check=False
        )

        # Convert milliseconds to seconds.
        time_limit_sec = time_limit / 1000

        # TODO: For non-python code, we need to compile it first, return CE if compilation fails.
        # if compilation fails
        # return Verdict.CE, [Verdict.CE for _ in range(len(testcases))]
        for testcase in testcases:
            proc = subprocess.run(
                [
                    'isolate',
                    '--box-id', f'{self.box_id}',
                    '-M', metadata_path,
                    '-t', f'{time_limit_sec}',
                    '-w', f'{time_limit_sec+1}',
                    '-m', f'{memory_limit}',
                    '--run',
                    PYTHON_PATH,
                    'code.py',
                ],
                input=testcase.input.encode('utf-8'),
                capture_output=True,
                check=False,
            )

            output = proc.stdout.decode('utf-8')
            metadata = self.read_metadata(metadata_path)
            return_code = proc.returncode
            yield (output, metadata, return_code, testcase)

        logging.info('Finished running.')

    def read_metadata(self, metadata_path: str) -> Dict[str, str]:
        """Reads metadata file and return dictionary of metadata.

        Args:
            metadata_path (str): Path to metadata file.

        Returns:
            dict[str, str]: Metadata.

        """
        metadata = {}
        with open(metadata_path, 'r', encoding='utf-8') as metadata_file:
            for line in metadata_file.readlines():
                key, value = line.split(':', maxsplit=1)
                metadata[key] = value.strip()
        return metadata

    def check_output(self, output: str, answer: str) -> bool:
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
        if Verdict.WJ in verdicts:
            return Verdict.WJ
        if Verdict.SE in verdicts:
            return Verdict.SE
        if Verdict.WA in verdicts:
            return Verdict.WA
        if Verdict.RE in verdicts:
            return Verdict.RE
        if Verdict.TLE in verdicts:
            return Verdict.TLE
        if Verdict.MLE in verdicts:
            return Verdict.MLE
        return Verdict.AC
