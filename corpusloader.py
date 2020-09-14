import pyconll
import os

class CorpusLoader:
    def __init__(self):
        pass

    @staticmethod
    def iter_from_file(filename):
        """Simple port of pyconll iter_from_file function"""
        yield from pyconll.iter_from_file(filename)

    @staticmethod
    def iter_from_url(url):
        """Simple port of pyconll iter_from_url function"""
        yield from pyconll.iter_from_url(url)

    @staticmethod
    def iter_from_string(source):
        """Simple port of pyconll iter_from_string function"""
        yield from pyconll.iter_from_string(source)

    @staticmethod
    def iter_from_dir(directory, recursive=False):
        """
        Iters from all conll files in a directory.
        @args
            directory: str: The directory to search in. Probably needs to be fullpath.
            recursive: bool: If true, search subdirectories recursively.
        @output
            generator object that yields a sentence at a time
        """
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext == '.conllu':
                        fullpath = os.path.join(root, file)
                        yield from pyconll.iter_from_file(fullpath)

        else:
            files = os.listdir(directory)
            for file in files:
                _, ext = os.path.splitext(file)
                if ext == '.conllu':
                    fullpath = os.path.join(directory, file)
                    yield from pyconll.iter_from_file(fullpath)