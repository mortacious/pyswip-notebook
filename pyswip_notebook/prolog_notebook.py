# The PrologNotebook class is derived from and uses code from the pyswip-package which is licensed under the  MIT license: 

# Copyright (c) 2007-2020 Yüce Tekol and PySwip contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import pyswip as pl
import uuid
import tempfile
import platform
from contextlib import contextmanager
import os


@contextmanager
def temp_file(temp_dir=None):
    pltfrm = platform.system()
    if pltfrm == "Windows":
        # create a temporary file manually and delete it on close
        if temp_dir is not None:
            # convert to a raw string for windows
            temp_dir = temp_dir.encode('unicode-escape').decode().replace('\\\\', '\\')
        else:
            temp_dir = ""

        fname = os.path.join(temp_dir, uuid.uuid4().hex)
        with open(fname, mode='w') as f:
            yield f
        # delete the file manually
        os.remove(fname)
    else:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pl') as f:
            yield f





class IsolatedProlog(pl.Prolog):
    """
    Simple wrapper around the basic Prolog-class from pyswip for use in notebooks. This wrapper uses a dedictated
    Prolog module for each of it's instances, separating them from one another.
    """
    
    class _QueryWrapper(pl.Prolog._QueryWrapper):
        def __call__(self, query, maxresult, catcherrors, normalize):
            for t in super().__call__(query, maxresult, catcherrors, False):
                if normalize:
                    try:
                        v = t.value
                    except AttributeError:
                        v = {}
                        for r in [x.value for x in t]:
                            r = self._normalize_values(r)
                            v.update(r)
                    yield v
                else:
                    yield t
                
        def _normalize_values(self, values):
            from pyswip.easy import Atom, Functor
            if isinstance(values, Atom):
                return values.value
            if isinstance(values, Functor):
                normalized = values.name.value
                if values.arity:
                    normalized_args = ([str(self._normalize_values(arg)) for arg in values.args])
                    normalized = normalized + '(' + ', '.join(normalized_args) + ')'
                return normalized
            elif isinstance(values, dict):
                return {key: self._normalize_values(v) for key, v in values.items()}
            elif isinstance(values, (list, tuple)):
                return [self._normalize_values(v) for v in values]
            return values
    
    def __init__(self, module=None):
        """
        Create a new prolog instance in it's own module to isolate it from other running prolog code.
        
        Parameters:
        ---
        module: str or None
            The module to connect this instance to. If None (default) a new random module is created
        """
        if module is None:
            module = "m" + uuid.uuid4().hex
        self.module_name = str(module)
        self.module = pl.newModule(self.module_name)
        
    def asserta(self, assertion, catcherrors=False):
        """
        call asserta/1 in the prolog instance
        """
        next(self.query(assertion.join(["asserta((", "))."]), catcherrors=catcherrors))

    def assertz(self, assertion, catcherrors=False):
        """
        call assertz/1 in the prolog instance
        """
        next(self.query(assertion.join(["assertz((", "))."]), catcherrors=catcherrors))

    def dynamic(self, term, catcherrors=False):
        """
        call dynamic/1 in the prolog instance
        """
        next(self.query(term.join(["dynamic((", "))."]), catcherrors=catcherrors))

    def retract(self, term, catcherrors=False):
        """
        call retract/1 in the prolog instance
        """
        next(self.query(term.join(["retract((", "))."]), catcherrors=catcherrors))

    def retractall(self, term, catcherrors=False):
        """
        call retractall/1 in the prolog instance
        """
        next(self.query(term.join(["retractall((", "))."]), catcherrors=catcherrors))
        
    def consult(self, knowledge_base, file=True, catcherrors=False, temp_dir=None):
        """
        Load the specified knowledge_base in the prolog interpreter. To circumvent a SWI-Prolog limitation,
        a new temporary file is created on every consult.
        
        Parameters:
        ---
        knowledge_base: str
            The knowledge base to load. This has to be a string containing either the filename (default)
            or the facts to load (if file is False). The knowledge base will be written into a temporary
            file before it is loaded into prolog.
        file: bool
            If True (default), the knowledge_base parameter is interpreted as a filename. If False the knowledge_base
            is assumed to contain the facts to load.
        catcherrors: bool
            Catch errors that might occur.
        temp_dir: str
            Optional temporary directory used for writing the knowledge base to a prolog file. Applies only on windows systems, 
            ignored otherwise.
        """
        # write all facts into a tempfile first to circumvent the prolog-consult limitation
        if file:
            with open(knowledge_base, 'r') as f:
                knowledge_base = f.read()

        pltfrm = platform.system()
        with temp_file(temp_dir) as f:
            f.write(knowledge_base)
            f.flush()
            f.seek(0)

            fname = f.name
            if pltfrm == "Windows":
                # replace backslash with forward slash because prolog apparently does not like windows paths...
                fname = fname.replace("\\", "/")
            next(self.query(fname.join(["consult('", "')"]), catcherrors=catcherrors))

    def query(self, query, maxresult=-1, catcherrors=True, normalize=True):
        """
        Run a prolog query and return a python-generator.
        If the query is a yes/no question, returns {} for yes, and nothing for no.
        Otherwise returns a generator of dicts with variables as keys.
        
        Parameters:
        ---
        query: str
            The prolog query to process.
        maxresult: int
            The maximum number of results to compute (default: -1 = all results).
        catcherrors: bool
            Catch errors that might occur (default: True).        
        normalize: bool
            Convert the prolog result objects (Terms) back to their python representation (default: True).
        
        Returns:
        ---
        query: _QueryWrapper
            The query result as an iterator.
        
        >>> prolog = IsolatedProlog()
        >>> prolog.assertz("father(michael,john)")
        >>> prolog.assertz("father(michael,gina)")
        >>> bool(list(prolog.query("father(michael,john)")))
        True
        >>> bool(list(prolog.query("father(michael,olivia)")))
        False
        >>> print sorted(prolog.query("father(michael,X)"))
        [{'X': 'gina'}, {'X': 'john'}]
        """
        return self._QueryWrapper()(self.module_name + ":" + query, maxresult, catcherrors, normalize)