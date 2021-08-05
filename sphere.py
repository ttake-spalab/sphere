#!/usr/bin/env python3
"""Stuff to parse SPHERE-headered files.

SPHERE is NIST SPeech HEader REsources.

Usage.

Reading SPHERE files:
      f = sphere.open(file, 'r')
where file is either the name of a file or an open file pointer.
The open file pointer must have methods read(), seek(), and close().
When the setpos() and rewind() methods are not used, the seek()
method is not necessary.
Note that this returns, unlike the wave module, does not have
any get* methods other than getparams.

This returns an instance of a class with the following public methods:
      getparams()     -- returns a namedtuple consisting of all of the
                         above in the above order
      readframes(n)   -- returns at most n frames of audio
      rewind()        -- rewind to the beginning of the audio stream
      setpos(pos)     -- seek to the specified position
      tell()          -- return the current position
      close()         -- close the instance (make it unusable)
The position returned by tell() and the position given to setpos()
are compatible and have nothing to do with the actual position in the
file.
The close() method is called automatically when the class instance
is destroyed.

If you want to use a wave-like interface, you can call the function
with is_wavelike=True as follows:
      f = sphere.open(file, 'r', is_wavelike=True)
This returns an instance of a class with the public methods same as wave.open.

Writing WAVE files:
      f = wave.open(file, 'w')
where file is either the name of a file or an open file pointer.
The open file pointer must have methods write(), tell(), seek(), and
close().

This returns an instance of a class with the following public methods:
      setparams(NamedTuple or dict)
                      -- set all parameters at once
      tell()          -- return current position in output file
      writeframesraw(data)
                      -- write audio frames without patching up the
                         file header
      writeframes(data)
                      -- write audio frames and patch up the file header
      close()         -- patch up the file header and close the
                         output file
You should set the parameters before the first writeframesraw or
writeframes.  The total number of frames does not need to be set,
but when it is set to the correct value, the header does not have to
be patched up.
It is best to first set all parameters, perhaps possibly the
compression type, and then write audio frames using writeframesraw.
When all frames have been written, either call writeframes(b'') or
close() to patch up the sizes in the header.
The close() method is called automatically when the class instance
is destroyed.

@author t-take
"""

import audioop
import builtins
import sys
import wave
from collections import namedtuple

ENCODE = 'ascii'

__all__ = ["open", "Error", "Sphere_read", "Sphere_write", "WaveLike_read"]
__version__ = '1.0.1'


class Error(Exception):
    pass


class Sphere_read(object):
    """Variables used in this class:

    These variables are available to the user though appropriate
    methods of this class:
    _file -- the open file with methods read(), close(), and seek()
              set through the __init__() method
    _headinfo -- the header information as dict
    _soundpos -- the position in the audio stream
              available through the tell() method, set through the
              setpos() method

    These variables are used internally only:
    _data_seek_needed -- 1 iff positioned correctly in audio
              file for readframes()
    _framesize -- size of one frame in the file
    """

    def initfp(self, file):
        self._convert = None
        self._soundpos = 0
        self._file = file
        if self._file.read(8) != b'NIST_1A\n':
            raise Error('file does not start with NIST_1A id')
        headsize = int(self._file.read(8).strip())  # generally: 1024-bytes

        # Reads the head_size of the header,
        # excluding the 16-bit header already read.
        self._headinfo = {}
        for line in self._file.read(headsize - 16).splitlines():
            if line == b'end_head':
                self._data_seek_needed = 0
                self._offset = self._file.tell()
                self._framesize = (self._headinfo['channel_count']
                                   * self._headinfo['sample_n_bytes'])
                break

            triple, *_ = line.decode(ENCODE).split(';', 1)  # ignore comment
            field_name, field_type, field_value = triple.split(' ', 2)
            field_value = field_value.rstrip()  # remove optional white spaces
            if field_type.startswith('-i'):     # INTEGER-FLAG
                field_value = int(field_value)
            elif field_type.startswith('-r'):   # REAL-FLAG
                field_value = float(field_value)
            elif field_type.startswith('-s'):   # STRING-FLAG
                n_str = int(field_type.lstrip('-s'))
                field_value = field_value[:n_str]
            else:
                raise Error('Invalid type flag in header: ' + line)
            self._headinfo[field_name] = field_value

        else:   # not reach the end of header
            raise Error('header chunk missing')

    def __init__(self, f):
        self._i_opened_the_file = None
        if not hasattr(f, 'read'):
            f = builtins.open(f, 'rb')
            self._i_opened_the_file = f
        # else, assume it is an open file object already
        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    #
    # User visible methods.
    #
    def getfp(self):
        return self._file

    def rewind(self):
        wave.Wave_read.rewind(self)

    def close(self):
        wave.Wave_read.close(self)

    def tell(self):
        return self._soundpos

    def getparams(self):
        _sph_params = namedtuple('_sph_params', self._headinfo.keys())
        return _sph_params(**self._headinfo)

    def setpos(self, pos):
        if pos < 0 or pos > self._headinfo['sample_count']:
            raise Error('position not in range')
        self._soundpos = pos
        self._data_seek_needed = 1

    def readframes(self, nframes):
        if self._data_seek_needed:
            self._file.seek(self._offset, 0)
            pos = self._soundpos * self._framesize
            if pos:
                self._file.seek(pos, 1)
            self._data_seek_needed = 0
        if nframes == 0:
            return b''
        data = self._file.read(nframes * self._framesize)
        if self._headinfo['sample_n_bytes'] != 1 and sys.byteorder == 'big':
            data = audioop.byteswap(data, self._sampwidth)
        if self._convert and data:
            data = self._convert(data)
        self._soundpos = self._soundpos + len(data) // self._framesize
        return data


