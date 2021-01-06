import math
import heapq
import re
import sys

import utils

#TOKEN SCORING
def score_token(results_container, token,
                measure='t-test', ignorecase=False, log=False, epsilon=1e-10, round_places=5,
                _counts=None):
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
        score = score_token_raw_freq(results_container, token,
                                     ignorecase=ignorecase, log=log, epsilon=epsilon, _counts=_counts)
    elif measure == 'rel-freq':
        score = score_token_rel_freq(results_container, token,
                                     ignorecase=ignorecase, log=log, epsilon=epsilon, _counts=_counts)
    elif measure == 'conditional-probability':
        score = score_token_conditional_probability(results_container, token,
                                                    ignorecase=ignorecase, log=log, epsilon=epsilon, _counts=_counts)
    elif measure == 'pmi':
        score = score_token_pmi(results_container, token,
                                ignorecase=ignorecase, epsilon=epsilon, _counts=_counts)
    elif measure == "pmi-norm":
        score = score_token_pmi_norm(results_container, token,
                                     ignorecase=ignorecase, epsilon=epsilon, _counts=_counts)
    elif measure == 't-test':
        score = score_token_t_test(results_container, token,
                                   ignorecase=ignorecase, epsilon=epsilon, _counts=_counts)
    elif measure == 'dice':
        score = score_token_dice(results_container, token,
                                 ignorecase=ignorecase, log=log, epsilon=epsilon, _counts=_counts)
    else:
        raise NameError("Unrecognised association measure. \
         Choose from raw-freq, rel-freq, pmi, pmi-norm, t-test, dice")
    return round(score, round_places)


def score_token_raw_freq(results_container, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5, _counts=None):
    """Scores using raw frequency association measure"""
    if isinstance(_counts, tuple):
        rf, *_ = _counts
    else:
        rf = results_container.n_token_query(token, ignorecase=ignorecase)

    if not log:
        return rf
    else:
        logscore = math.log(max(epsilon, rf))
        return round(logscore, round_places)


def score_token_rel_freq(results_container, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5, _counts=None):
    """Scores using relative frequency association measure"""
    if isinstance(_counts, tuple):
        rf, *_, aw = _counts
    else:
        rf = results_container.n_token_query(token, ignorecase=ignorecase)
        aw = results_container.n_words
    rf = max(rf, epsilon)

    score = rf / aw #Fine to just return P=0
    if log:
        score = math.log2(rf/aw)
    return round(score, round_places)

def score_token_conditional_probability(results_container, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5, _counts=None):
    """Scores using conditional probability association measure (P(token|context)))"""
    if isinstance(_counts, tuple):
        rf, _, nq, _ = _counts
    else:
        rf = results_container.n_token_query(token, ignorecase=ignorecase)
        nq = results_container.n_query

    if not log:
        score = rf / nq
    else:
        score = math.log(max(epsilon, rf) / nq)
    return round(score, round_places)


def score_token_pmi(results_container, token, ignorecase=True, epsilon=1e-10, round_places=5, _counts=None):
    """Scores using pointwise mutual information (PMI) association measure"""

    if isinstance(_counts, tuple):
        rf, nw, nq, aw = _counts
    else:
        aw = results_container.n_words
        nq = results_container.n_query
        rf, nw = results_container.n_token_both(token, ignorecase=ignorecase)
    rf = max(rf, epsilon)

    expression = (rf * aw**2) / (aw * (nq*nw)) # Simplification of the expression

    score = math.log2(expression)
    return round(score, round_places)

def score_token_pmi_norm(results_container, token, ignorecase=True, epsilon=1e-10, round_places=5, _counts=None):
    """Scores using normalised pointwise mutual information (NPMI) association measure"""

    if isinstance(_counts, tuple):
        rf, nw, nq, aw = _counts
    else:
        aw = results_container.n_words
        nq = results_container.n_query
        rf, nw = results_container.n_token_both(token, ignorecase=ignorecase)
    rf = max(rf, epsilon)

    expression = (rf * aw**2) / (aw * (nq*nw))  # Simplification of the expression

    pmi = math.log2(expression)

    p_query_word = rf / aw
    pmi_norm = pmi / -math.log2(p_query_word)
    return round(pmi_norm, round_places)

def score_token_t_test(results_container, token, ignorecase=True, epsilon=1e-10, round_places=5, _counts=None):
    """Scores using t-test association measure"""

    if isinstance(_counts, tuple):
        rf, nw, nq, aw = _counts
    else:
        aw = results_container.n_words
        nq = results_container.n_query
        rf, nw = results_container.n_token_both(token, ignorecase=ignorecase)
    rf = max(rf, epsilon)

    p_query_word = rf / aw
    p_query = nq / aw
    p_word = nw / nw

    score = (p_query_word - p_query * p_word) / math.sqrt(p_query * p_word)
    return round(score, round_places)

def score_token_dice(results_container, token, ignorecase=True, log=False, epsilon=1e-10, round_places=5, _counts=None):
    if isinstance(_counts, tuple):
        rf, nw, nq, aw = _counts
    else:
        rf, nw = results_container.n_token_both(token, ignorecase=ignorecase)
        nq = results_container.n_query
        rf = max(rf, epsilon)

    dice = (2*rf) / (nw + nq)
    if log:
        dice = math.log2(dice)
    return round(dice, round_places)

def _iter_score_set_tokens_(results_container, set_tokens, measure, log, ignorecase):
    """Iter through a set of unique words and score them according to specified measure

    Utility function for top_n_collocations"""
    aw = results_container.n_words
    nq = results_container.n_query

    for (query, rf, nw) in set_tokens:
        _counts = (rf, nw, nq, aw)
        score = score_token(results_container, query, measure=measure, log=log, ignorecase=ignorecase, _counts=_counts)
        yield query, score

def top_n_collocations(results_container, n=100, features='form upos', measure='pmi', log=False, ignorecase=True, min_freq=0, min_cxt=1, bottom=False):
    """Finds the top N highest (or lowest) scoring collocations of the searched context by association measure.
    @posit-args:
        results_container: Results: the results object for the query

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


    set_words = utils.unique_token_set(features, match_list=results_container.retrieved_tokens,
                                       min_freq=min_freq, min_cxt=min_cxt, ignorecase=ignorecase)

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