#!/bin/bash
# 把 dev.html + style.css + script.js 打包成單檔 index.html
set -e
cd "$(dirname "$0")"

CSS=$(cat style.css)
JS=$(cat script.js)

python3 - <<'PYEOF'
import re, sys

with open('dev.html') as f:
    html = f.read()

with open('style.css') as f:
    css = f.read().rstrip()

with open('script.js') as f:
    js = f.read().rstrip()

html = html.replace(
    '<link rel="stylesheet" href="style.css">',
    '<style>\n' + css + '\n</style>'
)
html = html.replace(
    '<script src="script.js"></script>',
    '<script>\n' + js + '\n</script>'
)

with open('index.html', 'w') as f:
    f.write(html)

print('✓ index.html built')
PYEOF