class WaveLike_read(wave.Wave_read):
    """wave.Wave_read like object
    You can use the SPHERE file same as the wave.Wave_read object
    """
    def initfp(self, file):
        Sphere_read.initfp(self, file)
        self._nchannels = self._headinfo['channel_count']
        self._nframes = self._headinfo['sample_count']
        self._sampwidth = self._headinfo['sample_n_bytes']
        self._framerate = self._headinfo['sample_rate']
        self._comptype = 'NONE'
        self._compname = 'not compressed'

    def readframes(self, nframes):
        return Sphere_read.readframes(self, nframes)

    def get_sphparams(self):
        return Sphere_read.getparams(self)


class Sphere_write(object):
    """Variables used in this class:

    These variables are user settable through appropriate methods
    of this class:
    _file -- the open file with methods write(), close(), tell(), seek()
              set through the __init__() method
    _headinfo -- the header information
              set through the setparams() method

    These variables are used internally only:
    _datalength -- the size of the audio samples written to the header
    _nframeswritten -- the number of frames actually written
    _datawritten -- the size of the audio samples actually written
    """
    def __init__(self, f):
        self._i_opened_the_file = None
        if not hasattr(f, 'write'):
            f = builtins.open(f, 'wb')
            self._i_opened_the_file = f
        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise

    def initfp(self, file):
        self._file = file
        self._convert = None
        self._headinfo = dict()
        self._nframeswritten = 0
        self._datawritten = 0
        self._datalength = 0
        self._headerwritten = False

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    #
    # User visible methods.
    #
    def setparams(self, params):
        if self._datawritten:
            raise Error('cannot change parameters after starting to write')
        if hasattr(params, '_asdict'):
            params = params._asdict()
        self._headinfo.update(params)

    def getparams(self):
        required_keys = ['sample_n_bytes', 'channel_count']
        if all(key not in self._headinfo for key in required_keys):
            raise Error('not all parameters set (sample_n_bytes'
                        ', channel_count are required.)')
        if ('sample_n_bytes' not in self._headinfo
                and 'channel_count' not in self._headinfo):
            raise Error('not all parameters set '
                        '(sample_n_bytes, channel_count are always required.)')
        if (self._headinfo.get('sample_coding', 'pcm') in ('pcm', 'ulaw')
                and 'sample_rate' not in self._headinfo):
            raise Error('not all parameters set (sample_rate is required '
                        "if sample_coding is 'pcm' or 'ulaw' [defualt: pcm])")
        for key, value in self._headinfo.items():
            if not isinstance(value, (int, float, str)):
                raise Error('params value must be int, float or str '
                            f'("{key}" value is {type(value)})')
        _sph_params = namedtuple('_sph_params', self._headinfo.keys())
        return _sph_params(**self._headinfo)

    def tell(self):
        return self._nframeswritten

    def writeframesraw(self, data):
        if not isinstance(data, (bytes, bytearray)):
            data = memoryview(data).cast('B')
        self._headinfo.setdefault('sample_count', self._datalength)
        self._ensure_header_written(len(data))
        nframes = len(data) // (self._headinfo['channel_count']
                                * self._headinfo['sample_n_bytes'])
        if self._convert:
            data = self._convert(data)
        if self._headinfo['sample_n_bytes'] != 1 and sys.byteorder == 'big':
            data = audioop.byteswap(data, self._sampwidth)
        self._file.write(data)
        self._datawritten += len(data)
        self._nframeswritten = self._nframeswritten + nframes

    def writeframes(self, data):
        wave.Wave_write.writeframes(self, data)

    def close(self):
        wave.Wave_write.close(self)

    #
    # Internal methods.
    #

    def _ensure_header_written(self, datasize):
        if not self._headerwritten:
            if 'channel_count' not in self._headinfo:
                raise Error('# channels not specified')
            if 'sample_n_bytes' not in self._headinfo:
                raise Error('# sample bytes not specified')
            if (self._headinfo.get('sample_coding', 'pcm') in ('pcm', 'ulaw')
                    and 'sample_rate' not in self._headinfo):
                raise Error('sampling rate not specified')
            self._write_header(datasize)

    def _write_header(self, initlength):
        self._file.write(b'NIST_1A\n'
                         b'   1024\n')
        if 'sample_count' not in self._headinfo:
            self._headinfo['sample_count'] = (
                initlength // (self._headinfo['channel_count']
                               * self._headinfo['sample_n_bytes']))
        self._datalength = (self._headinfo['sample_count']
                            * self._headinfo['channel_count']
                            * self._headinfo['sample_n_bytes'])
        for name, value in self._headinfo.items():
            if isinstance(value, int):
                self._file.write(f'{name} -i {value}\n'.encode(ENCODE))
            elif isinstance(value, float):
                self._file.write(f'{name} -r {value}\n'.encode(ENCODE))
            elif isinstance(value, str):
                strlen = len(value)
                self._file.write(f'{name} -s{strlen} {value}\n'.encode(ENCODE))
        self._file.write(b'end_head\n\n\n\n\n')
        curpos = self._file.tell()
        self._file.write(b' ' * (1024 - curpos))
        self._headerwritten = True

    def _patchheader(self):
        assert self._headerwritten
        if self._datawritten == self._datalength:
            return
        curpos = self._file.tell()
        self._file.seek(0, 0)
        self._write_header(self._datawritten)
        self._file.seek(curpos, 0)
        self._datalength = self._datawritten


