import math
import heapq
import random
import utils
import json
import os

from collections import defaultdict

class Results:

    __slots__ = ['tokens_map', 'sentences_map', 'retrieved_tokens', 'sentences',
                 'corpus_word_count', 'corpus_sent_count',
                 'n_words','n_query']

    def __init__(self, tokens: list, sents: list, context_match_list: list,
                 corpus_word_count: int, corpus_sent_count: int):
        """Container for search results."""

        self.retrieved_tokens = []  # This will be a JSON list
        self.sentences = []  # These ^ two go together

        for tok, sent, cxt in zip(tokens, sents, context_match_list):
            self.enter_token_sent(tok, sent, cxt)

        # Corpus statistics
        self.corpus_word_count = corpus_word_count
        self.corpus_sent_count = corpus_sent_count

        self._obtain_counts()

    def is_empty(self):
        empty: bool = self.n_words <= 0
        return empty

    def get_n_query(self):
        """Returns the number of quert-matching tokens"""
        return self.n_query

    def get_n_words(self):
        """Returns number of tokens that match on just the target level"""
        return self.n_words

    def n_token_occur(self, token, ignorecase=False):
        """Returns number of times a given token occurs as a target level match.
        May be string or namedtuple"""
        if isinstance(token, str):
            mydict = {"form": token}
        elif isinstance(token, dict):
            mydict = token
        else:
            raise TypeError("token argument must be either string or dict")

        count = 0
        for tokenJSON in self.retrieved_tokens:
            x = utils.feats_match(tokenJSON, **mydict, ignorecase=ignorecase)
            if x:
                count += tokenJSON["occur"]["n_times_all"]
        return count

    def n_token_query(self, token, ignorecase=False):
        """Returns number of times a given token occurs as a context-level match.
        May be string or namedtuple"""
        if isinstance(token, str):
            mydict = {"form": token}
        elif isinstance(token, dict):
            mydict = token
        else:
            raise TypeError("token argument must be either string or dict")

        count = 0
        for tokenJSON in self.retrieved_tokens:
            x = utils.feats_match(tokenJSON, **mydict, ignorecase=ignorecase)
            if x:
                count += tokenJSON["occur"]["n_times_in_context"]
        return count

    def n_token_both(self, token, ignorecase=False):
        """Returns both occurrences in context and overall"""
        if isinstance(token, str):
            mydict = {"form": token}
        elif isinstance(token, dict):
            mydict = token
        else:
            raise TypeError("token argument must be either string or dict")

        in_cxt = 0
        in_all = 0
        for tokenJSON in self.retrieved_tokens:
            x = utils.feats_match(tokenJSON, **mydict, ignorecase=ignorecase)
            if x:
                in_cxt += tokenJSON["occur"]["n_times_in_context"]
                in_all += tokenJSON["occur"]["n_times_all"]
        return in_cxt, in_all

    def enter_token_sent(self, token, sent, context_match: bool):
        """Takes token and set objects and converts them to the appropriate JSON format"""

        # This creates a card that can be used to look up the index of the token
        token_nt = utils.token_namedtuple(token.form, token.lemma, token.upos, token.xpos, token.deprel)

        sentences_map = {}
        tokens_map = {}

        if context_match and sent.id not in sentences_map:
            sentences_map[sent.id] = len(sentences_map)
            self.sentences.append(sent.conll())  # Dump the sentence as a conll string

        # If the tok_string has not been seen before
        # Instantiates and appends to list, creates index entry
        if token_nt not in tokens_map:
            tokens_map[token_nt] = len(tokens_map)

            # TODO: Find some way to add feats
            token_dict = {"form": token.form,
                          "lemma": token.lemma,
                          "upos": token.upos,
                          "xpos": token.xpos,
                          "deprel": token.deprel,
                          "occur": {
                              "postings": [],
                              "ids": [],
                              "n_times_in_context": int(context_match),
                              "n_times_all": 1
                          }
                          }

            self.retrieved_tokens.append(token_dict)

        # If the tok_string has been seen before
        else:
            self.retrieved_tokens[tokens_map[token_nt]]["occur"]["n_times_all"] += 1
        if context_match:
            self.retrieved_tokens[tokens_map[token_nt]]["occur"]["postings"].append(sent.id)
            self.retrieved_tokens[tokens_map[token_nt]]["occur"]["ids"].append(token.id)
            self.retrieved_tokens[tokens_map[token_nt]]["occur"]["n_times_in_context"] += 1

    def dump_to_json(self, filename: str, make_folder=False, outputdir='/tmp/', **json_kwargs):
        """Dumps contents of this Results object to json files
        These will be kept in a folder of their own, by default in /tmp/
        or wherever the user designates"""
        foldername = ''
        if make_folder == True:
            foldername += '{}/'.format(filename)
            os.mkdir(outputdir+foldername)
        # Dumps list of retrieved tokens as JSON list of dicts
        with open(outputdir+foldername+filename+'-tokens.json', 'w') as fout:
            json.dump(self.retrieved_tokens, fout, **json_kwargs)
        with open(outputdir+foldername+filename+'-sentences.json', 'w') as fout:
            json.dump(self.sentences, fout, **json_kwargs)

    @staticmethod
    def init_from_json(jsondir, file_prefix):
        fullpath = '{0}/{1}'.format(jsondir, file_prefix)
        with open(fullpath+'-tokens.json') as fin:
            tokens = json.load(fin)

        with open(fullpath+'-sentences.json') as fin:
            sentences = json.load(fin)



    # Private methods
    def _obtain_counts(self):
        """After all tokens and sents have been added, counts up basic statistics: n tokens in context,
        n tokens any, n sentence"""
        self.n_words: int = 0
        self.n_query: int = 0
        for tokenJSON in self.retrieved_tokens:
            self.n_query += tokenJSON["occur"]["n_times_in_context"]
            self.n_words += tokenJSON["occur"]["n_times_all"]
