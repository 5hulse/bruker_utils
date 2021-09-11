import pathlib
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
    spnam = ['<gauss>', '<Gaus1.1000>', '<Gaus1_180r.1000>', '<>', '<gauss>',
             '<gauss>', '<Squa100.1000>', '<>', '<gauss>', '<gauss>',
             '<gauss>', '<Sinc1.1000>', '<gauss>', '<gauss>', '<>', '<>',
             '<gauss>', '<gauss>', '<>', '<Sinc1.1000>', '<Sinc1.1000>',
             '<Sinc1.1000>', '<Sinc1.1000>'] \
            + 6 * ['<gauss>'] + ['<', '>', '<gauss>'] + 33 * ['<>']
    assert params['SPNAM'] == spnam
