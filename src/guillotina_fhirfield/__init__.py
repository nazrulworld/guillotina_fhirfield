# -*- coding: utf-8 -*-
from guillotina import configure


"""Top-level package for guillotina_fhirfield."""

__author__ = """Md Nazrul Islam"""
__email__ = 'email2nazrul@gmail.com'
__version__ = '0.1.0a1'

app_settings = {
    # provide custom application settings here...
}


def includeme(root):
    configure.scan('guillotina_fhirfield.patch')
    configure.scan('guillotina_fhirfield.field')
