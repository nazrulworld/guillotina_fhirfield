# _*_ coding: utf-8 _*_
""" """
import inspect
import json
import pkgutil
import re
import sys
import time
from importlib import import_module
from typing import Union
from urllib.parse import unquote_plus

from guillotina.configure.config import reraise
from zope.interface import Invalid

from .exc import SearchQueryError
from .variables import EMPTY_STRING
from .variables import FHIR_RESOURCE_LIST  # noqa: F401
from .variables import FHIR_RESOURCE_MODEL_CACHE  # noqa: F401
from .variables import FHIR_SEARCH_PARAMETER_SEARCHABLE
from .variables import NO_VALUE


__docformat__ = "restructuredtext"

PATH_WITH_DOT_AS = re.compile(r"\.as\([a-z]+\)$", re.I)
PATH_WITH_DOT_IS = re.compile(r"\.is\([a-z]+\)$", re.I)
PATH_WITH_DOT_WHERE = re.compile(r"\.where\([a-z]+=\'[a-z]+\'\)$", re.I)
NoneType = type(None)


def search_fhir_model(model_name: str, cache: bool = True) -> Union[str, NoneType]:  # noqa: E999
    """This function finds FHIR resource model class (from fhirclient.models) and return dotted path string.

    :arg model_name: the resource type name (required). i.e Organization
    :arg cache: (default True) the flag which indicates should query fresh or serve from cache if available.
    :return dotted full string path. i.e fhirclient.models.organization.Organization

    Example::

        >>> from guillotina_fhirfield.helpers import search_fhir_model
        >>> from zope.interface import Invalid
        >>> dotted_path = search_fhir_model('Patient')
        >>> 'fhirclient.models.patient.Patient' == dotted_path
        True
        >>> dotted_path = search_fhir_model('FakeResource')
        >>> dotted_path is None
        True
    """
    if model_name in FHIR_RESOURCE_MODEL_CACHE and cache:
        return "{0}.{1}".format(FHIR_RESOURCE_MODEL_CACHE[model_name], model_name)

    # Trying to get from entire modules
    from fhirclient import models

    for importer, module_name, ispkg in pkgutil.walk_packages(
        models.__path__, models.__name__ + ".", onerror=lambda x: None
    ):
        if ispkg or module_name.endswith("_tests"):
            continue

        module_obj = import_module(module_name)

        for klass_name, klass in inspect.getmembers(module_obj, inspect.isclass):

            if klass_name == model_name:
                FHIR_RESOURCE_MODEL_CACHE[model_name] = module_name
                return "{0}.{1}".format(module_name, model_name)

    return None


def resource_type_to_model_cls(resource_type: str) -> Union[Invalid, type]:
    """ """
    dotted_path = search_fhir_model(resource_type)
    if dotted_path is None:
        raise Invalid("`{0}` is not valid fhir resource type!".format(resource_type))

    return import_string(dotted_path)


def import_string(dotted_path: str) -> Union[Invalid, type]:
    """Shameless hack from django utils, please don't mind!"""
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
            reraise(ImportError(msg), None, tb)
        finally:
            del t, v, tb


def parse_json_str(str_val: str, encoding: str = "utf-8") -> Union[dict, NoneType]:
    """ """
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


def validate_index_name(name: str) -> Union[SearchQueryError, NoneType]:
    """ZCatalog index name validation"""

    parts = name.split("_")

    try:
        FHIR_RESOURCE_LIST[parts[0].lower()]
    except KeyError:
        msg = (
            "Invalid index name for FhirFieldIndex. Index name must start with "
            "any valid fhir resource type name as prefix or just use "
            "resource type name as index name.\n"
            "allowed format: (resource type as prefix)_(your name), "
            "(resource_type as index name)\n"
            "example: hospital_resource, patient"
        )

        t, v, tb = sys.exc_info()
        try:
            reraise(SearchQueryError(msg), None, tb)
        finally:
            del t, v, tb

    return None


def fhir_search_path_meta_info(path: str) -> Union[tuple, NoneType]:
    """ """
    resource_type = path.split(".")[0]
    properties = path.split(".")[1:]

    model_cls = resource_type_to_model_cls(resource_type)
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
    """Seprates if any logic_in_path is provided"""

    # replace with unique
    replacer = "XXXXXXX"

    if PATH_WITH_DOT_AS.search(raw_path):
        word = PATH_WITH_DOT_AS.search(raw_path).group()
        path = raw_path.replace(word, replacer)

        new_word = word[4].upper() + word[5:-1]
        path = path.replace(replacer, new_word)

    elif PATH_WITH_DOT_IS.search(raw_path):

        word = PATH_WITH_DOT_IS.search(raw_path).group()
        path = raw_path.replace(word, replacer)

        new_word = word[4].upper() + word[5:-1]
        path = path.replace(replacer, new_word)

    elif PATH_WITH_DOT_WHERE.search(raw_path):

        word = PATH_WITH_DOT_WHERE.search(raw_path).group()
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

    if not query_string:
        return list()
    params = list()

    for q in query_string.split("&"):
        parts = q.split("=")
        param_name = unquote_plus(parts[0])
        try:
            value = parts[1] and unquote_plus(parts[1]) or None
        except IndexError:
            if not allow_none:
                continue
            value = None

        params.append((param_name, value))

    return params