def open(f, mode=None, *, is_wavelike=False):
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        if is_wavelike:
            return WaveLike_read(f)
        else:
            return Sphere_read(f)
    elif mode in ('w', 'wb'):
        return Sphere_write(f)
    else:
        raise Error("mode must be 'r', 'rb', 'w', or 'wb'")


if __name__ == "__main__":

    import argparse
    from functools import partial
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description='SPHERE file converter',
        epilog=('Converte header from SPHERE or WAVE to WAVE, SPHERE or RAW. '
                'Input file format is automatically detected.'),
    )
    parser.add_argument('input', type=Path,
                        help='Input audio file (WAVE or SPHERE)')
    parser.add_argument('-o', '--output', type=Path,
                        help=('Output audio file path. If this is not given, '
                              'input name + format suffix will be used.'))
    parser.add_argument('-f', '--format', choices=['wav', 'sph', 'raw'],
                        help='Output file format.')

    # define variable from parsed arguments
    args = parser.parse_args()
    ifile = args.input
    ofile = args.output
    oform = args.format

    if not ifile.is_file():
        raise FileNotFoundError(f'Failed: Input file is not found: "{ifile}"')

    # Check the input file format
    try:
        fp = open(ifile)
        fp.close()
    except Error:
        try:
            wfp = wave.open(str(ifile))
            wfp.close()
        except wave.Error:
            msg = f'Failed: Input file type is not supported: "{ifile}"'
            raise RuntimeError(msg) from None
        else:
            in_opener = wave.open
            iform = 'wav'
    else:
        in_opener = partial(open, is_wavelike=True)
        iform = 'sph'

    if oform is None:
        oform = {'wav': 'sph', 'sph': 'wav'}[iform]

    if ofile is None:
        ofile = ifile.with_suffix('.' + oform)
    elif ofile.is_dir():
        ofile = ofile / f'{ifile.stem}.{oform}'

    if oform == 'wav':
        out_opener = wave.open
    elif oform == 'sph':
        out_opener = open
    elif oform == 'raw':
        out_opener = builtins.open

    # File read & write
    with (in_opener(str(ifile)) as in_fp,
          out_opener(str(ofile), 'wb') as out_fp):

        if oform == 'wav':
            out_fp.setparams(in_fp.getparams())
        if oform == 'sph':
            params = in_fp.getparams()
            out_fp.setparams({
                'channel_count': params.nchannels,
                'sample_n_bytes': params.sampwidth,
                'sample_count': params.nframes,
                'sample_rate': params.framerate,
            })

        out_fp.writeframes(in_fp.readframes(in_fp.getnframes()))

    oformat = {'wav': 'WAVE', 'sph': 'SPHERE', 'raw': 'RAW'}[oform]
    print(f'Success: Dump the {oformat} file: "{ofile}"')
