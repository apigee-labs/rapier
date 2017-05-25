from setuptools import setup
 
setup(
    name = 'rapier',
    packages = ['util'],
    entry_points = {
        'console_scripts': ['rapier = util.rapier:main']
        },
    version = '0.0.4',
    description = 'Generate OpenAPI specification from Rapier specification',
    long_description = 'Generate OpenAPI specification from Rapier specification',
    author = 'Martin Nally',
    author_email = 'mnally@apigee.com',
    url = 'https://github.com/apigee-labs/rapier',
    install_requires = ['PyYAML==3.11']
    )