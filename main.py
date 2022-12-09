import subprocess
import logging
from os import path
from typing import List, Tuple, Dict

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
        """Try to initialise by assigning to an available box.
        """
        self.ensure_isolate_installed()
        self.create()

    def ensure_isolate_installed(self) -> None:
        """Ensures isolate is installed.
        """
        proc = subprocess.run(['isolate', '--version'], capture_output=True)
        if proc.returncode != 0:
            raise Exception('Isolate is not installed.')

    def create(self):
        """Try assign to an available box.

        Also, initialise class attributes if box found successfully.

        Raises:
            Exception: If no boxes are available.

        """

        logging.info('Creating sandbox...')
        for id_ in range(0, MAX_BOX):
            proc = subprocess.run(['isolate',
                                   '--box-id', f'{id_}',
                                   '--init'],
                                  capture_output=True)
            if proc.returncode != 0:
                # Box already in use.
                logging.info('Box %d in use. Trying next...', id_)
                continue

            # Usually /var/local/lib/isolate/{box-id}/box
            self.box_path = proc.stdout.decode('utf-8')[:-1] + '/box'
            self.box_id = id_

            logging.info('Box %d available. Created box at %s',
                         self.box_id, self.box_path)
            return

        raise Exception('All boxes full')

    def cleanup(self):
        """Clean up the box.

        Note:
            If this method isn't eventually called (e.g., some error stopped program flow),
            then box will continue to be occupied. Manual cleanup is then needed.

        """
        subprocess.run(['isolate',
                        '--box-id', f'{self.box_id}',
                        '--cleanup'])
        logging.info('Cleaned up box %d.', self.box_id)

    # TODO: Make code a class, representing different languages.
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
            time_limit (int): Time limit in seconds.
            memory_limit (int): Memory limit in KB.

        Returns:
            tuple[Verdict, List[Result]]: Tuple of final verdict and results.

        """
        logging.info('Begin running code...')
        code_path = path.join(self.box_path, 'code.py')
        metadata_path = path.join(METADATA_FOLDER, f'{self.box_id}.txt')

        # Write code to `code.py`.
        subprocess.run(['touch', code_path])
        subprocess.run(['echo', code],
                       stdout=open(code_path, 'w', encoding='utf-8'))

        results = []

        # TODO: For non-python code, we need to compile it first, return CE if compilation fails.
        # if compilation fails
        # return Verdict.CE, [Verdict.CE for _ in range(len(testcases))]
        for testcase in testcases:
            proc = subprocess.run(['isolate',
                                   '--box-id', f'{self.box_id}',
                                   '-M', metadata_path,
                                   '-t', f'{time_limit}',
                                   '-w', f'{time_limit+1}',
                                   '-m', f'{memory_limit}',
                                   '--run', PYTHON_PATH, 'code.py'],
                                  input=testcase.input_.encode('utf-8'),
                                  capture_output=True)
            output = proc.stdout.decode('utf-8')

            metadata = self.read_metadata(metadata_path)

            if proc.returncode != 0:
                # TLE, MLE, RE, CE, SE.
                if metadata['status'] in ('RE', 'SG'):
                    verdict = Verdict.RE
                elif metadata['status'] == 'TO':
                    verdict = Verdict.TLE
                elif metadata['status'] == 'XX':
                    verdict = Verdict.SE
            else:
                # WA.
                if not self.check_output(output, testcase.answer):
                    verdict = Verdict.WA
                else:
                    verdict = Verdict.AC

            result = Result(verdict=verdict,
                            time=round(float(metadata['time']), 3),
                            memory=round(float(metadata['max-rss']) / 1024, 3))
            results.append(result)

        logging.info('Finished running.')

        verdicts = [r.verdict for r in results]
        final_verdict = self.decide_final_verdict(verdicts)

        self.cleanup()
        return (final_verdict, results)

    def generate_answer(
        self,
        code: str,
        testcases: List[Testcase],
        time_limit: int,
        memory_limit: int,
    ) -> None:
        """Runs code, then set the answer of each testcase to the output.

        Args:
            code (str): Source code.
            testcases (List[Testcase]): Testcase objects.
            time_limit (int): Time limit in seconds.
            memory_limit (int): Memory limit in KB.

        Returns:
            Verdict: Returns Verdict.AC if the code ran faithfully, other verdicts have their usual meanings.

        """
        logging.info('Begin running code...')
        code_path = path.join(self.box_path, 'code.py')
        metadata_path = path.join(METADATA_FOLDER, f'{self.box_id}.txt')

        # Write code to `code.py`.
        subprocess.run(['touch', code_path])
        subprocess.run(['echo', code],
                       stdout=open(code_path, 'w', encoding='utf-8'))

        verdicts = []

        # TODO: For non-python code, we need to compile it first, return CE if compilation fails.
        # if compilation fails
        # return Verdict.CE, [Verdict.CE for _ in range(len(testcases))]
        for testcase in testcases:
            proc = subprocess.run(['isolate',
                                   '--box-id', f'{self.box_id}',
                                   '-M', metadata_path,
                                   '-t', f'{time_limit}',
                                   '-w', f'{time_limit+1}',
                                   '-m', f'{memory_limit}',
                                   '--run', PYTHON_PATH, 'code.py'],
                                  input=testcase.input_.encode('utf-8'),
                                  capture_output=True)
            output = proc.stdout.decode('utf-8')

            metadata = self.read_metadata(metadata_path)

            if proc.returncode != 0:
                # TLE, RE, SE.
                if metadata['status'] in ('RE', 'SG'):
                    verdict = Verdict.RE
                elif metadata['status'] == 'TO':
                    verdict = Verdict.TLE
                elif metadata['status'] == 'XX':
                    verdict = Verdict.SE
            else:
                # Faithfully executed code.
                testcase.answer = output
                verdict = Verdict.AC

            verdicts.append(verdict)

        logging.info('Finished running.')
        self.cleanup()
        return self.decide_final_verdict(verdicts)

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
        if Verdict.SE in verdicts:
            return Verdict.SE
        if Verdict.WA in verdicts:
            return Verdict.WA
        if Verdict.RE in verdicts:
            return Verdict.RE
        if Verdict.TLE in verdicts:
            return Verdict.TLE
        return Verdict.AC
