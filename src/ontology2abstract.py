
import logging

import FuXi.Syntax.InfixOWL as owl
import rdflib as rdf
from Cheetah.Template import Template

from utils import *


def convert_ontology(signature,tbox,abox):

    g = owl.Graph()
    g.parse(tbox)

    signature['name'] = capitalize1(frag_file(tbox))

    # collect classes
    for c in owl.AllClasses(g):
        class_s = frag_uri(str(c.identifier))
        for d in signature['predefined']:
            if d['name'] == class_s: d['name'] = d['name']+'_p'
        signature['categories'].append( {'name': 'mk'+class_s, 'type': class_s} )
 
    # collect properties
    for p in owl.AllProperties(g):
        p_dict = {'name': frag_uri(p.identifier), 'argumentTypes': [], 'resultType': 'Default'}
        did_something = False
        for d in p.domain: 
            p_dict['argumentTypes'].append( capitalize1(frag_uri(d.identifier)) )
            did_something = True
        if not did_something: p_dict['argumentTypes'].append('owlThing')
        did_something = False
        for r in p.range:  
           p_dict['argumentTypes'].append( capitalize1(frag_uri(r.identifier)) )    
           did_something = True   
        if not did_something: p_dict['argumentTypes'].append('owlThing')
        signature['functions'].append(p_dict)

    #collect individuals
    ga = None
    if not abox: ga = g
    else:
        if abox.endswith('.owl'):
           ga = owl.Graph()
           ga.parse(abox)
        elif abox.endswith('.rdf'):
           ga = rdf.Graph()
           ga.parse(abox)
        elif abox.endswith('.ttl') or abox[:-3] in ('.n3','.nt'):
           ga = rdf.Graph()
           ga.parse(abox,format='n3')
        else: 
           logging.warning('Unknown format of: ' + abox)
    if ga:
       for c in owl.AllClasses(g):
           for triple in ga.triples((None,rdf.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),c.identifier)):
               signature['entities'].append( {'name': frag_uri(str(triple[0])), 'type': frag_uri(str(c.identifier))} )



def render_ontology(signature):

    abstract_in  = open('templates/abstract.tmpl','r').read()
    out_file = '../test/out/'+signature['name']+'.gf'
    abstract_out = open(out_file,'w')
    t = Template(abstract_in,searchList=[signature])
    abstract_out.write(str(t))
    abstract_out.close()
    logging.info('Abstract syntax (T-Box): '+ out_file)

