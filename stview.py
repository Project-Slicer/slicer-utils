#!/usr/bin/env python3

import sys
import struct


STRUCT_FMT = '<7QQ'
STRUCT_LEN = struct.calcsize(STRUCT_FMT)
unpack = struct.Struct(STRUCT_FMT).unpack_from


def fmt_i32(i: int) -> str:
  i &= 0xffffffff
  if i >= 0x80000000:
    i -= 0x100000000
  return str(i)


def fmt_u32(u: int) -> str:
  return str(u & 0xffffffff)


def fmt_ptr(ptr: int) -> str:
  return f'0x{ptr:x}'


def fmt_size(size: int) -> str:
  return str(size)


def fmt_off(off: int) -> str:
  if off >= 0x8000000000000000:
    off -= 0x10000000000000000
  return str(off)


SYS_TABLE = {
    93: ('exit', fmt_i32),
    94: ('exit_group', fmt_i32),
    172: ('getpid',),
    129: ('kill', fmt_i32, fmt_i32),
    131: ('tgkill', fmt_i32, fmt_i32, fmt_i32),
    63: ('read', fmt_i32, fmt_ptr, fmt_size),
    64: ('write', fmt_i32, fmt_ptr, fmt_size),
    56: ('openat', fmt_i32, fmt_ptr, fmt_i32, fmt_i32),
    57: ('close', fmt_i32),
    62: ('lseek', fmt_i32, fmt_off, fmt_i32),
    214: ('brk', fmt_ptr),
    37: ('linkat', fmt_i32, fmt_ptr, fmt_i32, fmt_ptr, fmt_i32),
    35: ('unlinkat', fmt_i32, fmt_ptr, fmt_i32),
    34: ('mkdirat', fmt_i32, fmt_ptr, fmt_i32),
    38: ('renameat', fmt_i32, fmt_ptr, fmt_i32, fmt_ptr),
    49: ('chdir', fmt_ptr),
    17: ('getcwd', fmt_ptr, fmt_size),
    80: ('fstat', fmt_i32, fmt_ptr),
    79: ('fstatat', fmt_i32, fmt_ptr, fmt_ptr, fmt_i32),
    48: ('faccessat', fmt_i32, fmt_ptr, fmt_i32),
    67: ('pread', fmt_i32, fmt_ptr, fmt_size, fmt_off),
    68: ('pwrite', fmt_i32, fmt_ptr, fmt_size, fmt_off),
    160: ('uname', fmt_ptr),
    174: ('getuid',),
    175: ('geteuid',),
    176: ('getgid',),
    177: ('getegid',),
    178: ('gettid',),
    222: ('mmap', fmt_ptr, fmt_size, fmt_i32, fmt_i32, fmt_i32, fmt_off),
    215: ('munmap', fmt_ptr, fmt_size),
    216: ('mremap', fmt_ptr, fmt_size, fmt_size, fmt_i32),
    226: ('mprotect', fmt_ptr, fmt_size, fmt_i32),
    261: ('prlimit64', fmt_i32, fmt_i32, fmt_ptr, fmt_ptr),
    134: ('rt_sigaction', fmt_i32, fmt_ptr, fmt_ptr, fmt_size),
    66: ('writev', fmt_i32, fmt_ptr, fmt_i32),
    169: ('gettimeofday', fmt_ptr),
    153: ('times', fmt_ptr),
    25: ('fcntl', fmt_i32, fmt_i32, fmt_i32),
    46: ('ftruncate', fmt_i32, fmt_off),
    61: ('getdents', fmt_i32, fmt_ptr, fmt_i32),
    23: ('dup', fmt_i32),
    24: ('dup3', fmt_i32, fmt_i32, fmt_i32),
    78: ('readlinkat', fmt_i32, fmt_ptr, fmt_ptr, fmt_size),
    135: ('rt_sigprocmask', fmt_i32, fmt_ptr, fmt_ptr),
    29: ('ioctl', fmt_i32, fmt_i32),
    163: ('getrlimit', fmt_i32, fmt_ptr),
    164: ('setrlimit', fmt_i32, fmt_ptr),
    165: ('getrusage', fmt_i32, fmt_ptr),
    113: ('clock_gettime', fmt_i32, fmt_ptr),
    96: ('set_tid_address', fmt_ptr),
    99: ('set_robust_list', fmt_ptr, fmt_size),
    233: ('madvise', fmt_ptr, fmt_size, fmt_i32),
    291: ('statx', fmt_i32, fmt_ptr, fmt_i32, fmt_u32, fmt_ptr),
    71: ('sendfile', fmt_i32, fmt_i32, fmt_off, fmt_size),
    1024: ('open', fmt_ptr, fmt_i32, fmt_i32),
    1025: ('link', fmt_ptr, fmt_ptr),
    1026: ('unlink', fmt_ptr),
    1030: ('mkdir', fmt_ptr, fmt_i32),
    1033: ('access', fmt_ptr, fmt_i32),
    1038: ('stat', fmt_ptr, fmt_ptr),
    1039: ('lstat', fmt_ptr, fmt_ptr),
    1062: ('time', fmt_ptr),
}


def print_syscall(data: bytes) -> None:
  a0, a1, a2, a3, a4, a5, n, epc = unpack(data)
  args = (a0, a1, a2, a3, a4, a5)
  if n in SYS_TABLE:
    name = SYS_TABLE[n][0]
    args_str = ', '.join(
        map(lambda x: x[0](x[1]), zip(SYS_TABLE[n][1:], args)))
  else:
    name = '<UNKNOWN>'
    args_str = ''
  print(f'{i:06d}: epc={epc:016x}, {name}({args_str})')


if __name__ == '__main__':
  if len(sys.argv) != 2:
    print(f'Usage: {sys.argv[0]} <strace file>')
    sys.exit(1)

  st_file = sys.argv[1]
  with open(st_file, 'rb') as f:
    i = 0
    while data := f.read(STRUCT_LEN):
      print_syscall(data)
      i += 1
