
import logging
from os.path import exists
import json
import re

from rdflib import Graph
from Cheetah.Template import Template

from utils import *


# Warning and error messages
language_error   = lambda x: "Lexicon "+x+" specifies either no language or more than one."
language_warning = lambda x: "There is no resource grammar for language "+x+". Resulting GF grammar will not compile."
too_many_pos_warning = lambda x: "The lexical entry "+x+" has more than one part of speech."
pos_or_frame_not_found_warning = lambda x: "No template for part of speech or frame (or both) in entry "+x+" found."
pos_not_found_warning = lambda x: "Unknown part of speech: "+x
complex_class_sense_warning = lambda x,y: "Found a complex class sense ("+x+") but cannot determine its argument; I use arg0 instead. This happened in entries: "+y
complex_property_sense_warning = lambda x,y: "Found a complex property sense ("+x+") with more than one subject argument. This will not work! I use arg1 instead. This happened in entries: "+y

# Query constructor
def q(x,y):
    f = 'sparql/'+x+'.sparql'
    if exists(f):
       return str(Template(file=f,searchList=[{'uri':y}]))
    else:
       return "FNF"

# default linearization categories
lincats = construct_lincats()


def convert_lexica(signature,lexica,gf_libs):

  lexicalizations = dict()

  # fill default lincats for categories and propositions
  for c in signature['categories']: c['lincat'] = lincats['category']
  signature['proposition'] = dict()
  signature['proposition']['lincat'] = print_lincat(lincats['proposition'])

  ## FOR ALL LEXICON FILES
  for lexicon_file in lexica:
    logging.info('Converting: ' + lexicon_file)

    # load RDF file
    g = Graph()
    file_ending = re.search('(\.\.)?.*\.([^\.]+)',lexicon_file).group(2)
    if file_ending in ('ttl','n3','nt'): g.parse(lexicon_file,format='n3')
    else: g.parse(lexicon_file)

    for lexicon in g.query(open('sparql/lexicon.sparql','r').read()).result:
        
        # determine language
        langs = g.query(q('language',str(lexicon))).result
        if len(langs) == 1:
           l = langs[0]
           if l in gf_libs.keys(): language = gf_libs[l]
           else: language = l ; logging.warning(language_warning(l))
        else: logging.error(language_error); system.exit()

        # build sense record from lexicon entries
        records = __construct_records__(g,lexicon,signature,dict())
        logging.info('Records:' + print_records(records))

        # build linearizations and opers

        linearizations = []
        opers = []

        for r in records:

            l = dict(ref=r['reference'],lin=[])
            args = ''
            if r.has_key('subjOfProp') and r.has_key('objOfProp'): 
               args += r['subjOfProp'] + ' '
               if type(r['objOfProp']) == list:
                  for o in r['objOfProp']: args += o + ' '
               else: args += r['objOfProp']
            elif r.has_key('isA'): args += r['isA']
            l['args'] = args

            for e in r['entries']:
                # render templates based on pos and synBehavior
                try: 
                   tmpl_path = 'templates/'+language+'/'+e['pos']+'.tmpl'
                   t_pos = str( Template(file=tmpl_path,searchList=[e,{'lang':language,'ref':r['reference']}]) )
                except (KeyError, IOError, OSError):
                   logging.warning(pos_or_frame_not_found_warning(str(e)))

                __split_lin_oper__(t_pos,l,opers,signature['name']+language+'.') 

            linearizations.append(l)

        __contract_lin_records__(linearizations)
        __fill_lin_records__(linearizations,signature)

        # collect linearizations and opers in lexicalizations    
        if lexicalizations.has_key(language):
           lexicalizations[language]['linearizations'].extend(linearizations)
           lexicalizations[language]['opers'].extend(opers)
        else:
           lexicalizations[language] = { 'linearizations': linearizations, 'opers': opers }
  ## END FOR ALL LEXICON FILES

  ## FOR ALL COLLECTED LEXICALIZATIONS
  # render concrete template as $domain_name$language.gf
  for language_key in lexicalizations.keys(): 

      t = Template(file='templates/concrete.tmpl')
      t.name = signature['name']
      t.lang = language_key
      t.signature = signature

      t.linearizations = lexicalizations[language_key]['linearizations']
      t.opers = lexicalizations[language_key]['opers']

      out_file = '../test/out/'+signature['name']+language_key+'.gf'
      concrete_out = open(out_file,'w')
      concrete_out.write(str(t))
      concrete_out.close()
      logging.info('Concrete syntax: ('+language_key+'): ' + out_file)
  ## END FOR ALL COLLECTED LEXICALIZATIONS


