#!/usr/bin/env python3

import re

BOLD = '\x02'
ITALIC = '\x1d'
UNDERLINE = '\x1f'
RESET = '\x0f'

MARKDOWN = {
    BOLD: '**',
    ITALIC: '_',
    UNDERLINE: '__',
}

# Codes with no Discord equivalent: color (with optional fg,bg digits),
# hex color, monospace, reverse video, legacy underline, and strikethrough.
# Stripped entirely.
STRIP_RE = re.compile(
    r'\x03(\d{1,2}(,\d{1,2})?)?|\x04([0-9a-fA-F]{6}(,[0-9a-fA-F]{6})?)?|[\x11\x15\x16\x1e]')


def irc_to_discord(text):
    text = STRIP_RE.sub('', text)
    out = []
    open_formats = []  # stack of control codes currently open, innermost last

    def close_all():
        while open_formats:
            out.append(MARKDOWN[open_formats.pop()])

    for char in text:
        if char in MARKDOWN:
            if char in open_formats:
                # Closing a format that isn't innermost: close everything
                # opened after it, close it, then reopen the others so the
                # markdown stays properly nested.
                reopen = []
                while open_formats[-1] != char:
                    code = open_formats.pop()
                    out.append(MARKDOWN[code])
                    reopen.append(code)
                out.append(MARKDOWN[open_formats.pop()])
                for code in reversed(reopen):
                    open_formats.append(code)
                    out.append(MARKDOWN[code])
            else:
                open_formats.append(char)
                out.append(MARKDOWN[char])
        elif char == RESET:
            close_all()
        else:
            out.append(char)

    close_all()
    return ''.join(out)


# Discord markdown -> IRC. Ordered longest-delimiter-first so *** is
# consumed before ** and __ before _. The (?![\s*]) / (?<!\s) guards mirror
# Discord's own rule that delimiters don't open/close next to whitespace.
# The _italic_ pattern additionally requires non-word boundaries so
# snake_case identifiers and URLs are never rewritten.
BOLD_ITALIC_RE = re.compile(r'\*\*\*(?![\s*])(.+?)(?<!\s)\*\*\*')
BOLD_RE = re.compile(r'\*\*(?![\s*])(.+?)(?<!\s)\*\*')
UNDERLINE_RE = re.compile(r'__(?![\s_])(.+?)(?<!\s)__')
ITALIC_STAR_RE = re.compile(r'\*(?![\s*])(.+?)(?<!\s)\*')
ITALIC_UNDERSCORE_RE = re.compile(
    r'(?<![A-Za-z0-9_])_(?![\s_])([^_]+)(?<!\s)_(?![A-Za-z0-9_])')

CODE_SPAN_RE = re.compile(r'``.+?``|`[^`]+`', re.DOTALL)
ESCAPED_CHAR_RE = re.compile(r'\\([*_~`\\])')

# Unterminated multi-char delimiters (after paired substitutions ran)
# convert to IRC open codes: the style runs to end of line, matching
# IRC's implicit per-message termination. Single */_ leftovers stay
# literal - they are usually genuine text (5*3, -_-), not styles.
UNTERMINATED_BOLD_ITALIC_RE = re.compile(r'(?<![A-Za-z0-9_*])\*\*\*(?=[^\s*])')
UNTERMINATED_BOLD_RE = re.compile(r'(?<![A-Za-z0-9_*])\*\*(?=[^\s*])')
UNTERMINATED_UNDERLINE_RE = re.compile(r'(?<![A-Za-z0-9_])__(?=[^\s_])')


def discord_to_irc(text):
    text = text.replace('\x00', '')
    protected = []

    def _protect(match):
        protected.append(match.group(0))
        return '\x00{}\x00'.format(len(protected) - 1)

    text = CODE_SPAN_RE.sub(_protect, text)
    text = ESCAPED_CHAR_RE.sub(_protect, text)
    text = BOLD_ITALIC_RE.sub(BOLD + ITALIC + r'\1' + ITALIC + BOLD, text)
    text = BOLD_RE.sub(BOLD + r'\1' + BOLD, text)
    text = UNDERLINE_RE.sub(UNDERLINE + r'\1' + UNDERLINE, text)
    text = ITALIC_STAR_RE.sub(ITALIC + r'\1' + ITALIC, text)
    text = ITALIC_UNDERSCORE_RE.sub(ITALIC + r'\1' + ITALIC, text)
    text = UNTERMINATED_BOLD_ITALIC_RE.sub(BOLD + ITALIC, text)
    text = UNTERMINATED_BOLD_RE.sub(BOLD, text)
    text = UNTERMINATED_UNDERLINE_RE.sub(UNDERLINE, text)
    return re.sub(r'\x00(\d+)\x00',
                  lambda m: protected[int(m.group(1))], text)
