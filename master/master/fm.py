import logging
import better_exceptions
from better_exceptions import format_exception


better_exceptions.MAX_LENGTH = 500

class ExceptionFormatter(logging.Formatter):
    def formatException(self, ei):
        return format_exception(*ei)
