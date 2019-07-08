import re
trans = {
    '<o>': {'add': {'text-decoration': 'overline'}},
    '</o>': {'del': {'text-decoration': 'overline'}},
    '<ins>': {'add': {'text-decoration': 'underline'}},
    '</ins>': {'del': {'text-decoration': 'underline'}},
    '<s>': {'add': {'text-decoration': 'line-through'}},
    '</s>': {'del': {'text-decoration': 'line-through'}},
    '<b>': {'add': {'font-weight': 'bold'}},
    '</b>': {'del': {'font-weight': 'bold'}},
    '<i>': {'add': {'font-style': 'italic'}},
    '</i>': {'del': {'font-style': 'italic'}},
    '<sub>': {'add': {'baseline-shift': 'sub', 'font-size': '.7em'}},
    '</sub>': {'del': {'baseline-shift': 'sub', 'font-size': '.7em'}},
    '<sup>': {'add': {'baseline-shift': 'super', 'font-size': '.7em'}},
    '</sup>': {'del': {'baseline-shift': 'super', 'font-size': '.7em'}},
    '<tt>': {'add': {'font-family': 'monospace'}},
    '</tt>': {'del': {'font-family': 'monospace'}}
}
pattern = '|'.join(re.escape(k) for k in trans.keys())

def dump(state):
    att = {}
    for k, v in state.items():
        for kk, vv in v.items():
            if vv == True:
                att[k] = kk
    return att


def tspan(str):
    state = {
        'text-decoration': {},
        'font-weight': {},
        'font-style': {},
        'baseline-shift': {},
        'font-size': {},
        'font-family': {}
    }

    res = []

    while True:
        m = re.search(pattern, str, flags=re.IGNORECASE | re.UNICODE)
        if m is None:
            res.append(['tspan', dump(state), str])
            break
        if m.start(0) > 0:
            res.append(['tspan', dump(state), str[:m.start(0)]])
        tag = m.group(0)
        cmd = trans[tag]
        if 'add' in cmd:
            for k, v in cmd['add'].items():
                state[k][v] = True
        if 'del' in cmd:
            for k, v in cmd['del'].items():
                del state[k][v]
        str = str[m.end(0):]
        if len(str) == 0:
            break
    return res


def t(x, y):
    return 'translate({}, {})'.format(x, y)


def typeStyle(t):
    styles = {
        '2': '0',
        '3': '80',
        '4': '170',
        '5': '45',
        '6': '126',
        '7': '215',
    }
    t = str(t)
    if t in styles:
        return ';fill:hsl(' + styles[t] + ',100%,50%)'
    else:
        return ''

def jsonml_stringify(res):
    if res is None:
        return ''
    tag = res[0]
    attributes = ' '.join('{}="{}"'.format(k, v) for k, v in res[1].items())
    if len(res) > 2 and isinstance(res[2], str):
        content = res[2]
    else:
        content = ''.join(jsonml_stringify(child) for child in res[2:])
    if len(content) > 0:
        return '<{0} {1}>{2}</{0}>'.format(tag, attributes, content)
    else:
        return '<{0} {1}/>'.format(tag, attributes)


