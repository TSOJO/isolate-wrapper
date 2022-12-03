from enum import Enum

class Verdict(Enum):
    AC = 0 # Accepted
    WA = 1 # Wrong Answer
    TLE = 2 # Time Limit Exceeded
    RE = 3 # Runtime Error
    CE = 4 # Compilation Error
    SE = 5 # System Error

    def __repr__(self) -> str:
        return self.name
    
    def __str__(self) -> str:
        return self.__repr__()
