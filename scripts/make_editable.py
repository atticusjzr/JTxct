#!/usr/bin/env python3
"""把「交通事故圖」工具 index.html 和一份專案 JSON 合成一個「點開就已載入、可直接編輯」的單檔 html。
用法：python3 make_editable.py <index.html> <專案.json> <輸出.html>
"""
import json, sys
tool, proj, out = sys.argv[1:4]
html = open(tool, encoding='utf-8').read()
data = json.load(open(proj, encoding='utf-8'))
payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
loader = '''<script>
(async () => {
  const data = %s;
  const wait = t => new Promise(r => setTimeout(r, t));
  for (let i = 0; i < 100 && (typeof Layer === 'undefined' || !_baseImg.complete || !_topImg.complete); i++) await wait(50);
  layers = [];
  for (const ld of data.layers) {
    const l = new Layer(ld.name);
    l.id = ld.id || l.id; l.visible = ld.visible !== false; l.opacity = ld.opacity ?? 1; l.locked = !!ld.locked;
    await l.loadDataURL(ld.data);
    l.specialType = ld.specialType || null; l.a123 = ld.a123 || 0; l.specialData = ld.specialData || null;
    if (l.specialType) { l.specialImg = l.specialType === 'base' ? _baseImg : _topImg; l.locked = true; }
    layers.push(l);
  }
  activeIdx = data.activeIdx ?? 0;
  objects = (data.objects || []).map(o => ({...o}));
  layers.forEach(l => { if (l.specialType && l.specialData) {
    if (!objects.some(o => o.specialRole && o.layerId === l.id)) _migrateSpecialDataToObjects(l); else l.specialData = null; } });
  _migrateA123Freetext();
  if (data.scale > 0) { _scale = data.scale; const sd = document.getElementById('scale-display'); if (sd) sd.textContent = '1:' + _scale; }
  selectedObjs = []; syncSel(); setProj(data.name || '事故現場圖');
  composite(); renderLayers(); clearDirty(); hist = []; histIdx = -1; saveSnap('開啟專案'); centerOnTemplate();
})();
</script>
''' % payload
i = html.rfind('</body>')
html = html[:i] + loader + html[i:] if i >= 0 else html + loader
open(out, 'w', encoding='utf-8').write(html)
print('ok', out, len(html))
