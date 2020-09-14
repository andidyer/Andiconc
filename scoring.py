import math
import heapq
import re

import utils

#TOKEN SCORING
def score_token(results_container, token, measure='t-test', ignorecase=False, log=False, epsilon=1e-5, round_places=5):
    """Basically just a wrapper for all the other score token methods
    @posit-args:
        results_container: Results: the results object for the query
        token: str OR dict: the input token to score
    @kwargs:
        measure: str: the association measure to use.
            options are 'raw-freq', 'rel-freq', 'pmi', 'pmi-norm', 't-test' (default='t-test')
        ignorecase: bool: whether to search ignorecase as well as uppercase (default true)
        log: bool: return result as log (natural). only applies to raw-freq and rel-freq measures. default false
        epsilon: float: small non-zero value to avoid nasty maths domain errors.  default 1e-5
        round_places: float: number of decimal places to round to
    @returns:
        score: float: the association score
        """
    if measure == 'raw-freq':
        score = score_token_raw_freq(results_container, token, ignorecase, log, epsilon)
    elif measure == 'rel-freq':
        score = score_token_rel_freq(results_container, token, ignorecase, log, epsilon)
    elif measure == 'pmi':
        score = score_token_pmi(results_container, token, ignorecase, epsilon)
    elif measure == "pmi-norm":
        score = score_token_pmi_norm(results_container, token, ignorecase, epsilon)
    elif measure == 't-test':
        score = score_token_t_test(results_container, token, ignorecase, epsilon)
    else:
        raise NameError("Unrecognised association measure.  Choose from raw-freq, rel-freq, pmi, pmi-norm, t-test")
    return round(score, round_places)

def score_token_raw_freq(results_container, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5):
    """Scores using raw frequency association measure"""
    results_container.empty_sanity_check()
    raw_freq = results_container.n_token_query(token, ignorecase=ignorecase)
    if not log:
        return raw_freq
    else:
        logscore = math.log(max(epsilon, raw_freq))
        return round(logscore, round_places)

def score_token_rel_freq(results_container, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5):
    """Scores using relative frequency association measure"""
    results_container.empty_sanity_check()
    raw_freq = results_container.n_token_query(token, ignorecase=ignorecase)
    if not log:
        score = raw_freq / results_container.n_words() #Fine to just return P=0
    else:
        score = math.log(max(epsilon, raw_freq) / results_container.n_words())
    return round(score, round_places)

def score_token_pmi(results_container, token, ignorecase=True, epsilon=1e-10, round_places=5):
    """Scores using pointwise mutual information (PMI) association measure"""
    results_container.empty_sanity_check()

    raw_freq = results_container.n_token_query(token, ignorecase=ignorecase)
    raw_freq = max(raw_freq, epsilon) #Avoids math domain error from zero query-word matches

    #OLD IMPLEMENTATION
    #P_query_word = raw_freq / self._n_words_()
    #P_query = self._n_query_() / self._n_words_()
    #P_word = self._n_word_occur_(token, ignorecase=ignorecase) / self._n_words_()

    nwords = results_container.n_words()
    nq = results_container.n_query()
    nw = results_container.n_token_occur(token, ignorecase=ignorecase)

    expression = (raw_freq * nwords**2) / (nwords * (nq*nw)) #Simplification of the expression

    score = math.log2(expression)
    return round(score, round_places)

def score_token_pmi_norm(results_container, token, ignorecase=True, epsilon=1e-10, round_places=5):
    """Scores using normalised pointwise mutual information (NPMI) association measure"""
    results_container.empty_sanity_check()

    raw_freq = results_container.n_token_query(token, ignorecase=ignorecase)
    raw_freq = max(raw_freq, epsilon)  # Avoids math domain error from zero query-word matches

    P_query_word = raw_freq / results_container.n_words()

    pmi = score_token_pmi(results_container, token, ignorecase=ignorecase)
    score = pmi / -math.log2(P_query_word)
    return round(score, round_places)

def score_token_t_test(results_container, token, ignorecase=True, epsilon=1e-10, round_places=5):
    """Scores using t-test association measure"""
    results_container.empty_sanity_check()

    raw_freq = results_container.n_token_query(token, ignorecase=ignorecase)
    raw_freq = max(raw_freq, epsilon)  # Avoids math domain error from zero query-word matches

    P_query_word = raw_freq / results_container.n_words()
    P_query = results_container.n_query() / results_container.n_words()
    P_word = max(epsilon, results_container.n_token_query(token, ignorecase=ignorecase) / results_container.n_words())

    score = (P_query_word - P_query * P_word) / math.sqrt(P_query * P_word)
    return score

def _iter_score_set_tokens_(results_container, set_tokens, measure, log, ignorecase):
    """Iter through a set of unique words and score them according to specified measure"""
    for word in set_tokens:
        query = word._asdict()
        score = score_token(results_container, query, measure=measure, log=log, ignorecase=ignorecase)
        yield word, score

def top_n_collocations(results_container, n=100, features='form upos', measure='pmi', log=False, ignorecase=True, count_negatives=False, min_freq=0, bottom=False):
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
        set_words = utils._unique_token_set_(features, match_list=results_container.target_all(), min_freq=min_freq, ignorecase=ignorecase)
    else:
        set_words = utils._unique_token_set_(features, match_list=results_container.target_in_context, min_freq=min_freq, ignorecase=ignorecase)

    n = len(set_words) if n == None else n


    words_and_scores_gen = _iter_score_set_tokens_(results_container, set_words, measure, log, ignorecase)
    if bottom:
        n_top = heapq.nsmallest(n, words_and_scores_gen, key=lambda x: x[1])
    else:
        n_top = heapq.nlargest(n, words_and_scores_gen, key=lambda x: x[1])

    for i, (tok_nt,score) in enumerate(n_top):
        #Converts namedtuples to compact format for display
        vals = (val for val in tok_nt if type(val) == str)
        n_top[i] = ('_'.join(vals), score)

    return n_top