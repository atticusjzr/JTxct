---
name: jtxct-accident-diagram
description: 用「交通事故圖」(JTxct) 這支純前端單檔繪圖工具畫台灣道路交通事故現場圖——開檔、擺圖層、依手繪草圖放路面標線／車輛／基準點與定位量測、填表頭與事故資訊、匯出 PNG 或 JSON 專案檔。可用 Playwright 程式化操作瀏覽器，也可直接產生可匯入的 JSON。TRIGGER：要畫、修改或核對一張事故現場圖；手上有現場手繪草圖要轉成正式圖；要批次產標準路口底圖；提到 JTxct 或「交通事故圖」工具。SKIP：只問肇事責任或法條、不需要畫圖。
---

# 交通事故圖（JTxct）現場圖繪製技能

本技能說明如何用「交通事故圖」工具（`index.html` 單檔，瀏覽器直接開，不需伺服器）畫出一張符合警察機關格式的道路交通事故現場圖。以下 `<工具目錄>` 指放 `index.html` 的資料夾。

所有座標都是**圖紙座標**（底圖模板 1123×794 px，A4 橫向），不是螢幕像素。

---

> 🔴 **直接產 JSON 時：所有圖形都必須是 `objects` 裡的向量物件。** 圖層的 `data` 只放 1×1 透明 PNG，⛔ 禁止把線條、車、文字畫成點陣塞進 `data`——那在工具裡等於鉛筆筆跡，不能選取、移動、量距，定位數字也不會算。匯出的 `objects` 不能是空陣列。

## 1. 開檔與圖層（每張圖的第一步）

畫任何東西之前，先從圖層面板右上角 ★ 放兩個特殊圖層並鎖定，其他東西一律畫在兩者之間：

```python
pg.goto('file://<工具目錄>/index.html')
pg.evaluate("()=>{addSpecialLayer('base');}")   # 底圖：灰路面＋黃比例格
pg.evaluate("()=>{addSpecialLayer('top');}")    # 頂層圖：現場圖表框、標題、各欄位
pg.evaluate("""()=>{
  layers.forEach(l=>{ if(l.specialType) l.locked=true; });
  // 開頁自帶一個空的「圖層 1」，先刪掉
  const i=layers.findIndex(l=>!l.specialType&&!objects.some(o=>o.layerId===l.id)); if(i>=0) layers.splice(i,1);
  activeIdx=0; addLayer(); layers[activeIdx].name='路面標線';
  addLayer(); layers[activeIdx].name='車輛';          // addLayer 插在作用層上方
  renderLayers(); composite(); }""")
```

建議圖層（由下到上）：`底圖(鎖) → 路面標線 → 車輛 → 頂層圖(鎖)`，需要時再在中間加「量測」等層。

| 放哪一層 | 內容 |
|---|---|
| 路面標線 | 路緣、分向線、斑馬線、停止線、待轉區、網格線、路段方向標示 |
| 車輛 | 基準點、基準線、車輛、定位標記、行向箭頭、車輛註記 |
| 頂層圖 | **所有文字資訊**：表頭單位、時間地點、車牌清單、事故經過、製圖日期、指北針、比例尺 |

路面框外（y>597 或 x>1013）的東西若不在頂層圖，會被頂層圖的白色表框蓋掉。

## 2. 座標換算（程式化操作時）

畫布有 `CANVAS_MARGIN=300` 的外框、左上可能是負值，視窗大小一變，硬寫螢幕像素整張就歪。一律從畫布換算：

```python
env=pg.evaluate("""()=>{const c=document.querySelector('canvas');const r=c.getBoundingClientRect();
  return {l:r.left,t:r.top,zoom:zoom,m:CANVAS_MARGIN};}""")
L,T,Z,M=env['l'],env['t'],env['zoom'],env['m']
def S(x,y): return (L+(x+M)*Z, T+(y+M)*Z)       # 圖紙座標 → 螢幕座標
def drag(x1,y1,x2,y2):
    pg.mouse.move(*S(x1,y1)); pg.mouse.down(); pg.mouse.move(*S(x2,y2),steps=20); pg.mouse.up()
```

用手型工具捲動畫布後 L/T 會變，要重抓 env。

**程式直接 `objects.push(...)` 建物件後，一定接 `composite(); saveSnap('說明');`**——沒進歷史的物件，按一次復原就會消失。

