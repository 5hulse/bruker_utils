from pathlib import Path
import re
from typing import FrozenSet, Iterable, List, NewType, Set, Tuple, Union


TAGS = ['', '2', '3']


def parse_jcampdx(
    path: Union[Path, str], convert_numerical_values: bool = True
) -> dict:
    """Retrieve parameters from files written in JCAMP-DX format.

    Parameters
    ----------
    path
        The path to the parameter file.

    convert_numerical_values
        If ``True``, all values which can be converted to numerical objects
        (``int`` or ``float``) will be converted from ``str``.

    Returns
    -------
    dict
        Parameters in file.

    Raises
    ------
    ValueError
        If ``path`` does not exist in the filesystem.
    """
    try:
        with open(path, 'r') as fh:
            txt = fh.read()
    except IOError:
        raise ValueError(f'The path {path} does not exist!')

    params = {}
    array_pattern = r'(?=##\$(.+?)= \(\d+\.\.\d+\)\n([\s\S]+?)##)'
    array_matches = re.finditer(array_pattern, txt)

    for match in array_matches:
        key, value = match.groups()
        params[key] = value.rstrip('\n').replace('\n', ' ').split(' ')

    oneline_pattern = r'(?=##\$(.+?)= (.+?)\n##)'
    oneline_matches = re.finditer(oneline_pattern, txt)

    for match in oneline_matches:
        key, value = match.groups()
        params[key] = value

    if convert_numerical_values:
        for key, value in params.items():
            if isinstance(value, str) and _isint(value):
                params[key] = int(value)
            elif isinstance(value, str) and _isfloat(value):
                params[key] = float(value)
            elif isinstance(value, list) and all(_isint(v) for v in value):
                params[key] = [int(v) for v in value]
            elif isinstance(value, list) and all(_isfloat(v) for v in value):
                params[key] = [float(v) for v in value]

    return params

def _isint(string: str) -> bool:
    """Determine whether ``string`` represents an integer."""
    return re.match(r'^-?\d+$', string) is not None


def _isfloat(string: str) -> bool:
    """Determine whether ``string`` represents a float."""
    return re.match(r'^-?\d+\.\d+$', string) is not None


