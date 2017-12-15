import os

import jsonschema

import anyconfig

from eth_utils import (
    to_tuple,
)

from populus import ASSETS_DIR


@to_tuple
def get_validation_errors(config, schema):
    validator = jsonschema.Draft4Validator(schema)
    for error in validator.iter_errors(dict(config)):
        yield error


CONFIG_SCHEMA_PATH = os.path.join(ASSETS_DIR, 'config.schema.json')


def validate_project_config(config):
    schema = anyconfig.load(CONFIG_SCHEMA_PATH)
    errors = get_validation_errors(config, schema)
    if errors:
        error_message = format_errors(errors)
        raise ValueError(error_message)


def format_errors(errors):
    return '\n'.join((
        '\n--------------------{e.path}-----------------\n{e.message}\n'.format(
            e=error,
        )
        for error in errors
    ))
