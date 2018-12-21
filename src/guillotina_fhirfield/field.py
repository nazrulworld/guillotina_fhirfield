# -*- coding: utf-8 -*-
from fhirclient.models.fhirabstractbase import FHIRValidationError
from .helpers import import_string
from .helpers import parse_json_str
from .helpers import resource_type_str_to_fhir_model
from .helpers import search_fhir_model
from .interfaces import IFhirField
from .interfaces import IFhirResource
from .interfaces import IFhirFieldValue
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface.exceptions import BrokenImplementation
from zope.interface.exceptions import BrokenMethodImplementation
from zope.interface.exceptions import DoesNotImplement
from zope.interface.interfaces import IInterface
from zope.interface.verify import verifyObject
from guillotina import configure
from guillotina.schema import get_fields
from guillotina.schema import Object
from guillotina.schema.exceptions import ConstraintNotSatisfied
from guillotina.schema.interfaces import IFromUnicode
from guillotina.schema.exceptions import WrongContainedType
from guillotina.schema.exceptions import WrongType
from collections import OrderedDict
from guillotina.json.serialize_schema_field import DefaultSchemaFieldSerializer
from guillotina.interfaces import ISchemaFieldSerializeToJson
from guillotina.configure.config import reraise
from zope.interface import Interface

import jsonpatch
import six
import sys
import ujson

__docformat__ = "restructuredtext"


@implementer(IFhirFieldValue)
class FhirFieldValue(object):
    """FhirResourceValue is a proxy class for holding any object derrived from
    fhirclient.models.resource.Resource"""

    __slot__ = ("_resource_obj",)

    def foreground_origin(self):
        """Return the original object of FHIR model that is proxied!"""
        if bool(self._resource_obj):
            return self._resource_obj
        else:
            return None

    def patch(self, patch_data):

        if not isinstance(patch_data, (list, tuple)):
            raise WrongType(
                "patch value must be list or tuple type! but got `{0}` type.".format(
                    type(patch_data)
                )
            )

        if not bool(self):
            raise Invalid(
                "None object cannot be patched! Make sure fhir resource value is not empty!"
            )
        try:
            patcher = jsonpatch.JsonPatch(patch_data)
            value = patcher.apply(self._resource_obj.as_json())

            new_value = self._resource_obj.__class__(value)

            object.__setattr__(self, "_resource_obj", new_value)

        except jsonpatch.JsonPatchException:
            t, v, tb = sys.exc_info()
            try:
                reraise(Invalid(str(v)), None, tb)
            finally:
                del t, v, tb

    def stringify(self, prettify=False):
        """ """
        params = {}
        if prettify:
            # will make little bit slow, so apply only if needed
            params["indent"] = 2

        return (
            self._resource_obj is not None
            and ujson.dumps(self._resource_obj.as_json(), **params)
            or ""
        )

    def _validate_object(self, obj):
        """ """
        if obj is None:
            return

        try:
            verifyObject(IFhirResource, obj, False)

        except (BrokenImplementation, BrokenMethodImplementation) as exc:

            t, v, tb = sys.exc_info()
            try:
                reraise(Invalid(str(v)), None, tb)
            finally:
                del t, v, tb

        except DoesNotImplement:
            msg = "Object must be derived from valid FHIR resource model class!"
            msg += "But it is found that object is derived from `{0}`".format(
                obj.__class__.__module__ + "." + obj.__class__.__name__
            )

            t, v, tb = sys.exc_info()

            msg += "\nOriginal Exception: {0!s}".format(str(v))

            try:
                reraise(WrongType(msg), None, tb)
            finally:
                del t, v, tb

    def __init__(self, obj=None, encoding="utf-8"):
        """ """
        # Let's validate before value assignment!
        self._validate_object(obj)

        object.__setattr__(self, "_resource_obj", obj)

    def __getattr__(self, name):
        """Any attribute from FHIR Resource Object is accessible via this class"""
        try:
            return super(FhirFieldValue, self).__getattr__(name)
        except AttributeError:
            return getattr(self._resource_obj, name)

    def __getstate__(self):
        """ """
        odict = OrderedDict([("_resource_obj", self._resource_obj)])
        return odict

    def __setattr__(self, name, val):
        """This class kind of unmutable! All changes should be applied on FHIR Resource Object"""
        setattr(self._resource_obj, name, val)

    def __setstate__(self, odict):
        """ """
        for attr, value in six.iteritems(odict):
            object.__setattr__(self, attr, value)

    def __str__(self):
        """ """
        return self.stringify()

    def __repr__(self):
        """ """
        if self.__bool__():
            return "<{0} object represents object of {1} at {2}>".format(
                self.__class__.__module__ + "." + self.__class__.__name__,
                self._resource_obj.__class__.__module__
                + "."
                + self._resource_obj.__class__.__name__,
                hex(id(self)),
            )
        else:
            return "<{0} object represents object of {1} at {2}>".format(
                self.__class__.__module__ + "." + self.__class__.__name__,
                None.__class__.__name__,
                hex(id(self)),
            )

    def __eq__(self, other):
        if not isinstance(other, FhirFieldValue):
            return NotImplemented
        return self._resource_obj == other._resource_obj

    def __ne__(self, other):
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    def __bool__(self):
        """ """
        return bool(self._resource_obj is not None)

    __nonzero__ = __bool__


