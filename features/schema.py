# http://terrapyn.org/datasets/my-data/?col1__like=foo%&col2=bar&col

import functools
import operator

class And(object):
    def __init__(self, *clauses):
        self.clauses = clauses

    def compile(self):
        return " AND \n".join("({0})".format(clause.compile()) for clause in self.clauses)

    def rvals(self):
        functools.reduce(operator.add, (c.rvals() for c in self.clauses))

    def add(self, clause):
        if isinstance(clause, And):
            self.clauses += clause.clauses
        else:
            self.clauses += (clause,)
        return self

class Or(object):
    def __init__(self, *clauses):
        self.clauses = clauses

    def compile(self):
        return " OR \n".join("({0})".format(clause.compile()) for clause in self.clauses)

    def rvals(self):
        functools.reduce(operator.add, (c.rvals() for c in self.clauses))

    def add(self, clause):
        if isinstance(clause, Or):
            self.clauses += clause.clauses
        else:
            self.clauses += (clause,)
        return self

class Not(object):
    def __init__(self, clause):
        self.clause = clause

    def compile(self):
        return "NOT ({0})".format(self.clause.compile())

    def rvals(self):
        return self.clause.rvals()


class Clause(object):
    def __init__(self, lval, rval):
        self.lval = lval
        self.rval = rval

    def repr_lval(self):
        return '"{0}"."{1}"'.format(self.rval.dataset.name, self.rval.name)

    def repr_rval(self):
        if hasattr(self.rval, 'name'):
            return '"{0}"."{1}"'.format(self.rval.dataset.name, self.rval.name)
        else:
            return "%s"

    def rvals(self):
        """
        This is the value that gets plugged into the cursor.execute for this clause.

        :return:
        """
        if hasattr(self.rval, 'name'):
            return []
        else:
            return [self.parse_rval()]

    def parse_rval(self):
        return self.rval


class BinaryOperator(Clause):
    op = None

    def __init__(self, lval, rval):
        super(BinaryOperator, self).__init__(lval, rval)

    def compile(self):
        return "{0} {1} {2}".format(self.repr_lval(), self.op, self.repr_rval())


class Equals(BinaryOperator):
    op = "="


class SimpleKeywordArgumentFilterParser(object):
    separator = '__'
    ops = {
        'eq': Equals,
    }

    def __init__(self, kwargs):
        self.kwargs = kwargs

    def parse_arg(self, arg):
        k, v = arg
        if self.separator in k:
            name, op = k.rsplit(self.separator, 1)
            return self.ops[op](name, v)
        else:
            return Equals(k, v)

    def parse(self):
        if len(self.kwargs) == 1:
            return self.parse_arg(self.kwargs.items().next())
        else:
            return And(*[self.parse_arg(arg) for arg in self.kwargs.items()])



class SimpleFeatureSet(object):

    def __init__(self, dataset, offset=None, limit=None):
        self.dataset = dataset
        self.filters = None
        self.offset = offset
        self.limit = limit
        self.cursor = None

    def sql(self):
        select_order = ','.join(field.selection_name for field in self.dataset)

        query = """\
            select {select_order}
            from {table_name}""".format(
            select_order=select_order,
            table_name=self.dataset.name,
        )
        if self.filters:
            query += "\nwhere {filters}".format(filters=self.filters.compile())
        if self.offset:
            query += "\noffset {filters}".format(filters=self.filters.compile())
        if self.limit:
            query += "\nlimit {limit}".format(limit=self.limit)

        return query

    def get_cursor(self):
        self.cursor = self.dataset.get_cursor()
        self.cursor.execute(self.sql(), *self.filters.rvals())
        return self.cursor

    def __iter__(self):
        self.get_cursor()
        return self

    def next(self):
        record = self.cursor.fetchone()
        if record:
            return self.dataset.feature(record=record)
        else:
            raise StopIteration

    def filter(self, **kwargs):
        new_filters = SimpleKeywordArgumentFilterParser(kwargs).parse()
        if self.filters is None:
            self.filters = new_filters
        elif not isinstance(self.filters, And):
            self.filters = And(self.filters)
            self.filters.add(new_filters)
        else:
            self.filters.add(new_filters)

    def exclude(self, **kwargs):
        new_filters = Not(SimpleKeywordArgumentFilterParser(kwargs).parse())
        if self.filters is None:
            self.filters = new_filters
        elif not isinstance(self.filters, And):
            self.filters = And(self.filters)
            self.filters.add(new_filters)
        else:
            self.filters.add(new_filters)









