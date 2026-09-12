# -*- coding: utf-8 -*-
"""The AEO Loop — DATA-DRIVEN elevated carousel renderer (1080x1350).
Generalises the approved 2026-08-16 graphic style (tools/graphic_carousel.py,
which was hardcoded to one carousel) into a batch renderer that reads
content/carousels.json and renders content/posts/<slug>/slide-N.jpg for every
entry, so tools/build_manifest.py can schedule them.

Each carousel entry:
  { slug, vertical: surgeon|law|general,
    eyebrow, hook, accent: stethoscope|none,        # cover
    deck: [ {type, ...} ],                            # middle slides (see below)
    cta_headline,                                     # cta big line
    caption, firstComment }                           # used by build_manifest

deck slide types (reusable elevated components):
  phone      {prompt, names[], you_label?, caption?}      -> phone mockup shortlist
  signals    {title, items[{icon(star|pin|building|doc), title, sub}], caption?}
  statement  {kicker, lines[], caption?, tone(coral|mint)?}
  leaderboard{title, rows[{rank, name, hot?}], caption?}
  point      {num, kicker?, text}                          -> elevated single point
  bars       {title, bars[{label, value(0-1)}], caption?}
  compare    {left{title, items[]}, right{title, items[]}, caption?}

Slide order = cover -> deck... -> cta. Rules still apply: CTA pill = free scan,
link in bio + "Be the name AI recommends."; invented example names only; no
fabricated stats (verified Ahrefs 58% / Adobe 42% / July-2026 73% study ok WITH
the source stamped on the slide).
Run: python tools/graphic_deck.py
"""
import os, math, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "content", "carousels.json")
OUTROOT = os.path.join(HERE, "content", "posts")
SS = 2
W, H = 1080*SS, 1350*SS

# ---- brand palette (identical to graphic_carousel.py) ----
BG    = (10, 14, 21)
BG_HI = (17, 25, 36)
CARD  = (18, 26, 37)
CARD2 = (24, 34, 47)
LINE  = (40, 53, 64)
MINT  = (26, 214, 160)
MINT_D= (15, 120, 92)
WHITE = (240, 243, 240)
MUTE  = (128, 142, 136)
CORAL = (231, 96, 84)
INKTX = (198, 208, 202)
MINT_DIM = (17, 104, 84)

def fp(*c):
    for p in c:
        if os.path.exists(p): return p
    return c[-1]
F_BLACK = fp("C:/Windows/Fonts/seguibl.ttf", "C:/Windows/Fonts/segoeuib.ttf")
F_BOLD  = fp("C:/Windows/Fonts/segoeuib.ttf")
F_SEMI  = fp("C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeuib.ttf")
F_REG   = fp("C:/Windows/Fonts/segoeui.ttf")
def font(p, s): return ImageFont.truetype(p, int(s*SS))

# ---------- primitives ----------
def vgrad(top, bot):
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y/(H-1)
        col.putpixel((0, y), tuple(int(top[i]+(bot[i]-top[i])*t) for i in range(3)))
    return col.resize((W, H))

def glow(img, cx, cy, r, color, strength=150, squash=1.0):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    steps = 48
    for i in range(steps):
        rr = r*(steps-i)/steps
        a = int(strength*(i/steps)**2.2)
        d.ellipse([cx-rr, cy-rr*squash, cx+rr, cy+rr*squash], fill=a)
    m = m.filter(ImageFilter.GaussianBlur(60*SS))
    tint = Image.new("RGB", (W, H), color)
    return Image.composite(ImageChops.screen(img, tint), img, m)

def shadow(img, box, radius, blur=26, alpha=150, dy=16):
    x0, y0, x1, y1 = box
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, y0+dy*SS, x1, y1+dy*SS], radius,
                                         fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur*SS))
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh.split()[3])

def rrect(d, box, radius, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=int(width*SS))

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur+" "+w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out

def para(d, x, y, text, f, fill, maxw, lh, anchor="la", align="left"):
    for ln in wrap(d, text, f, maxw):
        xx = x
        if align == "center": xx = x - d.textlength(ln, font=f)/2
        d.text((xx, y), ln, font=f, fill=fill, anchor=anchor); y += lh
    return y

