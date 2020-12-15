from io import StringIO, BytesIO
from string import Formatter
from typing import Iterable, Tuple

from rewrite_magic.encoding_glue import FileRewriter, register
from tokenize import generate_tokens, TokenInfo
from token import STRING, NEWLINE


class FStringBackport(FileRewriter):
    def _transform_fstring(self, s: str) -> str:
        if s[-3:] == '"""' or s[-3:] == "'''":
            sep = s[-3:]
        else:
            sep = s[-1]
        assert set(sep) == {'"'} or set(sep) == {"'"}
        content_start = s.find(sep) + len(sep)
        content_end = len(s) - len(sep)
        out = [s[:content_start]]
        i = content_start
        while i < content_end:
            j = s.find('{', i)
            if j == -1:
                break
            out.append(s[i:j])
            i = j + 1
            if s[i] == '{':
                out.append('{{')
                i += 1
                continue
            # Ok we are within an expression. Find the end
            stack = []
            expr_end = None
            for j in range(i, content_end):
                if s[j] in '{([':
                    stack.append(s[j])
                elif stack:
                    if s[j] in '})]':
                        stack.pop()
                elif s[j] in ':!}':  # These mark the end of an expression
                    if expr_end is None:
                        expr_end = j
                    if s[j] == '}':
                        break
            else:
                # We run into the end of the string. Something is wrong. Let python throw an exception
                out.append('{' + s[i:j])
                break
            assert expr_end is not None
            expr = s[i:expr_end]
            if expr.rstrip()[-1] == '=': # we have an debug expression
                out.append(expr)
                expr = expr.rstrip()[:-1]
            out.append('{'+expr + s[expr_end:j+1])
            i = j+1
        out.append(s[content_end:])
        return ''.join(out)

    def _transform(self, tokens: Iterable[TokenInfo]) -> Iterable[Tuple[TokenInfo, TokenInfo]]:
        for t in tokens:
            if t.type == STRING and 'f' in t.string.partition(t.string[-1])[0].lower():
                yield t, TokenInfo(STRING, self._transform_fstring(t.string), t.start, t.end, t.line)
            else:
                yield t, t

    def _reconstruct(self, tokens: Iterable[Tuple[TokenInfo, TokenInfo]]) -> Iterable[str]:
        last_end = 0
        for orig, new in tokens:
            if orig is not None:
                if orig.type != NEWLINE:
                    missing_ws = orig.line[last_end:orig.start[1]]
                    if missing_ws != '':
                        yield missing_ws
                    last_end = orig.end[1]
                else:
                    last_end = 0
            yield new.string

    def rewrite(self, s: str) -> str:
        s = generate_tokens(StringIO(s).readline)
        s = self._transform(s)
        return ''.join(self._reconstruct(s))


register('fstringbackport', FStringBackport())
