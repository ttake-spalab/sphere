#!/usr/bin/env python3
"""
Create on Tue Aug 03 2021 15:49:09
I/O unittest
@author t-take
"""

import io
import tempfile
import unittest
from pathlib import Path

import sphere

DATA_DIR = Path(__file__).parents[1] / 'example' / 'example_data'


class TestOpen(unittest.TestCase):
    """Test open funciton
    In this case, we only test that the function returns correctly
    and do not care about its content.
    """

    def setUp(self):
        self.testfile = str(DATA_DIR / 'speech.sph')

    def test_read_filepath(self):
        """Test with read-mode and give the file path
        In this case, it is expected to return the Sphere_read object.
        """
        for mode in ['r', 'rb', None]:
            with (self.subTest(mode=mode),
                  sphere.open(self.testfile, mode) as fp):
                self.assertIsInstance(fp, sphere.Sphere_read)

    def test_read_filepath_with_wavelike(self):
        """Test with read-mode and is_wavelike option
        In this case, it is expected to return the WaveLike_read object.
        """
        for mode in ['r', 'rb', None]:
            with (self.subTest(mode=mode),
                  sphere.open(self.testfile, mode, is_wavelike=True) as fp):
                self.assertIsInstance(fp, sphere.WaveLike_read)

    def test_read_filelike(self):
        """Test with read-mode and give the file-like object
        In this case, it is expected to return the Sphere_read object.
        """
        with (open(self.testfile, 'rb') as ffp,
              sphere.open(ffp) as fp):
            self.assertIsInstance(fp, sphere.Sphere_read)

    def test_read_filelike_with_wavelike(self):
        """Test with read-mode and is_wavelike option
        In this case, it is expected to return the WaveLike_read object.
        """
        with (open(self.testfile, 'rb') as ffp,
              sphere.open(ffp, is_wavelike=True) as fp):
            self.assertIsInstance(fp, sphere.WaveLike_read)

    def test_write_filepath(self):
        """Test with write-mode and give the file path
        In this case, it is expected to return the Sphere_write object.
        """
        for mode in ['w', 'wb']:
            with (self.subTest(mode=mode),
                  tempfile.NamedTemporaryFile() as tmp):
                fp = sphere.open(tmp, mode)
                self.assertIsInstance(fp, sphere.Sphere_write)

                try:
                    fp.close()
                except sphere.Error:
                    pass

    def test_write_filelike(self):
        """Test with write-mode and give the file-like object
        In this case, it is expected to return the Sphere_write object.
        """
        for mode in ['w', 'wb']:
            with (self.subTest(mode=mode),
                  tempfile.NamedTemporaryFile(mode) as tmp):
                fp = sphere.open(tmp)
                self.assertIsInstance(fp, sphere.Sphere_write)

                try:
                    fp.close()
                except sphere.Error:
                    pass

    def test_invalid_mode_filepath(self):
        """Test the invalid file mode
        In this case, it is expected to raise the error.
        """
        for invalid_mode in [
                'x', 'a', 'b', 't', 'rt', 'wt', 'r+', 'r+b', 'w+', 'w+b'
        ]:
            with (self.subTest(mode=invalid_mode),
                  tempfile.NamedTemporaryFile() as tmp):
                self.assertRaises(sphere.Error, sphere.open,
                                  tmp.name, mode=invalid_mode)

    def test_invalid_mode_filelike(self):
        """Test with a file opened in a mode it cannot handle
        In this case, it is expected to raise the error too.
        """
        for invalid_mode in ['x', 'a', 'rt', 'wt', 'r+', 'r+b', 'w+', 'w+b']:
            with (self.subTest(mode=invalid_mode),
                  tempfile.TemporaryFile(mode=invalid_mode) as tmp):
                self.assertRaises(sphere.Error, sphere.open, tmp)


class TestRead(unittest.TestCase):
    """Test reader objecet"""

    def setUp(self):
        self.test_files = [
            (DATA_DIR / 'speech.sph', 1024, {
                'database_id': 'RM1',
                'database_version': '1.0',
                'utterance_id': 'aks0_st0783',
                'channel_count': 1,
                'sample_count': 48743,
                'sample_rate': 16000,
                'sample_min': -4326,
                'sample_max': 5772,
                'sample_n_bytes': 2,
                'sample_byte_format': '01',
                'sample_sig_bits': 16,
            }),
            (DATA_DIR / 'SA1.WAV', 1024, {
                'database_id': 'TIMIT',
                'database_version': '1.0',
                'utterance_id': 'cjf0_sa1',
                'channel_count': 1,
                'sample_count': 46797,
                'sample_rate': 16000,
                'sample_min': -2191,
                'sample_max': 2790,
                'sample_n_bytes': 2,
                'sample_byte_format': '01',
                'sample_sig_bits': 16,
            }),
        ]

    def test_known_params(self):
        """Test audio parameters"""
        for file, _, known_params in self.test_files:
            with (self.subTest(file=str(file.relative_to(DATA_DIR))),
                  sphere.Sphere_read(file) as fp):
                params = fp.getparams()
                self.assertEqual(params._asdict(), known_params)

    def test_values(self):
        for file, head_size, _ in self.test_files:
            with (self.subTest(file=str(file.relative_to(DATA_DIR))),
                  sphere.Sphere_read(file) as sph_fp,
                  open(file, 'rb') as fp):
                params = sph_fp.getparams()
                sph_bdat = sph_fp.readframes(params.sample_count)

                fp.seek(head_size)
                bdat = fp.read(len(sph_bdat))
                self.assertEqual(sph_bdat, bdat)


