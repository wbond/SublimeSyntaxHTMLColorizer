# Sublime Syntax HTML Colorizer

Uses `.sublime-syntax` syntax definitions to generate HTML to syntax highlight code in web pages.

Requires that code to be highlighted be contained between `<code class="syntax-{name}"><code>` where `{name}` is one of:

 - `python`
 - `html`
 - `css`
 - `js`
 - `json`
 - `yaml`
 - `c`
 - `xml`

## Installation

 - Install Package Control - https://packagecontrol.io
 - Run `Add Repository` command
 - Paste `https://github.com/wbond/SublimeSyntaxHTMLColorizer`
 - Run `Install Package` command
 - Select `SublimeSyntaxHTMLColorizer`

## Usage

Available commands in the command palette are:

 - *Sublime Syntax: Highlight Code Block* – highlights selected code between `<code>` tags
 - *Sublime Syntax: Clear Code Block* – clears highlighting of selected code between `<code>` tags
 - *Sublime Syntax: Highlight All Code Blocks* – finds and highlights all `<code>` blocks in file
 - *Sublime Syntax: Clear All Code Block* – clears highlighting of all `<code>` blocks in file

## Limitations

 - Uses your current color scheme
 - Doesn't deal with background colors
 - Doesn't apply glow 😁
