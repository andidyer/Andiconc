from corpussearch import *
from corpusloader import CorpusLoader
import scoring


#First things first, let's get the treebank we're going to work with.  I prefer to have this as an iterable.
treebank_file = '/Users/andrew/Downloads/UD_English-EWT/en_ewt-ud-train.conllu'
treebank_dir = '/Users/andrew/Downloads/Brown_UD'
#treebank_file = '/Users/andrew/Downloads/debug.conllu'
treebank = CorpusLoader.iter_from_dir(treebank_dir)

#Now, let's define a query
query = {"upos": "VERB",
         "child_search":
            [
              {"deprel": "obj", "n_times":"3:100"}
            ]
         }

#We instantiate the CorpusSearch and call collocations() on the query and the treebank
results = CorpusSearch().collocations(query, treebank)

# These are some tests.  Some of these words appear frequently in context, some in the target results
# but not in context, some never at all.
print('test words')
measure = 'pmi'
for word in ('research','anything','deal','blah','work','homework','book','defeat','things','it','newspaper','me'):
    try:
        x = results.score_token(word, measure=measure)
        print('word: {0}\t\t{2}: {1:.5f}'.format(word, x, measure))
    except:
        print('word: {0}\t\t{1}: Undefined'.format(word, measure))

#These are the collocations we find.
print('Top 20 collocations by pmi-norm association measure:')
print(*scoring.top_n_collocations(results, n=50, measure='conditional-probability', count_negatives=False, min_freq=3), sep='\n')