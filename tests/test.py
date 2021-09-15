import pathlib
import pytest
from typing import Union
import numpy as np
from context import bruker_utils


DIR = pathlib.Path(__file__).resolve().parent
FIDPATHS = [DIR / f'data/{i}' for i in range(1, 3)]
PDATAPATHS = [fidpath / 'pdata/1' for fidpath in FIDPATHS]
ALLPATHS = FIDPATHS + PDATAPATHS


def sigfig(
    value: Union[int, float, complex], sf: int
) -> Union[int, float, complex]:
    roundval = sf - int(np.floor(np.log10(abs(value)))) - 1
    return np.round(value, roundval)


def test_parse_jcampdx():
    path = FIDPATHS[0] / 'acqus'
    params = bruker_utils.parse_jcampdx(path)

    # Single value parameters
    assert params['BYTORDA'] == 0
    assert params['SFO1'] == 500.132249206
    # Multi-value parameters (values on one line)
    assert params['CPDPRG'] == 4 * ['<>'] + 5 * ['<mlev>']
    assert params['PCPD'] == [100, 60] + 8 * [100]
    # Multi-value parameters (values span multiple lines)
    assert params['PLW'] == 64 * [-1]
    spnam = [
        '<gauss>', '<Gaus1.1000>', '<Gaus1_180r.1000>', '<>', '<gauss>',
        '<gauss>', '<Squa100.1000>', '<>', '<gauss>', '<gauss>',
        '<gauss>', '<Sinc1.1000>', '<gauss>', '<gauss>', '<>', '<>',
        '<gauss>', '<gauss>', '<>', '<Sinc1.1000>', '<Sinc1.1000>',
        '<Sinc1.1000>', '<Sinc1.1000>'
    ] + 6 * ['<gauss>'] + ['<', '>', '<gauss>'] + 33 * ['<>']
    assert params['SPNAM'] == spnam


