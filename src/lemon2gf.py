
import sys
import argparse
import logging

from ontology2abstract import *
from lexicon2concrete  import *
from utils import print_signature


gf_libs   = dict()
signature = dict( predefined   = [ dict(name='Thing',   lincat='CN'),
                                   dict(name='String',  lincat='CN'),
                                   dict(name='Integer', lincat='CN'),
                                   dict(name='Decimal', lincat='CN'),
                                   dict(name='DateTime',lincat='CN') ],
                   categories = [],
                   functions  = [],
                   funcats    = [],
                   entities   = []
                 )


def run():

    p = argparse.ArgumentParser(description='lemon2gf')
    p.add_argument('-t', action='store',  dest='tbox', 
                   help='path to the ontology schema (an OWL/RDF file)')
    p.add_argument('-a', action='store',  dest='abox', 
                    help='path to the ontology instances (an OWL/RDF file)')
    p.add_argument('-l', action='append', dest='lexica', default=[],
                    help='path to the lexicon (a lemon RDF file)')
    p.add_argument('--apollo', action='store_false', dest='standalone', default=True,
                    help='switches from a standalone grammar to one that extends Core (requires apollo)')

    args = p.parse_args()


    logging.basicConfig(filename='../test/out/lemon2gf.log',
                        filemode='w', 
                        level=logging.INFO,
                        format='%(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logging.getLogger('').addHandler(console)

    __init__()

    __generateGF__(signature,args.tbox,args.abox,args.lexica,args.standalone)


def __init__():
    # language mappings
    for line in open('config/iso639','r').readlines():
        ls = line.split(':')
        if len(ls) == 5: 
           for l in ls[0:4]: gf_libs[l.strip()] = ls[4].strip()


def __generateGF__(signature,tbox,abox,lexica,standalone):

    domain_name = ''

    if not tbox is None: convert_tbox(signature,tbox)
    else: logging.warning('No T-Box specified. Resulting GF grammar will not compile.')

    if not abox is None: convert_abox(abox,domain_name)

    if lexica: convert_lexica(signature,lexica,gf_libs,standalone)
    else: logging.warning('No lexicon specified.')
    
    logging.info('Signature:' + print_signature(signature))

    render_tbox(signature,standalone)
    
    logging.info('Done.')



## MAIN #########

run()
