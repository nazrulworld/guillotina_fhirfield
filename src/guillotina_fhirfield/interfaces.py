# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""
from guillotina.interfaces import IResource
from guillotina.schema import DottedName
from guillotina.schema import TextLine
from guillotina.schema.interfaces import IObject
from zope.interface import Attribute
from zope.interface import Interface


class IFhirContent(IResource):
    """ """
    resource_type = TextLine(readonly=True)


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
    resource_class = DottedName(
        title='FHIR Resource class from fhir.resources',
        required=False,
    )
    resource_interface = DottedName(
        title='FHIR Resource Interface',
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