## 3. 模板格線（對齊用的硬數字）

一切照底圖黃格線對齊，別憑眼睛擺。

- 外框 x 50–1013、y 121–707；路面與底部欄分界 y 608；灰路面可畫區約 x 52–1013、y 121–597。
- 黃格橫線 y＝160,199,237,276,314,353,391,430,468,507,545,584
- 黃格豎線 x＝88,126,161,201,239,276,314,351,389,426,464,501,539,576,614,652,689,727,764,802,840,877,917,965
- 一格 ≈ 38.5 px ≈ 1 公尺（比例 1:100）。
- 左上「(以箭頭標示北方)」合併格：x 50–161、y 122–237。
- 底部欄：事故經過摘要格 x 80–838、車牌清單格 x 842–1012，皆 y 609–707；分隔線 x 840。
- 表頭小表：x 51–434、y 36–121，填寫行 y 70–121，四欄分界 x 51/161/244/351/434（警察局名稱／總編號／轄區分局名稱／處理編號）。
- 製圖日期「年／月／日」三個空格中心 x＝876／929／970，**垂直中心 y≈724**（與模板「年 月 日」同一行）。

標準十字路口（落在格線上）：橫路 y276–430（中央分向線 y353）、豎路 x464–614（中央分向線 x539）。

## 4. 比例尺比例

工具列「比例尺 1:100」可改；程式化用 `_applyGlobalScale(200)`，範圍 50–1000。

- `PX_PER_CM = 1123/29.7 ≈ 37.81`。1:100 時一格 ≈ 1 m；1:200 時一格 ≈ 2 m，所有量測讀數跟著變。
- **先定比例再畫**：`_applyGlobalScale` 只等比縮物件的 w/h、不動 x/y，畫完才改會走樣。
- 長路段、多車道用 1:200 或 1:250；一般路口 1:100。

## 5. 頂層圖的固定欄位

### 指北針與圖示比例尺
```js
const topL=layers.find(l=>l.specialType==='top');
objects.push({type:'compass', x:56,y:146,w:99,h:88, rotation:0,color:'#000000',layerId:topL.id});  // 左上北方格內置中
objects.push({type:'scalebar',x:781,y:130,w:231,h:32,rotation:0,color:'#000000',layerId:topL.id}); // 右上貼路面上緣
```
- 指北針 w/h 不要小於 70，否則只畫得出一段弧。`rotation` 依實際北方調整（見 §10）。
- 比例尺長度依場景判斷：範圍大就拉長（分段自動變 0–6 m、0–10 m…），小場景縮短。

### 文字欄位的共用寫法
印章工具（🖊 事故資訊／車牌清單）落下的其實就是 `freetext` 物件；程式化直接建 freetext 最準：

```js
const mk=(text,fs,x,y,lid)=>{ const lines=text.split('\n'), lh=fs*1.4;
  const t=document.createElement('canvas').getContext('2d'); t.font=fs+'px sans-serif';
  const maxW=Math.max(...lines.map(l=>t.measureText(l).width));
  objects.push({type:'freetext',text,fontSize:fs,fontFamily:'sans-serif',color:'#212121',
    bold:false,italic:false,underline:false,showBorder:false,rotation:0,x,y,
    w:Math.round(maxW+16),h:Math.round(lines.length*lh+8),layerId:lid}); };

mk('發生時間：○○○年○月○日○○時○○分\n發生地點：○○市○○區甲路○○號前',14,172,122,topL.id); // 路面左上，兩行
mk('A車：ABC-1234\nB車：XYZ-5678',17,850,621,topL.id);                                 // 車牌清單格
```
- 地點要寫完整（縣市、區、路名、門牌或交岔路口）。
- 車牌清單只寫「A車：車牌」，不加車種（加了會超出格子）。

### 事故經過摘要：字要撐滿格子
字少就大、字多就小，留白太多不好看。freetext 不會自動換行，所以由大到小試字級並手動斷行，取第一個塞得下的，再垂直置中：

