import html
import re

import sublime, sublime_plugin


SYNTAX_MAP = {
    'python': 'Packages/Python/Python.sublime-syntax',
    'js': 'Packages/JavaScript/JavaScript.sublime-syntax',
    'json': 'Packages/JSON/JSON.sublime-syntax',
    'html': 'Packages/HTML/HTML.sublime-syntax',
    'css': 'Packages/CSS/CSS.sublime-syntax',
    'xml': 'Packages/XML/XML.sublime-syntax',
    'yaml': 'Packages/YAML/YAML.sublime-syntax',
    'c': 'Packages/C++/C.sublime-syntax',
}


def select_code(view, region):
    start = region.a
    end = region.b
    text = view.substr(region)

    no_code_tag_error = 'No <code> or <pre> tag with class of syntax-* found preceeding selection'

    tag_end = start - 1
    if tag_end < 0:
        sublime.error_message(no_code_tag_error)
        return (None, None)

    if view.substr(tag_end) != '>':
        sublime.error_message(no_code_tag_error)
        return (None, None)

    tag_start = tag_end - 1
    while tag_start >= 0:
        if view.substr(tag_start) == '<' \
                and 'punctuation.definition.tag.begin' in view.scope_name(tag_start):
            break
        tag_start -= 1

    if tag_start < 0:
        sublime.error_message(no_code_tag_error)

    open_tag = view.substr(sublime.Region(tag_start, tag_end + 1))
    tag_match = re.match(r'<(code|pre) class="syntax-(\w+)">', open_tag)
    if not tag_match:
        sublime.error_message(no_code_tag_error)
        return (None, None)

    close_tag = view.substr(sublime.Region(end, end + 7))
    if close_tag != '</' + tag_match.group(1) + '>':
        sublime.error_message('No matching close tag found following selection')
        return (None, None)

    syntax_name = tag_match.group(2)
    syntax_file = SYNTAX_MAP.get(syntax_name)
    if not syntax_file:
        sublime.error_message('Syntax ' + syntax_name + ' is unrecognized')
        return (None, None)

    return (syntax_name, text)


def strip_highlighting(text):
    text = re.sub(
        r'(<span style="[^"]*">|</span>)',
        '',
        text
    )
    return html.parser.HTMLParser().unescape(text)


def create_panel(window, color_scheme, syntax_name):
    panel_name = 'convert_html_' + syntax_name
    panel = window.create_output_panel(panel_name, True)
    panel.settings().set('panel_name', panel_name)
    panel.settings().set('color_scheme', color_scheme)
    panel.set_syntax_file(SYNTAX_MAP.get(syntax_name))
    return panel


def token_info(panel, region, scope):
    fg = None
    bold = False
    italic = False

    style = panel.style_for_scope(scope)
    if style.get('foreground'):
        fg = style.get('foreground')
    if style.get('bold'):
        bold = True
    if style.get('italic'):
        italic = True

    return (panel.substr(region), fg, bold, italic)


def extract_tokens(panel, text):
    panel.run_command('select_all')
    panel.run_command('left_delete')
    panel.run_command('append', {'disable_tab_translation': True, 'characters': text})

    tokens = []
    max_tp = panel.size()
    tp = 0
    token_start = 0
    last_scope = None
    while tp < max_tp:
        scope = panel.scope_name(tp)
        if last_scope is not None and last_scope != scope:
            tokens.append(token_info(
                panel,
                sublime.Region(token_start, tp),
                last_scope
            ))
            token_start = tp
        last_scope = scope
        tp += 1
    tokens.append(token_info(
        panel,
        sublime.Region(token_start, tp),
        last_scope
    ))
    return tokens


def highlight_tokens(panel, tokens):
    scope = None
    for s in sublime.list_syntaxes():
        if s["path"] == panel.settings().get('syntax'):
            scope = s["scope"]
    default_foreground = panel.style_for_scope(scope).get('foreground')

    output = []
    for token in tokens:
        if token[0] == '\n':
            output.append(token[0])
        else:
            props = []
            if token[1] and token[1] != default_foreground:
                props.append('color: ' + token[1])
            if token[2]:
                props.append('font-weight: bold')
            if token[3]:
                props.append('font-style: italic')
            if props:
                output.append('<span style="')
                output.append('; '.join(props))
                output.append('">')
            output.append(html.escape(token[0]))
            if props:
                output.append('</span>')
    return '<span style="color: ' + default_foreground + '">' + ''.join(output) + '</span>'


def destroy_panel(window, panel):
    if panel is None:
        return
    window.destroy_output_panel(panel.settings().get('panel_name'))


class HighlightAllCodeBlocksCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        panels = {}

        view = self.view
        window = view.window()
        color_scheme = view.settings().get('color_scheme')

        try:
            tp = 0
            while tp < view.size():
                open_tag = view.find('<(pre|code) class="syntax-\\w+">', tp)
                if open_tag.a == -1:
                    break

                open_tag_name = re.sub(r'<(pre|code).*>', '\\1', view.substr(open_tag))

                close_tag = view.find('</' + open_tag_name + '>', open_tag.b)
                if close_tag.a == -1:
                    break

                tp = close_tag.b

                code_region = sublime.Region(open_tag.b, close_tag.a)

                syntax, text = select_code(view, code_region)
                if syntax is None:
                    continue

                text = strip_highlighting(text)

                if syntax not in panels:
                    panels[syntax] = create_panel(window, color_scheme, syntax)
                panel = panels[syntax]

                highlighted_text = highlight_tokens(
                    panel,
                    extract_tokens(panel, text)
                )

                tp += len(highlighted_text) - len(code_region)
                view.replace(
                    edit,
                    code_region,
                    highlighted_text
                )

        finally:
            for syntax in panels:
                destroy_panel(window, panels[syntax])


class ClearAllCodeBlocksCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view

        tp = 0
        while tp < view.size():
            open_tag = view.find('<(pre|code) class="syntax-\\w+">', tp)
            if open_tag.a == -1:
                break

            open_tag_name = re.sub(r'<(pre|code).*>', '\\1', view.substr(open_tag))

            close_tag = view.find('</' + open_tag_name + '>', open_tag.b)
            if close_tag.a == -1:
                break

            tp = close_tag.b

            code_region = sublime.Region(open_tag.b, close_tag.a)

            syntax, text = select_code(view, code_region)
            if syntax is None:
                continue

            stripped_text = strip_highlighting(text)
            text = html.escape(stripped_text, quote=False)

            tp -= len(code_region) - len(text)
            view.replace(
                edit,
                code_region,
                text
            )


class ClearCodeBlockCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()[0]

        syntax_name, text = select_code(view, sel)
        if syntax_name is None:
            return

        text = strip_highlighting(text)
        view.replace(
            edit,
            sel,
            text
        )


class HighlightCodeBlockCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()[0]

        syntax_name, text = select_code(view, sel)
        if syntax_name is None:
            return

        text = strip_highlighting(text)

        panel = None
        try:
            panel = create_panel(
                view.window(),
                view.settings().get('color_scheme'),
                syntax_name
            )

            view.replace(
                edit,
                sel,
                highlight_tokens(panel, extract_tokens(panel, text))
            )

        finally:
            destroy_panel(view.window(), panel)
