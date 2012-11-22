
import logging

import FuXi.Syntax.InfixOWL as owl
from Cheetah.Template import Template

from utils import *


def convert_tbox(signature,tbox):

    g = owl.Graph()
    g.parse(tbox)

    signature['name'] = capitalize1(frag_file(tbox))

    # collect classes
    for c in owl.AllClasses(g):
        class_s = frag_uri(str(c.identifier))
        to_check = signature['predefined']
        if signature.has_key('proposition') and signature.has_key('entity'):
           to_check = to_check + [signature['proposition'],signature['entity']]
        for d in to_check:
            if d['name'] == class_s: d['name'] = d['name']+'_p'
        signature['categories'].append( {'name': "mk"+class_s, 'type': class_s} )
 
    # collect properties
    for p in owl.AllProperties(g):
        p_dict = {'name': frag_uri(p.identifier)}
        for d in p.domain: p_dict['domain'] = capitalize1(frag_uri(d.identifier))
        if not p_dict.has_key('domain'): p_dict['domain'] = 'Thing'
        for r in p.range:  p_dict['range']  = capitalize1(frag_uri(r.identifier))
        if not p_dict.has_key('range'):  p_dict['range'] = 'Thing'
        
        signature['functions'].append(p_dict)


def render_tbox(signature,standalone):

    if standalone: tmpl = 'templates/abstract_standalone.tmpl'
    else:          tmpl = 'templates/abstract.tmpl'
    abstract_in  = open(tmpl,'r').read()
    out_file = '../test/out/'+signature['name']+'.gf'
    abstract_out = open(out_file,'w')
    t = Template(abstract_in,searchList=[signature])
    abstract_out.write(str(t))
    abstract_out.close()
    logging.info('Abstract syntax (T-Box): '+ out_file)


def convert_abox(abox,log):
    logging.info('Skipping A-Box... (Not implemented yet.)')