```js
const fit=(text,x,y,cw,ch,lid)=>{
  const t=document.createElement('canvas').getContext('2d'); let best=null;
  for(let fs=40;fs>=9;fs--){ t.font=fs+'px sans-serif'; const lh=fs*1.35; let lines=[],cur='';
    for(const c of text){ if(t.measureText(cur+c).width>cw){lines.push(cur);cur=c;} else cur+=c; }
    if(cur)lines.push(cur); if(lines.length*lh<=ch){best={fs,lines,lh};break;} }
  const {fs,lines,lh}=best;
  objects.push({type:'freetext',text:lines.join('\n'),fontSize:fs,fontFamily:'sans-serif',color:'#212121',
    bold:false,italic:false,underline:false,showBorder:false,rotation:0,
    x, y:y+Math.max(0,(ch-lines.length*lh)/2), w:cw+16, h:Math.round(lines.length*lh+8), layerId:lid}); };
fit('A車沿甲路往○○方向直行，……，兩車於○○處發生碰撞。',92,613,738,90,topL.id);
```

### 表頭單位欄
單位依承辦單位填寫，不要寫死；總編號、處理編號沒有就留空。四欄要**左右對稱**：先取四欄共同的最小字級，再在字間插空格分散對齊撐滿欄寬（與模板「警 察 局 名 稱」同風格）：

```js
const COLS=[[u.bureau,51,161],[u.serial,161,244],[u.branch,244,351],[u.station,351,434]];
const t=document.createElement('canvas').getContext('2d'); let FS=22;
for(const [s,x0,x1] of COLS){ if(!s)continue; let fs=22;
  for(;fs>=8;fs--){ t.font=fs+'px sans-serif'; if(t.measureText(s).width<=(x1-x0)-12) break; } if(fs<FS) FS=fs; }
t.font=FS+'px sans-serif'; const sw=t.measureText(' ').width, lh=FS*1.25;
for(const [s,x0,x1] of COLS){ if(!s)continue; const cs=[...s], w0=t.measureText(s).width; let out=s;
  if(cs.length>1){ const k=Math.max(0,Math.floor(((x1-x0)-12-w0)/(cs.length-1)/sw)); if(k>0) out=cs.join(' '.repeat(k)); }
  const wo=t.measureText(out).width;
  objects.push({type:'freetext',text:out,fontSize:FS,fontFamily:'sans-serif',color:'#212121',bold:false,italic:false,
    underline:false,showBorder:false,rotation:0,x:Math.round((x0+x1)/2-wo/2-8),y:Math.round(95.5-lh/2-4),
    w:Math.round(wo+16),h:Math.round(lh+8),layerId:topL.id}); }
```

### 事故類別 A1／A2／A3
表頭右側三格是按鈕，程式化直接設：`topL.a123=2; composite(); renderLayers();`（1/2/3，0＝不勾）。
- **A1**：有人死亡。
- **A2**：有人受傷（不論是否送醫；各單位定義可能微調）。
- **A3**：僅財物損失、無人受傷。

### 製圖日期
寫**事故發生日期**（不是畫圖當天）。三個數字 14 級、水平置中於 x＝876／929／970，垂直中心 y≈724：
```js
t.font='14px sans-serif';
for(const [s,cx] of [[年,876],[月,929],[日,970]]){ const w=t.measureText(s).width;
  objects.push({type:'freetext',text:s,fontSize:14,fontFamily:'sans-serif',color:'#212121',bold:false,italic:false,
    underline:false,showBorder:false,rotation:0,x:Math.round(cx-w/2-8),y:Math.round(724-14*1.4/2-4),
    w:Math.round(w+16),h:Math.round(14*1.4+8),layerId:topL.id}); }
```

## 6. 路面標線

工具鈕的選項都在**懸停選單**：先 `pg.click('#btn-X')` 再 `pg.hover('#btn-X')`，然後點 `[onclick="setXxx('值',this)"]`。要擺準的一律直接建物件。

| 選項值（setMarkingVariant） | 物件 type | 手勢 | 備註 |
|---|---|---|---|
| single-solid／single-dashed | marking-single-solid／-dashed | 拖一條線 | 虛線有 dashLen/gapLen |
| dbl-solid | marking-dbl-solid | 拖線 | 預設黃 `#f9c400` |
| zebra | marking-zebra | 拖**一小段** | 自動放大 5×3；拖太長變大白塊、拖斜線會斜 |
| turn | marking-turn | 拖矩形 | 圓弧路緣，見下 |
| grid | marking-grid | 拖矩形 | 路口黃網格，cellSize 30 |
| moto-zone | marking-moto-zone | 拖矩形 | 機車停等區 |
| parking | marking-parking | 拖矩形 | 停車格 |
| rect | marking-rect | 拖矩形 | 實心塊；白色窄條＝停止線 |
| arrow／arrow-turn／arrow-straight-turn／arrow-three-way | marking-arrow… | 拖矩形 | 用 rotation 轉向 |
| sepisle | marking-sepisle | 拖線 | 分隔島 |
| chanl | marking-chanl | 拖矩形 | 導引島（槽化線） |

