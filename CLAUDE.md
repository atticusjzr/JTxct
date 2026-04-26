# JTxct — 台灣警察交通事故繪圖工具

單檔離線 HTML 工具，用於繪製交通事故現場圖。

## 構建流程

```bash
bash build.sh   # 將 style.css + script.js 內嵌進 dev.html → 產出 index.html
```

開發改 `dev.html` / `script.js` / `style.css`，完成後跑 build.sh，交付 `index.html`。

## 版本控制

```bash
git --git-dir=/home/user/git-repos/JTxct --work-tree=/mnt/linux_share/JTxct <command>
```

每次改完 build 後自動 commit。

## Canvas 尺寸

- 畫布：`W=1123, H=794`（A4 橫向 px）
- `CANVAS_MARGIN=300`（四周留白，顯示畫布為 `(W+600)×(H+600)`）

## 關鍵型別與約定

### marking-turn（轉彎線）
- 使用自有幾何：`cx, cy, a1x, a1y, a2x, a2y`，**不用** 標準 `x,y,w,h`
- 改完幾何後必須呼叫 `syncTurnBBox(obj)` 更新 bbox
- flip 要直接修改幾何（bake in），不能在 draw time 套 transform
- 多選縮放時要特殊處理（見 group-resize 裡的 marking-turn 分支）

### _noObjTx set
不套外層 rotation/flip transform 的型別：`marking-turn`, `refline`, `reflabel`, `freetext`

### _boxMarking set
box 型標線（走 resizeCorner/resizeEdge）：  
`marking-grid`, `marking-moto-zone`, `marking-parking`, `marking-rect`,  
`marking-arrow`, `marking-arrow-turn`, `marking-arrow-straight-turn`, `marking-text`

其餘 `marking-*` 走 `resizeMarkingLength`（鎖定厚度）。

### 標線箭頭
- `drawMarkingArrow` — 直行箭頭，尖朝上
- `drawMarkingArrowTurn` — 轉向箭頭，尾直頭右（80° 轉角，-10° from horizontal）
- `drawMarkingArrowStraightTurn` — 直行轉向，頂部直行箭頭 + 右側轉向分支

### 標字（marking-text）
`_MTEXT_MAP` 映射 variant → `{text, dir}`，dir='v' 直排 / 'h' 橫排。

### markingVariantToTypeColor(v)
variant 字串 → `{type, color}`，新增標線型別記得在這裡加對應。

## 用戶偏好
- 回答簡短直接
- 每次改完自動 build + commit
- 截圖放在 `/mnt/linux_share/JTxct/`（對話中會直接讀取）