def fit_para(d, x, y, text, path, start, mins, fill, maxw, gap=1.12, max_h=None,
             align="left"):
    """Shrink font until the wrapped paragraph fits max_h, then draw it."""
    s = start
    while s >= mins:
        f = font(path, s); lines = wrap(d, text, f, maxw)
        a, de = f.getmetrics(); lh = int((a+de)*gap/SS)*SS
        if max_h is None or lh*len(lines) <= max_h:
            break
        s -= 3
    for ln in lines:
        xx = x
        if align == "center": xx = x - d.textlength(ln, font=f)/2
        d.text((xx, y), ln, font=f, fill=fill, anchor="la" if align=="left" else "la")
        y += lh
    return y

def glyph(d, cx, cy, scale, color=MINT):
    segs=[((16,16),(12,8),(5,8),(5,16)),((5,16),(5,24),(12,24),(16,16)),
          ((16,16),(20,8),(27,8),(27,16)),((27,16),(27,24),(20,24),(16,16))]
    r=2.9*scale/2
    for p0,p1,p2,p3 in segs:
        for i in range(101):
            t=i/100; u=1-t
            xx=u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0]
            yy=u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]
            d.ellipse([cx+(xx-16)*scale-r, cy+(yy-16)*scale-r,
                       cx+(xx-16)*scale+r, cy+(yy-16)*scale+r], fill=color)

def base(pageno=None, footer=True):
    img = vgrad(BG_HI, BG)
    d = ImageDraw.Draw(img)
    if footer:
        glyph(d, W//2-118*SS, H-92*SS, 3.0)
        d.text((W//2-92*SS, H-92*SS), "theaeoloop.com", font=font(F_BOLD, 21),
               fill=MINT, anchor="lm")
    if pageno:
        d.text((W-84*SS, 78*SS), pageno, font=font(F_BOLD, 20), fill=MUTE, anchor="rm")
    return img, d

def eyebrow(d, x, y, text, color=MINT):
    d.text((x, y), "  ".join(list(text.upper())), font=font(F_BOLD, 22), fill=color, anchor="lm")

def icon_chip(d, cx, cy, s, kind):
    rrect(d, [cx-s, cy-s, cx+s, cy+s], radius=int(s*0.5),
          fill=(20, 42, 36), outline=(30, 82, 66), width=2)
    c = MINT; r = s*0.52
    if kind == "star":
        pts=[]
        for i in range(10):
            ang=-math.pi/2+i*math.pi/5
            rad=r if i%2==0 else r*0.44
            pts.append((cx+rad*math.cos(ang), cy+rad*math.sin(ang)))
        d.polygon(pts, fill=c)
    elif kind == "pin":
        d.ellipse([cx-r*0.7, cy-r*0.9, cx+r*0.7, cy+r*0.5], fill=c)
        d.polygon([(cx-r*0.5, cy+r*0.1), (cx+r*0.5, cy+r*0.1), (cx, cy+r*1.05)], fill=c)
        d.ellipse([cx-r*0.24, cy-r*0.42, cx+r*0.24, cy+r*0.06], fill=(20,42,36))
    elif kind == "building":
        d.polygon([(cx-r, cy-r*0.35), (cx, cy-r), (cx+r, cy-r*0.35)], fill=c)
        for i in range(4):
            x=cx-r*0.78+i*(r*1.56/3)
            d.rectangle([x-r*0.11, cy-r*0.2, x+r*0.11, cy+r*0.8], fill=c)
        d.rectangle([cx-r, cy+r*0.8, cx+r, cy+r*1.0], fill=c)
    elif kind == "doc":
        d.rounded_rectangle([cx-r*0.7, cy-r, cx+r*0.7, cy+r], radius=int(r*0.18), fill=c)
        for i in range(3):
            yy=cy-r*0.4+i*r*0.42
            d.rectangle([cx-r*0.42, yy-r*0.06, cx+r*0.42, yy+r*0.06], fill=(20,42,36))

def draw_star(d, cx, cy, r, color):
    pts=[]
    for i in range(10):
        ang=-math.pi/2+i*math.pi/5
        rad=r if i%2==0 else r*0.44
        pts.append((cx+rad*math.cos(ang), cy+rad*math.sin(ang)))
    d.polygon(pts, fill=color)

def bez(p0, p1, p2, p3, n=54):
    pts=[]
    for i in range(n+1):
        t=i/n; u=1-t
        pts.append((u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0],
                    u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]))
    return pts

