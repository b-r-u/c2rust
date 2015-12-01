#!/usr/bin/python3

import unittest
import c2rust
import re


def add_whitespace(c_fn):
    """ Add two spaces between all tokens of a C function
    """
    tok = re.compile(r'[a-zA-Z0-9_]+|\*|\(|\)|\,|\[|\]')
    return '  ' + '  '.join(tok.findall(c_fn)) + '  '


def collapse_whitespace(c_fn):
    """ Collapse whitespace between tokens of a C function,
    when possible whithout altering semantics.
    """
    tok = re.compile(r'[a-zA-Z0-9_]+|\*|\(|\)|\,|\[|\]')
    ident = re.compile(r'[a-zA-Z0-9_]+')

    def tok_is_ident(s):
        if ident.match(s) is None:
            return False
        else:
            return True

    col = []
    last_tok_is_ident = False
    for m in tok.finditer(c_fn):
        is_ident = tok_is_ident(m.group(0))
        if is_ident and last_tok_is_ident:
            col.append(' ')
        col.append(m.group(0))
        last_tok_is_ident = is_ident

    return ''.join(col)


class TestC2Rust(unittest.TestCase):
    def c2r(self, c_fn, rust_fn):
        """ Test if the from c_fn generated Rust function equals the given rust_fn
        """

        (gen_c, gen_rust) = c2rust.c_functions_2_rust(c_fn)
        self.assertEqual(rust_fn, gen_rust[0], msg=c_fn)

        # C function with added whitespace should yield same result
        (gen_c, gen_rust) = c2rust.c_functions_2_rust(add_whitespace(c_fn))
        self.assertEqual(rust_fn, gen_rust[0], msg=add_whitespace(c_fn))

        # C function with collapsed whitespace should yield same result
        (gen_c, gen_rust) = c2rust.c_functions_2_rust(collapse_whitespace(c_fn))
        self.assertEqual(rust_fn, gen_rust[0], msg=collapse_whitespace(c_fn))

        # test helper functions
        self.assertEqual(collapse_whitespace(c_fn),
                         collapse_whitespace(add_whitespace(c_fn)))

        self.assertEqual(add_whitespace(c_fn),
                         add_whitespace(collapse_whitespace(c_fn)))

    def test_basic(self):
        self.c2r('int foo()',
                 'pub fn foo() -> c_int;')
        self.c2r('int foo(int a)',
                 'pub fn foo(a: c_int) -> c_int;')
        self.c2r('int foo(int a, int b)',
                 'pub fn foo(a: c_int, b: c_int) -> c_int;')
        self.c2r('object_t foo(object_t a)',
                 'pub fn foo(a: object_t) -> object_t;')

    def test_void(self):
        self.c2r('void foo()',
                 'pub fn foo();')
        self.c2r('void foo(void)',
                 'pub fn foo();')
        self.c2r('void foo(int x)',
                 'pub fn foo(x: c_int);')

    def test_pointers(self):
        self.c2r('int* foo()',
                 'pub fn foo() -> *mut c_int;')
        self.c2r('void foo(const int* x)',
                 'pub fn foo(x: *const c_int);')
        self.c2r('void foo(const int* x, const int* y)',
                 'pub fn foo(x: *const c_int, y: *const c_int);')
        self.c2r('const int* foo()',
                 'pub fn foo() -> *const c_int;')

    def test_multi_pointers(self):
        self.c2r('void foo(const char **data)',
                 'pub fn foo(data: *const *const c_char);')
        self.c2r('void foo(char **data)',
                 'pub fn foo(data: *mut *mut c_char);')
        self.c2r('int** foo()',
                 'pub fn foo() -> *mut *mut c_int;')
        self.c2r('const int** foo()',
                 'pub fn foo() -> *const *const c_int;')

    def test_arrays(self):
        self.c2r('void foo(const char data[])',
                 'pub fn foo(data: *const c_char);')
        self.c2r('void foo(const char data[][])',
                 'pub fn foo(data: *const *const c_char);')
        self.c2r('void foo(const char data[3])',
                 'pub fn foo(data: *const c_char);')
        self.c2r('void foo(const char data[static 3])',
                 'pub fn foo(data: *const c_char);')

    def test_types(self):
        self.c2r('unsigned int* foo()',
                 'pub fn foo() -> *mut c_uint;')
        self.c2r('void foo(unsigned int *x)',
                 'pub fn foo(x: *mut c_uint);')
        self.c2r('void foo(const unsigned long long int *x)',
                 'pub fn foo(x: *const c_ulonglong);')
        self.c2r('void foo(const unsigned long long int * const x)',
                 'pub fn foo(x: *const c_ulonglong);')
        self.c2r('const unsigned long long int* foo()',
                 'pub fn foo() -> *const c_ulonglong;')

if __name__ == '__main__':
    unittest.main()
