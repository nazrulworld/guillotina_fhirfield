from guillotina import configure
from guillotina.content import Folder
from guillotina.interfaces import IResource
from guillotina_fhirfield.field import FhirField


class IOrganization(IResource):
    organization_resource = FhirField(
        title='Organization Resource',
        resource_type='Organization'
    )


@configure.contenttype(
    type_name="Organization",
    schema=IOrganization)
class Organization(Folder):
    pass
