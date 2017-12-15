class BaseContractBackend(object):
    web3 = None
    registrar = None
    config = None

    def __init__(self, web3, registrar, config):
        self.web3 = web3
        self.registrar = registrar
        self.config = config

    def get_contract_data(self, contract_identifier):
        raise NotImplementedError("Must be implemented by subclasses")

    def get_deployment_data(self, contract_identifier):
        raise NotImplementedError("Must be implemented by subclasses")
