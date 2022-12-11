from dataclasses import dataclass
from enum import Enum

@dataclass
class Testcase:
    """Testcase.

    Attributes:
        input_ (str): Input for testcase.
        answer (str): Answer for testcase

    """
    input: str
    answer: str

class Verdict(Enum):
    """Verdict type.

    Will be one of AC/WA/TLE/MLE/RE/CE/SE

    """
    AC = 'Accepted'
    WA = 'Wrong Answer'
    TLE = 'Time Limit Exceeded'
    MLE = 'Memory Limit Exceeded'
    RE = 'Runtime Error'
    CE = 'Compilation Error'
    SE = 'System Error'

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.__repr__()

    def is_ac(self) -> bool:
        """Returns if object is AC

        Returns:
            bool: Whether or not object is AC
        """
        return self is Verdict.AC

@dataclass
class Result:
    """ Result.

    Attributes:
        verdict (Verdict): Verdict of result.
        time (float): Execution time in seconds.
        memory (float): Memory used in MB.

    """
    verdict: Verdict
    time: float
    memory: float

    def __repr__(self) -> str:
        return f'(Verdict: {self.verdict}; time: {self.time}; memory: {self.memory})'

    def __str__(self) -> str:
        return self.__repr__()
