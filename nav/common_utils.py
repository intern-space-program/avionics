def weighted_avg(values, weights):
    '''
    Takes a list of values and a list of weights associated
    with those values (index-to-index) and returns a weighted
    averaged of those values as a float.

    :param values: `list` of values to be averaged
    :param weights: `list` of weights for each value (index-to-index)

    :return: `float` The weighted average of the values
    '''
    denom = sum([1 / w ** 2 for w in weights])
    num = sum([1 / w ** 2 * v for v, w in zip(values, weights)])

    return num / denom