class TestWrite(unittest.TestCase):
    """Test writer objecet"""

    def setUp(self):
        self.test_files = [
            (DATA_DIR / 'speech.sph', 1024, {
                'database_id': 'RM1',
                'database_version': '1.0',
                'utterance_id': 'aks0_st0783',
                'channel_count': 1,
                'sample_count': 48743,
                'sample_rate': 16000,
                'sample_min': -4326,
                'sample_max': 5772,
                'sample_n_bytes': 2,
                'sample_byte_format': '01',
                'sample_sig_bits': 16,
            }, b'\n'.join([
                b'NIST_1A',
                b'   1024',
                b'database_id -s3 RM1',
                b'database_version -s3 1.0',
                b'utterance_id -s11 aks0_st0783',
                b'channel_count -i 1',
                b'sample_count -i 48743',
                b'sample_rate -i 16000',
                b'sample_min -i -4326',
                b'sample_max -i 5772',
                b'sample_n_bytes -i 2',
                b'sample_byte_format -s2 01',
                b'sample_sig_bits -i 16',
                b'end_head',
            ])),
            (DATA_DIR / 'SA1.WAV', 1024, {
                'database_id': 'TIMIT',
                'database_version': '1.0',
                'utterance_id': 'cjf0_sa1',
                'channel_count': 1,
                'sample_count': 46797,
                'sample_rate': 16000,
                'sample_min': -2191,
                'sample_max': 2790,
                'sample_n_bytes': 2,
                'sample_byte_format': '01',
                'sample_sig_bits': 16,
            }, b'\n'.join([
                b'NIST_1A',
                b'   1024',
                b'database_id -s5 TIMIT',
                b'database_version -s3 1.0',
                b'utterance_id -s8 cjf0_sa1',
                b'channel_count -i 1',
                b'sample_count -i 46797',
                b'sample_rate -i 16000',
                b'sample_min -i -2191',
                b'sample_max -i 2790',
                b'sample_n_bytes -i 2',
                b'sample_byte_format -s2 01',
                b'sample_sig_bits -i 16',
                b'end_head',
            ])),
        ]

    def test_known_params(self):
        """Test audio parameters"""
        for file, _, head_info, head_value in self.test_files:
            with (self.subTest(file=str(file.relative_to(DATA_DIR))),
                  io.BytesIO() as fp):

                with sphere.Sphere_write(fp) as sph_fp:
                    sph_fp.setparams(head_info)
                    sph_fp.writeframesraw(b'')

                fp.seek(0)
                self.assertEqual(fp.read1(len(head_value)), head_value)


class TestReadWrite(unittest.TestCase):
    """Test with read & write"""

    def setUp(self):
        self.test_files = [DATA_DIR / 'speech.sph', DATA_DIR / 'SA1.WAV']

        self.head_info = {
            'database_id': 'RM1',
            'database_version': '1.0',
            'utterance_id': 'aks0_st0783',
            'channel_count': 1,
            'sample_count': 48743,
            'sample_rate': 16000,
            'sample_min': -4326,
            'sample_max': 5772,
            'sample_n_bytes': 2,
            'sample_byte_format': '01',
            'sample_sig_bits': 16,
        }
        with open(self.test_files[0], 'rb') as fp:
            fp.seek(1024)
            self.data = fp.read()

    def test_write_read(self):
        file = self.test_files[0]
        with (self.subTest(file=str(file.relative_to(DATA_DIR))),
              tempfile.TemporaryFile() as tmp):

            with sphere.Sphere_write(tmp) as wfp:
                wfp.setparams(self.head_info)
                wfp.writeframes(self.data)

            tmp.seek(0)

            with sphere.Sphere_read(tmp) as rfp:
                params = rfp.getparams()
                data = rfp.readframes(params.sample_count)

            self.assertEqual(params._asdict(), self.head_info)
            self.assertEqual(data, self.data)

    def test_read_write(self):
        for file in self.test_files:
            with (self.subTest(file=str(file.relative_to(DATA_DIR))),
                  sphere.Sphere_read(file) as rfp,
                  tempfile.TemporaryFile() as tmp):

                params = rfp.getparams()._asdict()
                data = rfp.readframes(params['sample_count'])

                with sphere.Sphere_write(tmp) as wfp:
                    wfp.setparams(params)
                    wfp.writeframes(data)

                rfp._file.seek(0)
                tmp.seek(0)
                self.assertEqual(tmp.read(), rfp._file.read())


if __name__ == "__main__":
    unittest.main()
