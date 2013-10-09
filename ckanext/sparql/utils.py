# -*- coding: utf8 -*-
import requests
import json
import urlparse
import os
import ConfigParser

#Configuration load
config = ConfigParser.ConfigParser()
config.read(os.environ['CKAN_CONFIG'])

MAIN_SECTION = 'app:main'
PLUGIN_SECTION = 'plugin:sparql'

SITE_URL = config.get(MAIN_SECTION, 'ckan.site_url')
API_URL = urlparse.urljoin(SITE_URL, 'api/')
API_KEY = config.get(PLUGIN_SECTION, 'api_key')
CRON_HOUR = config.get(PLUGIN_SECTION, 'cron_hour')
CRON_MINUTE = config.get(PLUGIN_SECTION, 'cron_minute')
DATASET_URL = urlparse.urljoin(SITE_URL, 'dataset/')


def get_task_status(package_id):
    res = requests.post(
        API_URL + 'action/task_status_show', json.dumps({'entity_id': package_id, 'task_type': u'sparql', 'key': u'celery_task_status'}),
        headers = {'Authorization': API_KEY,
                   'Content-Type': 'application/json'}
    )

    if res.status_code == 200:
        return json.loads(res.content)['result']
    else:
        data = json.loads(res.content)
        if not data['error']['message'] == "Not found":
            print 'ckan failed to get task_status, status_code (%s), error %s' % (res.status_code, res.content)
        return {}

def get_package_list():
    res = requests.post(
        API_URL + 'action/package_list', json.dumps({}),
        headers = {'Authorization': API_KEY,
                   'Content-Type': 'application/json'}
    )

    if res.status_code == 200:
        return json.loads(res.content)['result']
    else:
        print 'ckan failed to get package list, status_code (%s), error %s' % (res.status_code, res.content)
        return ()

def update_task_status(task_info):
    print "Updating task status for entity_id %s" % task_info['entity_id']
    res = requests.post(
        API_URL + 'action/task_status_update', json.dumps(task_info),
        headers = {'Authorization': API_KEY,
                   'Content-Type': 'application/json'}
    )

    if res.status_code == 200:
        return json.loads(res.content)['result']
    else:
        print 'ckan failed to update task_status, status_code (%s), error %s' % (res.status_code, res.content)
        return None

def execute_query(query, resultformat, endpoint, graph=None):
    errors = False
    content_type = None
    error_message = ''
    query_results = []

    index = query.lower().find('where')

    # Insert graph info in SPARQL query
    if endpoint.isglobal and graph:
        query = query[:index] + ' FROM <' + str(graph) + '> ' + query[index:]
    else:
        from_clause = 'FROM <' + str(endpoint.graph) + '> ' if len(str(endpoint.graph)) > 0 else ' '
        query = query[:index] + from_clause + query[index:]

    result = 'json' if resultformat == 'html' else resultformat
    params = {'query': str(query), 'format': str(result)}

    try:
        r = requests.get(endpoint.sparqlurl, params=params)
        r.raise_for_status()
        if resultformat == 'html':
            jsn = r.json()
            variables = tuple(jsn['head']['vars'])
            query_results.append(variables)

            for res in jsn['results']['bindings']:
                val = []
                for var in variables:
                    val.append(res[var]['value'])
                query_results.append(tuple(val))
        else:
            content_type = r.headers['Content-Type']
            query_results = r.content

    except requests.exceptions.HTTPError as e:
        errors = True
        error_message = 'HTTP Error:', str(e)

    except requests.exceptions.ConnectionError as e:
        errors = True
        error_message = 'Unable to connect to the endpoint'

    except requests.exceptions.Timeout as e:
        errors = True
        error_message = 'Connexion timeout error'

    except requests.exceptions.TooManyRedirects  as e:
        errors = True
        error_message = 'Too many redirects in connection'

    return query_results, content_type, errors, error_message
