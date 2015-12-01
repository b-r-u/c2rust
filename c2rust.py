#!/usr/bin/python3

"""Convert C function definitions to Rust using dirty regex-hacks
"""

import re


def _count_occurences(needle, haystack):
    """ Count occurences of the string needle in haystack
    """
    return len(haystack.split(needle)) - 1


def _c_ptr_2_rust(c_ptr, c_const_type, c_array=''):
    """ Return Rust pointer from some C fragments
    """
    c_ptr = c_ptr.strip()
    c_const_type = c_const_type.strip()
    c_array = c_array.strip()

    if c_ptr == '' and c_array == '':
        return ''
    else:
        # TODO Just because the type is const, not all pointers are const too.
        ptr_num = _count_occurences('*', c_ptr)
        array_num = _count_occurences('[', c_array)
        if c_const_type == 'const':
            return ''.join(['*const '] * (ptr_num + array_num))
        else:
            return ''.join(['*mut '] * (ptr_num + array_num))


def _c_type_is_void(c_type):
    if c_type.strip() == 'void':
        return True
    else:
        return False


def get_ident_regex():
    """ Return regex matching identifiers
    """
    return r'[a-zA-Z_][a-zA-Z0-9_]*'


def get_ptr_regex():
    """ Return regex matching C pointers
    """
    return '(?:(?:\s*\*\s*|\s*\*\s*const\s+)+|\s+)'


def get_fn_regex():
    """ Return regex matching C functions
    """
    return (r'(?P<return_const>const\s+|)'
            '(?P<return_type>{})\s*'
            '(?P<return_ptr>{})\s*'
            '(?P<fn_name>{})\s*'
            '\((?P<inner>[^\(\)]*)\)\s*[;]?'
            .format(get_ctypes_regex(),
                    get_ptr_regex(),
                    get_ident_regex()))


def get_params_regex():
    """ Return regex matching C function parameters
    """
    return (r'\s*(?P<param_const_type>const\s+|)\s*'
            '(?P<param_type>{})'
            '(?P<param_ptr>{})'
            '(?P<param_name>{})\s*'
            '(?P<param_array>(?:\[\s*(?:static)?\s*[0-9]*\s*\]\s*)*)\s*'
            '(?P<end_sep>$|\,)'
            .format(get_ctypes_regex(),
                    get_ptr_regex(),
                    get_ident_regex()))


def get_ctypes_regex():
    """ Return a regex matching all C types,
    especially the standard types with whitespace in between
    """
    return (r'char|'
            'signed\s+char|'
            'unsigned\s+char|'
            'short|'
            'short\s+int|'
            'signed\s+short|'
            'signed\s+short\s+int|'
            'unsigned\s+short|'
            'unsigned\s+short\s+int|'
            'int|'
            'signed\s+int|'
            'unsigned|'
            'unsigned\s+int|'
            'long|'
            'long\s+int|'
            'signed\s+long|'
            'signed\s+long\s+int|'
            'unsigned\s+long|'
            'unsigned\s+long\s+int|'
            'long\s+long|'
            'long\s+long\s+int|'
            'signed\s+long\s+long|'
            'signed\s+long\s+long\s+int|'
            'unsigned\s+long\s+long|'
            'unsigned\s+long\s+long\s+int|'
            'float|'
            'double|'
            'long\s+double|'
            '{}'
            .format(get_ident_regex()))