def __construct_records__(graph,lexicon,signature,renaming):

    senses = __collect_senses__(graph,lexicon,signature,renaming)
    __add_lexical_information__(graph,senses,renaming)

    return senses

def __collect_senses__(graph,lexicon,signature,renaming):

    senses = []
    # collect simple senses
    for entry in graph.query(q('entry',str(lexicon))).result:
        j = graph.query(q('sense',str(entry))).serialize(format='json')
        for b in json.loads(j)['results']['bindings']:
            sense = dict(entries=str(entry))
            for var in b.keys(): sense[var] = toGF(b[var]['value'])
            senses.append(sense)
    # collect complex senses
    for entry in graph.query(q('entry',str(lexicon))).result:
        j = graph.query(q('subsense',str(entry))).serialize(format='json')
        sense = dict(entries=str(entry),subsenses=[])
        for b in json.loads(j)['results']['bindings']:
            subsense = dict()
            for var in b.keys(): 
                if not var == 'sense': subsense[var] = toGF(b[var]['value'])
            sense['subsenses'].append(subsense)
        if  sense['subsenses']: 
            new_sense = __construct_reference_chain__(sense,signature)
            senses.append(new_sense)

    # group entries with the same sense(s)
    new_senses = []
    for s in senses:
        s['entries'] = [s.pop('entries',None)]
        if not new_senses: new_senses.append(s)
        else: 
           new = True
           for e in new_senses:
               e_entry = e.pop('entries',None)
               s_entry = s.pop('entries',None)
               if e['reference'] == s['reference']: 
                  e['entries'] = e_entry + s_entry; 
                  if __sense_args_differ__(e,s):
                      r = dict()
                      r[s['subjOfProp']] = e['subjOfProp']
                      r[s['objOfProp']]  = e['objOfProp']
                      renaming[s_entry[0]] = r
                  new = False; break
               else: 
                  e['entries'] = e_entry
                  s['entries'] = s_entry
           if new: new_senses.append(s)

    for s in senses: 
        # rename category constructors
        # and if class has an isA argument, move it from categories to functions
        swap = None
        for c in signature['categories']:
            if s['reference'] == c['type']: 
               s['reference'] =  c['name'] 
#               if s.has_key('isA'): swap = c
               break
#        if swap:
#           signature['categories'].remove(swap)
#           swap['domain'] = 
#           swap['range']  = c['type']
#           signature['functions'].append(swap)
        # process domain and range restrictions
        domain_res = s.has_key('propertyDomain')
        range_res  = s.has_key('propertyRange')
        if domain_res or range_res:
           for p in signature['functions']:
               if p['name'] == s['reference']:
                  new_p = dict()
                  new_p['name'] = s['reference'] = p['name']+'_restr'
                  new_p['argumentTypes'] = []
                  if domain_res: new_p['argumentTypes'].append( s['propertyDomain'] )
                  else: new_p['argumentTypes'].extend( p['argumentTypes'] )
                  if range_res:  new_p['argumentTypes'].append( s['propertyRange'] )
                  else: new_p['argumentTypes'].append( p['resultType'] )
                  signature['functions'].append(new_p)
                  break

    return new_senses

def __sense_args_differ__(s1,s2):
     if s1.has_key('subjOfProp') and s2.has_key('subjOfProp'):
        if not s1['subjOfProp'] == s2['subjOfProp']: return True
     if s1.has_key('objOfProp') and s2.has_key('objOfProp'):
        if not s1['objOfProp'] == s2['objOfProp']: return True
     return False


