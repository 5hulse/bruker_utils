import pathlib
import pytest
from context import bruker_utils


DIR = pathlib.Path(__file__).resolve().parent
FIDPATHS = [DIR / f'data/{i}' for i in range(1, 3)]
PDATAPATHS = [fidpath / 'pdata/1' for fidpath in FIDPATHS]
ALLPATHS = FIDPATHS + PDATAPATHS


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
