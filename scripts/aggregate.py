#!/usr/bin/python
"""
Compute aggregated results by voting locals from desaggregated results by voting
tables.

Input:
  - CSV file with results by voting table.
  ('data/80222-solo-cba-resultados-diputados-nacionales.csv')
  - CSV file with voting locals.
  ('data/80268-escuelas-segun-la-dne.csv')

Output:
  - CSV file with reuslts by voting local.
  ('input/votos_establecimiento_cordoba_octubre.csv')
"""

import csv
import json

paso = False
if paso:
    results_input_filename = 'data/80267-paso-por-cirduito-y-mesa.csv'
    output_filename = 'input/votos_establecimiento_cordoba_paso.csv'
else:
    results_input_filename = 'data/80222-solo-cba-resultados-diputados-nacionales.csv'
    output_filename = 'input/votos_establecimiento_cordoba_octubre.csv'

#results_input_filename = 'data/80222-solo-cba-resultados-diputados-nacionales.csv'
#results_input_filename = 'data/80267-paso-por-cirduito-y-mesa.csv'
results_file = open(results_input_filename)
results_csvreader = csv.reader(results_file)

locals_input_filename ='data/80268-escuelas-segun-la-dne.csv'
locals_file = open(locals_input_filename)
locals_csvreader = csv.reader(locals_file)

locals = {}
locals_csvreader.next()
for row in locals_csvreader:
    # "id", "mesa_hasta", "codigo_distrito", "mesa_desde", "codigo_postal", "cant_mesas", "direccion",
    # "seccion","circuito","localidad","distrito","establecimiento","dne_distrito_id","dne_seccion_id"
    mesa_desde = int(row[3])
    mesa_hasta = int(row[1])
    local = locals.get(mesa_desde, {})
    local['mesa_desde'] = mesa_desde
    local['mesa_hasta'] = mesa_hasta
    
    locals[mesa_desde] = local

sorted_locals = sorted(locals.items(), key=lambda x: x[0])

# assert "input ordenado por codigo de mesa"

current_local_index = 0
current_local = sorted_locals[current_local_index][1]

results_csvreader.next()
results = {}
for row in results_csvreader:
    # "codigo_provincia","codigo_departamento","codigo_circuito","codigo_mesa","codigo_votos","votos"
    codigo_mesa = int(row[3])
    while codigo_mesa > current_local['mesa_hasta']:
        current_local_index += 1
        current_local = sorted_locals[current_local_index][1]
    
    # OUTPUT:
    # mesa_hasta votacion mesa_desde dne_distri vot_parcodigo total id dne_seccio the_geom cartodb_id created_at updated_at
    # claves: mesa_desde, voto_parcodigo:
    mesa_desde = current_local['mesa_desde']
    vot_parcodigo = int(row[4])
    key = (mesa_desde, vot_parcodigo)
    
    # result = results.get(key, {})    
    if key not in results:
        result = {}
        result['id'] = '_'
        result['dne_distri'] = 4 # hardcoded: Cordoba. usar 'codigo_provincia'?
        #result['dne_seccion'] = int(row[])
        #result['votacion'] = 'D'
    else:
        result = results[key]

    # columnas interesantes:
    result['mesa_desde'] = mesa_desde
    result['mesa_hasta'] = current_local['mesa_hasta']
    result['vot_parcodigo'] = vot_parcodigo
    result['total'] = result.get('total', 0) + int(row[5])    
    
    results[key] = result

sorted_results = sorted(results.items(), key=lambda x: x[0])

# write output:
#output_filename = 'input/votos_establecimiento_cordoba_octubre.csv'
#output_filename = 'input/votos_establecimiento_cordoba_paso.csv'
outf = open(output_filename, 'w')
csvwriter = csv.writer(outf)
#header = 'mesa_hasta,votacion,mesa_desde,dne_distri,vot_parcodigo,total,id,dne_seccio,the_geom,cartodb_id,created_at,updated_at'
header = 'mesa_desde,mesa_hasta,vot_parcodigo,total'
header = header.split(',')
csvwriter.writerow(header)

for key, result in sorted_results:
    # skip total numbers of voters:
    if result['vot_parcodigo'] not in [9001, 9002]:
        mesa_desde = result['mesa_desde']
        mesa_hasta = result['mesa_hasta']
        #vot_parcodigo = result['vot_parcodigo']
        # fill with zeros:
        vot_parcodigo = str(result['vot_parcodigo']).rjust(3, '0')
        total = result['total']
        
        row = [mesa_desde,mesa_hasta,vot_parcodigo,total]
        csvwriter.writerow(row)

outf.close()


#
# Add special entry for not geolocalized schools
#

geojson_input_filename = 'input/locales_cordoba_geocode.geojson'
geojson_input_file = open(geojson_input_filename)
geojson_input = json.load(geojson_input_file)
geomanual_list = geojson_input[u'features']
known_mesa_desde = set()
for entry in geomanual_list:
    known_mesa_desde.add(int(entry[u'properties'][u'mesa_desde']))

# read results
#results_input_filename = 'input/votos_establecimiento_cordoba_octubre.csv'
results_input_filename = output_filename
results_file = open(results_input_filename)
results_csvreader = csv.reader(results_file)

results_csvreader.next()

unknown = []
result = {}
for row in results_csvreader:
    # mesa_desde,mesa_hasta,vot_parcodigo,total
    mesa_desde = int(row[0])
    if mesa_desde not in known_mesa_desde:
        partido = row[2]
        votos = int(row[3])
        result[partido] = result.get(partido, 0) + votos
        unknown.append(mesa_desde)

results_file.close()

# append results
#results_output_filename = 'input/votos_establecimiento_cordoba_octubre.csv'
results_output_filename = output_filename
results_file = open(results_output_filename, 'a')
results_csvwriter = csv.writer(results_file)

for partido, votos in result.items():
    results_csvwriter.writerow([0, 0, partido, votos])

results_file.close()

