# -*- coding: utf-8 -*-
# @Date    : 2018-08-09 10:07:41
# @Author  : Md Nazrul Islam <email2nazrul@gmail.com>
# @Link    : http://nazrul.me/
# @Version : $Id$
# All imports here
import io
import logging
import os
import pathlib
from collections import defaultdict

import ujson


__author__ = 'Md Nazrul Islam <email2nazrul@gmail.com>'


class NO_VALUE(object):
    def __repr__(self):
        return '<NO_VALUE>'


NO_VALUE = NO_VALUE()
EMPTY_STRING = ''
LOGGER = logging.getLogger('guillotina-fhirfield')
FHIR_VERSION = 'STU3'
FHIR_FIELD_DEBUG = os.environ.get('FHIR_FIELD_DEBUG', '').lower() in \
    ('y', 'yes', 't', 'true', '1')
ERROR_PARAM_UNKNOWN = 'EP001'
ERROR_PARAM_UNSUPPORTED = 'EP002'
ERROR_PARAM_WRONG_DATATYPE = 'EP003'

ERROR_MESSAGES = {
    ERROR_PARAM_UNKNOWN: 'Parameter is unrecognized by FHIR search.',
    ERROR_PARAM_UNSUPPORTED: 'Parameter is not supported for this resource type',
    ERROR_PARAM_WRONG_DATATYPE: 'The value\'s data type is not excepted',
}

FHIR_RESOURCE_CLASS_CACHE: dict = defaultdict()

FHIR_STATIC_DIR = pathlib.Path(os.path.abspath(__file__)).parent / 'static' / 'HL7' / 'FHIR'

FHIR_RESOURCE_LIST_DIR = FHIR_STATIC_DIR / 'ResourceList'
FHIR_RESOURCE_MAPPING_DIR = FHIR_STATIC_DIR / 'mappings'

with io.open(
        str(FHIR_STATIC_DIR / 'search' / 'FHIR-Search-Parameter-Registry.json'),
        'r',
        encoding='utf8') as f:

    FHIR_SEARCH_PARAMETER_REGISTRY = ujson.load(f)['object']

with io.open(
        str(FHIR_STATIC_DIR / 'search' / 'FHIR-Search-Parameter-Registry-searchable.json'),
        'r',
        encoding='utf8') as f:

    FHIR_SEARCH_PARAMETER_SEARCHABLE = ujson.load(f)['searchable']
    FHIR_SEARCH_PARAMETER_SEARCHABLE_KEYS = \
        FHIR_SEARCH_PARAMETER_SEARCHABLE.keys()

FSPR_KEYS_BY_GROUP = dict()

for group, rows in FHIR_SEARCH_PARAMETER_REGISTRY.items():
    FSPR_KEYS_BY_GROUP[group] = list()
    for row in rows[1:]:
        FSPR_KEYS_BY_GROUP[group].append(row[0])

FSPR_VALUE_PRIFIXES_MAP = {
    'eq': None,
    'ne': None,
    'gt': 'gt',
    'lt': 'lt',
    'ge': 'gte',
    'le': 'lte',
    'sa': None,
    'eb': None,
    'ap': None}

SEARCH_PARAM_MODIFIERS = (
    'missing',
    'exists',
    'exact',
    'not',
    'text',
    'in',
    'below',
    'above',
    'not-in')

with open(str(FHIR_RESOURCE_LIST_DIR / '{0}.json'.format(FHIR_VERSION)), 'r', encoding='utf8') as f:
    """ """
    FHIR_RESOURCE_LIST = ujson.load(f)['resources']


FHIR_ES_MAPPINGS_CACHE: dict = {}  # noqa: E999
