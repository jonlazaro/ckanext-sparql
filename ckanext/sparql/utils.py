# -*- coding: utf8 -*- 
import requests

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
