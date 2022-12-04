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

    def is_AC(self) -> bool:
        return self is Verdict.AC

    def long_name(self) -> str:
        if self is Verdict.AC:
            return 'Accepted'
        elif self is Verdict.WA:
            return 'Wrong Answer'
        elif self is Verdict.TLE:
            return 'Time Limit Exceeded'
        elif self is Verdict.RE:
            return 'Runtime Error'
        elif self is Verdict.CE:
            return 'Compilation Error'
        elif self is Verdict.SE:
            return 'System Error'
        else:
            raise Exception('Invalid Verdict')
