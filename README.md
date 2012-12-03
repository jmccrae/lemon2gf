# lemon2gf

Transforms an ontology and a <a href="http://lemon-model.net/">lemon</a> lexicon into a <a href="http://www.grammaticalframework.org">GF</a> grammar.

## Test
```
$ python lemon2gf.py -o ../test/ontology/travelDomain.owl -a ../test/ontology/travelDomain_ABox.ttl -l ../test/lexicon/travelDomain_en.ttl
```

*Works with:*

* Python 2.7
* rdflib <3 (higher versions are not compatible with fuxi)
* <a href="http://code.google.com/p/fuxi/">fuxi</a> (infixOWL)
* <a href="http://www.cheetahtemplate.org/">Cheetah</a>

## Note

lemon2gf is work in progress, so things are constantly changing and might not always work (or at least not as expected). A proper documentation is under development.
