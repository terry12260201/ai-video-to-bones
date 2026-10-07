"""把「只有一支動畫」的 GLB（例如 beagle_shake_loop.glb）原封不動併進審片室的 beagle.glb。

為什麼不用 Blender 重匯出：抖毛 GLB 是 96 Hz 取樣（保留 1/4 幀腳底修正），也已做過回讀驗證；
用 Blender 全部動作一起重匯出會重新取樣成 24 fps，等於把驗證過的資料換掉。
這支只在 glTF 層搬「動畫的時間／數值 accessor」，模型、骨架、其他動畫一個 byte 都不動。

用法：
  python3 merge_into_review.py <來源.glb> <審片室 beagle.glb> <新動畫名> [--out 輸出.glb]
  沒給 --out 就直接覆寫審片室 beagle.glb（先自己備份或靠 git）。
  已有同名動畫會被取代。
條件：兩顆 GLB 的骨頭節點名稱要一致（同一隻模型）；來源動畫指到的節點在目標裡找不到就停下。
"""
import json, struct, sys, argparse, math

def read_glb(p):
    b = open(p, 'rb').read()
    magic, ver, total = struct.unpack_from('<III', b, 0)
    assert magic == 0x46546C67 and ver == 2, f'{p} 不是 glTF 2.0 GLB'
    jl, jt = struct.unpack_from('<II', b, 12); assert jt == 0x4E4F534A
    j = json.loads(b[20:20 + jl])
    off = 20 + jl
    bin_ = b''
    if off < len(b):
        bl, bt = struct.unpack_from('<II', b, off); assert bt == 0x004E4942
        bin_ = b[off + 8: off + 8 + bl]
    return j, bytearray(bin_)

def write_glb(p, j, bin_):
    js = json.dumps(j, ensure_ascii=False, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    bin_ = bytes(bin_) + b'\0' * ((4 - len(bin_) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_)
    with open(p, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(bin_), 0x004E4942)); f.write(bin_)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('name'); ap.add_argument('--out')
    a = ap.parse_args()
    sj, sb = read_glb(a.src); dj, db = read_glb(a.dst)
    assert len(sj.get('animations', [])) == 1, '來源 GLB 要剛好一支動畫'
    anim = json.loads(json.dumps(sj['animations'][0]))
    dname = {n.get('name'): i for i, n in enumerate(dj['nodes'])}
    # 1) 節點對應（依名稱）
    for ch in anim['channels']:
        nm = sj['nodes'][ch['target']['node']].get('name')
        assert nm in dname, f'目標 GLB 找不到節點 {nm}'
        ch['target']['node'] = dname[nm]
    # 2) 搬 accessor＋bufferView（每個 accessor 各自一個新 bufferView，資料 4-byte 對齊後接在 BIN 尾端）
    amap = {}
    def copy_acc(i):
        if i in amap: return amap[i]
        acc = json.loads(json.dumps(sj['accessors'][i]))
        assert 'sparse' not in acc, '不支援 sparse accessor'
        bv = sj['bufferViews'][acc['bufferView']]
        start = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
        comp = {5126: 4, 5123: 2, 5125: 4, 5121: 1, 5122: 2, 5120: 1}[acc['componentType']]
        ncomp = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[acc['type']]
        stride = bv.get('byteStride', comp * ncomp)
        assert stride == comp * ncomp, '不支援交錯 bufferView'
        data = bytes(sb[start: start + acc['count'] * stride])
        while len(db) % 4: db.append(0)
        newbv = {'buffer': 0, 'byteOffset': len(db), 'byteLength': len(data)}
        db.extend(data)
        dj['bufferViews'].append(newbv)
        acc['bufferView'] = len(dj['bufferViews']) - 1; acc.pop('byteOffset', None)
        dj['accessors'].append(acc)
        amap[i] = len(dj['accessors']) - 1
        return amap[i]
    for s in anim['samplers']:
        s['input'] = copy_acc(s['input']); s['output'] = copy_acc(s['output'])
    anim['name'] = a.name
    anims = [x for x in dj.get('animations', []) if x.get('name') != a.name]
    replaced = len(anims) != len(dj.get('animations', []))
    anims.append(anim)
    anims.sort(key=lambda x: x.get('name', ''))
    dj['animations'] = anims
    dj['buffers'][0]['byteLength'] = len(db)
    out = a.out or a.dst
    write_glb(out, dj, db)
    # 3) 自我檢查：讀回來，新動畫的時間與數值要跟來源逐 byte 相同
    cj, cb = read_glb(out)
    new = next(x for x in cj['animations'] if x['name'] == a.name)
    for s0, s1 in zip(sj['animations'][0]['samplers'], new['samplers']):
        for k in ('input', 'output'):
            A0, A1 = sj['accessors'][s0[k]], cj['accessors'][s1[k]]
            b0 = sj['bufferViews'][A0['bufferView']]; b1 = cj['bufferViews'][A1['bufferView']]
            o0 = b0.get('byteOffset', 0) + A0.get('byteOffset', 0); o1 = b1.get('byteOffset', 0)
            n = b1['byteLength']
            assert sb[o0:o0 + n] == cb[o1:o1 + n], '搬過去的資料不一致'
    t = sj['accessors'][sj['animations'][0]['samplers'][0]['input']]
    print(f'OK：{"取代" if replaced else "新增"}動畫 {a.name}；通道 {len(anim["channels"])}；'
          f'時間 {t.get("min")}–{t.get("max")} 秒、{t["count"]} 點；目標共 {len(cj["animations"])} 支 → {out}')

if __name__ == '__main__':
    main()