def stethoscope(d, cx, cy, scale, color, diaphragm_glyph=True):
    k = SS*scale
    sw = max(2, int(14*k))
    earL=(cx-125*k, cy-165*k); earR=(cx+125*k, cy-165*k)
    J=(cx, cy-25*k); ro=58*k
    L=bez(J, (cx-180*k, cy-60*k), (cx-150*k, cy-165*k), earL)
    R=bez(J, (cx+180*k, cy-60*k), (cx+150*k, cy-165*k), earR)
    M=bez(J, (cx-10*k, cy+45*k), (cx+10*k, cy+85*k), (cx, cy+112*k))
    for p in (L, R, M):
        d.line(p, fill=color, width=sw, joint="curve")
    for e in (earL, earR):
        d.ellipse([e[0]-20*k, e[1]-20*k, e[0]+20*k, e[1]+20*k], fill=color)
    cc=(cx, cy+112*k+ro)
    d.ellipse([cc[0]-ro, cc[1]-ro, cc[0]+ro, cc[1]+ro], outline=color, width=int(sw*1.15))
    if diaphragm_glyph:
        glyph(d, cc[0], cc[1], 2.2*k, color)
    else:
        d.ellipse([cc[0]-ro*0.5, cc[1]-ro*0.5, cc[0]+ro*0.5, cc[1]+ro*0.5],
                  outline=color, width=int(sw*0.7))

def stethoscope_rotated(img, cx, cy, scale, color, angle, diaphragm_glyph=False):
    k = SS*scale
    tw, th = int(390*k), int(510*k)
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    stethoscope(ImageDraw.Draw(tile), tw//2, int(th*0.43), scale, color,
                diaphragm_glyph=diaphragm_glyph)
    tile = tile.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(tile, (int(cx-tile.width/2), int(cy-tile.height/2)), tile)

def _phone(d, x0, y0, w, h):
    rrect(d, [x0, y0, x0+w, y0+h], radius=int(58*SS), fill=(6, 9, 14),
          outline=LINE, width=3)
    rrect(d, [x0+w/2-70*SS, y0+22*SS, x0+w/2+70*SS, y0+44*SS], radius=int(12*SS), fill=LINE)
    return x0+34*SS, y0+70*SS, w-68*SS

