
import FuXi.Syntax.InfixOWL as owl
import rdflib as rdf
from Cheetah.Template import Template

from utils import frag_uri

import sys


def generate_lemon(f,l):

    g = None
    if f.endswith('.owl'):
       g = owl.Graph()
       g.parse(f)
    elif f.endswith('.rdf'):
       g = rdf.Graph()
       g.parse(f)
    elif f.endswith('.ttl') or f[:-3] in ('.n3','.nt'):
       g = rdf.Graph()
       g.parse(f,format='n3')
    else: print 'ERROR Unknown file format.'; system.exit()

    if g:
       signature = { 'language': l, 'individuals': [] }
       for triple in g.triples((None,rdf.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),None)):
           signature['individuals'].append( { 'uri': str(triple[0]), 'name': frag_uri(str(triple[0])), 'class': str(triple[2]), 'labels': dict() } )

       for i in signature['individuals']:
           for triple in g.triples((rdf.URIRef(i['uri']),rdf.URIRef("http://www.w3.org/2000/01/rdf-schema#label"),None)):
               i['labels'][triple[2].language] = str(triple[2])

       tmpl_file = open('templates/aux/abox_lexicon.tmpl','r').read()
       tmpl = Template(tmpl_file,searchList=[signature])
       out = open('../test/out/abox_'+l+'.ttl','w')
       out.write(str(tmpl))
       out.close()
          


## MAIN #### 

generate_lemon(sys.argv[1],sys.argv[2])
