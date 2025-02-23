import logging
logger = logging.getLogger(__name__)

class ClassNameAttribute(logging.LoggerAdapter):
    """This class "injects" a class name into a logging record.  There isn't a LogRecord attribute for a class name,
    but this gets pretty close."""
    def __init__(self, logger, class_name: str):
        """:param logger: the logger object that will have its format modified
        :param class_name: name of the class that's being "injected" into the record

        Examples:
            The class is instantiated within an __init__() of another class:
                >>> import pydb
                >>> from logging import getLogger
                >>> LOGGER = getLogger(__name__)
                >>> self.logger = pydb.ClassNameAttribute(logger=LOGGER, class_name=self.__class__.__name__)"""
        super(ClassNameAttribute, self).__init__(logger=logger, extra={})
        self.class_name = class_name

    def process(self, msg, kwargs):
        return f"{self.class_name}-{msg}", kwargs