直接建物件的格式：
```js
// 線段：中心 (cx,cy)、長 len、角度 rot
{type:'marking-single-solid', x:cx-len/2, y:cy-10, w:len, h:20, rotation:rot, color:'#ffffff', layerId}
// 斑馬線：rotation=0 時 w＝條紋重複方向、h＝條紋長度（跨越路寬）
{type:'marking-zebra', x, y, w, h, rotation:0, color:'#ffffff', dashLen:22, gapLen:18, thickness:2, layerId}
```

**路面標字**（`#btn-marking-text`，拖矩形，字撐滿框）：停／讓／慢／禁行機車／人行道／待轉區（唯一 markDir 'h'）／公車專用／公車停靠區／機車專用／機慢車專用。

**待轉區與機車停等區要朝來車方向轉**：物件以自身中心旋轉，轉 90° 時 w/h 對調。東西向道路上，西側（東行車道）轉 +π/2、東側（西行車道）轉 −π/2。待轉區字用 `markDir:'h'` 再旋轉，才會是直排、每字側躺。

**轉彎線 marking-turn**：
- 拖矩形得到 L 形，轉角在矩形左下、兩臂朝上與朝右（不論拖的方向）。
- 把手：轉角點往內拖＝圓角；臂端點＝長短；臂中點＝夾角；旋轉把手會連位置一起繞開。對角縮放點點不到，要縮放就分別拖兩臂端。
- 四個方向用右鍵「水平翻轉／垂直翻轉」最準。
- 精準建法：`{type:'marking-turn',cx,cy,a1x,a1y,a2x,a2y,radius:40,thickness:5,color:'#ffffff',rotation:0,x:0,y:0,w:0,h:0,layerId}`，(cx,cy)＝轉角點，a1/a2＝兩臂向量，建完呼叫 `syncTurnBBox(o)`。

**路段方向標示**：`addRoadsign('h')` 或 `('v')` 生在視窗中央（往那裡／某某路／往這裡），生完改 `leftText/centerText/rightText`、呼叫 `_syncRoadsignBBox(o)` 再移位置。放在路面上緣外的空白帶（約 y≈198），別放進車道，免得蓋住車或行向箭頭。

## 7. 放車：基準點 → 基準線 → 車 → 定位

**順序不能反**，定位標記會綁在基準線上。都放「車輛」層。

1. **基準點**：`#btn-refpoint` 後在畫布點一下（全圖限一個），放在固定地物上（路緣、電桿、門牌）。預設 60×60 太大，以中心縮成約 28×28：`o.w=o.h=28; o.x=cx-14; o.y=cy-14;`。
2. **基準線**：切 `#btn-select` → 右鍵基準點 → `#ctx-refline-create`「建立基準線」→ 在畫布點一下終點（右鍵取消）。
3. **放車**：`#btn-car` 選車種後拖矩形（車頭朝右＝rotation 0）；機車 `#btn-moto`。車照實際比例：1:100 下小客車 4.5×1.8 m ≈ 170×68 px。
4. **定位**：右鍵車身 → hover `#ctx-posmark-item`「標記定位 ▶」→ 四角定位或車輪定位。機車右鍵只有單項 `#ctx-posmark-moto`（車輪定位）。會產生 `position-mark`（到基準線的垂距）與 `pos-seg-mark`（沿基準線的距離）。
5. **車長車寬**：右鍵「標記車長車寬」`#ctx-sizemark-item`。

程式化等效：`selectedObjs=[i]; syncSel(); ctxMarkPosition('wheel');`（或 `'corner'`）。

**多台車時刪掉多餘的 `'rp'` 線段**：每台車做定位，只要基準線連著基準點，就會多一條 `segIdx:'rp'`（基準點到這台車最近垂足），車一多基準線上會疊好幾條。只留草圖有量的那條（通常是離基準點最近的車），其他整條刪：
`for(let i=objects.length-1;i>=0;i--){const o=objects[i]; if(o.type==='pos-seg-mark'&&o.segIdx==='rp'&&o.carId!=='carA') objects.splice(i,1);}`
同一台車兩輪之間的線段（segIdx 0）草圖沒量就 `measure.show=false`。

