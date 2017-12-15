class BaseRegistrarBackend(object):
    config = None

    def __init__(self, config):
        self.config = config

    def record_package(self, package):
        """
        Returns the address for the contract instance in the registrar.
        """
        raise NotImplementedError("Must be implemented by subclasses")

    def lookup_package(self, package_identifier):
        """
        Returns all known address of the requested contract instance.
        """
        raise NotImplementedError("Must be implemented by subclasses")
