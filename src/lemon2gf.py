
import sys
import getopt
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


def run(argv):

    logging.basicConfig(filename='../test/out/lemon2gf.log',
                        filemode='w', 
                        level=logging.INFO,
                        format='%(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logging.getLogger('').addHandler(console)

    __init__()
    standalone = True
    tbox = None
    abox = None
    lexica = []

    try: opts,args = getopt.getopt(argv,"hl:t:a:",["help","apollo"]) 
    except getopt.GetoptError: __usage__(); sys.exit()

    if not opts: __usage__(); sys.exit()
    for opt,arg in opts:
        if opt == '--apollo': standalone = False
        if opt in ('-h','--help'): __usage__(); sys.exit()
        elif opt == '-t': tbox = arg
        elif opt == '-a': abox = arg
        elif opt == '-l': lexica.append(arg)

    if standalone:
       signature['proposition'] = dict(name='Proposition')
       signature['entity']      = dict(name='Entity')

    __generateGF__(signature,tbox,abox,lexica,standalone)


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


def __usage__():
    print "\nlemon2gf expects the following arguments:"
    print " -t <ontology_tbox>   # the ontology schema (an OWL/RDF file)" 
    print "(-a <ontology_abox>)  # the ontology instances (an OWL/RDF file)" 
    print "(-l <lexicon>)        # the lexicon (a lemon RDF file)"
    print "                      # (for several lexica, mark each one with the -l flag)" 
    print "(--apollo)            # generates a grammar that extends Core"
    print "                        (if this option is not specified, a standalone lexicon is generated)"



## MAIN #########

run(sys.argv[1:])
