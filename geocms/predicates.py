import math


def unique(series):
    try:
        return series.unique().size == series.size
    except:
        return False

def some_null(series):
    return series.count() < series.size


def all_null(series):
    return series.count() == 0

def mostly_null(series):
    return series.count() < series.size / 2

def not_null(series):
    return series.count() == series.size


def categorical(series):
    try:
        return series.unique().size < math.sqrt(series.size)
    except:
        return False

def continuous(series):
    return series.dtype.name != 'object' and not categorical(series)

def uniform(series):
    try:
        return series.unique().size == 1
    except:
        return False