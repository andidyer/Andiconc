import re
from collections import namedtuple, Counter
import time

#TODO:
#   1. Extend child_search to be able to search for multiple instances of a pattern
#       E.g. "A token with two oblique dependants"
#   2. Abstract form and lemma match to a single function, accepting ignorecase and regex as arguments
#   3. Add linear (surface order) window search

def is_match(token, tree, deprel=None, form=None, lemma=None,
             upos=None, xpos=None,
             head_search=None, child_search=None,
             regex=False, ignorecase=False):
    """The basic function for finding tokens that match the query.
    This function should be used for both collocation searches and
    concordancing.

    @posit-args:
        token: pyconll.Token: A pyconll token object. This will need to have been extended with a
                children attribute.
        tree: pyconll.Sentence: A pyconll sentence.  Note that this will need to have been
                extended with a map attribute.

    @kwargs:
        deprel: str: The target deprel
        form: str: The target form
        lemma: str: The target lemma
        upos: The target upos
        xpos: The target xpos

        head_search: dict: A kwargs dict of the specified attributes of the token's head.
                    Uses same keywords as this
        child_search: list: A list of kwargs dicts of the specified attributes of the token's children.
                    Uses same keywords as this.

        regex: bool: Whether to use regular expression matching for form and lemma
        ignorecase: bool: Whether the search should be case-sensitive

    @return:
        bool: True/False"""

    if deprel != None:
        try:
            deprel_match = re.match(deprel, token.deprel)
        except TypeError:  # This will be a token without a deprel, like a bridge
            return False  # or an enhanced dependency
        if not deprel_match:
            return False

    if upos != None:
        if token.upos != upos:
            return False

    if xpos != None:
        if token.xpos != xpos:
            return False

    if form != None:

        form_x = form.lower() if ignorecase else form
        form_y = token.form.lower() if ignorecase else token.form

        if regex:
            form_match = re.fullmatch(form_x, form_y)
            if not form_match:
                return False
        elif form_x != form_y:
            return False

    if lemma != None:

        lemma_x = lemma.lower() if ignorecase else lemma
        lemma_y = token.lemma.lower() if ignorecase else token.lemma

        if regex:
            lemma_match = re.fullmatch(lemma_x, lemma_y)
            if not lemma_match:
                return False
        elif lemma_x != lemma_y:
            return False

    if head_search != None:
        head_search['regex'] = regex
        head_search['ignorecase'] = ignorecase
        if token.head == '0':
            return False  # Exclude root node; this is the predicate
        elif token.head == None:
            return False  # Will be a bridge or an ED.
        head_tok = tree.map[token.head]
        if not is_match(head_tok, tree, **head_search):
            return False

    if child_search != None:
        for child_item in child_search:
            child_item['regex'] = regex
            child_item['ignorecase'] = ignorecase
            matches = []
            for i, cid in enumerate(token.children):
                child_token = tree.map[cid]
                matches += [is_match(child_token, tree, **child_item)]
            if not any(matches):
                return False

    #Returns true if it has passed all specified conditions.
    #If no conditions are specified, just returns true.
    return True

def feats_match(token, deprel=None, form=None, lemma=None,
             upos=None, xpos=None, ignorecase=False):
    """Function for checking that a token conll object matches a given pattern.
        Note that this does not check context within a sentence and so does not
        need a tree.  It also does not support regex; only ignorecase

        @posit-args:
            token: pyconll.token: A pyconll token object

        @kwargs:
            deprel: str: The deprel to check the token against
            form: str: The form to check the token against
            lemma: str: The lemma to check the token against
            upos: str: The UPOS to check the token against
            xpos: str: The XPOS to check the token against
            ignorecase: bool: Whether to ignore case (case insensitive) when matching form

        @return:
            bool: True/False
    """

    if form != None:
        form_x = form.lower() if ignorecase else form
        form_y = token.form.lower() if ignorecase else token.form
        if form_x != form_y:
            return False

    if lemma != None:
        lemma_x = lemma.lower() if ignorecase else lemma
        lemma_y = token.lemma.lower() if ignorecase else token.lemma
        if lemma_x != lemma_y:
            return False

    if deprel != None:
        try:
            deprel_match = re.match(deprel, token.deprel)
        except TypeError:  # This will be a token without a deprel, like a bridge
            return False  # or an enhanced dependency
        if not deprel_match:
            return False

    if upos != None:
        if token.upos != upos:
            return False

    if xpos != None:
        if token.xpos != xpos:
            return False

    return True

def _unique_token_set_(features, match_list, ignorecase=False, min_freq=0):
    """Given a list of features and an iterable of tokens, iterates through the tokens and adds them
        to a set as namedtuples.  These named tuples contain the attributes form, lemma, upos, xpos, and deprel.
        If a feature is not specified, when the namedtuple attribute for that feature will be None.

        Private function, mainly used for top_n_collocations

        @posit-args:
            features: iterable: An iterable of token feature attributes to specify
            match_list: iterable: An iterable of pyconll.Token objects"""

    global counter_out
    counter_out = Counter()
    for token in match_list:
        # make dict to load into the namedtuple
        mydict = {}
        for feat in features:
            feat_value = getattr(token, feat)
            if ignorecase and feat == 'form':
                feat_value = feat_value.lower()
            mydict[feat] = feat_value
        token_nt = token_namedtuple(**mydict)  # Namedtuple
        counter_out.update([token_nt])  # Can add to set because it's immutable

    return set(k for k, v in counter_out.items() if v >= min_freq)

def _map_tokens(tree):
    """Assigns map attribute to tree"""
    tree.map = {}  # Simple dictionary to map IDs to tokens.
    for tok in tree:
        tok.children = []  # Add children attribute
        tree.map[tok.id] = tok  # map token ID to token object pointer


def _assign_children(tree):
    """Assigns child attribute to tokens in tree

    Assumes _map_tokens has already been called on tree"""
    for tok in tree:
        try:
            head_tok = tree.map[tok.head]
            head_tok.children += [tok.id]  # Populate children for whole tree
        except KeyError:
            pass


def _make_token_query_(token, ignorecase=False):
    """Coerces word to a dictionary query.
        word: int OR dict: the word to search for in the target matches.  If int, returns a dict
                containing form and ignorecase.  If dict, returns a dict with the specified features
                plus ignorecase"""
    if isinstance(token, str):
        tokenquery = {"form": token, "ignorecase": ignorecase}
    elif isinstance(token, dict):
        tokenquery = {k:v for (k,v) in token.items() if k in ['form','lemma','upos','xpos','deprel']}
        tokenquery["ignorecase"] = ignorecase
    else:
        raise TypeError('token parameter must be either a string or a dict')

    return tokenquery

def top_n_sublist(iterable, n=100, key=lambda x: x, reverse=False):
    """Function for finding top N of the iterable while holding only i<=N items in memory at a time"""
    raise NotImplementedError("Not implemented yet")

class OOVError(Exception):
    pass

class EmptyQueryError(Exception):
    pass

#namedtuple for the collocation search
token_namedtuple = namedtuple('token', ['form', 'lemma', 'upos', 'xpos', 'deprel'], defaults=[None] * 5)