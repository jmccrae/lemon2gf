
import sys
import getopt
from ontology2abstract import *
from lexicon2concrete  import *
from utils import print_signature


gf_libs   = dict()
signature = dict( proposition  = dict(name='Proposition'), 
                  entity       = dict(name='Entity'),
                  predefined   = [ dict(name='Thing',   lincat='CN'),
                                   dict(name='String',  lincat='CN'),
                                   dict(name='Integer', lincat='CN'),
                                   dict(name='Decimal', lincat='CN'),
                                   dict(name='DateTime',lincat='CN') ],
                   classes    = [],
                   funclasses = [],
                   functions  = [],
                   entities   = []
                 )


def run(argv):

    __init__()
    verbose = False
    tbox = None
    abox = None
    lexica = []

    try: opts,args = getopt.getopt(argv,"hl:t:a:",["help"]) 
    except getopt.GetoptError: __usage__(); sys.exit()

    for opt,arg in opts:
        if opt in ('-h','--help'): __usage__(); sys.exit()
        elif opt == '-t': tbox = arg
        elif opt == '-a': abox = arg
        elif opt == '-l': lexica.append(arg)

    __generateGF__(signature,tbox,abox,lexica)


def __init__():
    # language mappings
    for line in open('config/iso639','r').readlines():
        ls = line.split(':')
        if len(ls) == 5: 
           for l in ls[0:4]: gf_libs[l.strip()] = ls[4].strip()


def __generateGF__(signature,tbox,abox,lexica):

    domain_name = ''
    log = open('../test/out/log','wa')

    if not tbox is None: convert_tbox(signature,tbox,log)
    else: print '[Warning] No T-Box specified. Resulting GF grammar will not compile.'

    if not abox is None: convert_abox(abox,domain_name,log)

    if lexica: convert_lexica(signature,lexica,gf_libs,log)
    else: print '[Warning] No lexicon specified.'
    
    log.write(print_signature(signature))

    render_tbox(signature)
    
    print 'Done.'
    print 'Log written to: /test/out/log' 
    log.close()


def __usage__():
    print "\nlemon2gf expects the following arguments:"
    print " -t <ontology_tbox>   # the ontology schema (an OWL/RDF file)" 
    print "(-a <ontology_abox>)  # the ontology instances (an OWL/RDF file)" 
    print "(-l <lexicon>)        # the lexicon (a lemon RDF file)"
    print "                      # (for several lexica, mark each one with the -l flag)" 



## MAIN #########

run(sys.argv[1:])
