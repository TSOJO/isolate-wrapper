from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Testcase:
	"""Testcase.

	Attributes:
		input (str): Input for testcase.
		answer (str): Answer for testcase.
		batch_number (int): Batch number for testcase.

	"""

	input: str
	answer: str
	batch_number: int = 1
	
	@classmethod
	def cast_from_document(cls, document: str) -> Language:
		return Testcase(
			input=document['input'],
			answer=document['answer'],
			batch_number=document['batch_number'],
		)

	def cast_to_document(self) -> str:
		return {
			'input': self.input,
			'answer': self.answer,
			'batch_number': self.batch_number,
		}


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
		return {'verdict': self.name, 'verdict_long': self.value}

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
	"""Result.

	Attributes:
		verdict (Verdict): Verdict of result.
		time (int): Execution time in milliseconds.
		memory (int): Memory used in KB.

	"""

	verdict: Verdict
	time: float
	memory: float
	message: str

	@classmethod
	def empty(cls):
		return Result(Verdict.WJ, -1, -1, '')

	@classmethod
	def cast_from_document(cls, document: Any):
		result_obj = Result(
			verdict=Verdict.cast_from_document(document['verdict']),
			time=document['time'],
			memory=document['memory'],
			message=document['message'],
		)
		return result_obj

	def cast_to_document(self) -> Dict[str, Any]:
		return {
			'verdict': Verdict.cast_to_document(self.verdict),
			'time': self.time,
			'memory': self.memory,
			'message': self.message,
		}

	def __repr__(self) -> str:
		return f'(Verdict: {self.verdict}; time: {self.time}; memory: {self.memory}; message: {self.message})'

	def __str__(self) -> str:
		return self.__repr__()
	

class Language(Enum):
	# https://stackoverflow.com/questions/12680080/python-enums-with-attributes
	def __new__(cls, *args, **kwds):
		value = len(cls.__members__) + 1
		obj = object.__new__(cls)
		obj._value_ = value
		return obj
	def __init__(self, file_extension):
		self.file_extension = file_extension
	
	CPLUSPLUS = ('cpp')
	PYTHON = ('py')

	def cast_to_document(self) -> str:
		return self.name
	
	@classmethod
	def cast_from_document(cls, document: str) -> Language:
		return Language[document]

	