# -*- coding: utf-8 -*-
from guillotina_fhirfield.interfaces import IFhirResource
import pathlib
import os


FHIR_FIXTURE_PATH = pathlib.Path(os.path.abspath(__file__)).parent / 'static' / 'FHIR'


class NoneInterfaceClass(object):
    """docstring for ClassName"""


class IWrongInterface(IFhirResource):
    """ """
    def meta():
        """ """
