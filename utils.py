import re
from collections import namedtuple

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
        """

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
    """Function for checking that a token conll object matches a given pattern
        Note that this does not check context within a sentence and so does not
        need a tree.  It also does not support regex; only ignorecase"""

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

def top_n_sublist(iterable, n=100, key=lambda x: x, reverse=False):
    """Function for finding top N of the iterable while holding only i<=N items in memory at a time"""
    raise NotImplementedError("Not implemented yet")

class OOVError(Exception):
    pass

class EmptyQueryError(Exception):
    pass

#namedtuple for the collocation search
uniq_tok = namedtuple('token',['form','lemma','upos','xpos','deprel'], defaults=[None]*5)