from corpussearch import *
from corpusloader import CorpusLoader
import scoring


#First things first, let's get the treebank we're going to work with.  I prefer to have this as an iterable.
treebank_file = '/Users/andrew/Downloads/UD_English-EWT/en_ewt-ud-train.conllu'
treebank_dir = '/Users/andrew/Downloads/Brown_UD'
#debug_file = '/Users/andrew/Downloads/debug.conllu'
#treebank = CorpusLoader.iter_from_dir(treebank_dir)
treebank = CorpusLoader.iter_from_file(treebank_file)

#Now, let's define a query
query = {"upos": "VERB",
         "child_search": [
             {"deprel": "iobj", "n_times": "+"},
             {"deprel": "obj", "n_times": "0"}
         ]}

# We instantiate the CorpusSearch and call collocations() on the query and the treebank
results = CorpusSearch().collocations(query, treebank)