class TestBrukerDataset:
    def testinit(self):
        bruker_dataset = bruker_utils.BrukerDataset(FIDPATHS[0])
        assert bruker_dataset.dim == 1
        assert bruker_dataset.dtype == 'fid'
        assert list(bruker_dataset._paramfiles.keys()) == ['acqus']
        assert bruker_dataset._paramfiles['acqus'] == \
            FIDPATHS[0] / 'acqus'
        assert bruker_dataset._datafile == FIDPATHS[0] / 'fid'
        assert bruker_dataset.directory == FIDPATHS[0]

        with pytest.raises(RuntimeError) as exc_info:
            bruker_dataset.dim = 2
        assert str(exc_info.value) == '`dim` cannot be mutated!'

        with pytest.raises(RuntimeError) as exc_info:
            bruker_dataset.dtype = 'pdata'
        assert str(exc_info.value) == '`dtype` cannot be mutated!'

        with pytest.raises(RuntimeError) as exc_info:
            bruker_dataset.directory = pathlib.Path().cwd().resolve()
        assert str(exc_info.value) == '`directory` cannot be mutated!'

    def test_get_parameters(self):
        bruker_dataset_fid_1d = bruker_utils.BrukerDataset(FIDPATHS[0])
        # Single relavent parameter file: acqus, so an un-nested dict
        # is returned.
        params = bruker_dataset_fid_1d.get_parameters()
        # Check a few of the same parameters as in test_parse_jcampdx
        assert params['acqus']['BYTORDA'] == 0
        assert params['acqus']['SFO1'] == 500.132249206
        assert params['acqus']['PCPD'] == [100, 60] + 8 * [100]
        assert params['acqus']['CPDPRG'] == 4 * ['<>'] + 5 * ['<mlev>']

        # For 1D pdata, both acqus and procs will be present.
        bruker_dataset_pdata_1d = bruker_utils.BrukerDataset(PDATAPATHS[0])
        params = bruker_dataset_pdata_1d.get_parameters()
        assert set(params.keys()) == {'acqus', 'procs'}
        assert params['procs']['F1P'] == 5.04740305849404
        assert params['acqus']['SFO1'] == 500.132249206

        bruker_dataset_fid_2d = bruker_utils.BrukerDataset(FIDPATHS[1])
        params = bruker_dataset_fid_2d.get_parameters()
        assert set(params.keys()) == {'acqus', 'acqu2s'}

        bruker_dataset_pdata_2d = bruker_utils.BrukerDataset(PDATAPATHS[1])
        params = bruker_dataset_pdata_2d.get_parameters()
        assert set(params.keys()) == {'acqus', 'acqu2s', 'procs', 'proc2s'}

        # Test getting parameters from a subset of files
        params = bruker_dataset_pdata_2d.get_parameters(
            filenames=['acqus', 'proc2s'])
        assert set(params.keys()) == {'acqus', 'proc2s'}

        # ---Errors---
        # Invalid argument type for filenames
        with pytest.raises(TypeError) as exc_info:
            bruker_dataset_pdata_2d.get_parameters(0)
        assert str(exc_info.value) == 'Invalid type for `filenames`.'

        # One or more filename not valid
        with pytest.raises(ValueError) as exc_info:
            bruker_dataset_pdata_2d.get_parameters(
                ['acqus', 'proc2s', 'INVALID'])
        assert str(exc_info.value) == \
            ('`INVALID` is an invalid filename. Valid options are:\n'
             'acqus, acqu2s, procs, proc2s.')

    def test_binary_format(self):
        bruker_dataset = bruker_utils.BrukerDataset(FIDPATHS[0])
        assert bruker_dataset.binary_format == '<i4'

        with pytest.raises(RuntimeError) as exc_info:
            bruker_dataset.binary_format = 'blah'
        assert str(exc_info.value) == '`binary_format` cannot be mutated!'

    def test_data(self):
        bruker_dataset_fid_1d = bruker_utils.BrukerDataset(FIDPATHS[0])
        data = bruker_dataset_fid_1d.data
        # Check that a few random points match what is seen in TopSpin
        assert sigfig(data[0], 4) == complex(2.550E4, 3.217E4)
        assert sigfig(data[953], 4) == complex(-5211, -1064)
        assert sigfig(data[3938], 4) == complex(540.6, -191.2)
        assert data.shape == (65384 // 2,)

        bruker_dataset_pdata_1d = bruker_utils.BrukerDataset(PDATAPATHS[0])
        data = bruker_dataset_pdata_1d.data
        assert sigfig(data[5570], 4) == 1.922E5
        assert sigfig(data[18368], 4) == 1.642E6
        assert sigfig(data[20970], 4) == 2.073E6
        assert data.shape == (32768,)

        # Seem to be unable to view datapoints of ser for multidimensional
        # data! Cannot easily test 2d FID...

        bruker_dataset_pdata_2d = bruker_utils.BrukerDataset(PDATAPATHS[1])
        data = bruker_dataset_pdata_2d.data
        assert sigfig(data[185, 332], 4) == 1.238E7
        assert sigfig(data[870, 1672], 4) == 5.782E6
        assert sigfig(data[419, 1244], 4) == 1.984E7
        assert data.shape == (1024, 2048)

    def test_samples(self):
        bruker_dataset_fid_1d = bruker_utils.BrukerDataset(FIDPATHS[0])
        samples = bruker_dataset_fid_1d.get_samples()
        assert sigfig(samples[103 // 2], 3) == 0.00928
        assert sigfig(samples[5587 // 2], 3) == 0.508
        assert sigfig(samples[16349 // 2], 3) == 1.49

        bruker_dataset_pdata_1d = bruker_utils.BrukerDataset(PDATAPATHS[0])
        samples = bruker_dataset_pdata_1d.get_samples()
        assert sigfig(samples[12786], 3) == 5.70
        assert sigfig(samples[22315], 3) == 2.51
        assert sigfig(samples[27547], 3) == 0.754

        samples = bruker_dataset_pdata_1d.get_samples(pdata_unit='hz')
        assert sigfig(samples[11938], 4) == 2995
        assert sigfig(samples[15155], 4) == 2455
        assert sigfig(samples[25301], 4) == 753.9

        bruker_dataset_pdata_2d = bruker_utils.BrukerDataset(PDATAPATHS[1])
        data = bruker_dataset_pdata_2d.data
        samples = bruker_dataset_pdata_2d.get_samples()
        contours = bruker_dataset_pdata_2d.contours

        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot()
        ax.contour(*samples, data, levels=contours)
        ax.set_xlim(*reversed(ax.get_xlim()))
        ax.set_ylim(*reversed(ax.get_ylim()))
        plt.show()
