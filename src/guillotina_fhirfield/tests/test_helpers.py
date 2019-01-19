#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `guillotina_fhirfield.helpers` package."""
import pytest
from zope.interface import Invalid

import json
import uuid
from guillotina.db.oid import get_short_oid
from guillotina.component import get_utility
from guillotina.interfaces import ICatalogUtility
from guillotina_fhirfield.helpers import fhir_resource_mapping
from guillotina_fhirfield.variables import FHIR_ES_MAPPINGS_CACHE
from guillotina_fhirfield.variables import FHIR_RESOURCE_MAPPING_DIR
from .helpers import FHIR_FIXTURE_PATH


async def test_fhir_resource_mapping(dummy_guillotina):  # noqa: C901,E999
    """ """
    # test with normal
    # already had one! from tests/fhir_content.py
    assert len(FHIR_ES_MAPPINGS_CACHE) == 1

    patient_mapping = fhir_resource_mapping('Patient')

    with open(str(FHIR_RESOURCE_MAPPING_DIR / 'Patient.mapping.json'), 'r') as f:

        patient_mapping_dict = json.load(f)

    assert patient_mapping == patient_mapping_dict['mapping']
    assert len(FHIR_ES_MAPPINGS_CACHE) == 2

    # Test with non supporting FHIR Resource mapping
    address_mapping = fhir_resource_mapping('Address')

    with open(str(FHIR_RESOURCE_MAPPING_DIR / 'Resource.mapping.json'), 'r') as f:

        default_mapping_dict = json.load(f)

    assert address_mapping == default_mapping_dict['mapping']

    with pytest.raises(Invalid):

        fhir_resource_mapping('FakeResource')


async def test_elasticsearch_query_builder(es_requester):

    with open(str(FHIR_FIXTURE_PATH / 'Organization.json'), 'r', encoding='utf-8') as f:
        organization_json = json.load(f)

    async with es_requester as requester:
        id_ = str(uuid.uuid4())
        organization_json['id'] = id_
        resp, status = await requester(
            'POST',
            '/db/guillotina/',
            data=json.dumps({
                '@type': 'Organization',
                'title': 'Burgers University Medical Center',
                'id': id_,
                'organization_resource': organization_json
            })
        )

        catalog = get_utility(ICatalogUtility)
        assert status == 201

        # assert indexes were created
        index_ = 'guillotina-db-guillotina__organization-{0!s}'\
            .format(get_short_oid(resp['@uid']))
        result = await catalog.conn.indices.get_alias(index=index_)

        assert index_ in str(result)

        index_ = '1_guillotina-db-guillotina__organization-{0!s}'\
            .format(get_short_oid(resp['@uid']))

        result = await catalog.conn.indices.get_alias(index=index_)
        assert index_ in str(result)

        # test search
        data = (
            ('part-of:missing', 'true'),
            ('identifier', 'CPR|240365-0002'),
            ('identifier', 'CPR|240365-0001'),
            ('price-override', 'gt39.99|urn:iso:std:iso:4217|EUR')
        )
        response, status = await requester(
            'GET',
            '/db/guillotina/@fhir/Organization',
            params=data
        )
        assert status == 200
