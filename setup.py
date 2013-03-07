from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-sparql',
	version=version,
	description="SPARQL adapter for CKAN.",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Jon Lazaro',
	author_email='jlazaro@deusto.es',
	url='http://www.morelab.deusto.es/',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.sparql'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
    """
    [ckan.plugins]
        sparql=ckanext.sparql.plugin:SPARQLExtension
        
    [ckan.celery_task]
        tasks = ckanext.sparql.celery_import:task_imports
    """,
)
