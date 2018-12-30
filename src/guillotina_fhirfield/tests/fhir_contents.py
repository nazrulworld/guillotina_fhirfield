from guillotina import configure
from guillotina.content import Folder
from guillotina.directives import index_field
from guillotina_elasticsearch.directives import index
from guillotina_elasticsearch.interfaces import IContentIndex

from guillotina_fhirfield.field import FhirField
from guillotina_fhirfield.helpers import fhir_resource_mapping
from guillotina_fhirfield.interfaces import IFhirContent


class IOrganization(IFhirContent, IContentIndex):

    index_field(
        'organization_resource',
        type='object',
        field_mapping=fhir_resource_mapping('Organization'),
        fhir_field_indexer=True,
        resource_type='Organization'

    )

    organization_resource = FhirField(
        title='Organization Resource',
        resource_type='Organization'
    )


@configure.contenttype(
    type_name="Organization",
    schema=IOrganization)
class Organization(Folder):
    """ """
    index(
        schemas=[IOrganization],
        settings={

        }
    )
    resource_type = 'Organization'