class BrukerDataset:

    def __init__(self, directory: str = '.') -> None:
        directory = Path(directory).resolve()
        if not directory.is_dir():
            raise IOError(f'{directory} doesn\'t exist.')

        info = self._determine_experiment_type(directory)
        if info is None:
            raise ValueError(
                '{directory} does not possess the requisite files.'
            )

        self._dim, self._dtype, files = \
            [info[key] for key in ['dim', 'dtype', 'files']]
        del info

        self._datafile = files.pop('data')
        self._paramfiles = files

    def __str__(self):
        datatype = 'Time domain' if self.dtype == 'fid' else 'Processed data'
        paramfiles = ','.join([k for k in self._paramfiles.keys()])
        string = (f'<{__class__.__module__}.{__class__.__qualname__} at '
                  f'{hex(id(self))}>\n'
                  f'Dataset directory:   {str(self.directory)}\n'
                  f'Dimensions:          {self.dim}\n'
                  f'Data type:           {datatype}\n'
                  f'Parameter filenames: {paramfiles}')
        return string

    def __repr__(self):
        return (f'{__class__.__module__}.{__class__.__qualname__}'
                f'(\'{str(self.directory)}\')')

    @property
    def dim(self) -> int:
        return self._dim

    @dim.setter
    def dim(self, value):
        raise RuntimeError('`dim` cannot be mutated!')

    @property
    def dtype(self) -> str:
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        raise RuntimeError('`dtype` cannot be mutated!')

    @property
    def directory(self) -> Path:
        return self._datafile.parent

    @directory.setter
    def directory(self, value):
        raise RuntimeError('`directory` cannot be mutated!')

    @property
    def binary_format(self) -> str:
        if self.dtype == 'fid':
            params = self.get_parameters(filenames='acqus')
            dtyp = params['DTYPA']
            bytord = params['BYTORDA']
        elif self.dtype == 'pdata':
            params = self.get_parameters(filenames='procs')
            dtyp = params['DTYPP']
            bytord = params['BYTORDP']

        return (('<' if bytord == 0 else '>') +
                ('i4' if dtyp == 0 else 'f8'))

    @binary_format.setter
    def binary_format(self, value):
        raise RuntimeError('`binary_format` cannot be mutated!')

    def get_parameters(
        self, filenames: Union[Iterable[str], str, None] = None
    ) -> dict:
        if isinstance(filenames, str):
            filenames = [filenames]
        elif isinstance(filenames, (list, tuple, set, frozenset)):
            pass
        elif filenames is None:
            filenames = [k for k in self._paramfiles.keys()]
        else:
            raise TypeError('Invalid type for `filenames`.')

        params = {}
        for name in filenames:
            try:
                params[name] = parse_jcampdx(self._paramfiles[name])
            except KeyError:
                raise ValueError(
                    f'`{name}` is an invalid filename. Valid options '
                    f"are:\n{', '.join([k for k in self._paramfiles.keys()])}."
                )

        return next(iter(params.values())) if len(params) == 1 else params

    def _determine_experiment_type(self, directory: Path) -> Union[dict, None]:
        """Determine the type of Bruker data stored in ``directory``.

        This function is used to determine

        a) whether the specified data is time-domain or pdata
        b) the dimension of the data (checks up to 3D).

        If the data satisfies the required criteria for a particular dataset
        type, a dictionary of information will be returned. Otherwise,
        ``None`` will be returned.

        Parameters
        ----------
        directory
            The path to the directory of interest.

        Returns
        -------
        Dictionary with the entries:

        * ``'dim'`` (``int``) The dimension of the data.
        * ``'dtype'`` (``'fid'`` or ``'pdata'``) The type of data (raw
          time-domain or pdata).
        * ``'files'`` (``List[pathlib.Path]``) Paths to data and parameter
          files.
        """
        for option in self._compile_experiment_options(directory):
            files = option['files'].values()
            if self._all_paths_exist(files):
                return option
        return None

    @staticmethod
    def _all_paths_exist(files: Iterable[Path]) -> bool:
        """Determine if all the paths in ``files`` exist.

        Parameters
        ----------
        files
            File paths to check.
        """
        return all([f.is_file() for f in files])

    @staticmethod
    def _compile_experiment_options(directory: Path) -> List[dict]:
        """Generate information dictionaries for different experiment types.

        Compiles dictionaries of information relavent to each experiment type:

        * ``'files'`` - The expected paths to data and parameter files.
        * ``'dim'`` - The data dimension.
        * ``'dtype'`` - The type of data (time-domain or pdata).

        Parameters
        ----------
        directory
            Path to the directory of interest.
        """
        twoback = directory.parents[1]
        options = []
        for i in range(1, 4):
            acqusnames = [f'acqu{x}s' for x in TAGS[:i]]
            acqusfiles = {
                name: path for (name, path) in
                zip(
                    acqusnames,
                    (directory / name for name in acqusnames)
                )
            }

            fidfiles = {
                **{'data': directory / ('fid' if i == 1 else 'ser')},
                **acqusfiles
            }
            options.append(
                {
                    'files': fidfiles,
                    'dtype': 'fid',
                    'dim': i
                }
            )

            acqusfiles = {
                name: path for (name, path) in
                zip(
                    acqusnames,
                    (twoback / path.name for path in acqusfiles.values())
                )
            }
            procsnames = [f'proc{x}s' for x in TAGS[:i]]
            procsfiles = {
                name: path for (name, path) in
                zip(
                    procsnames,
                    (directory / name for name in procsnames)
                )
            }
            pdatafiles = {
                **{'data': directory / f"{i}{i * 'r'}"},
                **acqusfiles,
                **procsfiles,
            }

            options.append(
                {
                    'files': pdatafiles,
                    'dtype': 'pdata',
                    'dim': i
                }
            )

        return options
