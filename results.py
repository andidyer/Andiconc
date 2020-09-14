#Not sure what needs importing here, but guess we'll find out.
import math
import heapq
import random
import utils

class Results:
    def __init__(self, target_in_context: list, sentences: list, target_outta_context: list):
        """Container for search results."""
        self.target_in_context = target_in_context  # aka "query"
        self.sentences = sentences  # These ^ two go together
        self.target_outta_context = target_outta_context  # aka "retr", "words"

        self._n_query_ = len(self.target_in_context)
        self._n_words_ = len(self.target_in_context) + len(self.target_outta_context)

    def __str__(self):
        n_query = self.n_query()
        n_words = self.n_words()
        x = "Collocations search result containing {} full query matches over {} tokens".format(n_query, n_words)
        return x

    def target_all(self):
        """Concatenates the full query matches and target only matches, to give all target matches"""
        return self.target_in_context + self.target_outta_context

    ##BASIC STATS RETRIEVERS##
    def n_words(self):
        """
        Number of tokens that match the target word criteria of the search,
        disregarding context.
        This is the divisor used for all other counts.
        """
        #return len(self.target_all())
        return self._n_words_

    def n_query(self):
        """
        Number of tokens that match the full query, both target and context.
        For any given word, this is the divisor for finding P(word|query).
        """
        return self._n_query_

    def n_token_occur(self, token, ignorecase=False):
        """
        Number of times a specified token appears as a target level match.
        """
        tokenquery = utils._make_token_query_(token, ignorecase=ignorecase)

        i = 0
        gen = (tok for tok in self.target_all() if utils.feats_match(tok, **tokenquery))
        for _ in gen:
            i+= 1
        if i == 0:
            raise utils.OOVError("This word does not appear among retrieved words; cannot perform further analysis")
        else:
            return i

    def n_token_query(self, token, ignorecase=True):
        """
        Number of times a specified token appears as a full query match.
        """

        # coerces to non-recursive query object with constrained feature options
        tokenquery = utils._make_token_query_(token, ignorecase=ignorecase)

        gen = (tok for tok in self.target_in_context if utils.feats_match(tok, **tokenquery))
        return len(list(gen))

    def is_empty(self):
        """
        Returns bool: query found no matches.
        If true, all other functions are vacuous.
        """
        return self.n_query() < 1

    #SANITY CHECKS
    #TODO: Move these to utils or a new file
    def empty_sanity_check(self):
        """Raises an error if the query result is empty."""
        if self.is_empty():
            raise utils.EmptyQueryError("Query returned no matches; cannot perform any further analysis")

    #OTHER FUNCTIONS
    def sample_kwic(self, features='word', n=100, randomize=False):
        """Display n matching tokens and sentences"""
        raise NotImplementedError("Trying to think of a neat way to do this...")

    def sample_kwic_token(self, token, n=100, randomize=False):
        """Display n specified tokens and sentence contexts"""
        raise NotImplementedError("Trying to think of a neat way to do this...")



