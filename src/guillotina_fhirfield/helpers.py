# _*_ coding: utf-8 _*_
""" """
import inspect
import io
import json
import pkgutil
import re
import sys
import time
import warnings
from importlib import import_module
from typing import Union
from urllib.parse import unquote_plus

from guillotina.configure.config import reraise
from multidict import MultiDict
from multidict import MultiDictProxy
from zope.interface import Invalid

import ujson

from .exc import SearchQueryError
from .variables import EMPTY_STRING
from .variables import FHIR_ES_MAPPINGS_CACHE
from .variables import FHIR_RESOURCE_LIST  # noqa: F401
from .variables import FHIR_RESOURCE_MAPPING_DIR
from .variables import FHIR_RESOURCE_CLASS_CACHE  # noqa: F401
from .variables import FHIR_SEARCH_PARAMETER_SEARCHABLE
from .variables import NO_VALUE


__docformat__ = "restructuredtext"

PATH_WITH_DOT_AS = re.compile(r"\.as\([a-z]+\)$", re.I)
PATH_WITH_DOT_IS = re.compile(r"\.is\([a-z]+\)$", re.I)
PATH_WITH_DOT_WHERE = re.compile(r"\.where\([a-z]+=\'[a-z]+\'\)$", re.I)
NoneType = type(None)


def search_fhir_resource_cls(
    resource_type: str, cache: bool = True, fhir_release: str = None
) -> Union[str, NoneType]:  # noqa: E999
    """This function finds FHIR resource model class (from fhir.resources) and return dotted path string.

    :arg resource_type: the resource type name (required). i.e Organization
    :arg cache: (default True) the flag which indicates should query fresh or serve from cache if available.
    :arg fhir_release: FHIR Release (version) name. i.e STU3, R4
    :return dotted full string path. i.e fhir.resources.organization.Organization

    Example::

        >>> from guillotina_fhirfield.helpers import search_fhir_resource_cls
        >>> from zope.interface import Invalid
        >>> dotted_path = search_fhir_resource_cls('Patient')
        >>> 'fhir.resources.patient.Patient' == dotted_path
        True
        >>> dotted_path = search_fhir_resource_cls('FakeResource')
        >>> dotted_path is None
        True
    """
    if resource_type in FHIR_RESOURCE_CLASS_CACHE and cache:
        return "{0}.{1}".format(
            FHIR_RESOURCE_CLASS_CACHE[resource_type],
            resource_type,
        )

    # Trying to get from entire modules
    prime_module = 'fhir.resources'
    if fhir_release:
        prime_module = f'{prime_module}.{fhir_release}'

    prime_module_level = len(prime_module.split('.'))
    prime_module = import_module(prime_module)

    for importer, module_name, ispkg in pkgutil.walk_packages(
        prime_module.__path__, prime_module.__name__ + ".", onerror=lambda x: None
    ):
        if ispkg or (prime_module_level + 1) < len(module_name.split('.')):
            continue

        module_obj = import_module(module_name)

        for klass_name, klass in inspect.getmembers(module_obj, inspect.isclass):

            if klass_name == resource_type:
                FHIR_RESOURCE_CLASS_CACHE[resource_type] = module_name
                return f"{module_name}.{resource_type}"

    return None


def resource_type_to_resource_cls(resource_type: str, fhir_release: str = None) -> Union[Invalid, type]:
    """ """
    dotted_path = search_fhir_resource_cls(resource_type, fhir_release=fhir_release)
    if dotted_path is None:
        raise Invalid(f"`{resource_type}` is not valid fhir resource type!")

    return import_string(dotted_path)


def import_string(dotted_path: str) -> type:
    """Shameless hack from django utils, please don't mind!"""
    module_path, class_name = None, None
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except (ValueError, AttributeError):

        t, v, tb = sys.exc_info()
        msg = "{0} doesn't look like a module path".format(dotted_path)
        try:
            reraise(ImportError(msg), None, tb)
        finally:
            del t, v, tb

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "{0}" does not define a "{1}" attribute/class'.format(
            module_path, class_name
        )
        t, v, tb = sys.exc_info()
        try:
            return reraise(ImportError(msg), None, tb)
        finally:
            del t, v, tb


def parse_json_str(str_val: str, encoding: str = "utf-8") -> Union[dict, NoneType]:
    """ """
    json_dict: dict

    if str_val in (NO_VALUE, EMPTY_STRING, None):
        # No parsing for empty value
        return None

    try:
        json_dict = json.loads(str_val, encoding=encoding)
    except ValueError as exc:
        msg = "Invalid JSON String is provided!\n{0!s}".format(exc)
        t, v, tb = sys.exc_info()
        try:
            reraise(Invalid(msg), None, tb)
        finally:
            del t, v, tb

    return json_dict


def fhir_search_path_meta_info(path: str) -> Union[tuple, NoneType]:
    """ """
    resource_type = path.split(".")[0]
    properties = path.split(".")[1:]

    model_cls = resource_type_to_resource_cls(resource_type)
    result = None
    for prop in properties:
        for (
            name,
            jsname,
            typ,
            is_list,
            of_many,
            not_optional,
        ) in model_cls().elementProperties():
            if prop != name:
                continue
            if typ not in (int, float, bool, str):
                model_cls = typ

            result = (jsname, is_list, of_many)
            break

    return result