**機車圖示的選法**：
- 俯視（`variant:'top'`）＝立著的車。
- 側視（`'left'`／`'right'`）＝倒地的車。草圖上把手往車身一側伸出就是倒地，把手那側是離地那側。
- **倒地（側視）的方向**：看車身（座墊、車把）在畫面上倒向哪一側，別只憑左右手口訣（畫布 y 軸朝下，很容易判反）：
  - 站在「前輪→後輪」方向看畫面，車身在**左手邊** → `variant:'left'`、`rotation=atan2(後輪−前輪)`。
  - 車身在**右手邊** → `variant:'right'`、`rotation=atan2(前輪−後輪)`。
  - 例：前輪左上、後輪右下、車把朝右上伸出 → 車身在左手邊 → `'left'`。
  - 放完**截圖放大看**：座墊和車把要落在草圖車把伸出的那一側。
- 精準擺法：側視車長 w ≈ 軸距／0.61、h ≈ 0.6w；俯視車長 w ≈ 軸距／0.76、h ≈ 0.36w、`rotation=atan2(前−後)`。建好後用 `getMotoWheelBottoms(o)`（回傳 [後輪, 前輪]）取兩輪著地點中點，把物件平移到目標中點。

**程式化精準建法**（不用滑鼠，位置最準）：
```js
const M = PX_PER_CM;   // 1:100 下 1 公尺的像素數
// 基準點（全圖限一個），id 自訂，基準線要用
objects.push({type:'refpoint',x:px-14,y:py-14,w:28,h:28,rotation:0,color:'#212121',thickness:3,id:'rp1',layerId:carL.id});
// 基準點名稱（例如電桿編號）：angle＝相對基準點方向（0 右、π/2 下、π 左），radius＝距離
objects.push({type:'reflabel',refpointId:'rp1',text:'○○○○○○',angle:Math.PI,radius:44,
  fontSize:14,color:'#212121',layerId:carL.id,rotation:0,x:0,y:0,w:60,h:20});
// 基準線：起點會被 computeReflineP1 自動拉回基準點中心
const rl={type:'refline',x1:px,y1:py,x2:ex,y2:ey,color:'#212121',thickness:3,len1:0,refpointId:'rp1',id:'rl1',
  layerId:carL.id,rotation:0,x:0,y:0,w:0,h:0,measure:{show:false,t:0.5,d:20,maxD:60,text:'',color:'#e53935',size:11}};
computeReflineP1(rl); syncReflineBBox(rl); objects.push(rl);
// 機車：先定角度與尺寸，再平移讓兩輪著地點對到目標
const placeMoto=(o,rear,front)=>{ o.x=0;o.y=0; const b=getMotoWheelBottoms(o);
  o.x+=(rear.x+front.x)/2-(b[0].x+b[1].x)/2; o.y+=(rear.y+front.y)/2-(b[0].y+b[1].y)/2; };
const A={type:'moto',variant:'left',w:WB/0.61,h:WB/0.61*0.6,rotation:Math.atan2(rear.y-front.y,rear.x-front.x),
  color:'#c62828',id:'carA',layerId:carL.id,x:0,y:0};
placeMoto(A,rear,front); objects.push(A); composite(); saveSnap('放車');
```
**從草圖反推座標**（基準線水平時）：某輪沿基準線 s 公尺、垂距 d 公尺 ⇒ `(基準點x + s*M, 基準線y ∓ d*M)`，路面那一側用減號。草圖只給前輪沿線距離時，後輪沿線位置 ＝ 前輪沿線 ＋ √(軸距² − 兩輪垂距差²)；軸距沒量就先假設 1.3 m，回報時註明是假設值。

**車輛旋轉**：`selectedObjs=[i]; syncSel(); rotInput.value='-8'; applyRotInput(); composite();`（度，逆時針為負），定位標記自動重算。

