import sphinx_py3doc_enhanced_theme

extensions = [
    'autoapi.extension',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.ifconfig',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]
autoapi_type = 'python'
autoapi_dirs = ['../src']

source_suffix = '.rst'
master_doc = 'index'
project = 'tblib'
year = '2013-2022'
author = 'Ionel Cristian Mărieș'
copyright = f'{year}, {author}'
version = release = '1.7.0'

pygments_style = 'trac'
templates_path = ['.']
extlinks = {
    'issue': ('https://github.com/ionelmc/python-tblib/issues/%s', '#'),
    'pr': ('https://github.com/ionelmc/python-tblib/pull/%s', 'PR #'),
}
html_theme = 'sphinx_py3doc_enhanced_theme'
html_theme_path = [sphinx_py3doc_enhanced_theme.get_html_theme_path()]
html_theme_options = {
    'githuburl': 'https://github.com/ionelmc/python-tblib/',
}

html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_sidebars = {
    '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
}
html_short_title = f'{project}-{version}'

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
