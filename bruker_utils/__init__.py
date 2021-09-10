from pathlib import Path
import re
from typing import Union


def parse_jcampdx(path: Union[Path, str]) -> dict:
    """Retrieve parameters from files written in JCAMP-DX format.

    Parameters
    ----------
    path
        The path to the parameter file.

    Returns
    -------
    dict
        Parameters in file. All values are either strings or lists of strings,
        if the attribute is stored an array of values.

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

    return params