def __add_lexical_information__(graph,senses,renaming):

    pos_map = __read_pos_map__()

    for sense in senses:
        extended_entries = []
        for e in sense['entries']: 
            extended_e = dict()

            # canonical form
            __queryupdate__(graph,extended_e,'canonicalForm',str(e),toGF)

            # part of speech
            j = graph.query(q('pos',str(e))).serialize(format='json')
            for b in get_bindings(j,lambda x:x):
                if len(b.keys()) > 1: logging.warning(too_many_pos_warning(str(e)))
                for k in b.keys(): 
                    if pos_map.has_key(b[k]):
                       pos = pos_map[b[k]]
                       extended_e['pos'] = pos
                       # and part-of-speech-specific information
                       __queryupdate__(graph,extended_e,pos,str(e),toGF)
                    else: logging.warning(pos_not_found_warning(b[k]))

            # syntactic behaviors
            extended_e['synBehaviors'] = []
            j = graph.query(q('synBehavior',str(e))).serialize(format='json')
            for b in get_bindings(j,lambda x:x):
                b['frame'] = toGF(b['frame'])
                # query for argument-specific information (e.g. markers)
                for k in b.keys():
                    if k != 'frame':
                       if type(b[k]) == set: 
                          args = []
                          for arg in b[k]: 
                              a = dict(name=toGF(arg))
                              __queryupdate__(graph,a,'synArg',str(arg),toGF)
                              if not a in args: args.append(a)
                          b[k] = args
                       else: 
                          a = dict(name=toGF(b[k]))
                          __queryupdate__(graph,a,'synArg',str(b[k]),toGF)
                          b[k] = a 
                # renaming args
                if e in renaming.keys(): 
                   for v in b.values():
                       if type(v) == dict and v.has_key('name') and v['name'] in renaming[e].keys():
                          v['name'] = renaming[e][v['name']]
                # add syn behavior
                extended_e['synBehaviors'].append(b)                

            # put everything together again
            extended_entries.append(extended_e)
        sense['entries'] = extended_entries


def __read_pos_map__():
    pos_map = dict()
    f_pos_map = open('config/lingonto_pos_map','r')
    for line in f_pos_map.readlines():
        words = line.split()
        for w in words[1:]:
            pos_map[w] = words[0]
    return pos_map

def __queryupdate__(graph,d,query,string,fun):
    to_query = q(query,string)
    if (to_query != "FNF"):
        j = graph.query(to_query).serialize(format='json')
        for b in get_bindings(j,fun): d.update(b)



def __construct_reference_chain__(sense,signature): 

    new_sense = dict(entries=sense['entries'])
    subs = sense['subsenses']

    # extract categories
    cs  = []
    isA = []
    for s in subs:
        if isCat(s['reference'],signature):
           cs.append(subs.pop(subs.index(s)))
           if s.has_key('isA'): isA.append(s['isA'])

    # find all start and end terms
    start_s = []
    end_o   = []
    for s in subs:
        found_start = True
        found_end   = True
        for ss in subs:
            if ss['objOfProp']  == s['subjOfProp']: found_start = False
            if ss['subjOfProp'] == s['objOfProp']:  found_end   = False
        if found_start: start_s.append(s['subjOfProp'])
        if found_end  : end_o.append(s['objOfProp'])

    # construct all paths from start to end terms
    chains = []
    for start in start_s:
        stack = []
        # init stack
        chain = dict(reference=[],subjOfProp=start)
        stack.append( dict(chain=chain,i=start) )
        # recurse over stack
        while stack:
              step = stack.pop(0)
              chain = step['chain']
              i = step['i']
              if i in end_o:
                 chain['objOfProp'] = i
                 chains.append(chain)
              else:
                 for s in sense['subsenses']:
                     if s['subjOfProp'] == i: 
                        new_chain = chain.copy();    new_ref = [] 
                        for r in chain['reference']: new_ref.append(r)
                        new_ref.append(s['reference'])
                        new_chain['reference'] = new_ref
                        stack.append( dict(chain=new_chain,i=s['objOfProp']) )
    
    # build new sense by flattening chains
    ref = ''; args = []; result = 'Default'
    visited_subjs  = []; visited_objs = [];
    for chain in chains:
        if not ref == '':  ref += '_AND'
        if len(chain) > 1: ref += '_composition'
        for i,r in enumerate(chain['reference']): 
            ref += '_'+r
            is_first = i == 0; is_last = i == len(chain['reference'])-1
            if is_first or is_last:
               for p in signature['functions']:
                   if p['name'] == r:
                      if is_first and not chain['subjOfProp'] in visited_subjs: args.append(p['argumentTypes'][0])
                      if is_last  and not chain['objOfProp']  in visited_objs:  args.append(p['argumentTypes'][-1])
        visited_subjs.append(chain['subjOfProp'])
        visited_objs.append(chain['objOfProp'])
    if  ref.startswith('_'): ref = ref[1:]

    # add to signature
    if cs:
       if len(cs) == 1:
          ref = cs[0]['reference'] + '_WITH_' + ref
       if len(cs) > 1: 
          pref = 'union_'
          for c in cs: pref += c['reference'] + '_'
          pref += 'with_' + ref
       if args:
          signature['categories'].append( {'type': ref} )
          signature['functions'].append( {'name': 'mk'+ref, 'argumentTypes': args, 'resultType': ref} )
       else:
          signature['categories'].append( {'name': 'mk'+ref, 'type': ref} )
    else:
          if not args: args = ['owlThing']
          signature['functions'].append( {'name': ref, 'argumentTypes': args, 'resultType': result} )

    new_sense['reference'] = ref
    # determine arguments
    if   len(isA) == 1: new_sense['isA'] = isA[0]
    elif len(isA) > 1: 
         logging.warning(complex_class_sense_warning(ref,str(sense['entries'])))
         new_sense['isA'] = 'arg0'
    if   len(start_s) == 1: new_sense['subjOfProp'] = start_s[0]
    elif len(start_s) > 1: 
         logging.warning(complex_property_sense_warning(ref,str(sense['entries'])))
         new_sense['subjOfProp'] = 'arg1'
    if   len(end_o) == 1: new_sense['objOfProp'] = end_o[0]
    elif len(end_o) > 1:  new_sense['objOfProp'] = end_o

    return new_sense


