import utils
import sys

from results import Results

class CorpusSearch:
    """Class object for searching the corpus.  Not sure if
         this needs to be a proper object or just a
         namespace."""

    def __init__(self):
        pass

    def collocations(self, query, treebank):
        """Collocations finder.

        @args:
             query: dict - A dictionary object detailing the target token
                  attributes and context
             treebank: iterable - the corpus to search through.
        @output:
             results_container: Results - A container for the search
                  results

        This function will parse a query into two parts:
            Target:
                This is the specification of the type of token that is being
                searched for.  For example, if the query is something like
                {"deprel": "obj", "upos": "NOUN"}, it will only look at tokens
                that match these attributes.
                In a query with recursive sub-queries, this is the top layer
                exclusively, disregarding any head_ or dep_ searches.
            Context:
                This is the context of the target token; the sub-queries of the
                Target.  Context is a pseudo-query, where the top level is empty
                and the sub-query levels are preserved.

        The results container will be instantiated before the corpus search starts,
        and then it will be added to.

        If the search returns no target level results and is thus empty, the results
        container will not be returned and the method will instead return None.
        """


        # parse the query into target and context
        context = {k: v for (k, v) in query.items() if k in ("head_search",
            "child_search", "regex", "ignorecase")}

        target = {k: v for (k, v) in query.items() if k not in ("head_search",
            "child_search")}

        #This container will hold the results of the search, and
        #will be the driver for various stats stuff
        results_container = Results()

        # Treebank must be iterable, but may be generator
        for sent in treebank:

            #Preprocess sents by adding required attributes for navigation
            utils._map_tokens(sent)
            utils._assign_children(sent)

            #Context matches is a small bit of dynamic programming to reduce recursion
            context_matches = []
            for tok in sent:

                if utils.is_match(tok, sent, **context):
                    context_matches.append(tok.id)

            #Second loop is where the actual stuff happens.
            for tok in sent:
                if utils.is_match(tok, sent, **target):
                    # Instance of target sans recursive context
                    results_container.target_all.append(tok)
                    if tok.id in context_matches:
                        #This is a match of target and recursive context
                        results_container.target_in_context.append(tok)
                        results_container.sentences.append(sent)

        if results_container._is_empty_():
            print('Query returned no matches', file=sys.stderr)
            return None
        else:
            print(results_container, file=sys.stderr)
            return results_container