from dataclasses import dataclass
from typing import Any, Dict
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
    WJ = 'Waiting for Judge'

    @classmethod
    def cast_from_document(cls, document: Any):
        return Verdict[document['verdict']]

    def cast_to_document(self) -> Dict[str, Any]:
        return {
            'verdict': self.name,
            'verdict_long': self.value
        }

    def is_ac(self) -> bool:
        """Returns if object is AC

        Returns:
            bool: Whether or not object is AC
        """
        return self is Verdict.AC
    
    def is_wj(self) -> bool:
        return self is Verdict.WJ

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class Result:
    """ Result.

    Attributes:
        verdict (Verdict): Verdict of result.
        time (int): Execution time in milliseconds.
        memory (int): Memory used in KB.

    """
    verdict: Verdict
    time: float
    memory: float

    @classmethod
    def cast_from_document(cls, document: Any):
        result_obj = Result(
			verdict=Verdict.cast_from_document(document['verdict']),
            time=document['time'],
            memory=document['memory']
		)
        return result_obj

    def cast_to_document(self) -> Dict[str, Any]:
        return {
            'verdict': Verdict.cast_to_document(self.verdict),
            'time': self.time,
            'memory': self.memory
		}

    def __repr__(self) -> str:
        return f'(Verdict: {self.verdict}; time: {self.time}; memory: {self.memory})'

    def __str__(self) -> str:
        return self.__repr__()
