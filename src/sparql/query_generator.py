
import os
from Cheetah.Template import Template


def __instantiate_queries__():

    # read map
    mapping = dict()
    f_map = open('../config/lingonto_map','r')
    for line in f_map.readlines():
        if line.strip():
           words = line.split()
           mapping[words[0]] = words[1:]

    # instantiate templates
    meta = 'meta/'
    for f_in in os.listdir(meta):
        if not f_in.endswith('~'):
           if '.' in f_in: 
                 filename = f_in[:f_in.rindex('.')]
           else: filename = f_in
           f_out = open(filename + '.sparql','w')
           t = Template(file=meta+f_in,searchList=[mapping])
           f_out.write(str(t))

def run():
    __instantiate_queries__()


run()
