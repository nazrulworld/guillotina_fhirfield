# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""
from guillotina.schema import DottedName
from guillotina.schema import TextLine
from guillotina.schema.interfaces import IObject
from zope.interface import Attribute
from zope.interface import Interface


class IFhirResource(Interface):
    """ """
    resource_type = Attribute(
        'resource_type',
        'Resource Type',
    )
    id = Attribute(
        'id',
        'Logical id of this artifact.',
    )
    implicitRules = Attribute(
        'implicitRules',
        'A set of rules under which this content was created.',
    )
    language = Attribute(
        'language',
        'Language of the resource content.',
    )
    meta = Attribute(
        'meta',
        'Metadata about the resource',
    )

    def as_json():
        """ """


class IFhirField(IObject):
    """ """
    resource_type = TextLine(
        title='FHIR Resource Type',
        required=False,
    )
    model = DottedName(
        title='FHIR Resource Model from fhirclient',
        required=False,
    )
    model_interface = DottedName(
        title='FHIR Model Interface',
        required=False,
    )

    def from_dict(dict_value):
        """ """



class IFhirFieldValue(Interface):
    """ """
    _resource_obj = Attribute(
        '_resource_obj',
        '_resource_obj to hold Fhir resource model object.',
    )

    def stringify(prettify=False):
        """Transformation to JSON string representation"""

    def patch(patch_data):
        """FHIR Patch implementation: https://www.hl7.org/fhir/fhirpatch.html"""

    def foreground_origin():
        """Return the original object of FHIR model that is proxied!"""
