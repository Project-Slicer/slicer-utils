#!/usr/bin/env python3

import sys
import os
from typing import Optional, Any, List, Iterable
from struct import unpack, pack, calcsize
from shutil import copyfile


HELP = '''
Optimize the file dump for checkpoints.

This script will copy the source files that specified in the kfd dumps
to the parent directory of the checkpoint directory, and keep only one
copy of the files referenced by multiple kfd dumps.

You should use the option `--dump-after-open` to generate checkpoints
without using `--dump-file`.

  Usage: {prog_name} <parent directory>
'''.strip()


O_ACCMODE = 0o0003
O_RDONLY = 0o0000
O_WRONLY = 0o0001
O_RDWR = 0o0002


class PlatInfo:
  '''
  A `platinfo` file of a checkpoint.
  '''

  def __init__(self) -> None:
    self.endian: Optional[str] = None

  def __check_field(self, field_name: str, value: Any, file: str) -> None:
    field = getattr(self, field_name)
    if field is None:
      setattr(self, field_name, value)
    elif field != value:
      raise RuntimeError(f'`{field_name}` mismatch in "{file}"')

  def check(self, file: str) -> None:
    '''
    Checks (or initializes) the data of `platinfo`.
    '''
    with open(file, 'rb') as f:
      magic, endian = unpack('<2sc', f.read(calcsize('<2sc')))
      if magic != b'pi':
        raise RuntimeError(f'"{file}" is not a valid platinfo file')
      self.__check_field('endian', '<' if endian == b'\x00' else '>', file)


class KfdDump:
  '''
  A kfd dump file (`kfd/x`) of a checkpoint.
  '''

  def __init__(self, platinfo: PlatInfo, file: str) -> None:
    self.file = file
    self.fmt = f'{platinfo.endian}QII'
    fmt_len = calcsize(self.fmt)
    with open(file, 'rb') as f:
      self.offset, self.flags, path_len = unpack(self.fmt, f.read(fmt_len))
      self.path = f.read(path_len).decode('ascii')

  def update(self) -> None:
    '''
    Updates the data of the kfd dump.
    '''
    with open(self.file, 'wb') as f:
      f.write(pack(self.fmt, self.offset, self.flags, len(self.path)))
      f.write(self.path.encode('ascii'))

  def read_only(self) -> bool:
    '''
    Returns whether the kfd is read-only.
    '''
    return self.flags & O_ACCMODE == O_RDONLY

  def write_only(self) -> bool:
    '''
    Returns whether the kfd is write-only.
    '''
    return self.flags & O_ACCMODE == O_WRONLY

  def read_write(self) -> bool:
    '''
    Returns whether the kfd is read-write.
    '''
    return self.flags & O_ACCMODE == O_RDWR

  def is_abs_path(self) -> bool:
    '''
    Returns whether the path is an absolute path.
    '''
    return self.path[0] == '/'


def scan_kfd_dumps(checkpoint_dir: str, platinfo: PlatInfo) -> Iterable[KfdDump]:
  '''
  Scans the kfd dumps of a checkpoint.

  Returns an iterator of `KfdDump` objects.
  '''
  kfd_dir = os.path.join(checkpoint_dir, 'file', 'kfd')
  kfd_files = [f for f in os.listdir(kfd_dir) if f.isnumeric()]
  return map(lambda f: KfdDump(platinfo, os.path.join(kfd_dir, f)), kfd_files)


def collect_kfd_dumps(parent_dir: str) -> Iterable[KfdDump]:
  '''
  Collects the kfd dumps in all checkpoints.

  Returns an iterator of `KfdDump` objects.
  '''
  platinfo = PlatInfo()
  # for each checkpoint directory
  for f in os.listdir(parent_dir):
    checkpoint_dir = os.path.join(parent_dir, f)
    if not os.path.isdir(checkpoint_dir):
      continue
    # check the platinfo file
    platinfo.check(os.path.join(checkpoint_dir, 'platinfo'))
    # for each kfd dumps
    for kfd in scan_kfd_dumps(checkpoint_dir, platinfo):
      if kfd.is_abs_path():
        yield kfd


def get_native_path(kfd: KfdDump, path: str) -> str:
  '''
  Returns a path that applies to the native OS of the given kfd and path.
  '''
  split_kfd_path = kfd.file.split('/')
  assert split_kfd_path[-3] == 'file' and split_kfd_path[-2] == 'kfd'
  return os.path.join(*split_kfd_path[:-3], *path.split('/'))


def copy_files(parent_dir: str) -> None:
  '''
  Copy files to parent/checkpoint directory.
  '''
  copied_files = {}
  kfds: List[KfdDump] = []
  # for each kfd object, copy the associated file to directory
  for kfd in collect_kfd_dumps(parent_dir):
    if kfd.read_only():
      id = copied_files.get(kfd.path, len(copied_files))
      new_path = f'../{kfd.path.split("/")[-1]}.{id}'
      if kfd.path not in copied_files:
        copyfile(kfd.path, get_native_path(kfd, new_path), follow_symlinks=True)
        copied_files[kfd.path] = id
      kfd.path = new_path
    else:
      new_path = f'file/kfd/{kfd.path.split("/")[-1]}.{kfd.file.split("/")[-1]}'
      native_path = get_native_path(kfd, new_path)
      if kfd.write_only():
        open(native_path, 'w').close()
      elif kfd.read_write():
        copyfile(kfd.path, native_path, follow_symlinks=True)
      else:
        raise RuntimeError(f'unknown kfd type in "{kfd.file}"')
      kfd.path = new_path
    kfds.append(kfd)
  # update kfds
  for kfd in kfds:
    kfd.update()


if __name__ == '__main__':
  if len(sys.argv) != 2:
    print(HELP.format(prog_name=sys.argv[0]))
    sys.exit(1)

  copy_files(sys.argv[1])
