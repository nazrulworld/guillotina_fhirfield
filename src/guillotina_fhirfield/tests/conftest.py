from pytest_docker_fixtures import images
images.configure(
        'elasticsearch',
        'elasticsearch', '5.6.14')
        # 'docker.elastic.co/elasticsearch/elasticsearch-oss', '6.5.4')
pytest_plugins = [
    'aiohttp.pytest_plugin',
    'pytest_docker_fixtures',
    'guillotina.tests.fixtures',
    'guillotina_elasticsearch.tests.fixtures',
    'guillotina_fhirfield.tests.fixtures'
]
