#Not sure what needs importing here, but guess we'll find out.
import math
import heapq
import random
import utils

class Results:
    def __init__(self):
        """Container for search results."""
        #TODO: Lists as instantiation arguments
        # Search results
        self.target_in_context = []  # aka "query"
        self.sentences = []  # These ^ two go together
        self.target_outta_context = []  # aka "retr", "words"

    def __str__(self):
        n_query = self._n_query_()
        n_words = self._n_words_()
        x = "Collocations search result containing {} full query matches over {} tokens".format(n_query, n_words)
        return x

    def target_all(self):
        """Concatenates the full query matches and target only matches, to give all target matches"""
        return self.target_in_context + self.target_outta_context

    ##BASIC STATS RETRIEVERS##
    def _n_words_(self):
        """
        Number of tokens that match the target word criteria of the search,
        disregarding context.
        This is the divisor used for all other counts.
        """
        #return len(self.target_all())
        return len(self.target_in_context) + len(self.target_outta_context)

    def _n_query_(self):
        """
        Number of tokens that match the full query, both target and context.
        For any given word, this is the divisor for finding P(word|query).
        """
        return len(self.target_in_context)

    def _n_word_occur_(self, token, ignorecase=False):
        """
        Number of times a specified word appears as a target level match.
        """
        tokenquery = self._make_token_query_(token, ignorecase=ignorecase)

        i = 0
        gen = (tok for tok in self.target_all() if utils.feats_match(tok, **tokenquery))
        for _ in gen:
            i+= 1
        if i == 0:
            raise utils.OOVError("This word does not appear among retrieved words; cannot perform further analysis")
        else:
            return i

    def _n_word_query_(self, token, ignorecase=True):
        """
        Number of times a specified word appears as a full query match.
        """

        # coerces to non-recursive query object with constrained feature options
        tokenquery = utils._make_token_query_(token, ignorecase=ignorecase)

        gen = (tok for tok in self.target_in_context if utils.feats_match(tok, **tokenquery))
        return len(list(gen))

    def _is_empty_(self):
        """
        Returns bool: query found no matches.
        If true, all other functions are vacuous.
        """
        return self._n_query_() < 1

    #SANITY CHECKS
    #TODO: Move these to utils or a new file
    def _empty_sanity_check_(self):
        """Raises an error if the query result is empty."""
        if self._is_empty_():
            raise utils.EmptyQueryError("Query returned no matches; cannot perform any further analysis")

    #TOKEN SCORING
    def score_token(self, token, measure='t-test', ignorecase=False, log=False, epsilon=1e-5, round_places=5):
        """Basically just a wrapper for all the other score token methods
        @args:
            token: str: the input token to score
            measure: str: the association measure to use.
                options are 'raw-freq', 'rel-freq', 'pmi', 'pmi-norm', 't-test' (default='t-test')
            ignorecase: bool: whether to search ignorecase as well as uppercase (default true)
            log: bool: return result as log (natural). only applies to raw-freq and rel-freq measures. default false
            epsilon: float: small non-zero value to avoid nasty maths domain errors.  default 1e-5"""
        if measure == 'raw-freq':
            score = self.score_token_raw_freq(token, ignorecase, log, epsilon)
        elif measure == 'rel-freq':
            score = self.score_token_rel_freq(token, ignorecase, log, epsilon)
        elif measure == 'pmi':
            score = self.score_token_pmi(token, ignorecase, epsilon)
        elif measure == "pmi-norm":
            score = self.score_token_pmi_norm(token, ignorecase, epsilon)
        elif measure == 't-test':
            score = self.score_token_t_test(token, ignorecase, epsilon)
        else:
            raise NameError("Unrecognised association measure.  Choose from raw-freq, rel-freq, pmi, pmi-norm, t-test")
        return round(score, round_places)

    def score_token_raw_freq(self, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5):
        """Scores using raw frequency association measure"""
        self._empty_sanity_check_()
        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        if not log:
            return raw_freq
        else:
            logscore = math.log(max(epsilon, raw_freq))
            return round(logscore, round_places)

    def score_token_rel_freq(self, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5):
        """Scores using relative frequency association measure"""
        self._empty_sanity_check_()
        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        if not log:
            score = raw_freq / self._n_words_() #Fine to just return P=0
        else:
            score = math.log(max(epsilon, raw_freq) / self._n_words_())
        return round(score, round_places)

    def score_token_pmi(self, token, ignorecase=True, epsilon=1e-10, round_places=5):
        """Scores using pointwise mutual information (PMI) association measure"""
        self._empty_sanity_check_()

        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        raw_freq = max(raw_freq, epsilon) #Avoids math domain error from zero query-word matches

        #OLD IMPLEMENTATION
        #P_query_word = raw_freq / self._n_words_()
        #P_query = self._n_query_() / self._n_words_()
        #P_word = self._n_word_occur_(token, ignorecase=ignorecase) / self._n_words_()

        nwords = self._n_words_()
        nq = self._n_query_()
        nw = self._n_word_occur_(token, ignorecase=ignorecase)

        expression = (raw_freq * nwords**2) / (nwords * (nq*nw)) #Simplification of the expression

        score = math.log2(expression)
        return round(score, round_places)

    def score_token_pmi_norm(self, token, ignorecase=True, epsilon=1e-10, round_places=5):
        """Scores using normalised pointwise mutual information (NPMI) association measure"""
        self._empty_sanity_check_()

        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        raw_freq = max(raw_freq, epsilon)  # Avoids math domain error from zero query-word matches

        P_query_word = raw_freq / self._n_words_()

        pmi = self.score_token_pmi(token, ignorecase=ignorecase)
        score = pmi / -math.log2(P_query_word)
        return round(score, round_places)

    def score_token_t_test(self, token, ignorecase=True, epsilon=1e-10, round_places=5):
        """Scores using t-test association measure"""
        self._empty_sanity_check_()

        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        raw_freq = max(raw_freq, epsilon)  # Avoids math domain error from zero query-word matches

        P_query_word = raw_freq / self._n_words_()
        P_query = self._n_query_() / self._n_words_()
        P_word = max(epsilon, self._n_word_query_(token, ignorecase=ignorecase) / self._n_words_())

        score = (P_query_word - P_query * P_word) / math.sqrt(P_query * P_word)
        return score

    def _iter_score_set_tokens_(self, set_tokens, measure, log, ignorecase):
        """Iter through a set of unique words and score them according to specified measure"""
        for word in set_tokens:
            query = word._asdict()
            score = self.score_token(query, measure=measure, log=log, ignorecase=ignorecase)
            yield word, score

    def top_n_collocations(self, n=100, features='form upos', measure='pmi', log=False, ignorecase=True, count_negatives=False, min_freq=0, bottom=False):
        """Finds the top N highest (or lowest) scoring collocations of the searched context by association measure.
        @kwargs:
            n: int: the n highest or lowest
            features: str: A string specifying the token features to distinguish by.
            measure: str: The association measure.
            log: bool: Whether to give the logscore.  Only relevant for raw-freq and rel-freq association measures.
            ignorecase: bool: Whether to lowercase all results (i.e. "Book" == "book")
            count_negatives: bool: Whether to score words which have zero cooccurence with the context.
                                Useful (potentially) for pmi and pmi-norm.
                                Use with caution as this will greatly increase the search space and slow the search.
            min_freq: int: Minimum frequency filter so that only tokens which appear more than min_freq times in the
                            target_all list will be scored.  May avoid spurious results for some measures.
            bottom: bool: Collects n lowest scoring collocations instead.
                            Useful for pmi and pmi-norm, as it finds anti-collocations - context and token pairs
                            which occur often but rarely or never in conjunction (e.g. cxt="eat", token="name").

        @return:
            n_top: list: a list of tuples containing a token and its association score.
                        E.g.: ("year_NOUN_obl", 2.55321)


        """
        features = tuple(features.strip().split(' '))

        if count_negatives:
            set_words = utils._unique_token_set_(features, match_list=self.target_all(), min_freq=min_freq, ignorecase=ignorecase)
        else:
            set_words = utils._unique_token_set_(features, match_list=self.target_in_context, min_freq=min_freq, ignorecase=ignorecase)

        n = len(set_words) if n == None else n


        words_and_scores_gen = self._iter_score_set_tokens_(set_words, measure, log, ignorecase)
        if bottom:
            n_top = heapq.nsmallest(n, words_and_scores_gen, key=lambda x: x[1])
        else:
            n_top = heapq.nlargest(n, words_and_scores_gen, key=lambda x: x[1])

        for i, (tok_nt,score) in enumerate(n_top):
            #Converts namedtuples to compact format for display
            vals = (val for val in tok_nt if type(val) == str)
            n_top[i] = ('_'.join(vals), score)

        return n_top

    def sample_kwic(self, features='word', n=100, randomize=False):
        """Display n matching tokens and sentences"""
        raise NotImplementedError("Trying to think of a neat way to do this...")

    def sample_kwic_token(self, token, n=100, randomize=False):
        """Display n specified tokens and sentence contexts"""
        raise NotImplementedError("Trying to think of a neat way to do this...")



