from dataclasses import dataclass
from enum import Enum

@dataclass
class Testcase:
    """Testcase.

    Attributes:
        input_ (str): Input for testcase.
        answer (str): Answer for testcase

    """
    input_: str
    answer: str

class Verdict(Enum):
    """Verdict type.

    Will be one of AC/WA/TLE/RE/CE/SE

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

    # def long_name(self) -> str:
    #     if self is Verdict.AC:
    #         return 'Accepted'
    #     elif self is Verdict.WA:
    #         return 'Wrong Answer'
    #     elif self is Verdict.TLE:
    #         return 'Time Limit Exceeded'
    #     elif self is Verdict.RE:
    #         return 'Runtime Error'
    #     elif self is Verdict.CE:
    #         return 'Compilation Error'
    #     elif self is Verdict.SE:
    #         return 'System Error'
    #     else:
    #         raise Exception('Invalid Verdict')

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
