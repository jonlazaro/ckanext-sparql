from sqlalchemy import Column, Table, MetaData, UnicodeText, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import mapper, relationship
from ckan.model.types import make_uuid
from ckan.model.package import Package, package_table, PACKAGE_NAME_MAX_LENGTH

from datetime import datetime

metadata = MetaData()

packageendpoint_table = Table('package_endpoint', metadata,
    Column('package_name', UnicodeText(PACKAGE_NAME_MAX_LENGTH), ForeignKey(package_table.c.name), primary_key=True),
    Column('endpoint_id', UnicodeText, ForeignKey('sparql_endpoint.id'), primary_key=True)
)

sparqlendpoint_table = Table('sparql_endpoint', metadata,
        Column('id', UnicodeText, primary_key=True, default=make_uuid),
        Column('name', UnicodeText),
        Column('sparqlurl', UnicodeText),
        Column('sparulurl', UnicodeText),
        Column('graph', UnicodeText),
        Column('storetype', UnicodeText),
        Column('username', UnicodeText, default=None),
        Column('passwd', UnicodeText, default=None),
        Column('isauthrequired', Boolean, unique=False, default=False),
        Column('isglobal', Boolean, unique=False, default=False),
        Column('isdataallowed', Boolean, unique=False, default=False),
        Column('isenabled', Boolean, unique=False, default=True)
)

rdfuploadinglog_table = Table('rdf_uploading_log', metadata,
    Column('id', UnicodeText, primary_key=True, default=make_uuid),
    Column('status', UnicodeText),
    Column('task_name', UnicodeText),
    Column('task_id', UnicodeText),
    Column('errors', UnicodeText),
    Column('time', DateTime, default=datetime.now),
    Column('endpoint_id', UnicodeText, ForeignKey('sparql_endpoint.id')),
    Column('package_name', UnicodeText(PACKAGE_NAME_MAX_LENGTH), ForeignKey(package_table.c.name))
)

class SparqlEndpoint(object):
    def __init__(self, *initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

mapper(SparqlEndpoint, sparqlendpoint_table, properties={
    'packages' : relationship(Package, secondary=packageendpoint_table, backref='endpoints')
    })

class RdfUploadingLog(object):
    def __init__(self, *initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

mapper(RdfUploadingLog, rdfuploadinglog_table)
