# -*- coding: utf-8 -*-


def patch_fhir_base_model():
    """" """
    from zope.interface import implementer
    import fhir.resources.resource as fmr
    from guillotina_fhirfield.interfaces import IFhirResource
    # We force implement IFhirResource
    fmr.Resource = \
        implementer(IFhirResource)(fmr.Resource)


patch_fhir_base_model()
