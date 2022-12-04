from dataclasses import dataclass
from .verdict import Verdict

@dataclass
class Result:
    verdict: Verdict
    time: float
    memory: float
    
    def __repr__(self) -> str:
        return f'(Verdict: {self.verdict}; time: {self.time}; memory: {self.memory})'
    
    def __str__(self) -> str:
        return self.__repr__()

