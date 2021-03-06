import json
import time
import datetime

class Record(object):
    def __init__(self, attrs=None):
        self._attrs = attrs or []
    def get_attr(self, name):
        ret = None
        if hasattr(self, name):
            ret = getattr(self, name)
        else:
            getter = "get_"+name
            if hasattr(self, getter):
                ret = getattr(self, getter)
        if callable(ret):
            return ret()
        else:
            return ret
    def to_dict(self):
        ret = {}
        for p in self._attrs:
            ret[p] = self.get_attr(p)
        return ret


class RecordEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Record):
            return o.to_dict()
        return json.JSONEncoder.default(self, o)

_re = RecordEncoder(
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    encoding='utf-8',
    default=None,
)

def dump_json(obj, fp, skipkeys=False, ensure_ascii=True, check_circular=False,
        allow_nan=True, cls=None, indent=None, separators=None,
        encoding='utf-8', default=None, **kw):
    # cached encoder
    if (not skipkeys and ensure_ascii and
        check_circular and allow_nan and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and default is None and not kw):
        iterable = _re.iterencode(obj)
    else:
        if cls is None:
            cls = RecordEncoder
        iterable = cls(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
            check_circular=check_circular, allow_nan=allow_nan, indent=indent,
            separators=separators, encoding=encoding,
            default=default, **kw).iterencode(obj)
    # could accelerate with writelines in some versions of Python, at
    # a debuggability cost
    for chunk in iterable:
        fp.write(chunk)

def dumps_json(obj, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, cls=None, indent=None, separators=None,
        encoding='utf-8', default=None, **kw):
    # cached encoder
    if (not skipkeys and ensure_ascii and
        check_circular and allow_nan and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and default is None and not kw):
        return _re.encode(obj)
    if cls is None:
        cls = RecordEncoder
    return cls(
        skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan, indent=indent,
        separators=separators, encoding=encoding, default=default,
        **kw).encode(obj)


def to_csv_value(v):
    if v == None:
        return ''
    if isinstance(v, str):
        return v.replace(',', '')
    return str(v)

def table_to_csv(ret, fout):
    f = False
    if isinstance(fout, str):
        fout = open(fout, 'w')
        f = True
    fout.write(",".join(ret["columns"]))
    fout.write("\n")
    for e in ret["data"]:
        fout.write(",".join([to_csv_value(c) for c in e]))
        fout.write("\n")
    if f:
        fout.close()

def load_csv(fin):
    f = False
    if isinstance(fin, str):
        fin = open(fin)
        f = True
    def pline(line):
        if line[-1] == '\n':
            line = line[:-1]
        fs = line.split(',')
        return [int(e) if e.isdigit() else e for e in fs]
    columns = pline(fin.readline())
    data = []
    for line in fin:
        data.append(pline(line))
    if f:
        fin.close()
    return {'columns':columns, 'data':data}

def time_to_string(t, full=True):
    return time.strftime("%m-%d %H:%M:%S" if full else "%H:%M:%S", time.localtime(t))

def get_date_ranges(mindate, maxdate, period):
    mintm = datetime.datetime.strptime(mindate, "%Y-%m-%d").date()
    maxtm = datetime.datetime.strptime(maxdate, "%Y-%m-%d").date()
    delta = datetime.timedelta(days = 1)
    ret = []
    def add_new_range(start, end):
        s = start.strftime("%Y-%m-%d")
        e = end.strftime("%Y-%m-%d")
        if len(ret) == 0 or ret[-1][0] != s:
            ret.append((s, e))
    curtm = mintm
    while curtm <= maxtm:
        if period == 'day':
            add_new_range(curtm, curtm+delta)
        elif period == 'week':
            sd = curtm - datetime.timedelta(days = curtm.weekday())
            ed = sd + datetime.timedelta(days = 7)
            add_new_range(sd, ed)
        elif period == 'month':
            sd = datetime.date(curtm.year, curtm.month, 1)
            ed = None
            if curtm.month == 12:
                ed = datetime.date(curtm.year+1, 1, 1) - delta
            else:
                ed = datetime.date(curtm.year, curtm.month+1, 1) - delta
            add_new_range(sd, ed)
        else:
            raise Exception("Illegal period %s" % period)
        curtm  = curtm + delta
    return ret
