SPHERE file I/O
===============

Python simple interface for NIST SPeech HEader REsources (SPHERE) file

`sphere` provides an interface like the `wave` module without any third-party modules.



## Usage

Basic SPHERE file input
```python
import sphere

file = 'example/speech.sph'     # path to SPHERE file
with sphere.open(file, 'r') as fp:
    params = fp.getparams()
    sph_wave = fp.readframes(params.sample_count)

print(params)
# _sph_params(database_id='RM1', database_version='1.0', utterance_id='aks0_st0783', channel_count=1, sample_count=48743, sample_rate=16000, sample_min=-4326, sample_max=5772, sample_n_bytes=2, sample_byte_format='01', sample_sig_bits=16)
```


`shpere.open` function has `is_wavelike` option.
If you give `is_wavelike = True` to `open` function, this function return object (`WaveLike_read`) that has build-in `wave` module like interface.
So it has follow methods:
    `getnchannels`, `getsampwidth`, `getframerate`, `getnframes`, `getparams`, ...
```python
import sphere

file = 'example/SA1.WAV'
with sphere.open(file, 'r', is_wavelike=True) as fp:
    nframes = fp.getnframes()
    sample_rate = fp.getframerate()
    sph_wave = fp.readframes(nframes)
    params = fp.getparams()

print(params)
# _wave_params(nchannels=1, sampwidth=2, framerate=16000, nframes=46797, comptype='NONE', compname='not compressed')
```


Basic SPHERE file output
```python
import sphere

file = 'example/test.sph'     # path to SPHERE file
with sphere.open(file, 'r') as fp:
    params = fp.setparams({
        'channel_count': 1,
        'sample_count': len(sph_wave),
        'sample_n_bytes': 2,
    })
    fp.writeframes(sph_wave)
```


## TODO
- [x] LICENSE file
- [x] Jupyter notebook examples
- [x] Enough comments
- [x] setup.py
- [ ] make documentation
- [ ] provide cli interface (convert to raw or wav)
