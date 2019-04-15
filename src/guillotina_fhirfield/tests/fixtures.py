from guillotina import testing
from guillotina_elasticsearch.tests.fixtures import elasticsearch


def base_settings_configurator(settings):

    if 'applications' not in settings:
        settings['applications'] = list()

    if 'guillotina_elasticsearch' in settings['applications']:
        settings['applications'].append('guillotina_elasticsearch')

    settings['applications'].append('guillotina_fhirfield')
    settings['applications'].append('guillotina_fhirfield.tests.fhir_contents')

    settings['elasticsearch'] = {
        "index_name_prefix": "guillotina-",
        "connection_settings": {
            "hosts": ['{}:{}'.format(
                getattr(elasticsearch, 'host', 'localhost'),
                getattr(elasticsearch, 'port', '9200'),
            )],
            "sniffer_timeout": None
        }
    }
    settings["load_utilities"]["catalog"] = {
        "provides": "guillotina_elasticsearch.utility.IElasticSearchUtility",  # noqa
        "factory": "guillotina_elasticsearch.utility.ElasticSearchUtility",
        "settings": {}
    }


testing.configure_with(base_settings_configurator)
