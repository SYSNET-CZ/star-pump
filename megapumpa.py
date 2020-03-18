#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import csv
import json
import os
from urllib.parse import urlparse

import requests
import unicodedata
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm, TqdmTypeError, TqdmKeyError

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # This is your Project Root
ERROR_LOG_FILE = "err.json"
ERROR_LOG_PATH = os.path.join(ROOT_DIR, "logs", ERROR_LOG_FILE)
DATA_DIR = os.path.join(ROOT_DIR, "data")
DUMP_PATH = os.path.join(DATA_DIR, "data.json")
CSV_PATH = os.path.join(DATA_DIR, "csv.json")
PCKG_PATH = os.path.join(DATA_DIR, "pckg.json")
API = 'f5f8bf22-799d-4b8f-852b-504577ff279c'  # plati od 2020-03-18
# API = "43fd2090-bb75-423c-889f-483d4de53888"


def chunks(source, num):
    for index in range(0, len(source), num):
        yield source[index:index + num]


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


h = {"Authorization": API}
INDEX_NAME = "star-ckan"
DOCTYPE = 'record'
es_client = Elasticsearch(['elasticsearch:9200'])

r = requests.get('http://ckan:5000/api/3/action/current_package_list_with_resources?limit=99999', headers=h)
pkdict = json.loads(r.text)
fo = open("data/pckg.json", "w")
fo.write(json.dumps(pkdict["result"], indent=2))
fo.close()
pid = {}
body = []
indices = []
for numr, j in enumerate(pkdict["result"]):
    pid[j["name"]] = j["id"]
    body.append({
        #      '_op_type': 'update',
        "_index": INDEX_NAME,
        "_type": DOCTYPE,
        "_id": j["id"],
        "_source": copy.deepcopy(j)})
    for d in j["resources"]:
        if d["format"].lower() == "csv":
            b = []
            url_source = urlparse(d["url"])  # puvodni URL datasetu
            url_docker = url_source._replace(netloc='ckan:5000', scheme='http')  # nahradit http://star.env.cz
            r = requests.get(url_docker.geturl(), headers=h)
            fo = open(CSV_PATH, "wb")
            fo.write(r.content)
            fo.close()
            try:
                content = r.content.decode("utf-8").split("\n")
            except OSError:
                content = r.content.decode("cp1250").split("\n")

            #          print(content)
            print(numr, j["name"], r.encoding, d["name"])
            if content[0].count(",") > content[0].count(";"):
                sep = ","
            else:
                sep = ";"
            date = d["last_modified"].split("T")[0] if d["last_modified"] else d["created"].split("T")[0]
            INDEX_NAME_REC = "star-data-" + j["name"] + "_" + date
            indices.append(INDEX_NAME_REC)
            for n, line in enumerate(csv.DictReader(content, delimiter=sep)):
                line_dict = dict(line)
                for m in line_dict:
                    if m is not None:
                        if not m.strip():
                            del line_dict[m]
                        elif m != strip_accents(m):
                            line_dict[strip_accents(m)] = line_dict[m]
                            del line_dict[m]
                        if line_dict[strip_accents(m)] == "":
                            line_dict[strip_accents(m)] = None
                line_dict["rec"] = {}
                for item in d:
                    line_dict["rec"][item] = d[item]
                    if line_dict["rec"][item] == "":
                        line_dict["rec"][item] = None
                line_dict["dataset"] = {}
                line_dict["dataset"]["db-name"] = j["name"]
                line_dict["dataset"]["db-title"] = j["title"]
                line_dict["dataset"]["organization"] = j["organization"]["title"]
                line_dict["dataset"]["id"] = j["id"]
                line_dict["tags"] = [w["name"] for w in j["tags"]]

                rd = {
                    "_index": INDEX_NAME_REC,
                    "_type": "cell",
                    "_id": d["id"] + "-" + str(n),
                    "_source": line_dict}
                body.append(rd)
#           exit()
fo = open(DUMP_PATH, "w")
fo.write(json.dumps(body, indent=2))
fo.close()

err_js = []
indices = list(set([w["_index"] for w in body]))
print(indices)
for i in indices:
    es_client.indices.delete(index=i, ignore=[400, 404])
    es_client.indices.create(index=i, ignore=400, body={"settings": {"index.mapping.ignore_malformed": True}})
CHUNK = 500
for chunk in tqdm(chunks(body, CHUNK), total=len(body) // CHUNK + 1):
    try:
        res = helpers.bulk(es_client, chunk, chunk_size=10000, request_timeout=120)
    except (TqdmTypeError, TqdmKeyError):
        err_js += chunk
fo = open(ERROR_LOG_PATH, "w")
fo.write(json.dumps(err_js, indent=2))
fo.close()
