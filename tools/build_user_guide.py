"""Export the authoritative Studio help as a portable, offline HTML document."""
from collections import OrderedDict
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ('Getting started', 'Brief & sources', 'Understanding', 'Review',
            'Resources', 'Codex & QA', 'How to Use', 'Production skills', 'Troubleshooting')


def _validate(data):
    version = data.get('schema_version') if isinstance(data, dict) else None
    if isinstance(version, bool) or not isinstance(version, (int, float)) or version != 1:
        raise ValueError('Guide schema_version must be 1')

    def text(value, label):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{label} must be a nonempty string')

    text(data.get('title'), 'title')
    articles = data.get('articles')
    if not isinstance(articles, list) or not articles:
        raise ValueError('articles must be a nonempty list')
    ids = set()
    for article in articles:
        if not isinstance(article, dict):
            raise ValueError('Each article must be an object')
        for field in ('id', 'section', 'title', 'summary', 'status'):
            text(article.get(field), field)
        if article['section'] not in SECTIONS:
            raise ValueError('Article section must match a supported guide section')
        identifier = article['id']
        if not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', identifier) or identifier in ids:
            raise ValueError(f'Invalid or duplicate article id: {identifier!r}')
        ids.add(identifier)
        for field in ('steps', 'notes'):
            values = article.get(field)
            if not isinstance(values, list) or (field == 'steps' and not values):
                raise ValueError(f'{field} must be a list; steps cannot be empty')
            for value in values:
                text(value, field)
        if 'prompt' in article:
            text(article['prompt'], 'prompt')


STYLE = '''
:root { color-scheme: light; --paper:#fffaf1; --ink:#282a2e; --accent:#9e392d; --line:#d7cfc2; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font:17px/1.65 system-ui,-apple-system,sans-serif; }
a { color:var(--accent); text-underline-offset:3px; }
a:hover { text-decoration-thickness:2px; }
:focus-visible { outline:3px solid var(--accent); outline-offset:4px; }
.skip { position:absolute; left:1rem; top:-5rem; background:white; padding:1rem; }
.skip:focus { top:1rem; }
header { border-bottom:1px solid var(--line); padding:3rem max(1.5rem, calc((100vw - 1200px)/2)); }
.eyebrow { text-transform:uppercase; letter-spacing:.13em; font-size:.75rem; font-weight:700; color:var(--accent); }
h1 { font-size:clamp(2rem,5vw,3.6rem); line-height:1.12; margin:.5rem 0 1rem; }
h2 { line-height:1.25; margin:.5rem 0; }
h3 { font-size:1rem; }
header p { max-width:46rem; }
.layout { display:grid; grid-template-columns:260px minmax(0,1fr); gap:3rem; max-width:1200px; margin:auto; padding:2rem 1.5rem 4rem; }
nav { font-size:.92rem; }
nav ul { list-style:none; padding:0; }
nav li { margin:.55rem 0; }
nav h2 { font-size:1.2rem; }
nav h3 { margin:1.8rem 0 .5rem; }
main { min-width:0; }
.search { padding:1.3rem; background:#f4eadb; border-radius:12px; margin-bottom:2rem; }
label { display:block; font-weight:650; }
.search-row { display:flex; gap:.7rem; margin-top:.5rem; }
input { min-width:0; width:100%; padding:.7rem; border:1px solid #82796d; border-radius:6px; background:white; font:inherit; }
button { padding:.6rem .9rem; border:1px solid var(--accent); background:white; color:var(--accent); font:inherit; border-radius:6px; cursor:pointer; }
button:hover { background:#fce4db; }
#result_count { margin:.6rem 0 0; font-size:.9rem; }
article { border-top:1px solid var(--line); padding:2rem 0; scroll-margin-top:1.5rem; }
.section { color:var(--accent); font-weight:650; font-size:.85rem; margin:0; }
.status { display:inline-block; background:#f4eadb; padding:.25rem .65rem; border-radius:5px; font-size:.85rem; }
.steps { padding-left:1.6rem; }
.steps li { padding-left:.3rem; margin:.7rem 0; white-space:pre-wrap; overflow-wrap:anywhere; }
.notes { border-left:3px solid #cc7f65; padding:.2rem 1rem; }
.notes li { margin:.5rem 0; }
pre { white-space:pre-wrap; overflow-wrap:anywhere; background:#f4eadb; padding:1rem; border-radius:8px; font:inherit; }
.summary,.notes li { white-space:pre-wrap; overflow-wrap:anywhere; }
[hidden] { display:none !important; }
@media(max-width:760px) { .layout { grid-template-columns:1fr; gap:1rem; } nav { border-bottom:1px solid var(--line); padding-bottom:1rem; } }
@media print { body { background:white; font-size:11pt; } header { padding:0 0 1rem; } .layout { display:block; padding:0; } nav,.search,.copy-example,.skip,#no_results,noscript { display:none !important; } article[hidden] { display:block !important; } article { padding:1rem 0; } h2,h3 { break-after:avoid; } li,pre { break-inside:avoid; } a { color:inherit; } }
'''