**改數字＝移車**：右上角「自由編輯」切成「約束編輯」（`#btn-constraint`），再雙擊尺標數字輸入新值。自由編輯模式下改數字只改文字、車不動。約束解算器不完全可靠（可能靠轉角度湊數、牽動其他角讀數），改完務必核對；不對就切回自由編輯手動移車。
  - 成因（已實測）：`_unifiedSolve` 的權重 `W2=[9,9,1,4,4]` 把角度（弧度）和平移（像素）混在一起比，轉角度看起來幾乎不花成本，所以改一個垂距時車幾乎不平移、只會轉（例：-8° 改一角 0.3 m 後變 -14.8°）。修法：`const R2=(car.w*car.w+car.h*car.h)/4; const W2=[1,1,25*R2,25,25];`，修後同一例車平移約 0.3 m、角度只多 0.2°。工具若已套用此修法（搜 `25*R2`），約束編輯改數字會以平移為主；工具若已有 `_markRawLen`，鎖定的線段（`constraintLocked`，含基準點到車那段 `'rp'`）改其他數字時保證不變：解算後逐條核對已鎖線段實際長度，動到就改用固定角度、再固定車長車寬重解，都不行就還原並跳「改不到」提示，這時要先解鎖一條再改。舊版工具仍請直接算座標，別靠約束編輯。

**命名車輛**：`_doAddCarlabel(car,'letter','A')`。**車色**：照實際顏色；同色車用同色系深淺區分；無資料時用明顯不同的顏色。

## 8. 整理定位數字

- 車擺好後數字要散開、不互相重疊。每個尺標有 `measure.t`（沿線位置 0–1）與 `measure.d`（垂直於**該尺標本身**的偏移，限 ±maxD）：垂距尺標是直的，d 讓數字左右移；沿線尺標 d 讓數字上下移。正負號依尺標方向而定，先試 +25、−25 再選。選取工具按住數字拖即可同時改 t/d。
- 短尺標（< 0.3 m，只有幾 px，t 幾乎移不動）或兩台車垂足落在同一處時，原生數字擺不開：藏掉原生數字（`measure.show=false`），改放紅色粗體 freetext 貼在該輪旁空處：`{type:'freetext',text:'0.1',fontSize:12,color:'#e53935',bold:true,showBorder:false,...}`。數字要貼近它量的那個輪子，且別落在別條尺標的線或垂足上，否則會被誤讀成那條的讀數。
- 自動散開：逐一對每個數字試一串 (t,d) 候選，選第一個不與已放數字重疊、也不壓車身的；此法不防「字壓線」，散完仍要目視並手調。
- **量不到的數字要刪掉，畫面才乾淨**：只藏字留線用 `objects[i].measure.show=false`；整條刪就選取該標記按 Delete。
- 距離為 0 時工具不畫線也不顯示數字，需要時手動補一個 freetext「0」。
- 兩車之間沿基準線的間距工具不會自動產生，用固定長度尺寸線補：`{type:'dimline',cx,cy,rotation:0,maxLen:W,autoAdapt:false,fixedLen:x2-x1,color:'#43a047',thickness:1.5,layerId}`。

## 9. 其他元件

- **手繪箭頭** `#btn-free-arrow`：按住畫曲線（至少 4 點），放開自動成箭頭；用於「自述行向」。掛標籤：`selectedObjs=[i]; syncSel(); ctxAddArrowlabel('A');`。標籤預設貼在箭頭**起點**旁，長箭頭把 `offsetX` 設成約箭頭長度一半移到中段（改完 `_syncArrowlabelBBox(al)`），免得跑到外框邊；線寬 `lineWidth=4` 後 `syncFreeArrowBBox`。
- **尺寸線** `#btn-dimline-h`／`-v`：點一下就放，自動往兩端延伸到碰到物件，顯示公尺數。
- **符號** `#btn-symbol`：消防栓、指北針、比例尺、紅綠燈、電線杆。選單用 `pg.click('.symbol-opt:has-text("比例尺")')`；別用滑鼠點空白處關選單，會用筆刷畫出一筆。
- **文字** `#btn-freetext`：拖框後自動進編輯，打完字點別的工具收尾；未輸入就按 Esc 會刪掉整個框。
- **筆刷／橡皮擦**：畫在圖層像素上、不是物件，選不到也移不動，正式圖少用；橡皮擦只擦筆刷像素。
- **水平垂直校正**：把選取物角度吸到最近的 0/90/180/270°。
- **復原／重做** 最多 100 步；Ctrl+C／V、Delete 可用。
- **插入圖片**：生成 `type:'image'`，預設鋪滿寬度，需自行縮放。
- **圖層面板**：刪除圖層不檢查鎖定，刪完作用層會跳到相鄰層，連按可能誤刪鎖定的頂層圖。

