import itertools
import os
import sys

from eth_utils import (
    to_tuple,
)

from populus.compilation import (
    compile_project_contracts,
)
from populus.config import (
    validate_project_config,
)

from populus.utils.compile import (
    get_build_asset_dir,
    get_compiled_contracts_asset_path,
    get_contracts_source_dirs,
)

from populus.utils.filesystem import (
    get_latest_mtime,
)

from populus.utils.testing import (
    get_tests_dir,
)


if sys.version_info.major == 2:
    FileNotFoundError = OSError


class Project(object):
    project_dir = None
    config = None

    def __init__(self,
                 config=None,
                 project_dir=None):

        if project_dir is None:
            self.project_dir = os.getcwd()
        else:
            self.project_dir = os.path.abspath(project_dir)

        if config is None:
            config = {}

        validate_project_config(config)
        self.config = config

    #
    # Project
    #
    @property
    def tests_dir(self):
        return get_tests_dir(self.project_dir)

    #
    # Contracts
    #
    @property
    def compiled_contracts_asset_path(self):
        return get_compiled_contracts_asset_path(self.build_asset_dir)

    @property
    @to_tuple
    def contracts_source_dirs(self):
        source_dirs = self.config.get('compilation.contracts_source_dirs')
        if source_dirs:
            return [os.path.join(self.project_dir, contracts_dir) for contracts_dir in source_dirs]
        else:
            return get_contracts_source_dirs(self.project_dir)

    @property
    def build_asset_dir(self):
        return get_build_asset_dir(self.project_dir)

    _cached_compiled_contracts_mtime = None
    _cached_compiled_contracts = None

    @to_tuple
    def get_all_source_file_paths(self):
        compiler_backend = self.get_compiler_backend()
        return itertools.chain.from_iterable(
            compiler_backend.get_project_source_paths(source_dir)
            for source_dir
            in self.contracts_source_dirs
        )

    def is_compiled_contract_cache_stale(self):
        if self._cached_compiled_contracts is None:
            return True

        source_mtime = get_latest_mtime(self.get_all_source_file_paths())

        if source_mtime is None:
            return True
        elif self._cached_compiled_contracts_mtime is None:
            return True
        else:
            return self._cached_compiled_contracts_mtime < source_mtime

    def fill_contracts_cache(self, compiled_contracts, contracts_mtime):
        """
        :param contracts: become the Project's cache for compiled contracts
        :param contracts_mtime: last modification of supplied contracts
        :return:
        """
        self._cached_compiled_contracts_mtime = contracts_mtime
        self._cached_compiled_contracts = compiled_contracts

    @property
    def compiled_contract_data(self):
        if self.is_compiled_contract_cache_stale():
            source_file_paths, compiled_contracts = compile_project_contracts(self)
            contracts_mtime = get_latest_mtime(source_file_paths)
            self.fill_contracts_cache(
                compiled_contracts=compiled_contracts,
                contracts_mtime=contracts_mtime,
            )
        return self._cached_compiled_contracts

    #
    # Compiler Backend
    #
    def get_compiler_backend(self):
        compilation_config = self.config.get_config(
            'compilation.backend',
            config_class=CompilerConfig,
        )
        return compilation_config.backend

    #
    # Local Blockchains
    #
    def get_chain_config(self, chain_name):
        chain_config_key = 'chains.{chain_name}'.format(chain_name=chain_name)

        if chain_config_key in self.config:
            return self.config.get_config(chain_config_key, config_class=ChainConfig)
        else:
            raise KeyError(
                "Unknown chain: {0!r} - Must be one of {1!r}".format(
                    chain_name,
                    sorted(self.config.get('chains', {}).keys()),
                )
            )

    def get_chain(self, chain_name, chain_config=None):
        """
        Returns a context manager that runs a chain within the context of the
        current populus project.

        Alternatively you can specify any chain name that is present in the
        `chains` configuration key.
        """
        if chain_config is None:
            chain_config = self.get_chain_config(chain_name)
        chain = chain_config.get_chain(self, chain_name)
        return chain

    @property
    def base_blockchain_storage_dir(self):
        return get_base_blockchain_storage_dir(self.project_dir)
