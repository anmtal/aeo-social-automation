# -*- coding: utf-8 -*-
"""The AEO Loop - GRAPHIC carousel style (1080x1350), the elevated look approved
2026-08-16. Pillow-only, renders at 2x then downsamples. Reusable design system:
helpers glow / soft-shadow / phone-mockup / icon-grid / leaderboard / CTA-pill /
stethoscope (medical accent; hero use puts the infinity glyph in the diaphragm,
accent use is a bigger angled dim mark lower-right and keeps the logo as the hero).
Reuse these helpers for future practice carousels; swap the slide functions + copy.
Rules still apply: carousel-generation-quality checklist (CTA ends 'free scan,
link in bio' then 'Be the name AI recommends.'), invented example names only,
no fabricated stats (verified Ahrefs 58% / Adobe 42% ok WITH the source stamped).
Run: python tools/graphic_carousel.py  ->  content/posts/<SLUG>/slide-N.jpg
"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

SLUG = "ai-shortlist-patients"
SS = 2
W, H = 1080*SS, 1350*SS
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "content", "posts", SLUG)
os.makedirs(OUT, exist_ok=True)

# ---- brand ----
BG    = (10, 14, 21)
BG_HI = (17, 25, 36)      # lifted top of gradient
CARD  = (18, 26, 37)
CARD2 = (24, 34, 47)
LINE  = (40, 53, 64)
MINT  = (26, 214, 160)
MINT_D= (15, 120, 92)
WHITE = (240, 243, 240)
MUTE  = (128, 142, 136)
CORAL = (231, 96, 84)
INKTX = (198, 208, 202)
MINT_DIM = (17, 104, 84)   # quiet accent (mint blended toward the background)

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
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline,
                        width=int(width*SS))

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

# ---------- icons (drawn) ----------
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
        d.polygon([(cx-r, cy-r*0.35), (cx, cy-r), (cx+r, cy-r*0.35)], fill=c)   # roof
        for i in range(4):
            x=cx-r*0.78+i*(r*1.56/3)
            d.rectangle([x-r*0.11, cy-r*0.2, x+r*0.11, cy+r*0.8], fill=c)       # columns
        d.rectangle([cx-r, cy+r*0.8, cx+r, cy+r*1.0], fill=c)                    # base
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
    """Line-art stethoscope: binaural top, tube to a chestpiece. When
    diaphragm_glyph, the diaphragm is our infinity glyph (hero use); else a
    plain inner ring (small accent use)."""
    k = SS*scale
    sw = max(2, int(12*k))
    earL=(cx-125*k, cy-165*k); earR=(cx+125*k, cy-165*k)
    J=(cx, cy-25*k)
    ro=58*k
    L=bez(J, (cx-180*k, cy-60*k), (cx-150*k, cy-165*k), earL)
    R=bez(J, (cx+180*k, cy-60*k), (cx+150*k, cy-165*k), earR)
    M=bez(J, (cx-10*k, cy+45*k), (cx+10*k, cy+85*k), (cx, cy+112*k))
    for p in (L, R, M):
        d.line(p, fill=color, width=sw, joint="curve")
    for e in (earL, earR):                                   # ear tips
        d.ellipse([e[0]-19*k, e[1]-19*k, e[0]+19*k, e[1]+19*k], fill=color)
    cc=(cx, cy+112*k+ro)                                     # chestpiece centre
    d.ellipse([cc[0]-ro, cc[1]-ro, cc[0]+ro, cc[1]+ro], outline=color, width=int(sw*1.15))
    if diaphragm_glyph:
        glyph(d, cc[0], cc[1], 2.2*k, color)                 # infinity as the diaphragm
    else:
        d.ellipse([cc[0]-ro*0.5, cc[1]-ro*0.5, cc[0]+ro*0.5, cc[1]+ro*0.5],
                  outline=color, width=int(sw*0.7))          # plain diaphragm (accent)

def stethoscope_rotated(img, cx, cy, scale, color, angle, diaphragm_glyph=False):
    """Draw the stethoscope on a transparent tile, rotate it, composite onto img
    centred at (cx,cy). Lets the accent hang at a natural angle."""
    k = SS*scale
    tw, th = int(390*k), int(510*k)
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    stethoscope(ImageDraw.Draw(tile), tw//2, int(th*0.43), scale, color,
                diaphragm_glyph=diaphragm_glyph)
    tile = tile.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(tile, (int(cx-tile.width/2), int(cy-tile.height/2)), tile)

# ---------- slides ----------
def s1_cover():
    img, d = base(pageno="1 / 6")
    img = glow(img, W//2, int(H*0.30), 560*SS, MINT, strength=105, squash=0.9)
    d = ImageDraw.Draw(img)
    glyph(d, W//2, int(H*0.235), 12.0)
    stethoscope_rotated(img, int(W*0.80), int(H*0.755), 0.56, MINT_DIM, angle=-22, diaphragm_glyph=False)
    d.text((W//2, int(H*0.40)), "  ".join(list("THE NEW FRONT DOOR")),
           font=font(F_BOLD, 22), fill=MINT, anchor="mm")
    fB=font(F_BLACK, 78)
    y=int(H*0.46)
    y=para(d, W//2, y, "Your next patient asks AI before they ask you",
           fB, WHITE, int(W*0.82), int(96*SS), align="center")
    d.text((W//2, y+30*SS), "ChatGPT  ·  Gemini  ·  Perplexity  ·  Claude",
           font=font(F_SEMI, 26), fill=MUTE, anchor="ma")
    # swipe cue
    d.text((W//2, int(H*0.86)), "swipe →", font=font(F_BOLD, 24), fill=MINT, anchor="mm")
    return img

def _phone(d, x0, y0, w, h):
    rrect(d, [x0, y0, x0+w, y0+h], radius=int(58*SS), fill=(6, 9, 14),
          outline=LINE, width=3)
    # notch
    rrect(d, [x0+w/2-70*SS, y0+22*SS, x0+w/2+70*SS, y0+44*SS], radius=int(12*SS), fill=LINE)
    return x0+34*SS, y0+70*SS, w-68*SS  # inner x, y, width

def s2_shortlist():
    img, d = base(pageno="2 / 6")
    eyebrow(d, 96*SS, 150*SS, "The moment", MINT)
    para(d, 96*SS, 188*SS, "AI hands them a shortlist",
         font(F_BLACK, 62), WHITE, int(W*0.82), int(74*SS))
    pw, ph = 720*SS, 820*SS
    px, py = (W-pw)//2, 300*SS
    shadow(img, [px, py, px+pw, py+ph], 58, blur=30, alpha=140, dy=18)
    d = ImageDraw.Draw(img)
    ix, iy, iw = _phone(d, px, py, pw, ph)
    # user prompt bubble (mint, right)
    pf = font(F_BOLD, 29)
    bw = iw*0.92
    bx1 = ix+iw; bx0 = bx1-bw
    lines = wrap(d, "Who is the best rhinoplasty surgeon near me?", pf, bw-56*SS)
    bh = len(lines)*42*SS + 46*SS
    rrect(d, [bx0, iy, bx1, iy+bh], radius=int(28*SS), fill=MINT)
    yy = iy+24*SS
    for ln in lines:
        d.text((bx0+28*SS, yy), ln, font=pf, fill=(8, 12, 18)); yy += 42*SS
    # AI answer card fills the rest of the screen
    ay = iy+bh+30*SS
    card_h = (py+ph-30*SS) - ay
    rrect(d, [ix, ay, ix+iw, ay+card_h], radius=int(28*SS), fill=CARD)
    d.text((ix+30*SS, ay+28*SS), "A I   R E C O M M E N D S", font=font(F_BOLD, 21), fill=MUTE)
    names = ["Meridian Aesthetics", "Park Avenue Facial", "Downtown Cosmetic"]
    ry = ay+86*SS
    for i, nm in enumerate(names):
        d.text((ix+30*SS, ry), f"{i+1}.", font=font(F_BLACK, 32), fill=MINT)
        d.text((ix+84*SS, ry), nm, font=font(F_BOLD, 32), fill=WHITE); ry += 70*SS
    d.text((ix+30*SS, ry+4*SS), "4.", font=font(F_BLACK, 32), fill=CORAL)
    d.line([ix+84*SS, ry+26*SS, ix+iw-150*SS, ry+26*SS], fill=MUTE, width=int(3*SS))
    d.text((ix+iw-128*SS, ry+4*SS), "you?", font=font(F_BLACK, 32), fill=CORAL)
    d = ImageDraw.Draw(img)
    para(d, W//2, py+ph+40*SS, "Most practices are not on it, and never find out.",
         font(F_SEMI, 30), INKTX, int(W*0.84), int(40*SS), align="center")
    return img

def s3_signals():
    img, d = base(pageno="3 / 6")
    eyebrow(d, 96*SS, 150*SS, "Before it answers", MINT)
    para(d, 96*SS, 192*SS, "What AI reads before it names anyone",
         font(F_BLACK, 58), WHITE, int(W*0.82), int(70*SS))
    items = [("star", "Your Google reviews", "recency and what they say"),
             ("pin", "Your Business Profile", "complete, current, consistent"),
             ("building", "Directories it trusts", "RealSelf, ASPS and more"),
             ("doc", "Pages it can quote", "clear answers on your site")]
    gx, gy = 96*SS, 470*SS
    cw, ch = (W-96*SS*2-40*SS)//2, 300*SS
    for i, (kind, t, sub) in enumerate(items):
        cx0 = gx + (i % 2)*(cw+40*SS)
        cy0 = gy + (i//2)*(ch+40*SS)
        shadow(img, [cx0, cy0, cx0+cw, cy0+ch], 40, blur=22, alpha=110, dy=12)
        d = ImageDraw.Draw(img)
        rrect(d, [cx0, cy0, cx0+cw, cy0+ch], radius=int(34*SS), fill=CARD,
              outline=LINE, width=2)
        icon_chip(d, cx0+78*SS, cy0+82*SS, 52*SS, kind)
        d.text((cx0+44*SS, cy0+168*SS), t, font=font(F_BOLD, 33), fill=WHITE)
        para(d, cx0+44*SS, cy0+214*SS, sub, font(F_REG, 25), MUTE, cw-80*SS, int(34*SS))
    d = ImageDraw.Draw(img)
    para(d, W//2, gy+2*ch+40*SS+34*SS, "Thin in these, and the engine has nothing to say about you.",
         font(F_SEMI, 30), INKTX, int(W*0.86), int(40*SS), align="center")
    return img

def s4_cost():
    img, d = base(pageno="4 / 6")
    img = glow(img, W//2, int(H*0.52), 520*SS, CORAL, strength=60, squash=0.8)
    d = ImageDraw.Draw(img)
    d.text((W//2, 300*SS), "  ".join(list("THE QUIET COST")),
           font=font(F_BOLD, 22), fill=CORAL, anchor="mm")
    y = 420*SS
    for ln in ["No missed call.", "No failed form."]:
        d.text((W//2, y), ln, font=font(F_BLACK, 96), fill=WHITE, anchor="ma"); y += 118*SS
    # coral down-arrow motif
    ay = y+40*SS
    d.line([W//2, ay, W//2, ay+120*SS], fill=CORAL, width=int(8*SS))
    d.polygon([(W//2-38*SS, ay+96*SS), (W//2+38*SS, ay+96*SS), (W//2, ay+156*SS)], fill=CORAL)
    para(d, W//2, ay+210*SS, "Just a patient who quietly booked the name AI gave them.",
         font(F_SEMI, 34), INKTX, int(W*0.78), int(48*SS), align="center")
    return img

def s5_fix():
    img, d = base(pageno="5 / 6")
    img = glow(img, W//2, int(H*0.42), 460*SS, MINT, strength=80, squash=0.9)
    d = ImageDraw.Draw(img)
    eyebrow(d, 96*SS, 150*SS, "When the signals are right", MINT)
    para(d, 96*SS, 192*SS, "Be the name it recommends",
         font(F_BLACK, 62), WHITE, int(W*0.82), int(74*SS))
    rows = [("1", "Your practice", MINT, True),
            ("2", "Meridian Aesthetics", MUTE, False),
            ("3", "Park Avenue Facial", MUTE, False)]
    ry = 420*SS
    rw = W-96*SS*2
    for rank, nm, col, hot in rows:
        rh = 148*SS if hot else 120*SS
        box = [96*SS, ry, 96*SS+rw, ry+rh]
        if hot:
            shadow(img, box, 34, blur=26, alpha=130, dy=14); d = ImageDraw.Draw(img)
            rrect(d, box, radius=int(30*SS), fill=(18, 44, 37), outline=MINT, width=3)
        else:
            rrect(d, box, radius=int(30*SS), fill=CARD, outline=LINE, width=2)
        cyc = ry+rh//2
        d.text((150*SS, cyc), rank, font=font(F_BLACK, 60 if hot else 46),
               fill=col, anchor="mm")
        d.text((240*SS, cyc), nm, font=font(F_BOLD, 44 if hot else 38),
               fill=WHITE if hot else INKTX, anchor="lm")
        if hot:
            draw_star(d, 96*SS+rw-58*SS, cyc, 28*SS, MINT)
        ry += rh+28*SS
    para(d, W//2, ry+16*SS, "The signals are fixable. That is the whole game.",
         font(F_SEMI, 32), INKTX, int(W*0.84), int(42*SS), align="center")
    return img

def s6_cta():
    img, d = base(pageno="6 / 6", footer=False)
    img = glow(img, W//2, int(H*0.40), 520*SS, MINT, strength=95, squash=0.9)
    d = ImageDraw.Draw(img)
    glyph(d, W//2, int(H*0.30), 12.0)
    y = int(H*0.44)
    y = para(d, W//2, y, "See who AI names in your city",
             font(F_BLACK, 64), WHITE, int(W*0.8), int(80*SS), align="center")
    # link-in-bio pill
    pill = "Run the free scan  ·  link in bio"
    fpill = font(F_BOLD, 34)
    tw = d.textlength(pill, font=fpill)
    px0 = W//2-tw//2-44*SS; px1 = W//2+tw//2+44*SS
    py0 = y+34*SS; py1 = py0+92*SS
    rrect(d, [px0, py0, px1, py1], radius=int(46*SS), fill=MINT)
    d.text((W//2, (py0+py1)//2), pill, font=fpill, fill=(8, 12, 18), anchor="mm")
    d.text((W//2, py1+80*SS), "Be the name AI recommends.",
           font=font(F_BLACK, 46), fill=MINT, anchor="ma")
    glyph(d, W//2-118*SS, H-92*SS, 3.0)
    d.text((W//2-92*SS, H-92*SS), "theaeoloop.com", font=font(F_BOLD, 21), fill=MINT, anchor="lm")
    return img

slides = [s1_cover(), s2_shortlist(), s3_signals(), s4_cost(), s5_fix(), s6_cta()]
for i, im in enumerate(slides, 1):
    im.resize((1080, 1350), Image.LANCZOS).save(os.path.join(OUT, f"slide-{i}.jpg"),
                                                "JPEG", quality=92)
print("rendered", len(slides), "slides ->", OUT)