# ---------- slide components ----------
def c_cover(spec, page):
    img, d = base(pageno=page)
    img = glow(img, W//2, int(H*0.28), 560*SS, MINT, strength=105, squash=0.9)
    d = ImageDraw.Draw(img)
    glyph(d, W//2, int(H*0.215), 11.0)
    if spec.get("accent") == "stethoscope":
        stethoscope_rotated(img, int(W*0.80), int(H*0.775), 0.52, MINT_DIM, angle=-22)
        d = ImageDraw.Draw(img)
    d.text((W//2, int(H*0.37)), "  ".join(list(spec["eyebrow"].upper())),
           font=font(F_BOLD, 22), fill=MINT, anchor="mm")
    top, bot = int(H*0.42), int(H*0.80)
    # choose a size that fits, then vertically center
    text = spec["hook"]; s = 78
    while s >= 46:
        f = font(F_BLACK, s); lines = wrap(d, text, f, int(W*0.82))
        a, de = f.getmetrics(); lh = int((a+de)*1.14)
        if lh*len(lines) <= (bot-top): break
        s -= 3
    y = top + ((bot-top) - lh*len(lines))//2
    for ln in lines:
        d.text((W//2, y), ln, font=f, fill=WHITE, anchor="ma"); y += lh
    d.text((W//2, int(H*0.865)), "swipe →", font=font(F_BOLD, 24), fill=MINT, anchor="mm")
    return img

def c_phone(v, page):
    img, d = base(pageno=page)
    eyebrow(d, 96*SS, 150*SS, v.get("kicker", "The moment"), MINT)
    para(d, 96*SS, 188*SS, v.get("title", "AI hands them a shortlist"),
         font(F_BLACK, 58), WHITE, int(W*0.82), int(70*SS))
    pw, ph = 720*SS, 812*SS
    px, py = (W-pw)//2, 306*SS
    shadow(img, [px, py, px+pw, py+ph], 58, blur=30, alpha=140, dy=18)
    d = ImageDraw.Draw(img)
    ix, iy, iw = _phone(d, px, py, pw, ph)
    pf = font(F_BOLD, 29); bw = iw*0.92
    bx1 = ix+iw; bx0 = bx1-bw
    lines = wrap(d, v["prompt"], pf, bw-56*SS)
    bh = len(lines)*42*SS + 46*SS
    rrect(d, [bx0, iy, bx1, iy+bh], radius=int(28*SS), fill=MINT)
    yy = iy+24*SS
    for ln in lines:
        d.text((bx0+28*SS, yy), ln, font=pf, fill=(8, 12, 18)); yy += 42*SS
    ay = iy+bh+30*SS
    card_h = (py+ph-30*SS) - ay
    rrect(d, [ix, ay, ix+iw, ay+card_h], radius=int(28*SS), fill=CARD)
    d.text((ix+30*SS, ay+28*SS), "  ".join(list("AI RECOMMENDS")),
           font=font(F_BOLD, 20), fill=MUTE)
    names = v["names"]; ry = ay+86*SS
    for i, nm in enumerate(names):
        d.text((ix+30*SS, ry), f"{i+1}.", font=font(F_BLACK, 32), fill=MINT)
        d.text((ix+84*SS, ry), nm, font=font(F_BOLD, 32), fill=WHITE); ry += 70*SS
    d.text((ix+30*SS, ry+4*SS), f"{len(names)+1}.", font=font(F_BLACK, 32), fill=CORAL)
    d.line([ix+84*SS, ry+26*SS, ix+iw-150*SS, ry+26*SS], fill=MUTE, width=int(3*SS))
    d.text((ix+iw-128*SS, ry+4*SS), v.get("you_label", "you?"),
           font=font(F_BLACK, 32), fill=CORAL)
    d = ImageDraw.Draw(img)
    if v.get("caption"):
        para(d, W//2, py+ph+38*SS, v["caption"], font(F_SEMI, 29), INKTX,
             int(W*0.84), int(39*SS), align="center")
    return img

def c_signals(v, page):
    img, d = base(pageno=page)
    eyebrow(d, 96*SS, 150*SS, v.get("kicker", "Before it answers"), MINT)
    para(d, 96*SS, 192*SS, v["title"], font(F_BLACK, 54), WHITE, int(W*0.82), int(66*SS))
    items = v["items"]
    gx, gy = 96*SS, 468*SS
    cw, ch = (W-96*SS*2-40*SS)//2, 296*SS
    for i, it in enumerate(items[:4]):
        cx0 = gx + (i % 2)*(cw+40*SS)
        cy0 = gy + (i//2)*(ch+40*SS)
        shadow(img, [cx0, cy0, cx0+cw, cy0+ch], 40, blur=22, alpha=110, dy=12)
        d = ImageDraw.Draw(img)
        rrect(d, [cx0, cy0, cx0+cw, cy0+ch], radius=int(34*SS), fill=CARD,
              outline=LINE, width=2)
        icon_chip(d, cx0+78*SS, cy0+80*SS, 50*SS, it.get("icon", "star"))
        d.text((cx0+44*SS, cy0+164*SS), it["title"], font=font(F_BOLD, 32), fill=WHITE)
        para(d, cx0+44*SS, cy0+210*SS, it["sub"], font(F_REG, 24), MUTE, cw-80*SS, int(33*SS))
    d = ImageDraw.Draw(img)
    if v.get("caption"):
        para(d, W//2, gy+2*ch+40*SS+30*SS, v["caption"], font(F_SEMI, 29), INKTX,
             int(W*0.86), int(39*SS), align="center")
    return img

def c_statement(v, page):
    tone = CORAL if v.get("tone") == "coral" else MINT
    img, d = base(pageno=page)
    img = glow(img, W//2, int(H*0.50), 520*SS, tone, strength=62, squash=0.8)
    d = ImageDraw.Draw(img)
    if v.get("kicker"):
        d.text((W//2, 300*SS), "  ".join(list(v["kicker"].upper())),
               font=font(F_BOLD, 22), fill=tone, anchor="mm")
    lines = v["lines"]
    # size the big lines to fit width
    s = 92
    while s >= 52:
        f = font(F_BLACK, s)
        if all(d.textlength(l, font=f) <= W*0.82 for l in lines): break
        s -= 3
    a, de = f.getmetrics(); lh = int((a+de)*1.05)
    y = 430*SS
    for ln in lines:
        d.text((W//2, y), ln, font=f, fill=WHITE, anchor="ma"); y += lh
    ay = y+30*SS
    d.line([W//2, ay, W//2, ay+112*SS], fill=tone, width=int(8*SS))
    d.polygon([(W//2-38*SS, ay+90*SS), (W//2+38*SS, ay+90*SS), (W//2, ay+148*SS)], fill=tone)
    if v.get("caption"):
        para(d, W//2, ay+200*SS, v["caption"], font(F_SEMI, 33), INKTX,
             int(W*0.80), int(46*SS), align="center")
    return img

def c_leaderboard(v, page):
    img, d = base(pageno=page)
    img = glow(img, W//2, int(H*0.40), 460*SS, MINT, strength=78, squash=0.9)
    d = ImageDraw.Draw(img)
    eyebrow(d, 96*SS, 150*SS, v.get("kicker", "When the signals are right"), MINT)
    para(d, 96*SS, 192*SS, v["title"], font(F_BLACK, 58), WHITE, int(W*0.82), int(70*SS))
    rows = v["rows"]; ry = 420*SS; rw = W-96*SS*2
    for r in rows:
        hot = r.get("hot", False)
        rh = 148*SS if hot else 118*SS
        box = [96*SS, ry, 96*SS+rw, ry+rh]
        if hot:
            shadow(img, box, 34, blur=26, alpha=130, dy=14); d = ImageDraw.Draw(img)
            rrect(d, box, radius=int(30*SS), fill=(18, 44, 37), outline=MINT, width=3)
        else:
            rrect(d, box, radius=int(30*SS), fill=CARD, outline=LINE, width=2)
        cyc = ry+rh//2
        d.text((150*SS, cyc), str(r["rank"]), font=font(F_BLACK, 58 if hot else 44),
               fill=MINT if hot else MUTE, anchor="mm")
        d.text((240*SS, cyc), r["name"], font=font(F_BOLD, 43 if hot else 37),
               fill=WHITE if hot else INKTX, anchor="lm")
        if hot:
            draw_star(d, 96*SS+rw-58*SS, cyc, 27*SS, MINT)
        ry += rh+26*SS
    if v.get("caption"):
        para(d, W//2, ry+14*SS, v["caption"], font(F_SEMI, 31), INKTX,
             int(W*0.84), int(42*SS), align="center")
    return img

def c_point(v, page):
    img, d = base(pageno=page)
    if v.get("kicker"):
        eyebrow(d, 96*SS, 168*SS, v["kicker"], MINT)
    nf = font(F_BLACK, 116)
    d.text((96*SS, 208*SS), str(v["num"]), font=nf, fill=MINT, anchor="la")
    bb = d.textbbox((96*SS, 208*SS), str(v["num"]), font=nf, anchor="la")
    uy = bb[3] + 26*SS
    d.line([(96*SS, uy), (96*SS+78*SS, uy)], fill=MINT, width=int(6*SS))
    top, bot = uy+66*SS, H-200*SS
    s = 60
    while s >= 40:
        f = font(F_BOLD, s); lines = wrap(d, v["text"], f, int(W*0.80))
        a, de = f.getmetrics(); lh = int((a+de)*1.16)
        if lh*len(lines) <= (bot-top): break
        s -= 3
    y = top
    for ln in lines:
        d.text((96*SS, y), ln, font=f, fill=WHITE, anchor="la"); y += lh
    return img

def c_bars(v, page):
    img, d = base(pageno=page)
    eyebrow(d, 96*SS, 150*SS, v.get("kicker", "What moves the needle"), MINT)
    para(d, 96*SS, 192*SS, v["title"], font(F_BLACK, 52), WHITE, int(W*0.82), int(64*SS))
    bars = v["bars"]; y = 430*SS; bw = W-2*96*SS
    for b in bars:
        d.text((96*SS, y), b["label"], font=font(F_BOLD, 34), fill=WHITE, anchor="ls")
        by = y+26*SS
        rrect(d, [96*SS, by, 96*SS+bw, by+48*SS], radius=int(16*SS), fill=CARD)
        w = int(bw*max(0.12, min(1.0, b["value"])))
        rrect(d, [96*SS, by, 96*SS+w, by+48*SS], radius=int(16*SS), fill=MINT)
        y += 150*SS
    if v.get("caption"):
        para(d, W//2, y+6*SS, v["caption"], font(F_SEMI, 29), INKTX,
             int(W*0.84), int(39*SS), align="center")
    return img

def c_compare(v, page):
    img, d = base(pageno=page)
    eyebrow(d, 96*SS, 150*SS, v.get("kicker", "The difference"), MINT)
    para(d, 96*SS, 192*SS, v.get("title", ""), font(F_BLACK, 52), WHITE, int(W*0.82), int(64*SS))
    top, bot = 360*SS, H-220*SS
    midx = W//2
    d.line([(midx, top), (midx, bot)], fill=LINE, width=int(3*SS))
    def col(cx, title, items, accent):
        d.text((cx, top+20*SS), title, font=font(F_BLACK, 44), fill=accent, anchor="mm")
        y = top+120*SS
        for it in items:
            y = para(d, cx, y, it, font(F_REG, 34), WHITE, (W//2)-2*96*SS, int(46*SS),
                     align="center") + 22*SS
    col(W//4+20*SS, v["left"]["title"], v["left"]["items"], MUTE)
    col(3*W//4-20*SS, v["right"]["title"], v["right"]["items"], MINT)
    if v.get("caption"):
        para(d, W//2, bot+16*SS, v["caption"], font(F_SEMI, 29), INKTX,
             int(W*0.84), int(39*SS), align="center")
    return img

def c_cta(spec, page):
    img, d = base(pageno=page, footer=False)
    img = glow(img, W//2, int(H*0.38), 520*SS, MINT, strength=95, squash=0.9)
    d = ImageDraw.Draw(img)
    glyph(d, W//2, int(H*0.29), 11.0)
    top, bot = int(H*0.40), int(H*0.60)
    text = spec.get("cta_headline", "See who AI names in your city")
    s = 64
    while s >= 44:
        f = font(F_BLACK, s); lines = wrap(d, text, f, int(W*0.80))
        a, de = f.getmetrics(); lh = int((a+de)*1.08)
        if lh*len(lines) <= (bot-top): break
        s -= 3
    y = top
    for ln in lines:
        d.text((W//2, y), ln, font=f, fill=WHITE, anchor="ma"); y += lh
    pill = "Run the free scan  ·  link in bio"
    fpill = font(F_BOLD, 33); tw = d.textlength(pill, font=fpill)
    px0 = W//2-tw//2-44*SS; px1 = W//2+tw//2+44*SS
    py0 = y+30*SS; py1 = py0+92*SS
    rrect(d, [px0, py0, px1, py1], radius=int(46*SS), fill=MINT)
    d.text((W//2, (py0+py1)//2), pill, font=fpill, fill=(8, 12, 18), anchor="mm")
    d.text((W//2, py1+74*SS), "Be the name AI recommends.",
           font=font(F_BLACK, 44), fill=MINT, anchor="ma")
    glyph(d, W//2-118*SS, H-92*SS, 3.0)
    d.text((W//2-92*SS, H-92*SS), "theaeoloop.com", font=font(F_BOLD, 21), fill=MINT, anchor="lm")
    return img

DECK = {"phone": c_phone, "signals": c_signals, "statement": c_statement,
        "leaderboard": c_leaderboard, "point": c_point, "bars": c_bars,
        "compare": c_compare}

def render(post):
    deck = post.get("deck", [])
    total = 2 + len(deck)
    imgs = [c_cover(post, f"1 / {total}")]
    for i, v in enumerate(deck, start=2):
        imgs.append(DECK[v["type"]](v, f"{i} / {total}"))
    imgs.append(c_cta(post, f"{total} / {total}"))
    outdir = os.path.join(OUTROOT, post["slug"]); os.makedirs(outdir, exist_ok=True)
    for fn in os.listdir(outdir):
        if fn.startswith("slide-"): os.remove(os.path.join(outdir, fn))
    for i, im in enumerate(imgs, 1):
        im.resize((1080, 1350), Image.LANCZOS).save(
            os.path.join(outdir, f"slide-{i}.jpg"), "JPEG", quality=92)
    return len(imgs)

if __name__ == "__main__":
    import sys
    posts = json.load(open(SPEC, encoding="utf-8"))
    only = set(sys.argv[1:])
    for post in posts:
        if only and post["slug"] not in only: continue
        n = render(post); print(f"{post['slug']}: {n} slides")
    print("done")
