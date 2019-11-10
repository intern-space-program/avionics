'''
File name: NavFilter.py
Programmed by: Mike Bernard
Date: 2019-11-09

NavFilter.filter_main smooths out the data merged
by NavMerge.merge_main.
'''

from numpy import array, concatenate
from numpy.linalg import norm


def filter_main(state_history, merged_data):
    '''
    Filter the
    :param state_history: All of the previous states
    :type state_history: `dict`
    :param merged_data: The current state, provided by NavMerge
    :type merged_data: `dict`
    :return: `dict` of the current state, smoothed to fit the previous states
    '''
    pass
