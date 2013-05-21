# coding: utf-8

import string, re, base64

from bs4 import BeautifulSoup
from bs4.element import PreformattedString
from jslex.jslex import JsLexer

import config


def get_prev_js_token(tokens, idx):

    if idx == 0:
        return (None, None), None

    while True:
        idx -= 1
        if tokens[idx][0] != "ws":
            return tokens[idx], idx
        if idx <= 0:
            return (None, None), None

def get_next_js_token(tokens, idx):

    if idx == len(tokens) - 1:
        return (None, None), None

    while True:
        idx += 1
        if tokens[idx][0] != "ws":
            return tokens[idx], idx
        if idx >= len(tokens) - 1:
            return (None, None), None


def inject_in_html(content, payload_str):
    """ Injects payload into HTML:

    the values of attrs "src" and "href" are prefixed with payload_str.

    local <script> content is processed by inject_in_js.
    attribute-values beginning with "javascript:" are processed by inject_in_jsstring.
    local <style> content is processed by inject_in_css.


    """

    soup = BeautifulSoup(content)

    # src-attribute
    for el in soup.find_all(src = True):
        el.attrs["src"] = payload_str + el.attrs["src"]

    # href-attribute
    for el in soup.find_all(href = True):
        el.attrs["href"] = payload_str + el.attrs["href"]

    # local js
    for el in soup.find_all("script"):
        if el.string:
            el.string = PreformattedString(inject_in_js(el.string, payload_str))

    # local css
    for el in soup.find_all("style", type = "text/css"):
        if el.string:
            el.string = PreformattedString(inject_in_css(el.string, payload_str))

    # js in attributes
    for el in soup.find_all():
        for attr_name in el.attrs:
            attr_value = el[attr_name]
            if type(attr_value) is list: # strange thing...
                attr_value = attr_value[0]

            if attr_value.startswith("javascript:"):
                el[attr_name] = "javascript:" + inject_in_js(attr_value[11:], payload_str)

    return unicode(soup)

def inject_in_string(content, quote, payload_str):
    """
    This function handles string constants not exactly knowing if its HTML, JS, or parts of those
    or something completely different...
    So the quality of the result may be random ;-)

    It works like this:
    1. it searches for [. ]src= and [. ]href=
    2. then checks if a ' or " follows
    3. if yes, inject the payload directly after the quote (so HTML-Attributes stay intact)
    4. if no, it injects the payload as string-constant-concat ("payload"+...) (so JS stays intact)

    """

    expect = "dot/ws"
    pos = 0
    injections = []

    while pos < len(content):
        char = content[pos]

        if expect == "dot/ws" and char in "'\". \r\n\t":
            expect = "src/href"
        elif expect == "src/href":
            if content[pos:pos+3] == "src":
                expect = "eq"
                pos += 2
            elif content[pos:pos+4] == "href":
                expect = "eq"
                pos += 3
            else:
                expect = "dot/ws"
        elif expect == "eq":
            if char == "=":
                expect = "inject"
            elif char not in " \r\n\t":
                expect = "dot/ws"
        elif expect == "inject":
            if char in "'\"":
                injections.append((pos + 1, payload_str))
            else:
                injections.append((pos, "\\\"" + payload_str + "\\\"+"))
            expect = "dot/ws"

        pos += 1

    injections.reverse()
    for pos, inj_str in injections:
        content = content[:pos] + inj_str + content[pos:]

    return content

def inject_in_js(content, payload_str):
    """ injects payload into
    XXX.src = ...;
    XXX.href = ...;
    String constants are treated as HTML.

    The payload is injected as string-constant:
    obj.href = "PAYLOAD" + ...;
    """

    lexer = JsLexer()
    tokens = list(lexer.lex(content))
    out = []
    inject_queue = []

    for idx, token in enumerate(tokens):

        prev_token, prev_idx = get_prev_js_token(tokens, idx)
        next_token, next_idx = get_next_js_token(tokens, idx)

        if token[0] == "string":
            if token[1]:
                quote = token[1][0]
                content = token[1][1:-1]
                out.append(quote + inject_in_string(content, quote, payload_str) + quote)
        else:
            out.append(token[1])

        if inject_queue and (inject_queue[0][0] == idx):
            out.append(inject_queue[0][1])
            inject_queue.pop(0)

        if token == ("id", "src") and prev_token == ("punct", ".") and next_token == ("punct", "="):
            inject_queue.append((next_idx, '"' + payload_str + '"+'))
        elif token == ("id", "href") and prev_token == ("punct", ".") and next_token == ("punct", "="):
            inject_queue.append((next_idx, '"' + payload_str + '"+'))

    content = string.join(out, "")

    # dynamic modification of "src" and "href" attribute
    content = re.sub(r"\.setAttribute\(\s*[\"\']src[\"\']\s*,", ".setAttribute('src','" + payload_str + "'+", content)
    content = re.sub(r"\.setAttribute\(\s*[\"\']href[\"\']\s*,", ".setAttribute('href','" + payload_str + "'+", content)

    return content

def inject_in_css(content, payload_str):
    """
    Injects into url(...)
    """

    content = content.replace("url(", "url("+ payload_str)

    return content



def parse_path(path):
    """ Parses a complete path which is created by injecting the hrt-prefix.
    It returns the origin-url and the original-url """

    parts = path.split("/" + config.get("url_delimiter") + "/?", 1)

    if len(parts) == 2:
        url = parts[1]
        origin_url = parts[0][1:].decode("base64")
    else:
        url = path
        origin_url = config.get("url")

    return origin_url, url


def inject(content, content_type, payload_str):
    """ Frontend for the different inject-functions """

    if "css" in content_type:
        return inject_in_css(content, payload_str)
    elif "javascript" in content_type:
        return inject_in_js(content, payload_str)
    else:
        return inject_in_html(content, payload_str)

