import pyconll
import os

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
            for file in files:
                _, ext = os.path.splitext(file)
                if ext == '.conllu':
                    fullpath = os.path.join(directory, file)
                    yield from pyconll.iter_from_file(fullpath)

#Here we simply add this function to pyconll as a method.
pyconll.iter_from_dir = iter_from_dir