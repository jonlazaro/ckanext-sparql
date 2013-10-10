import ckan.model as model

from ckan.controllers.api import ApiController as BaseApiController
from ckan.lib.celery_app import celery
from ckan.lib.base import abort
from ckan.model.package import Package
from ckan.lib.helpers import check_access

import ckan.authz

from ckanext.sparql.utils import execute_query, RESULT_FORMATS, SUPPORTED_RDF_SYNTAXES
from ckanext.sparql.sparql_model.model import SparqlEndpoint

import uuid

from pylons import c

#pkg_graph = request.url.replace('/edit/sparql', '') if self.packageendpoint.isglobal else self.packageendpoint.graph
#pkg_data = {
    #'id': id,
    #'sparulurl': self.packageendpoint.sparulurl,
    #'storetype': self.packageendpoint.storetype,
    #'graph': pkg_graph,
    #'username': self.packageendpoint.username,
    #'passwd': self.packageendpoint.passwd,
    #'isauthrequired': self.packageendpoint.isauthrequired,
#}
#celery.send_task('upload_rdf', args=[pkg_data, rdf, request.params['rdf_format']], task_id=str(uuid.uuid4()))

class SparqlApiController(BaseApiController):

    def get_global_enpoint(self):
        if not ckan.authz.Authorizer().is_sysadmin(unicode(c.user)):
            return self._finish_not_authz()

        globalendpoint = model.Session.query(SparqlEndpoint).filter_by(isglobal=True).first()

        if not globalendpoint:
            abort(404, 'No global endpoint defined.')

        pkg_data = {
            'id': 'GLOBAL',
            'sparulurl': globalendpoint.sparulurl,
            'storetype': globalendpoint.storetype,
            'graph': globalendpoint.graph,
            'username': globalendpoint.username,
            'passwd': globalendpoint.passwd,
            'isauthrequired': globalendpoint.isauthrequired,
        }

        return self._finish_ok(pkg_data)

    def sparql_query(self, package_id=None):
        request = self._get_request_data()

        if not 'query' in request:
            abort(400, 'Please provide a suitable query parameter')

        if not 'format' in request:
            format = 'json'
        elif request['format'] in RESULT_FORMATS:
            format = request['format']
        else:
            abort(400, 'Please provide a suitable format parameter')

        if package_id:
            endpoint = model.Session.query(SparqlEndpoint).filter(SparqlEndpoint.packages.any(Package.name == package_id)).first()
            if not endpoint:
                abort(404, 'No endpoint defined for provided package')
        else:
            endpoint = model.Session.query(SparqlEndpoint).filter_by(isglobal=True).first()
            if not endpoint:
                abort(404, 'No global endpoint defined.')

        query_results, content_type, errors, error_message = execute_query(request['query'], format, endpoint)

        if errors:
            abort(400, error_message)
        else:
            return self._finish_ok(response_data=query_results, content_type=content_type)

    def upload_rdf(self):
        request = self._get_request_data()

        if not 'package_id' in request:
            abort(400, 'Please provide a suitable package_id parameter')
        elif not check_access('package_update', {'id':request['package_id']}):
            return self._finish_not_authz()

        if not 'data' in request:
            abort(400, 'Please provide a suitable data parameter')

        if not 'format' in request or request['format'] not in SUPPORTED_RDF_SYNTAXES:
            abort(400, 'Please provide a suitable format parameter')

        endpoint = model.Session.query(SparqlEndpoint).filter(SparqlEndpoint.packages.any(Package.name == request['package_id'])).first()
        if not endpoint:
            abort(404, 'No endpoint defined for provided package')

        pkg_data = {
            'id': request['package_id'],
            'sparulurl': endpoint.sparulurl,
            'storetype': endpoint.storetype,
            'graph': endpoint.graph,
            'username': endpoint.username,
            'passwd': endpoint.passwd,
            'isauthrequired': endpoint.isauthrequired,
        }

        celery.send_task('upload_rdf', args=[pkg_data, request['data'], request['format']], task_id=str(uuid.uuid4()))

        return self._finish_ok('Uploading... Check progress in package web.')