class Renderer(object):
    def __init__(self, options):
        defaults = {
            "vspace": 80,
            "hspace": 640,
            "lanes": 2,
            "bits": 32,
            "fontsize": 14,
            "bigendian": False,
            "fontfamily": 'sans-serif',
            "fontweight": 'normal',
        }

        if 'bigendian' not in options:
            options['bigendian'] = defaults['bigendian']

        if 'fontfamily' not in options:
            options['fontfamily'] = defaults['fontfamily']

        if 'fontweight' not in options:
            options['fontweight'] = defaults['fontweight']

        if 'vspace' not in options:
            options['vspace'] = defaults['vspace']
        else:
            if options['vspace'] <= 19:
                raise ValueError(
                    'vspace must be greater than 19, got {}.'.format(options['vspace']))

        if 'hspace' not in options:
            options['hspace'] = defaults['hspace']
        else:
            if options['vspace'] <= 39:
                raise ValueError(
                    'hspace must be greater than 39, got {}.'.format(options['hspace']))

        if 'lanes' not in options:
            options['lanes'] = defaults['lanes']
        else:
            if options['lanes'] <= 0:
                raise ValueError(
                    'lanes must be greater than 0, got {}.'.format(options['lanes']))

        if 'bits' not in options:
            options['bits'] = defaults['bits']
        else:
            if options['bits'] <= 4:
                raise ValueError(
                    'bits must be greater than 4, got {}.'.format(options['bits']))

        if 'fontsize' not in options:
            options['fontsize'] = defaults['fontsize']
        else:
            if options['fontsize'] <= 5:
                raise ValueError(
                    'fontsize must be greater than 5, got {}.'.format(options['fontsize']))

        self.vspace = options['vspace']
        self.hspace = options['hspace']
        self.lanes = options['lanes']
        self.bits = options['bits']
        self.fontsize = options['fontsize']
        self.bigendian = options['bigendian']
        self.fontfamily = options['fontfamily']
        self.fontweight = options['fontweight']

    def render(self, desc):
        res = ['svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': self.hspace + 9,
            'height': self.vspace * self.lanes + 5,
            'viewbox': ' '.join(str(x) for x in [0, 0, self.hspace + 9, self.vspace * self.lanes + 5])
        }]

        lsb = 0
        mod = self.bits // self.lanes
        self.mod = mod

        for e in desc:
            e['lsb'] = lsb
            e['lsbm'] = lsb % mod
            lsb += e['bits']
            e['msb'] = lsb - 1
            e['msbm'] = e['msb'] % mod
            if 'type' not in e:
                e['type'] = None

        for i in range(0, self.lanes):
            self.index = i
            res.append(self.lane(desc))

        return res

    def lane(self, desc):
        res = ['g', {
            'transform': t(4.5, (self.lanes - self.index - 1) * self.vspace + 0.5)
        }]
        res.append(self.cage(desc))
        res.append(self.labels(desc))
        return res

    def cage(self, desc):
        res = ['g', {
            'stroke': 'black',
            'stroke-width': 1,
            'stroke-linecap': 'round',
            'transform': t(0, self.vspace / 4)
        }]
        res.append(self.hline(self.hspace))
        res.append(self.vline(self.vspace / 2))
        res.append(self.hline(self.hspace, 0, self.vspace / 2))

        i, j = self.index * self.mod, self.mod
        while True:
            if j == self.mod or any(e['lsb'] == i for e in desc):
                res.append(self.vline((self.vspace / 2),
                                      j * (self.hspace / self.mod)))
            else:
                res.append(self.vline((self.vspace / 16),
                                      j * (self.hspace / self.mod)))
                res.append(self.vline((self.vspace / 16),
                                      j * (self.hspace / self.mod)))
            i += 1
            j -= 1
            if j == 0:
                break

        return res

    def labels(self, desc):
        return ['g', {'text-anchor': 'middle'}, self.labelArr(desc)]

    def labelArr(self, desc):
        step = self.hspace / self.mod
        bits = ['g', {'transform': t(step / 2, self.vspace / 5)}]
        names = ['g', {'transform': t(step / 2, self.vspace / 2 + 4)}]
        attrs = ['g', {'transform': t(step / 2, self.vspace)}]
        blanks = ['g', {'transform': t(0, self.vspace / 4)}]

        for e in desc:
            lsbm = 0
            msbm = self.mod - 1
            lsb = self.index * self.mod
            msb = (self.index + 1) * self.mod - 1
            if e['lsb'] // self.mod == self.index:
                lsbm = e['lsbm']
                lsb = e['lsb']
                if e['msb'] // self.mod == self.index:
                    msb = e['msb']
                    msbm = e['msbm']
            else:
                if e['msb'] // self.mod == self.index:
                    msb = e['msb']
                    msbm = e['msbm']
                else:
                    continue
            bits.append(['text', {
                'x': step * (self.mod - lsbm - 1),
                'font-size': self.fontsize,
                'font-family': self.fontfamily,
                'font-weight': self.fontweight
            }, str(lsb)])
            if lsbm != msbm:
                bits.append(['text', {
                    'x': step * (self.mod - msbm - 1),
                    'font-size': self.fontsize,
                    'font-family': self.fontfamily,
                    'font-weight': self.fontweight
                }, str(msb)])
            if 'name' in e:
                ltext = ['text', {
                    'x': step * (self.mod - ((msbm + lsbm) / 2) - 1),
                    'font-size': self.fontsize,
                    'font-family': self.fontfamily,
                    'font-weight': self.fontweight
                }] + tspan(e['name'])
                names.append(ltext)
            if 'name' not in e or e['type'] is not None:
                style = ''.join(['fill-opacity:0.1', typeStyle(e['type'])])
                blanks.append(['rect', {
                    'style': style,
                    'x': step * (self.mod - msbm - 1),
                    'y': 0,
                    'width': step * (msbm - lsbm + 1),
                    'height': self.vspace / 2
                }])
            if 'attr' in e:
                atext = ['text', {
                    'x': step * (self.mod - ((msbm + lsbm) / 2) - 1),
                    'font-size': self.fontsize,
                    'font-family': self.fontfamily,
                    'font-weight': self.fontweight
                }] + tspan(e['attr'])
                attrs.append(atext)
        res = ['g', {}, blanks, bits, names, attrs]
        return res

    def hline(self, len, x=None, y=None):
        res = ['line']
        att = {}
        if x is not None:
            att['x1'] = x
            att['x2'] = len
        else:
            att['x2'] = len
        if y is not None:
            att['y1'] = y
            att['y2'] = y
        res.append(att)
        return res

    def vline(self, len, x=None, y=None):
        res = ['line']
        att = {}
        if x is not None:
            att['x1'] = x
            att['x2'] = x
        if y is not None:
            att['y1'] = y
            att['y2'] = y + len
        else:
            att['y2'] = len
        res.append(att)
        return res


def plotBitfield(desc, options):
    renderer = Renderer(options)
    return jsonml_stringify(renderer.render(desc))

def renderBitfield(desc, options):
    renderer = Renderer(options)
    return renderer.render(desc)