def filter_logic_in_path(raw_path: str) -> str:
    """Separates if any logic_in_path is provided"""

    # replace with unique
    replacer = "XOOXXOOXXOOX"
    as_match = PATH_WITH_DOT_AS.search(raw_path)
    is_match = PATH_WITH_DOT_IS.search(raw_path)
    where_match = PATH_WITH_DOT_IS.search(raw_path)

    if as_match:
        word = as_match.group()
        path = raw_path.replace(word, replacer)

        new_word = word[4].upper() + word[5:-1]
        path = path.replace(replacer, new_word)

    elif is_match:

        word = is_match.group()
        path = raw_path.replace(word, replacer)

        new_word = word[4].upper() + word[5:-1]
        path = path.replace(replacer, new_word)

    elif where_match:

        word = where_match.group()
        path = raw_path.replace(word, "")

    else:
        path = raw_path

    return path


def _translate_param_name_to_real_path_key(*args):
    """ """
    keys = list()
    keys.append(args[0].__name__)
    keys.append(args[1])

    try:
        keys.append(args[2])
    except IndexError:
        keys.append("Resource")

    keys.append(time.time() // (60 * 60 * 24))

    return keys


def translate_param_name_to_real_path(param_name, resource_type=None):
    """ """
    resource_type = resource_type or "Resource"

    try:
        paths = FHIR_SEARCH_PARAMETER_SEARCHABLE.get(param_name, [])[1]
    except IndexError:
        return

    for path in paths:
        if path.startswith(resource_type):
            path = filter_logic_in_path(path)
            return path


def parse_query_string(request, allow_none=False):
    """We are not using self.request.form (parsed by Zope Publisher)!!
    There is special meaning for colon(:) in key field. For example `field_name:list`
    treats data as List and it doesn't recognize FHIR search modifier like :not, :missing
    as a result, from colon(:) all chars are ommited.

    Another important reason, FHIR search supports duplicate keys (defferent values) in query string.

    Build Duplicate Key Query String ::
        >>> import requests
        >>> params = {'patient': 'P001', 'lastUpdated': ['2018-01-01', 'lt2018-09-10']}
        >>> requests.get(url, params=params)
        >>> REQUEST['QUERY_STRING']
        'patient=P001&lastUpdated=2018-01-01&lastUpdated=lt2018-09-10'

        >>> from six.moves.urllib.parse import urlencode
        >>> params = [('patient', 'P001'), ('lastUpdated', '2018-01-01'), ('lastUpdated', 'lt2018-09-10')]
        >>> urlencode(params)
        'patient=P001&lastUpdated=2018-01-01&lastUpdated=lt2018-09-10'


    param:request
    param:allow_none
    """
    query_string = request.get("QUERY_STRING", "")
    params = MultiDict()

    for q in query_string.split("&"):
        parts = q.split("=")
        param_name = unquote_plus(parts[0])
        try:
            value = parts[1] and unquote_plus(parts[1]) or None
        except IndexError:
            if not allow_none:
                continue
            value = None

        params.add(param_name, value)

    return MultiDictProxy(params)


def fhir_resource_mapping(resource_type: str, cache: bool = True) -> dict:
    """"""
    if resource_type in FHIR_ES_MAPPINGS_CACHE and cache:

        return FHIR_ES_MAPPINGS_CACHE[resource_type]

    try:
        FHIR_RESOURCE_LIST[resource_type.lower()]
    except KeyError:
        msg = f"{resource_type} is not valid FHIR resource type"

        t, v, tb = sys.exc_info()
        try:
            reraise(Invalid(msg), None, tb)
        finally:
            del t, v, tb
    mapping_json = FHIR_RESOURCE_MAPPING_DIR / f"{resource_type}.mapping.json"

    if not mapping_json.exists():

        warnings.warn(
            f"Mapping for {resource_type} is currently not supported,"
            " default Resource's mapping is used instead!",
            UserWarning,
        )

        return fhir_resource_mapping("Resource", cache=True)

    with io.open(str(mapping_json), "r", encoding="utf8") as f:

        mapping_dict = ujson.load(f)
        # xxx: validate mapping_dict['meta']['profile']?

        FHIR_ES_MAPPINGS_CACHE[resource_type] = mapping_dict["mapping"]

    return FHIR_ES_MAPPINGS_CACHE[resource_type]


def validate_resource_type(resource_type: str) -> NoneType:
    """FHIR resource type validation"""

    try:
        FHIR_RESOURCE_LIST[resource_type.lower()]
    except KeyError:
        msg = (
            f"{resource_type} is not valid FHIR Resource! "
            "@see: https://hl7.org/fhir/"
        )

        t, v, tb = sys.exc_info()
        try:
            reraise(Invalid(msg), None, tb)
        finally:
            del t, v, tb