## FUNCTIONS ON LINEARIZATIONS

def __split_lin_oper__(t_pos,l,opers,prefix):
    flag = 'off'
    partial = ''
    for line in t_pos.split('\n'):
        if not line.strip(): 
           if flag == 'oper': 
              if not partial in opers: opers.append(partial) 
              partial = ''
        else:
           m = re.match('^((lin)|(oper))\s*$',line.strip())
           if m: 
              if flag == 'lin':
                 opers.append(partial) 
                 partial = ''
              flag = m.group(1)
           else:
              if flag == 'lin':
                 lin = line.split('=')
                 if len(lin) == 1: l['lin'].append( {'value': lin[0].strip()} )
                 if len(lin) == 2: l['lin'].append( {'field': lin[0].strip(), 'value': [lin[1].strip()]} )
              if flag == 'oper':
                 partial += '\n' + line
    l['lin']  = filter(lambda x: x != '',l['lin'])
    opers     = filter(lambda x: x != '',opers)
    # avoid name clashes with resource grammars
    for lin in l['lin']: 
        for oper in opers:
            m = re.match('^\s*(\w+_\w+)\s?:\s?\w+\s*;',oper)
            if m: 
               if type(lin['value']) == list: 
                  new_value = []
                  for v in lin['value']:
                      mv = re.match('.*[^A-Za-z0-9\.]('+m.group(1)+')\W.*',v)
                      if mv: new_value.append(v.replace(mv.group(1),prefix+mv.group(1)))
                      else:  new_value.append(v)
                  lin['value'] = new_value
               else:
                      mv = re.match('.*[^A-Za-z0-9\.]('+m.group(1)+')\W.*',lin['value'])
                      if mv: lin['value'] = v.replace(mv.group(1),prefix+mv.group(1)) 


def __contract_lin_records__(linearizations):
    for lin in linearizations:
        lin['isRecord'] = True
        new_lin = []
        for l in lin['lin']: 
            if not l.has_key('field'): lin['isRecord'] = False; break
            if not new_lin: 
               new_lin.append(l)
            else:
               foundField = False
               for ll in new_lin:
                   if l.has_key('field') and ll.has_key('field') and l['field'] == ll['field']: 
                         ll['value'] += l['value']
                         foundField = True
                         break
               if not foundField and not l in new_lin: new_lin.append(l)
        if lin['isRecord']: lin['lin'] = new_lin
        else:
           new_lin = dict(value=[])
           for l in lin['lin']: 
               if not l['value'] in new_lin['value']: new_lin['value'].append(l['value'])
           lin['lin'] = [ new_lin ]
                   
def __fill_lin_records__(linearizations,signature):
    for lin in linearizations:
        # determine relevant fields
        relevant_fields = []
        if isProposition(lin['ref'],signature):
           for l in lincats['proposition']: relevant_fields.append(l.split(':')[0].strip())
           # fill all non-realized relevant fields with []
           for rf in relevant_fields:
               filled = False
               for l in lin['lin']:
                   if l.has_key('field') and l['field'] == rf: filled = True; break
               if not filled:
                  lin['lin'].append( dict(field=rf,value=[]) )


