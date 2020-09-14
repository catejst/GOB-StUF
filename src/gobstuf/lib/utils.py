from functools import reduce
from operator import getitem


def get_value(dict, *args):
    """
    Get a dictionary value by path (a list of keys).

    Example:
        given a dict { 'a': { 'b': 'c' } }
        in order to access dict['a']['b'] without being sure that keys a en b exist
        you normally would program dict.get('a', {}).get('b')

        with this function you will have the same result using _get_value(dict, 'a', 'b')
    :param dict:
    :param *args: list of key values
    :return:
    """
    try:
        return reduce(getitem, args, dict)
    except (KeyError, TypeError):
        pass