SCRIPT = '''
const search = document.getElementById('guide_search');
const articles = [...document.querySelectorAll('main article')];
const count = document.getElementById('result_count');
const empty = document.getElementById('no_results');
function filter() {
  const query = search.value.trim().toLocaleLowerCase();
  let shown = 0;
  for (const article of articles) {
    article.hidden = !article.textContent.toLocaleLowerCase().includes(query);
    if (!article.hidden) shown++;
  }
  count.textContent = `${shown} of ${articles.length} topics shown`;
  empty.hidden = shown !== 0;
}
search.addEventListener('input', filter);
document.getElementById('clear_search').addEventListener('click', () => {
  search.value = ''; filter(); search.focus();
});
// A table-of-contents link always reveals its destination, even during a search.
function revealAnchor() {
  const target = document.getElementById(location.hash.slice(1));
  if (target && target.matches('article') && target.hidden) {
    search.value = ''; filter(); target.scrollIntoView();
  }
}
window.addEventListener('hashchange', revealAnchor);
document.querySelectorAll('nav a').forEach(link => link.addEventListener('click', () => {
  search.value = ''; filter();
}));
document.querySelectorAll('.copy-example').forEach(button => {
  button.addEventListener('click', async () => {
    const example = document.getElementById(button.dataset.example);
    const feedback = button.nextElementSibling;
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(example.textContent);
      feedback.textContent = 'Example copied.';
    } catch (_) {
      const range = document.createRange(); range.selectNodeContents(example);
      const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
      feedback.textContent = 'Example selected. Press Command-C or Ctrl-C to copy.';
    }
  });
});
filter(); revealAnchor();
'''


def render_guide(data: dict) -> str:
    """Validate plain-text guide data and render all topics without external assets."""
    _validate(data)
    esc = lambda value: escape(value, quote=True)
    sections = OrderedDict()
    for article in data['articles']:
        sections.setdefault(article['section'], []).append(article)
    toc = []
    for section, articles in sections.items():
        toc.append(f'<h3>{esc(section)}</h3><ul>')
        toc.extend(f'<li><a href="#{esc(a["id"])}">{esc(a["title"])}</a></li>' for a in articles)
        toc.append('</ul>')
    content = []
    for article in data['articles']:
        identifier = esc(article['id'])
        content.append(f'<article id="{identifier}" aria-labelledby="topic_title_{identifier}">'
                       f'<p class="section">{esc(article["section"])}</p>'
                       f'<h2 id="topic_title_{identifier}">{esc(article["title"])}</h2>'
                       f'<p class="summary">{esc(article["summary"])}</p>'
                       f'<p class="status">Availability: {esc(article["status"])}</p><ol class="steps">')
        content.extend(f'<li>{esc(step)}</li>' for step in article['steps'])
        content.append('</ol>')
        if article['notes']:
            content.append('<aside class="notes" aria-label="Notes and limits"><h3>Notes &amp; limits</h3><ul>')
            content.extend(f'<li>{esc(note)}</li>' for note in article['notes'])
            content.append('</ul></aside>')
        if 'prompt' in article:
            content.append(f'<h3>Example request</h3><pre id="example_{identifier}">{esc(article["prompt"])}</pre>'
                           f'<button type="button" class="copy-example" data-example="example_{identifier}" '
                           f'aria-label="Copy example for {esc(article["title"])}">Copy example</button> '
                           '<span role="status" aria-live="polite"></span>')
        content.append('</article>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data['title'])}</title><style>{STYLE}</style></head>
<body><a class="skip" href="#guide_content">Skip to guide</a>
<header><div class="eyebrow">Codex Media Studio · Field guide</div><h1>{esc(data['title'])}</h1>
<p>Find a topic, follow the steps, and check the notes for availability and limits. This guide works offline and can be printed.</p></header>
<div class="layout"><nav aria-label="Topics by section"><h2>In this guide</h2>{''.join(toc)}</nav>
<main id="guide_content" tabindex="-1"><div class="search" role="search"><label for="guide_search">Search this guide</label>
<div class="search-row"><input id="guide_search" type="search" placeholder="Search topics, steps, or examples" aria-controls="guide_topics"><button id="clear_search" type="button">Clear</button></div>
<p id="result_count" role="status" aria-live="polite"></p></div>
<noscript>All topics are shown. Use your browser’s Find command to search.</noscript>
<p id="no_results" hidden>No matching topics. Try a different word or clear the search.</p>
<div id="guide_topics">{''.join(content)}</div></main></div><script>{SCRIPT}</script></body></html>
'''


def main():
    data = json.loads((ROOT / 'docs/user-guide.json').read_text(encoding='utf-8'))
    destination = ROOT / 'docs/how-to-use.html'
    destination.write_text(render_guide(data), encoding='utf-8')
    print(destination)


if __name__ == '__main__':
    main()