def c_type_2_rust(c_type):
    """ Convert standard C95 and C99 types to corresponding Rust libc types
    """
    conv = dict()
    conv['char'] = 'c_char'
    conv['signed char'] = 'c_schar'
    conv['unsigned char'] = 'c_uchar'
    conv['short'] = 'c_short'
    conv['short int'] = 'c_short'
    conv['signed short'] = 'c_short'
    conv['signed short int'] = 'c_short'
    conv['unsigned short'] = 'c_ushort'
    conv['unsigned short int'] = 'c_ushort'
    conv['int'] = 'c_int'
    conv['signed int'] = 'c_int'
    conv['unsigned'] = 'c_uint'
    conv['unsigned int'] = 'c_uint'
    conv['long'] = 'c_long'
    conv['long int'] = 'c_long'
    conv['signed long'] = 'c_long'
    conv['signed long int'] = 'c_long'
    conv['unsigned long'] = 'c_ulong'
    conv['unsigned long int'] = 'c_ulong'
    conv['long long'] = 'c_longlong'
    conv['long long int'] = 'c_longlong'
    conv['signed long long'] = 'c_longlong'
    conv['signed long long int'] = 'c_longlong'
    conv['unsigned long long'] = 'c_ulonglong'
    conv['unsigned long long int'] = 'c_ulonglong'
    conv['float'] = 'c_float'
    conv['double'] = 'c_double'
    conv['long double'] = 'c_double'

    c_type = _reduce(c_type)
    return conv.get(c_type, c_type)


def _reduce(s):
    """ strip s and replace all whitespace runs with a single space
    """
    return re.sub(r'\s+', ' ', s.strip())


def rust_fn_from_match(fn_match, c_type_to_rust_fn):
    rust_fn = ['pub fn ']
    rust_fn += fn_match.group('fn_name')
    rust_fn += '('

    params_re = re.compile(get_params_regex())

    params = []
    for m in params_re.finditer(fn_match.group('inner')):
        param = m.group('param_name')
        param += ': '
        param += _c_ptr_2_rust(m.group('param_ptr'),
                               m.group('param_const_type'),
                               m.group('param_array'))
        param += c_type_to_rust_fn(_reduce(m.group('param_type')))
        params.append(param)

    rust_fn += ', '.join(params)
    rust_fn += ')'

    return_type = fn_match.group('return_type')

    if not _c_type_is_void(return_type):
        rust_fn += ' -> '

        ret_ptr = fn_match.group('return_ptr')
        ret_const = fn_match.group('return_const')
        rust_fn += _c_ptr_2_rust(ret_ptr, ret_const)

        rust_fn += c_type_to_rust_fn(_reduce(fn_match.group('return_type')))

    rust_fn += ';'

    return ''.join(rust_fn)


def c_functions_2_rust(source, c_type_to_rust_fn=c_type_2_rust):
    source = _reduce(source)

    fn_re = re.compile(get_fn_regex())

    rust_functions = []
    c_functions = []

    for fn_match in fn_re.finditer(source):
        rust_fn = rust_fn_from_match(fn_match,
                                     c_type_to_rust_fn)
        c_fn = _reduce(fn_match.group(0))

        rust_functions.append(rust_fn)
        c_functions.append(c_fn)

    return (c_functions, rust_functions)


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.\
    ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                   description='Convert C function definitions to Rust.\n'
                               'Use this tool to help in the creation of '
                               'foreign function interfaces.',
                   epilog='EXAMPLES:\n'
                          '  {} "int foo(int x, const char *s)"\n\n'
                          '  {} -f cfunctions.txt\n\n'
                          '  cat cfunctions.txt | {} -s\n'
                          .format(*(sys.argv[0],)*3))
    group = parser.add_mutually_exclusive_group()
    group.add_argument('cfunctions', nargs='?',
                       help="C function definitions")
    group.add_argument('-f', '--file', metavar='PATH',
                       help='specify path to file containing C functions',
                       type=str)
    group.add_argument('-s', '--stdin',
                       help='read C functions from standard input',
                       action='store_true')
    parser.add_argument('-c', '--show-c',
                        help='print corresponding C functions '
                             'next to Rust functions',
                        action='store_true')

    args = parser.parse_args()

    if args.file:
        f = open(args.file, 'r')
        source = f.read()
        c_fns, rust_fns = c_functions_2_rust(source)
    elif args.cfunctions:
        c_fns, rust_fns = c_functions_2_rust(args.cfunctions)
    elif args.stdin:
        source = sys.stdin.read()
        c_fns, rust_fns = c_functions_2_rust(source)
    else:
        parser.print_help()
        sys.exit(2)

    if args.show_c:
        for c, rust in zip(c_fns, rust_fns):
            print('{}\n{}\n'.format(c, rust))
    else:
        for r in rust_fns:
            print(r)
