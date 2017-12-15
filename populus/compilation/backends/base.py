import logging

from populus.utils.module_loading import (
    get_import_path,
)


class BaseCompilerBackend(object):
    config = None

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(get_import_path(type(self)))

    def get_compiled_contracts(self):
        raise NotImplementedError("Must be implemented by subclasses")

