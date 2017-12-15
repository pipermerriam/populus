def get_default_registrar_backends(web3):
    raise NotImplementedError("TODO")


class Registrar(object):
    """
    Abstraction for recording known contracts on a given chain.
    """
    backends = None

    def __init__(self, web3, config):
        self.web3 = web3
        self.config = config

        if 'backends' in config:
            raise NotImplementedError("TODO")
        else:
            self.backends = get_default_registrar_backends(web3)

    def record_package(self, package):
        raise NotImplementedError("Must be implemented by subclasses")

    def lookup_package(self, package_identifier):
        raise NotImplementedError("Must be implemented by subclasses")
