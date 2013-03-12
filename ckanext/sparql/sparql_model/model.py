from sqlalchemy import types, Column, Table, MetaData, UnicodeText, create_engine, Boolean, ForeignKey
import vdm.sqlalchemy
from sqlalchemy.orm import mapper, relationship
from ckan.model.types import make_uuid
from ckan.model.package import Package, package_table, PACKAGE_NAME_MAX_LENGTH

import sqlalchemy

metadata = MetaData()

packageendpoint_table = Table('packageendpoint', metadata,
    Column('package_name', UnicodeText(PACKAGE_NAME_MAX_LENGTH), ForeignKey(package_table.c.name), primary_key=True),
    Column('endpoint_id', UnicodeText, ForeignKey('sparqlendpoint.id'), primary_key=True)
)

sparqlendpoint_table = Table('sparqlendpoint', metadata,
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


'''def __init__(self, name, sparqlurl, sparulurl, graph, storetype, username, passwd, isglobal, isdataallowed, isenabled):
    self.name = name
    self.sparqlurl = sparqlurl
    self.sparulurl = sparulurl
    self.graph = graph
    self.storetype = storetype
    self.username = username
    self.passwd = passwd
    self.isglobal = isglobal
    self.isdataallowed = isdataallowed
    self.isenabled = isenabled'''