## 10. 從手繪草圖畫圖的流程

1. **取草圖**：案卷多為 PDF，草圖常是橫放的一頁：`pdftoppm -f N -l N -r 200 -png` 轉圖，旋轉轉正，**局部放大後再讀數字**（整頁縮圖容易讀錯小數）。
2. **讀草圖**：路型與車道寬（路側「↕3.1」＝每車道寬）、分向線虛實、⊗＋編號＝基準點（多為電桿）、沿基準點的虛線＝基準線、兩個相連圓圈＝機車兩輪（T 形短線＝車把＝車頭）、輪旁小數字＝垂距、沿線數字＝沿基準線距離。
3. **抄資料**：時間、地點、車牌、經過從登記聯單與談話紀錄抄；A/B/C 依第一／二／三當事人。抄的時候順便比對各份文件的日期、車牌、車種是否一致；不一致只**回報使用者**，不自行更正、也不寫進現場圖。已駛離、未測繪的車不畫車身，只列入車牌清單與經過，並在圖上空白處加註「○車事後已移動故未測繪」。
4. **定數字的優先做法（約束編輯＋逐條鎖定）**：車照草圖大致擺好、做完定位後，切「約束編輯」，照草圖一條一條定長度，**定好一條就鎖一條**（`constraintLocked=true`），再定下一條。順序：
   ① 靠近基準點的線段（例如基準點到最近輪的沿線距離）→ ② 靠近基準線的線段（垂距）→ ③ 其他。
   - 後面標不動（跳「改不到」提示）＝草圖測繪本身有誤差，這很常見（約八成的草圖都有）。這時剩下的數字切「自由編輯」直接改標籤文字，不再硬挪車。
   - 車的擺放跟草圖差很多＝草圖誤差太大：整張改用自由編輯，**以草圖上的車體擺放為準**，數字照草圖線段長度標上去；看起來比例怪也不必修，那是現場測繪的問題，不是畫圖的問題。
   - 回報時說明哪幾條是約束定出來的、哪幾條是自由編輯直接改的字。
   以下「放車對數字」是程式化時的替代做法（直接算座標），工具的約束編輯可用時優先用上面這套。
5. **放車對數字**：程式建車 → 做定位 → 讀工具算出的數字與草圖比對 → 差 0.1 就移車重跑，直到每個量過的數字都對上；沒量的數字隱藏。讀數用：
   ```js
   ()=>objects.flatMap(o=>
     o.type==='position-mark' ? [['垂距',o.carId,o.cornerIdx,posMarkMeasureText(o),o.measure.show]] :
     o.type==='pos-seg-mark'  ? [['沿線',o.carId,o.segIdx,posSegMeasureText(o),o.measure.show]] : [])
   ```
   機車 `cornerIdx` 0＝後輪、1＝前輪；`segIdx` 0＝兩輪之間、`'rp'`＝基準點到最近垂足。
6. **狀態與行向**：停放被撞的車在名稱旁加紅字「靜止」；依當事人陳述畫自述行向箭頭（台灣靠右行駛），箭頭停在車身外。
7. **北方**：照片常無定位資訊。可用 OpenStreetMap（Overpass 查該路 `way["name"="路名"]` 與門牌 `nwr["addr:street"="路名"]`）求事故路段走向：若畫面左端方位角為 B，畫面上方即 B+90°，指北針 `rotation = −(B+90−360)°`。門牌單雙號分邊，可順便核對事故點在路的哪一側。查不到（網路被擋、查無路名）時，指北針先放 `rotation:0` 佔位並問使用者哪一邊是北；即使查到路的走向，也要先知道畫面左右兩端各通往哪裡才能定北。
- 🔴 **機車停等區（機慢車停等區）不是車**：草圖停止線前、車道內畫的長方框（框內常有機車圖示或寫「機車停等」「停等區」、沒有輪子、沒有車號代號 A/B/C）是路面標線，畫成 `marking-moto-zone` 放「路面標線」層，⛔ 不要畫成 `car`。判斷是不是車：有沒有標 A/B/C 代號、有沒有輪子（圓圈）或車頭方向、有沒有定位量測數字連到它；三樣都沒有就是標線。待轉區框同理（`marking-text`「待轉區」＋框線）。
8. **草圖沒寫的**（北方、路段兩端通往何處、事故類別）不要猜，先放佔位並向使用者確認。
9. **寫了但有歧義的也要問**，碰到就在回報裡列出請使用者確認：
   - 單獨的沿線數字（例如只有一個「1.3」）：是某台車兩輪間距、兩車之間距離，還是距基準點的累計值？
   - 中間的虛線：雙向道路的黃色分向線，還是同向車道之間的白色車道線？
   - 路兩端的箭頭（←、→）：是路段通往何處，還是車輛行進方向？
   - 當事人說的「左側、右側」：配合行進方向與靠右行駛推算，跟草圖車輛位置互相核對，對不上就問。
   - 軸距、車長車寬：草圖沒量就不標數字，推算用的假設值要在回報裡寫明。

