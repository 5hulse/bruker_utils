import functools
from pathlib import Path
import re
from typing import Iterable, List, Union
import numpy as np

from ._version import __version__


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
    params: dict
        Parameters in the file.

    Raises
    ------
    ValueError
        If ``path`` does not exist in the filesystem.

    Notes
    -----
    There are two different parameters types which are stored in these files.
    One is for single values, and the other is for arrayed values.

    Single-valued parameters are denoted like this:

    .. code:: text

        ##$SW_h= 5494.50549450549

    These will appear in ``params`` as follows:

    .. code:: python3

        params = {..., 'SW_h': 5494.50549450549, ...}

    Arrayed values are denoted like this:

    .. code:: text

        ##$P= (0..63)
        10.8 10.8 21.6 0 0 19.8 30 60 20000 0 0 80000 80000 0 0
        200000 1000 2500 10000 600 2500 0 0 0 0 250 0 10.8 1000
        1200 0 0 0 0 0 0 0 0 0 0 0 0 0 0

    Each value in the array is separated by either a space or a newline. The
    values are stored in a list:

    .. code:: python3

        params = {...,
         'P': [10.8, 10.8, 21.6, 0, 0, 19.8, 30, 60, 20000, 0, 0,
               80000, 80000, 0, 0, 200000, 1000, 2500, 10000, 600,
               2500, 0, 0, 0, 0, 250, 0, 10.8, 1000, 1200, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         ...}

    Example
    -------

    .. code:: pycon

        >>> import bruker_utils as butils
        >>> path = '/path/to/.../file' # Can be relative or absolute
        >>> params = butils.parse_jcampdx(path)
        >>> for key, value in params.items():
        ...     print(f'{key}:  {value}')
        ACQT0:  -2.26890760309556
        AMP:  [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
               100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
               100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        AMPCOIL:  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        AQSEQ:  0
        AQ_mod:  3
        AUNM:  <au_zg>
        AUTOPOS:  <>
        BF1:  500.13
        BF2:  500.13
        BF3:  500.13
        BF4:  500.13
        BF5:  500.13
        BF6:  500.13
        BF7:  500.13
        BF8:  500.13
        --snip--
        YMAX_a:  5188289
        YMIN_a:  -3815309
        ZGOPTNS:  <>
        ZL1:  120
        ZL2:  120
        ZL3:  120
        ZL4:  120
        scaledByNS:  no
        scaledByRG:  no
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

    return dict(sorted(params.items()))


def _isint(string: str) -> bool:
    """Determine whether ``string`` represents an integer."""
    return re.match(r'^-?\d+$', string) is not None


def _isfloat(string: str) -> bool:
    """Determine whether ``string`` represents a float."""
    return re.match(r'^-?\d+\.\d+$', string) is not None


class BrukerDataset:
    """Represenation of a Bruker Dataset.

    Parameters
    ----------
    directory
        Path to the directory containing the data.

        Different files are expected to exist, dependent on the data type you
        are importing (note that ``..`` denotes the parent directory of the
        preceeding directory):

        * 1D data

          - Raw FID

            + ``directory/fid``
            + ``directory/acqus``

          - Processed data

            + ``directory/1r``
            + ``directory/../../acqus``
            + ``directory/procs``

        * 2D data

          - Raw FID

            + ``directory/ser``
            + ``directory/acqus``
            + ``directory/acqu2s``

          - Processed data

            + ``directory/2rr``
            + ``directory/../../acqus``
            + ``directory/../../acqu2s``
            + ``directory/procs``
            + ``directory/proc2s``

        * 3D data

          - Raw FID

            + ``directory/ser``
            + ``directory/acqus``
            + ``directory/acqu2s``
            + ``directory/acqu3s``

          - Processed data

            + ``directory/3rrr``
            + ``directory/../../acqus``
            + ``directory/../../acqu2s``
            + ``directory/../../acqu3s``
            + ``directory/procs``
            + ``directory/proc2s``
            + ``directory/proc3s``

    Raises
    ------
    IOError
        If ``directory`` doesn't exist.

    ValueError
        If ``directory`` does not contain the files expected of a
        Bruker dataset. See the description of the class for details.
    """
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
        """The number of experiment dimensions."""
        return self._dim

    @dim.setter
    def dim(self, value):
        raise RuntimeError('`dim` cannot be mutated!')

    @property
    def dtype(self) -> str:
        """Return the type of data.

        Will be either ``'fid'`` or ``'pdata'``.
        """
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        raise RuntimeError('`dtype` cannot be mutated!')

    @property
    def directory(self) -> Path:
        """Return the full path to the data directory."""
        return self._datafile.parent

    @directory.setter
    def directory(self, value):
        raise RuntimeError('`directory` cannot be mutated!')

    @property
    def binary_format(self) -> str:
        """Return the format of the binary datafiles.

        Four possibilities:

        * ``'<i4'`` - Little endian, 32-bit integer.
        * ``'>i4'`` - Big endian, 32-bit integer.
        * ``'<f8'`` - Little endian, 64-bit float.
        * ``'>f8'`` - Big endian, 64-bit float.
        """
        if self.dtype == 'fid':
            params = self.get_parameters(filenames='acqus')['acqus']
            dtyp = params['DTYPA']
            bytord = params['BYTORDA']
        elif self.dtype == 'pdata':
            params = self.get_parameters(filenames='procs')['procs']
            dtyp = params['DTYPP']
            bytord = params['BYTORDP']

        return (('<' if bytord == 0 else '>') +
                ('i4' if dtyp == 0 else 'f8'))

    @binary_format.setter
    def binary_format(self, value):
        raise RuntimeError('`binary_format` cannot be mutated!')

    @property
    def valid_parameter_filenames(self) -> List[str]:
        """Return a list of parameter filenames.

        The elements are a complete set of the valid strings for the
        ``filenames`` argument in :py:meth:`get_parameters`.
        """
        match = re.search(r'filenames: (.+?)$', self.__str__())
        return match.group(1).split(',')

    def get_parameters(
        self, filenames: Union[Iterable[str], str, None] = None
    ) -> dict:
        """Return parameters found in ``filenames``.

        Parameters
        ----------
        filenames
            Files to extract parameters from. If this is set to ``None``,
            all valid files will be read.

        Returns
        -------
        params: dict
            A dictionary containing the parameters of each file in
            sub-dictionaries.

        Raises
        ------
        TypeError
            If ``filenames`` has an invalid type. It should be ``None``, a
            ``str``, or an iterable object (``list``, ``tuple``, ``set``,
            etc.) of ``str`` objects.

        ValueError
            If at least one value in ``filenames`` is invalid.

        Notes
        -----
        To determine the list of valid names for ``filenames``, you can
        use :py:meth:`valid_parameter_filenames`:

        .. code:: pycon

            >>> import bruker_utils as butils
            >>> # This is a 2-dimensional processed dataset
            >>> dataset = butils.BrukerDataset(<path>)
            >>> print(dataset.valid_parameter_filenames)
            ['acqus', 'acqu2s', 'procs', 'proc2s']
        """
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

        return params

    def _determine_experiment_type(self, directory: Path) -> Union[dict, None]:
        """Determine the type of Bruker data stored in ``directory``.

        This function is used to determine:

        a) whether the specified data is time-domain or pdata
        b) the dimension of the data (checks up to 3D).

        If the data satisfies the required criteria for a particular
        experiment type, a dictionary of information will be returned.
        Otherwise, ``None`` will be returned.

        Parameters
        ----------
        directory
            The path to the directory of interest.

        Returns
        -------
        exptype: Union[dict, None]
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

        Returns
        -------
        allexist: bool
            ``True`` is all paths exist, ``False`` if not.
        """
        return all([f.is_file() for f in files])

    @staticmethod
    def _compile_experiment_options(directory: Path) -> List[dict]:
        """Generate information dictionaries for different experiment types.

        Compiles dictionaries of information relavent to each experiment type.


        Parameters
        ----------
        directory
            Path to the directory of interest.

        Returns
        -------
        options: List[dict]
            Infomation relating to each experiment option. Each item
            is a dictionary with the following entires:

            * ``'files'`` - The expected paths to data and parameter files.
            * ``'dim'`` - The data dimension.
            * ``'dtype'`` - The type of data (time-domain or pdata).
        """
        twoback = directory.parents[1]
        options = []
        tags = ['', '2', '3']
        # Start from higher dim datasets. A 2D FID dataset's files
        # are a subset of a 3D FID dataset's (ser, acqus, acqu2s).
        for i in range(3, 0, -1):
            acqusnames = [f'acqu{x}s' for x in tags[:i]]
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
            procsnames = [f'proc{x}s' for x in tags[:i]]
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

    @staticmethod
    def _complexify(data: np.ndarray) -> np.ndarray:
        """Make time-domain data complex.

        Parameters
        ----------
        data
            Data to be converted to complex form.

        Returns
        -------
        complex_data: numpy.ndarray
            Complex data.

            Complex data is stored in the form
            ``[re[0], im[0], re[1], im[1], ...]``, This function takes an
            input with shape ``(2N,)`` and returns
            ``[re[0] + im[0]j, re[1] + im[1]j, ...]`` with shape ``(N,)``.
            """
        return data[::2] + 1j * data[1::2]

    @staticmethod
    def _remove_zeros(data: np.ndarray, shape: Iterable[int]) -> np.ndarray:
        """Strip zeros from data.

        Bruker ensures that each stored FID takes up a multiple of 1024 bytes
        of storage, even if ``TD`` is not a multiple of 256 (each datapoint
        takes either 4 or 8 bytes of space). To do this, each FID is padded
        with zeros. This function determines the number of trailing zeros
        and removes them.

        Parameters
        ----------
        data
            Data to be treated. This should be a one-dimensional array with
            the number of elements matching the product of the elements in
            ``shape``.

        shape
            The expected shape of the data.

        Returns
        -------
        zeroless_data: numpy.ndarray
            Data with padded zeros removed.
        """
        size = data.size
        # Number of FIDs
        fids = functools.reduce(lambda x, y: x * y, shape[:-1])
        blocksize = size // fids
        slicesize = blocksize - shape[-1]
        mask = np.ones(size).astype(bool)
        for i in range(1, fids + 1):
            mask[(i * blocksize - slicesize):(i * blocksize)] = False
        return data[mask]

    @staticmethod
    def _repartition_data(
        data: np.ndarray, si: Iterable[int], xdim: Iterable[int]
    ) -> np.ndarray:
        """Correctly reorganise partitioned data.

        Some data (typically older data) is stored in `sub-matrix` format,
        such that chucnks of the data are partitioned into smaller blocks.
        The ``XDIM`` parameters in the ``procs`` files dictate the size of
        each partition. This function takes in partitioned data and
        re-arranges it to the correct order.

        Parameters
        ----------
        data
            Data to be repartitioned. This should be a one-dimensional array
            with the number of elements matching the product of the elements
            in ``shape``.

        si
            The expected shapoe of the data.

        xdim
            The size of partitions in each dimension.

        Returns
        -------
        repartitioned_data: numpy.ndarray
            Correctly repartitioned data.
        """
        newdata = np.zeros(data.shape, dtype=data.dtype)
        blocks = [i // j for i, j in zip(si, xdim)]
        x = 0
        for i in range(blocks[0]):
            for j in range(xdim[0]):
                for k in range(blocks[1]):
                    idx = j + (k * xdim[0]) + (i * blocks[0])
                    newslice = slice(x * xdim[1], (x + 1) * xdim[1])
                    oldslice = slice(idx * xdim[1], (idx + 1) * xdim[1])
                    newdata[newslice] = data[oldslice]
                    x += 1

        return newdata

    @property
    def data(self) -> np.ndarray:
        """Return the data."""
        data = np.fromfile(self._datafile,
                           dtype=self.binary_format).astype('float64')

        if self.dtype == 'fid':
            nc = self.get_parameters(filenames='acqus')['acqus']['NC']
            data = self._complexify(data)
            if self.dim > 1:
                # As digits are before characters in ASCII,
                # This will result in a list starting from the highest dim.
                # i.e. for 3D, list would be ['acqu3s', 'acqu2s', 'acqus']
                files = sorted([k for k in self._paramfiles if 'acqu' in k])
                shape = \
                    [self.get_parameters(filenames=f)[f]['TD'] for f in files]
                shape[-1] //= 2
                data = self._remove_zeros(data, shape)
                data = data.reshape(shape)

        elif self.dtype == 'pdata':
            nc = self.get_parameters(filenames='procs')['procs']['NC_proc']
            if self.dim > 1:
                files = sorted([k for k in self._paramfiles if 'proc' in k])
                params = self.get_parameters(filenames=files)
                shape = [p['SI'] for p in params.values()]
                xdim = [p['XDIM'] for p in params.values()]
                data = self._repartition_data(data, shape, xdim)
                data = data.reshape(shape)

        return data / (2 ** -nc)

    def get_samples(
        self, pdata_unit: str = 'ppm', meshgrid: bool = True
    ) -> Iterable[np.ndarray]:
        """Return the points at which the data is sampled.

        For time-domain data, this will return the timepoints at which the
        FID was sampeld. For processed data, this will return the chemical
        shifts.

        Parameters
        ----------
        pdata_unit
            The unit to expressed the chemical shifts if, if the dataset
            corresponds to processed data. Valid options are ``'ppm'`` or
            ``'hz'``.

        meshgrid
            If ``True``, samples for multidimensional experiments will be
            arrayed using
            `numpy.meshgrid <https://numpy.org/doc/stable/reference/\
                    generated/numpy.meshgrid.html>`_.

        Returns
        -------
        samples: Iterable[np.ndarray]
            The samples in each dimension.

        Notes
        -----
        For data with more than 1 dimension, the returned object is a list
        of arrays with the same shape as the data, formed by using
        `numpy.meshgrid
        <https://numpy.org/doc/stable/reference/generated/\
                numpy.meshgrid.html>`_,
        making the output very convienient for plotting pourposes.
        """
        if pdata_unit not in ['ppm', 'hz']:
            raise ValueError('`pdata_unit` should be \'ppm\' or \'hz\'.')

        acqusfiles = sorted([k for k in self._paramfiles if 'acqu' in k])
        acqusparams = self.get_parameters(filenames=acqusfiles)
        sw = [p['SW_h'] for p in acqusparams.values()]
        pts = self.data.shape
        if self.dtype == 'fid':
            samples = [np.linspace(0, (p - 1) / s, p) for p, s in zip(pts, sw)]
        elif self.dtype == 'pdata':
            offset = [p['O1'] for p in acqusparams.values()]
            samples = [np.linspace((s / 2) + off, -(s / 2) + off, p)
                       for p, s, off in zip(pts, sw, offset)]
            if pdata_unit == 'ppm':
                sfo = [p['SFO1'] for p in acqusparams.values()]
                samples = [samp / s for samp, s in zip(samples, sfo)]

        if self.dim > 1 and meshgrid:
            samples = np.meshgrid(*samples, indexing='ij')

        return list(reversed(samples))

    @property
    def contours(self) -> Union[Iterable[float], None]:
        """Return a stored list of contour levels.

        For multidimensional processed datasets, the file ``clevels`` is
        searched for, and if found, the contour levels stated in it are
        returned. If ``clevels`` could not be found, ``None`` is returned.
        """
        clevels = self.directory / 'clevels'
        if not clevels.is_file():
            print('WARNING: clevels file could not be found. None will be'
                  'returned')
            return None

        levels = \
            [float(x) for x in parse_jcampdx(clevels)['LEVELS']
             if x not in ['', '0']]
        return levels

        # I originally had this, but scaling seemed to be an issue...
        # params = parse_jcampdx(clevels)
        # maxlev = params['MAXLEV']
        # negbase = params['NEGBASE']
        # posbase = params['POSBASE']
        # negincr = params['NEGINCR']
        # posincr = params['POSINCR']
        # neg = [negbase * (negincr ** i) for i in range(maxlev - 1, -1, -1)]
        # pos = [posbase * (posincr ** i) for i in range(maxlev)]
        # levels = neg + pos
