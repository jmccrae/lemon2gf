import re
import json


# string utilities

def capitalize1(string):
    return string[:1].upper() + string[1:]

def snakecase(string):
    return re.sub('\B([A-Z])','_\g<1>',string).lower()

def frag_uri(string):
    return re.match('.*/([^/]+\#)?([^/]+)$',string).group(2)

def frag_file(string):
    if '/' in string: string = string[string.rindex('/')+1:]
    return string[:string.rindex('.')].replace('.','_')

def toGF(string):
    if not '/' in string: return string
    else: return frag_uri(string)


# print 

def print_signature(signature):
       sig  = '\n----------------------------\n'
       sig += '\nDomain: ' + signature['name'] + '\n'
       if signature.has_key('proposition') and signature.has_key('entity'):
          sig += '\nProposition: ' + str(signature['proposition'])
          sig += '\nEntity:      ' + str(signature['entity'])
       sig += '\n\nPredefined: \n' 
       for p in signature['predefined']: sig += str(p) + '\n'
       sig += '\nCategories:\n'
       for c in signature['categories']:    sig += str(c) + '\n'
       sig += '\nFunctional categories:\n'
       if signature['funcats']:
          for c in signature['funcats']: sig += str(c) + '\n'
       else: sig += ' None.\n' 
       sig += '\nFunctions:\n '
       for f in signature['functions']:  sig += str(f) + '\n'
       sig += '----------------------------\n'
       return sig

def print_records(records):
       rec = '\n----------------------------\n'
       for r in records: rec += '\n' + str(r) +'\n'
       rec += '----------------------------\n'
       return rec

# list and dict utilities

def intersect(a,b):
     return list(set(a) & set(b))

def listupdate(d1,d2):
    for k in intersect(d1.keys(),d2.keys()):
        if type(d1[k]) == set: d1[k].add(d2[k])
        else: d1[k] = set( [d1[k],d2[k]] )


# tests

def isCat(s,signature):
    if s.startswith('mk'): return True
    for c in signature['categories'] + signature['funcats']:
        if c['type'] == s or c['name'] == s: return True
    return False

# lincat helper functions

def construct_lincats():
    lincats = dict()
    for label in ('category','proposition','entity'):
      lincats[label] = []
      for line in open('config/lincat_default_'+label,'r').readlines():
          if line.strip() != '': lincats[label].append(line.strip())
    return lincats

def print_lincat(fields):
    lincat = '{ '
    for field in fields:
        lincat += field + '; '
    lincat += ' }'
    return lincat

# json helper

def get_bindings(j,postprocessing):
    # build [ { key:value } ]
    bindings = []
    for b in json.loads(j)['results']['bindings']:
        d = dict()
        for key in b.keys():
            d[key] = postprocessing(b[key]['value'])
        bindings.append(d)
    # aggregate blank node
    new_bindings = []
    for b in bindings:
        if not new_bindings: new_bindings.append(b)
        else:
           if 'blank' in b.keys():
              for nb in new_bindings:
                  if 'blank' in nb.keys() and nb['blank'] == b['blank']:
                      listupdate(nb,b)
           else: new_bindings.append(b)
    # remove blank nodes and singletons
    for nb in new_bindings: 
        if nb.has_key('blank'): del nb['blank']
        for (k,v) in nb.items():
            if type(v) == set and len(v) == 1: nb[k] = next(iter(v))
    # return result
    return new_bindings
