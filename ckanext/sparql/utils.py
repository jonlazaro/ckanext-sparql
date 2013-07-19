# -*- coding: utf8 -*- 
import requests

def execute_query(query, resultformat, endpoint, graph=None):
	errors = False
	error_message = ''
	query_results = []

	index = query.lower().find('where')

	# Insert graph info in SPARQL query
	if endpoint.isglobal and graph:
		query = query[:index] + ' FROM <' + str(graph) + '> ' + query[index:]
	else:
		query = query[:index] + ' FROM <' + str(endpoint.graph) + '> ' + query[index:]

	resultformat = 'json' if resultformat == 'html' else resultformat
	params = {'query': str(query), 'format': str(resultformat)}
	r = requests.get(endpoint.sparqlurl, params=params)

	try:
		jsn = r.json()
		variables = tuple(jsn['head']['vars'])
		query_results.append(variables)

		for res in jsn['results']['bindings']:
			val = []
			for var in variables:
				val.append(res[var]['value'])
			query_results.append(tuple(val))


	except ValueError:
		print r.content

	#query_results = [('p', 'o'), (1, 2), (3, 4), (4, 3), (1, str(resultformat))]
	if graph:
		query_results.append((2, str(graph)))

	return query_results, errors, error_message