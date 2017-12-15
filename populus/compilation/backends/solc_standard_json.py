import os
from urllib import parse
# TODO: python2

from cytoolz import (
    assoc,
    concatv,
    merge,
    partial,
    pipe,
)

from semantic_version import (
    Spec,
)

from eth_utils import (
    add_0x_prefix,
    to_dict,
    to_tuple,
    to_set,
    sort_return,
    apply_to_return_value
)

from solc import (
    get_solc_version,
    compile_standard,
)
from solc.exceptions import (
    ContractsNotFound,
)

from populus.utils.compile import (
    load_json_if_string,
    normalize_contract_metadata,
)
from populus.utils.filesystem import (
    is_same_path,
    recursive_find_files,
)
from populus.utils.linking import (
    normalize_standard_json_link_references,
)
from populus.utils.mappings import (
    has_nested_key,
    get_nested_key,
    set_nested_key,
)

from .base import (
    BaseCompilerBackend,
)


@to_dict
def normalize_standard_json_contract_data(contract_data):
    if 'metadata' in contract_data:
        yield 'metadata', normalize_contract_metadata(contract_data['metadata'])
    if 'evm' in contract_data:
        evm_data = contract_data['evm']
        if 'bytecode' in evm_data:
            yield 'bytecode', add_0x_prefix(evm_data['bytecode'].get('object', ''))
            if 'linkReferences' in evm_data['bytecode']:
                yield 'linkrefs', normalize_standard_json_link_references(
                    evm_data['bytecode']['linkReferences'],
                )
        if 'deployedBytecode' in evm_data:
            yield 'bytecode_runtime', add_0x_prefix(evm_data['deployedBytecode'].get('object', ''))
            if 'linkReferences' in evm_data['deployedBytecode']:
                yield 'linkrefs_runtime', normalize_standard_json_link_references(
                    evm_data['deployedBytecode']['linkReferences'],
                )
    if 'abi' in contract_data:
        yield 'abi', load_json_if_string(contract_data['abi'])
    if 'userdoc' in contract_data:
        yield 'userdoc', load_json_if_string(contract_data['userdoc'])
    if 'devdoc' in contract_data:
        yield 'devdoc', load_json_if_string(contract_data['devdoc'])


@to_tuple
def normalize_compilation_result(compilation_result):
    """
    Take the result from the --standard-json compilation and flatten it into an
    iterable of contract data dictionaries.
    """
    for source_path, file_contracts in compilation_result['contracts'].items():
        for contract_name, raw_contract_data in file_contracts.items():
            contract_data = normalize_standard_json_contract_data(raw_contract_data)
            yield pipe(
                contract_data,
                partial(assoc, key='source_path', value=source_path),
                partial(assoc, key='name', value=contract_name),
            )


@to_tuple
def deduplicate_source_paths(source_file_paths):
    for idx, path in enumerate(set(source_file_paths)):
        is_duplicated = any(
            is_same_path(path, other_path)
            for other_path
            in source_file_paths[idx + 1:]
        )
        if is_duplicated:
            continue
        else:
            yield path


@to_tuple
@apply_to_return_value(deduplicate_source_paths)
@sort_return
@to_set
def collect_source_files(source_paths, glob_pattern):
    for path in source_paths:
        if os.path.isdir(path):
            for source_file_path in recursive_find_files(path, glob_pattern):
                yield os.path.relpath(source_file_path)
        elif os.path.isfile:
            yield os.path.relpath(path)


def to_file_uri(file_path):
    return parse.urlunparse(('file', '', os.path.abspath(file_path), '', '', ''))


REQUIRED_OUTPUT_SELECTION = [
    'abi',
    'metadata',
    'evm.bytecode',
    'evm.bytecode.object',
    'evm.bytecode.linkReferences',
    'evm.deployedBytecode',
    'evm.deployedBytecode.object',
    'evm.deployedBytecode.linkReferences',
]
OUTPUT_SELECTION_KEY = 'settings.outputSelection.*.*'
SOURCES_KEY = 'sources'

DEFAULT_STD_INPUT = {
    'optimizer': {
        'enabled': True,
        'runs': 500,
    },
    'language': 'Solidity',
    'settings': {
        'outputSelection': {},
    }
}


class SolcStandardJSONBackend(BaseCompilerBackend):
    project_source_glob = ('*.sol', )
    test_source_glob = ('Test*.sol', )

    def __init__(self, *args, **kwargs):
        if get_solc_version() not in Spec('>=0.4.18'):
            raise OSError(
                "The 'SolcStandardJSONBackend can only be used with solc "
                "versions >=0.4.18."
            )
        super(SolcStandardJSONBackend, self).__init__(*args, **kwargs)

    def get_compiled_contracts(self):
        # source paths
        source_paths = self.config.get('source_paths', [])
        if not source_paths:
            return tuple()

        glob_pattern = self.config.get('source_file_glob_pattern', '*.sol')
        sources = collect_source_files(source_paths, glob_pattern)
        sources_setter_fn = assoc(key=SOURCES_KEY, value=sources)

        std_input = pipe(
            merge(DEFAULT_STD_INPUT, self.config.get('stdin', {})),
            sources_setter_fn,
        )

        # Make sure the output selection has all of the required output values.
        if has_nested_key(std_input, OUTPUT_SELECTION_KEY):
            current_selection = get_nested_key(std_input, OUTPUT_SELECTION_KEY)
            output_selection = list(set(concatv(current_selection, REQUIRED_OUTPUT_SELECTION)))
        else:
            output_selection = REQUIRED_OUTPUT_SELECTION

        set_nested_key(std_input, OUTPUT_SELECTION_KEY, output_selection)

        self.logger.debug("Input Description JSON settings are: %s", std_input["settings"])

        try:
            compilation_result = compile_standard(std_input)
        except ContractsNotFound:
            return tuple()

        compiled_contracts = normalize_compilation_result(compilation_result)

        return compiled_contracts
