#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `guillotina_fhirfield.helpers` package."""
import pytest
import ujson

from zope.interface import  Invalid

from guillotina_fhirfield.helpers import fhir_resource_mapping
from guillotina_fhirfield.variables import FHIR_RESOURCE_MAPPING_DIR
from guillotina_fhirfield.variables import FHIR_ES_MAPPINGS_CACHE


async def test_fhir_resource_mapping(dummy_guillotina):  # noqa: C901,E999
    """ """
    # test with normal
    # already had one! from tests/fhir_content.py
    assert len(FHIR_ES_MAPPINGS_CACHE) == 1

    patient_mapping = fhir_resource_mapping('Patient')

    with open(str(FHIR_RESOURCE_MAPPING_DIR / 'Patient.mapping.json'), 'r') as f:

        patient_mapping_dict = ujson.load(f)

    assert patient_mapping == patient_mapping_dict['mapping']
    assert len(FHIR_ES_MAPPINGS_CACHE) == 2

    # Test with non supporting FHIR Resource mapping
    address_mapping = fhir_resource_mapping('Address')

    with open(str(FHIR_RESOURCE_MAPPING_DIR / 'Resource.mapping.json'), 'r') as f:

        default_mapping_dict = ujson.load(f)

    assert address_mapping == default_mapping_dict['mapping']

    with pytest.raises(Invalid):

        fhir_resource_mapping('FakeResource')

