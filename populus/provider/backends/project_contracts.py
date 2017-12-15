from __future__ import absolute_import

from .base import (
    BaseProviderBackend,
)


class ProjectContractsBackend(BaseProviderBackend):
    compiler_backend = None

    def __init__(self, config):
        # TODO: setting of compiler backend from config
        pass

    #
    # New API
    #
    def get_contract_data(self, contract_identifier):
        raise NotImplementedError("Must be implemented by subclasses")

    def get_deployment_data(self, contract_identifier):
        raise NotImplementedError("Must be implemented by subclasses")
