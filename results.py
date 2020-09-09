#Not sure what needs importing here, but guess we'll find out.
import math
import heapq

import utils

class Results:
    def __init__(self):
        # Search results
        #TODO:  target_all should maybe be reduced to negatives (target match sans context), as
        #       this would be more space-efficient.  _n_words_ would count from adding
        #       target_in_context and target_all.  requires refactoring elsewhere too.
        self.target_in_context = []  # aka "query"
        self.sentences = []  # These ^ two go together
        self.target_all = []  # aka "retr", "words"

    def __str__(self):
        n_query = self._n_query_()
        n_words = self._n_words_()
        x = "Collocations search result containing {} full query matches over {} tokens".format(n_query, n_words)
        return x

    ##BASIC STATS RETRIEVERS##
    def _n_words_(self):
        """
        Number of tokens that match the target word criteria of the search,
        disregarding context.
        This is the divisor used for all other counts.
        """
        return len(self.target_all)

    def _n_query_(self):
        """
        Number of tokens that match the full query, both target and context.
        For any given word, this is the divisor for finding P(word|query).
        """
        return len(self.target_in_context)

    @staticmethod
    def makeTokenQuery(word, ignorecase=False):
        """Coerces word to a dictionary query.
            word: int OR dict: the word to search for in the target matches.  If int, returns a dict
                    containing form and ignorecase.  If dict, returns a dict with the specified features
                    plus ignorecase"""
        #TODO: Move to utils?
        if isinstance(word, str):
            tokenquery = {"form": word, "ignorecase": ignorecase}
        elif isinstance(word, dict):
            tokenquery = {k:v for (k,v) in word.items() if k in ['form','lemma','upos','xpos','deprel']}
            tokenquery["ignorecase"] = ignorecase

        return tokenquery

    def _n_word_occur_(self, word, ignorecase=False):
        """
        Number of times a specified word appears as a target level match.
        """
        tokenquery = self.makeTokenQuery(word, ignorecase=ignorecase)

        gen = (tok for tok in self.target_all if utils.feats_match(tok, **tokenquery))
        return len(list(gen))

    def _n_word_query_(self, word, ignorecase=True):
        """
        Number of times a specified word appears as a full query match.
        """

        # coerces to non-recursive query object with constrained feature options
        tokenquery = self.makeTokenQuery(word, ignorecase=ignorecase)

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

    def _OOV_sanity_check_(self, word, ignorecase=False):
        #TODO: Integrate this into the count functions to avoid an unnecessary first pass
        if self._n_word_occur_(word, ignorecase=ignorecase) == 0:
            raise utils.OOVError("This word does not appear among retrieved words; cannot perform further analysis")

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
            raise NameError("Unrecognised association measure.")
        return round(score, round_places)

    def score_token_raw_freq(self, token, ignorecase=True, log=False, epsilon=1e-10):
        """Scores using raw frequency association measure"""
        self._empty_sanity_check_()
        self._OOV_sanity_check_(token, ignorecase=ignorecase)
        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        if not log:
            return raw_freq
        else:
            return math.log(max(epsilon, raw_freq))

    def score_token_rel_freq(self, token, ignorecase=True, log=False, epsilon=1e-10):
        """Scores using relative frequency association measure"""
        self._empty_sanity_check_()
        self._OOV_sanity_check_(token, ignorecase=ignorecase)
        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        if not log:
            return raw_freq / self._n_words_() #Fine to just return P=0
        else:
            return math.log(max(epsilon, raw_freq) / self._n_words_())

    def score_token_pmi(self, token, ignorecase=True, epsilon=1e-10):
        """Scores using pointwise mutual information (PMI) association measure"""
        self._empty_sanity_check_()
        self._OOV_sanity_check_(token, ignorecase=ignorecase)

        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        raw_freq = max(raw_freq, epsilon) #Avoids math domain error from zero query-word matches

        #P_query_word = raw_freq / self._n_words_()
        #P_query = self._n_query_() / self._n_words_()
        #P_word = self._n_word_occur_(token, ignorecase=ignorecase) / self._n_words_()

        nwords = self._n_words_()
        nq = self._n_query_()
        nw = self._n_word_occur_(token, ignorecase=ignorecase)

        expression = (raw_freq * nwords**2) / (nwords * (nq*nw)) #Simplification of the expression

        return math.log(expression)

    def score_token_pmi_norm(self, token, ignorecase=True, epsilon=1e-10):
        """Scores using normalised pointwise mutual information (NPMI) association measure"""
        self._empty_sanity_check_()
        self._OOV_sanity_check_(token, ignorecase=ignorecase)

        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        raw_freq = max(raw_freq, epsilon)  # Avoids math domain error from zero query-word matches

        P_query_word = raw_freq / self._n_words_()

        pmi = self.score_token_pmi(token, ignorecase=ignorecase)
        return pmi / -math.log(P_query_word)

    def score_token_t_test(self, token, ignorecase=True, epsilon=1e-10):
        """Scores using t-test association measure"""
        self._empty_sanity_check_()
        self._OOV_sanity_check_(token, ignorecase=ignorecase)

        raw_freq = self._n_word_query_(token, ignorecase=ignorecase)
        raw_freq = max(raw_freq, epsilon)  # Avoids math domain error from zero query-word matches

        P_query_word = raw_freq / self._n_words_()
        P_query = self._n_query_() / self._n_words_()
        P_word = self._n_word_query_(token, ignorecase=ignorecase) / self._n_words_()

        return (P_query_word - P_query * P_word) / math.sqrt(P_query * P_word)

    def top_n_collocations(self, n=100, features='form upos', measure='pmi', ignorecase=True, count_negatives=False, bottom=False):
        #Whether we count from lowest or highest scores
        #Whether to count words which have zero co-occurrence with context
        #Useful in PMI, for example

        features = tuple(features.strip().split(' '))

        if count_negatives:
            set_words = self._unique_token_set_(features, match_list='all', ignorecase=ignorecase)
        else:
            set_words = self._unique_token_set_(features, match_list='full', ignorecase=ignorecase)

        n = len(set_words) if n == None else n


        words_and_scores_gen = self._iter_score_set_words_(set_words, measure, ignorecase)
        if bottom:
            n_top = heapq.nsmallest(n, words_and_scores_gen, key=lambda x: x[1])
        else:
            n_top = heapq.nlargest(n, words_and_scores_gen, key=lambda x: x[1])

        for i, (tok_nt,score) in enumerate(n_top):
            #Converts namedtuples to compact format
            vals = (val for val in tok_nt if type(val) == str)
            n_top[i] = ('_'.join(vals), score)

        return n_top

    def _iter_score_set_words_(self, set_words, measure, ignorecase):
        for word in set_words:
            score = self.score_token(word._asdict(), measure=measure, ignorecase=ignorecase)
            yield word, score

    def _unique_token_set_(self, features, match_list = 'full', ignorecase=False):
        """Takes a list of features and makes a set of unique namedtuples

            Private method, mainly used for top_n_collocations"""

        #TODO:
        #   1. Decide whether this should be a utils function agnostic of the list, or bound to the lists
        #       contained in the results object
        #   2. Maybe extend this to filter for min frequency?
        if match_list == 'full':
            listToSearch = self.target_in_context
        elif match_list == 'all':
            listToSearch = self.target_all

        set_out = set()
        for token in listToSearch:
            #make dict to load into the namedtuple
            mydict = {}
            for feat in features:
                feat_value = getattr(token, feat)
                if ignorecase and feat == 'form':
                    feat_value = feat_value.lower()
                mydict[feat] = feat_value
            token_nt = utils.uniq_tok(**mydict)
            set_out.add(token_nt)

        return set_out