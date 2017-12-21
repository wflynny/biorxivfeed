"""
Adopted from `github.com/pubs/pubs` repository
"""
import sys
import re
import os
import subprocess


COLOR_LIST = {u'black': '0', u'red': '1', u'green': '2', u'yellow': '3', u'blue': '4',
              u'magenta': '5', u'cyan': '6', u'grey': '7',
              u'brightblack': '8', u'brightred': '9', u'brightgreen': '10',
              u'brightyellow': '11', u'brightblue': '12', u'brightmagenta': '13',
              u'brightcyan': '14', u'brightgrey': '15',
              u'darkgrey': '8', # == brightblack
              u'gray': '7', u'darkgray': '8', u'brightgray': '15', # gray/grey spelling
              u'purple': '5', # for compatibility reasons
              u'white': '15' # == brightgrey
             }
for c in range(256):
    COLOR_LIST[str(c)] = str(c)

def _color_supported(stream, force=False):
    """Return the number of supported colors"""
    min_colors = 8 if force else 0
    if sys.platform == 'win32' and 'ANSICON' not in os.environ:
        return min_colors

    if hasattr(stream, 'isatty') and stream.isatty(): # we have a tty
        try:
            import curses
            curses.setupterm()
            return max(min_colors, curses.tigetnum('colors'))
        except Exception: # not picky.
            pass

    if force:
        p = subprocess.Popen(['tput', 'colors'], stdout=subprocess.PIPE)
        return max(min_colors, int(p.communicate()[0]))
    return 0

def generate_colors(stream, color=True, bold=True, italic=True, force_colors=False):
    """Generate 256 colors, based on configuration and detected support

    :param color:         generate colors. If False, bold and italic will not change
                          the current color.
    :param bold:          generate bold colors, if False, bold color are the same as
                          normal colors.
    :param italic:        generate italic colors
    """
    colors = {u'bold': u'', u'italic': u'', u'end': u'', u'': u''}
    for name, code in COLOR_LIST.items():
        colors[name]       = u''
        colors[u'b' +name] = u''
        colors[u'i' +name] = u''
        colors[u'bi'+name] = u''

    color_support = _color_supported(stream, force=force_colors) >= 8

    if (color or bold or italic) and color_support:
        bold_flag, italic_flag = '', ''
        if bold:
            colors['bold'] = u'\033[1m'
            bold_flag = '1;'
        if italic:
            colors['italic'] = u'\033[3m'
            italic_flag = '3;'
        if bold and italic:
            colors['bolditalic'] = u'\033[1;3m'

        for name, code in COLOR_LIST.items():
            if color:
                colors[name] = u'\033[38;5;{}m'.format(code)
                colors[u'b'+name] = u'\033[{}38;5;{}m'.format(bold_flag, code)
                colors[u'i'+name] = u'\033[{}38;5;{}m'.format(italic_flag, code)
                colors[u'bi'+name] = u'\033[{}38;5;{}m'.format(bold_flag, italic_flag, code)

            else:
                if bold:
                    colors.update({u'b'+name: u'\033[1m' for i, name in enumerate(COLOR_LIST)})
                if italic:
                    colors.update({u'i'+name: u'\033[3m' for i, name in enumerate(COLOR_LIST)})
                if bold or italic:
                    colors.update({u'bi'+name: u'\033[{}{}m'.format(bold_flag, italic_flag) for i, name in enumerate(COLOR_LIST)})

        if color or bold or italic:
            colors[u'end'] = u'\033[0m'

    return colors

COLORS_OUT = generate_colors(sys.stdout, color=True, bold=True, italic=True)
COLORS_ERR = generate_colors(sys.stderr, color=True, bold=True, italic=True)

def dye_out(s, color='end'):
    """Color a string for output on stdout"""
    return u'{}{}{}'.format(COLORS_OUT[color], s, COLORS_OUT['end'])

def dye_err(s, color='end'):
    """Color a string for output on stderr"""
    return u'{}{}{}'.format(COLORS_ERR[color], s, COLORS_OUT['end'])

# undye
undye_re = re.compile('\x1b\[[;\d]*[A-Za-z]')
def undye(s):
    """Purge string s of color"""
    return undye_re.sub('', s)
