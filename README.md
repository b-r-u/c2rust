# c2rust

Converts C function definitions to Rust. Use this tool to help in the creation of foreign function interfaces.

## Pros
* super simple
```sh
$ ./c2rust.py "int foo(const char *s, unsigned long len)"
pub fn foo(s: *const c_char, len: c_ulong) -> c_int;
```

## Cons

Does not handle:
* C preprocessor instructions
  * #include
  * macros
* variadic functions
* ...

For a more sophisticated tool take a look at [rust-bindgen](https://github.com/servo/rust-bindgen).

## Usage
```sh
$ ./c2rust.py --help
usage: c2rust.py [-h] [-f PATH] [-s] [-c] [cfunctions]

Convert C function definitions to Rust.
Use this tool to help in the creation of foreign function interfaces.

positional arguments:
cfunctions            C function definitions

optional arguments:
-h, --help            show this help message and exit
-f PATH, --file PATH  specify path to file containing C functions
-s, --stdin           read C functions from standard input
-c, --show-c          print corresponding C functions next to Rust functions

EXAMPLES:
./c2rust.py "int foo(int x, const char *s)"

./c2rust.py -f cfunctions.txt

cat cfunctions.txt | ./c2rust.py -s
```

## License

MIT, see LICENSE file