## 11. 檢查與出圖

- 每一步放完都**截圖目視核對**，確認位置、數字、遮擋，再說完成。
- 一張完整現場圖應有：表頭單位與事故類別、時間地點、路緣與標線、車輛與名稱、基準點與基準線、定位與車長車寬數字、行向箭頭、指北針、比例尺、路段方向標示、車牌清單、事故經過、製圖日期。
- 核對時直接讀匯出的 PNG（1123×794）裁切放大車輛周圍看，比截整個視窗準。
- 出圖：工具列「匯出圖檔」下載 PNG；「列印」為 A4 橫向；「匯出檔案」下載 JSON 專案檔，可用「匯入檔案」重新開啟。

- 🔴 **交件一定附「可直接編輯的 html」**：把工具 index.html 和專案 JSON 合成一個單檔，使用者雙擊打開就已載入整張圖（含圖層、鎖定、比例尺），可以直接改，不用再手動「匯入檔案」。檔名用「案件名-可編輯.html」，跟 PNG、JSON 一起交。
  - 有 Python：`python3 scripts/make_editable.py <index.html> <專案.json> <案件名-可編輯.html>`（本技能附的腳本）。
  - 沒有 Python（網頁版 AI）：原樣複製 index.html，在最後的 `</body>` 前插入一段 `<script>`，內容是把專案 JSON 放進 `const data = {...}`，等 `Layer`、`_baseImg`、`_topImg` 就緒後照 `cmdImport` 的步驟重建：`layers=[]` → 每層 `new Layer(name)`＋`await l.loadDataURL(data)`、帶回 `specialType／a123／locked`、特殊層 `specialImg` 指回 `_baseImg／_topImg` → `objects=data.objects` → `_migrateA123Freetext()` → 設 `_scale` → `setProj(name); composite(); renderLayers(); clearDirty(); saveSnap('開啟專案'); centerOnTemplate();`。JSON 裡的 `</` 要寫成 `<\/`，免得提早結束 script。
  - 交件前實際打開一次核對：圖層與物件數對得上、畫面跟 PNG 一致。

## 12. Playwright 操作備註

- 要給人看就開有畫面的瀏覽器：`p.chromium.launch(channel='chrome', headless=False, slow_mo=300, args=['--window-size=1600,1000'])`，結尾保持開啟（例如 `pg.wait_for_timeout(600000)`），別太快自動關閉。
- 未安裝 Playwright 自帶瀏覽器時，用 `channel='chrome'` 借系統 Chrome。
- 無畫面環境（雲端、CI）用 headless，並把 PNG 與 JSON 存下來：
  ```python
  b = p.chromium.launch()
  pg = b.new_page(viewport={'width':1600,'height':1000}, accept_downloads=True)
  pg.goto('file://<工具目錄>/index.html'); pg.wait_for_timeout(1500)
  pg.evaluate(BUILD_JS)
  pg.evaluate("setProj('<案件名>')")     # 決定下載檔名
  with pg.expect_download() as d: pg.evaluate('cmdExportImage()')
  d.value.save_as('out.png')
  with pg.expect_download() as d: pg.evaluate('cmdExport()')
  d.value.save_as('out.json')
  ```
- 關閉舊的腳本程序別用 `pkill -f 腳本名`（命令列本身含相同字串會把自己殺掉），改用 `ps -eo pid,args | grep "<腳本名>" | grep -v grep | awk '{print $1}' | xargs -r kill`。