@implementer(IFhirField, IFromUnicode)
class FhirField(Object):
    """FhirResource also known as FHIR field is the schema field derrived from z3c.form's field.

    It takes all initilial arguments those are derrived from standard schema field, with additionally
    ``model``, ``resource_type`` and ``model_interface``

    .. note::
        field name must be start with lowercase name of FHIR Resource.
    """

    _type = FhirFieldValue
    _model_class = None
    _model_interface_class = None

    def __init__(self, model=None, model_interface=None, resource_type=None, **kw):
        """
        :arg model: dotted path of FHIR Model class

        :arg resource_type:

        :arg model_interface
        """

        self.schema = IFhirFieldValue
        # self.model = model
        # self.resource_type = resource_type
        # self.model_interface = model_interface

        self._init(model, model_interface, resource_type, **kw)

        if "default" in kw:
            default = kw["default"]

            if isinstance(default, str):
                kw["default"] = self.from_unicode(default)

            elif isinstance(default, dict):
                kw["default"] = self.from_dict(default)

        super(FhirField, self).__init__(schema=self.schema, **kw)

    def from_unicode(self, str_val):
        """ """
        json_dict = parse_json_str(str_val)

        return self.from_dict(json_dict)

    def from_dict(self, dict_value):
        """ """
        if dict_value is None:
            value = None
        else:
            value = self._from_dict(dict_value)
        # do validation now
        self.validate(value)
        return value

    def _init(self, model, model_interface, resource_type, **kw):
        """ """

        if "default" in kw:

            if (
                isinstance(kw["default"], (str, dict)) or kw["default"] is None
            ) is False:
                msg = (
                    "Only dict or string or None is accepted as "
                    "default value but got {0}".format(type(kw["default"]))
                )

                raise Invalid(msg)

        field_attributes = get_fields(IFhirField)

        attribute = field_attributes['model'].bind(self)
        if model is None:
            attribute.validate(model)
            attribute_val = None
        else:
            attribute_val = attribute.from_unicode(model)
        attribute.set(self, attribute_val)

        attribute = field_attributes['model_interface'].bind(self)
        if model_interface is None:
            attribute.validate(model_interface)
            attribute_val = None
        else:
            attribute_val = attribute.from_unicode(model_interface)
        attribute.set(self, attribute_val)

        attribute = field_attributes['resource_type'].bind(self)
        if resource_type is None:
            attribute.validate(resource_type)
            attribute_val = None
        else:
            attribute_val = attribute.from_unicode(resource_type)
        attribute.set(self, attribute_val)

        if self.resource_type and self.model is not None:
            raise Invalid(
                "Either `model` or `resource_type` value is acceptable! you cannot provide both!"
            )

        if self.model:
            try:
                klass = import_string(self.model)
            except ImportError:
                msg = "Invalid FHIR Resource Model `{0}`! Please check the module or class name.".format(
                    self.model
                )

                t, v, tb = sys.exc_info()
                try:
                    reraise(Invalid(msg), None, tb)
                finally:
                    del t, v, tb

            if not IFhirResource.implementedBy(klass):

                raise Invalid(
                    "{0!r} must be valid model class from fhirclient.model".format(
                        klass
                    )
                )
            self._model_class = klass

        if self.resource_type and search_fhir_model(self.resource_type) is None:
            msg = "{0} is not valid fhir resource type!".format(self.resource_type)
            raise Invalid(msg)

        if self.model_interface:
            try:
                klass = import_string(self.model_interface)
            except ImportError:
                msg = "Invalid FHIR Model Interface`{0}`! Please check the module or class name.".format(
                    self.model_interface
                )
                t, v, tb = sys.exc_info()
                try:
                    reraise(Invalid(msg), None, tb)
                finally:
                    del t, v, tb

            if not IInterface.providedBy(klass):
                raise WrongType("An interface is required", klass, self.__name__)

            if klass is not IFhirResource and not issubclass(klass, IFhirResource):
                msg = "`{0!r}` must be derived from {1}".format(
                    klass,
                    IFhirResource.__module__ + "." + IFhirResource.__class__.__name__,
                )

                raise Invalid(msg)

            self._model_interface_class = klass

    def _pre_value_validate(self, fhir_json):
        """ """
        if isinstance(fhir_json, str):
            fhir_dict = parse_json_str(fhir_json).copy()

        elif isinstance(fhir_json, dict):
            fhir_dict = fhir_json.copy()

        else:
            raise WrongType(
                "Only dict type data is allowed but got `{0}` type data!".format(
                    type(fhir_json)
                )
            )

        if "resourceType" not in fhir_dict.keys() or "id" not in fhir_dict.keys():
            raise Invalid(
                "Invalid FHIR resource json is provided!\n{0}".format(fhir_json)
            )

    def _from_dict(self, dict_value):
        """ """
        self._pre_value_validate(dict_value)
        klass = None

        if self.model:
            # enforce use class from defined! this is kind of validation
            klass = self._model_class

        elif self.resource_type:
            klass = resource_type_str_to_fhir_model(self.resource_type)

        else:
            # relay on json value for resource type
            klass = resource_type_str_to_fhir_model(dict_value["resourceType"])

        # check constraint
        if klass.resource_type != dict_value.get("resourceType"):
            raise ConstraintNotSatisfied(
                "Fhir Model mismatched with provided resource type!\n"
                "`{0}` resource type is permitted but got `{1}`".format(
                    klass.resource_type, dict_value.get("resourceType")
                )
            )

        value = FhirFieldValue(obj=klass(dict_value))

        return value

    def _validate(self, value):
        """ """
        super(FhirField, self)._validate(value)

        if self.model_interface:
            try:
                verifyObject(
                    self._model_interface_class,
                    value.foreground_origin(),
                    False)

            except (BrokenImplementation, BrokenMethodImplementation, DoesNotImplement):

                t, v, tb = sys.exc_info()
                try:
                    reraise(Invalid(str(v)), None, tb)
                finally:
                    del t, v, tb

        if self.resource_type and value.resource_type != self.resource_type:
            msg = "Resource type must be `{0}` but we got {1} which is not allowed!".format(
                self.resource_type, value.resource_type
            )
            raise ConstraintNotSatisfied(msg)

        if self.model:
            klass = self._model_class

            if value.foreground_origin() is not None and not isinstance(
                value.foreground_origin(), klass
            ):
                msg = "Wrong fhir resource value is provided! Value should be object of {0!r} but got {1!r}".format(
                    klass, value.foreground_origin().__class__
                )
                raise WrongContainedType(msg)

        if value.foreground_origin() is not None:
            try:
                value.foreground_origin().as_json()
            except (FHIRValidationError, TypeError) as exc:
                msg = "There is invalid element inside fhir model object.\n{0!s}".format(
                    exc
                )
                t, v, tb = sys.exc_info()
                try:
                    reraise(Invalid(msg), None, tb)
                finally:
                    del t, v, tb


@configure.value_deserializer(IFhirField)
def fhir_field_deserializer(fhirfield, value, context=None):
    """ """
    if value in (None, ""):
        return None

    if isinstance(value, str):
        return IFhirField(fhirfield).from_unicode(value)
    elif isinstance(value, dict):
        return IFhirField(fhirfield).from_dict(value)
    else:
        raise ValueError(
            "Invalid data type({0}) provided! only dict or string data type is accepted.".format(
                type(value)
            )
        )


@configure.value_serializer(IFhirFieldValue)
def fhir_field_value_serializer(value):
    """ """
    if value:
        value = value.as_json()
    else:
        value = None

    return value


@configure.adapter(
    for_=(IFhirField, Interface, Interface),
    provides=ISchemaFieldSerializeToJson)
class DefaultFhirFieldSchemaSerializer(DefaultSchemaFieldSerializer):

    @property
    def field_type(self):
        return 'FhirField'
