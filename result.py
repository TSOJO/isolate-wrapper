from dataclasses import dataclass
from .verdict import Verdict

@dataclass
class Result:
    verdict: Verdict
    exec_time: float
    mem: float
    
    def __repr__(self) -> str:
        return f'(Verdict: {self.verdict}; time: {self.exec_time})'
    
    def __str__(self) -> str:
        return self.__repr__()

