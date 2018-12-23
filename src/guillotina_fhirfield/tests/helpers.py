# -*- coding: utf-8 -*-
import os
import pathlib

from guillotina_fhirfield.interfaces import IFhirResource


FHIR_FIXTURE_PATH = pathlib.Path(os.path.abspath(__file__)).parent / 'static' / 'FHIR'


class NoneInterfaceClass(object):
    """docstring for ClassName"""


class IWrongInterface(IFhirResource):
    """ """
    def meta():
        """ """
