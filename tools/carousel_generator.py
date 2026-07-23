# -*- coding: utf-8 -*-
"""The AEO Loop — Instagram carousel generator (1080x1350 4:5 slides).
Reads carousels.json; renders JPEG slides to content/posts/<slug>/.
Post shape: { slug, eyebrow, hook, points[], cta, caption, firstComment,
              visual?: {type: chat|compare|bars|flow, ...} }
Slide order: cover -> visual (if any) -> point slides -> cta.
Run:  python tools/carousel_generator.py"""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "content", "carousels.json")
OUTROOT = os.path.join(HERE, "content", "posts")

SS = 2
W, H = 1080*SS, 1350*SS
BG   = (10, 14, 21)      # #0A0E15
CARD = (18, 26, 37)      # slightly lighter card
MINT = (26, 214, 160)    # #1AD6A0
WHITE= (238, 241, 238)
MUTE = (120, 134, 128)
CORAL= (226, 86, 75)     # for "missing / gap"
MARGIN = 120*SS
FB = "C:/Windows/Fonts/segoeuib.ttf"
FR = "C:/Windows/Fonts/segoeui.ttf"
def font(p,s): return ImageFont.truetype(p, int(s))

def glyph(d, cx, cy, scale):
    segs=[((16,16),(12,8),(5,8),(5,16)),((5,16),(5,24),(12,24),(16,16)),
          ((16,16),(20,8),(27,8),(27,16)),((27,16),(27,24),(20,24),(16,16))]
    r=2.9*scale/2
    for p0,p1,p2,p3 in segs:
        for i in range(101):
            t=i/100;u=1-t
            x=u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0]
            y=u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]
            d.ellipse([cx+(x-16)*scale-r,cy+(y-16)*scale-r,cx+(x-16)*scale+r,cy+(y-16)*scale+r],fill=MINT)

def wrap_lines(d, text, f, max_w):
    out=[]; cur=""
    for w in text.split():
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)<=max_w: cur=t
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out

def fit(d, text, max_w, path, start, min_size, gap=1.16):
    s=start
    while s>=min_size:
        f=font(path,s); lines=wrap_lines(d,text,f,max_w)
        if all(d.textlength(l,font=f)<=max_w for l in lines):
            a,de=f.getmetrics(); return lines,f,int((a+de)*gap)
        s-=4*SS
    a,de=f.getmetrics(); return lines,f,int((a+de)*gap)

def base():
    img=Image.new("RGB",(W,H),BG); return img, ImageDraw.Draw(img)

def footer(d, idx, total):
    d.text((W-90*SS, 92*SS), f"{idx}/{total}", font=font(FB,26*SS), fill=MUTE, anchor="rm")
    d.text((W/2, H-120*SS), "theaeoloop.com", font=font(FB,30*SS), fill=MINT, anchor="mm")

def eyebrow_top(d, text):
    ef=font(FB,28*SS); eye="  ".join(list(text.upper()))
    d.text((W/2, 190*SS), eye, font=ef, fill=MINT, anchor="mm")

# ---------- text slides ----------
def slide_cover(spec, idx, total):
    img,d=base(); glyph(d, W//2, 250*SS, 11*SS)
    d.text((W/2, 375*SS), "  ".join(list(spec["eyebrow"].upper())), font=font(FB,30*SS), fill=MINT, anchor="mm")
    lines,hf,lh=fit(d, spec["hook"], W-2*MARGIN, FB, 100*SS, 56*SS)
    y=(H-lh*len(lines))//2+20*SS
    for l in lines: d.text((W/2,y),l,font=hf,fill=WHITE,anchor="mm"); y+=lh
    d.text((W/2, H-215*SS), "swipe →", font=font(FR,30*SS), fill=MUTE, anchor="mm")
    footer(d, idx, total); return img

def slide_point(num, text, idx, total):
    img,d=base()
    d.text((MARGIN, 300*SS), str(num), font=font(FB,120*SS), fill=MINT, anchor="lm")
    d.line([(MARGIN, 400*SS),(MARGIN+70*SS,400*SS)], fill=MINT, width=5*SS)
    lines,tf,lh=fit(d, text, W-2*MARGIN, FB, 82*SS, 46*SS)
    y=520*SS
    for l in lines: d.text((MARGIN,y),l,font=tf,fill=WHITE,anchor="lm"); y+=lh
    footer(d, idx, total); return img

def slide_cta(text, idx, total):
    img,d=base(); glyph(d, W//2, 320*SS, 11*SS)
    lines,tf,lh=fit(d, text, W-2*MARGIN, FB, 74*SS, 44*SS)
    y=(H-lh*len(lines))//2+30*SS
    for l in lines: d.text((W/2,y),l,font=tf,fill=WHITE,anchor="mm"); y+=lh
    footer(d, idx, total); return img

# ---------- visual slides ----------
def slide_chat(v, idx, total):
    img,d=base(); eyebrow_top(d, v.get("eyebrow","what AI answers"))
    # prompt bubble
    pf=font(FR,36*SS)
    d.rounded_rectangle([MARGIN,300*SS,W-MARGIN,430*SS], radius=28*SS, outline=MINT, width=3*SS)
    d.text((MARGIN+40*SS, 365*SS), v["prompt"], font=pf, fill=WHITE, anchor="lm")
    # answer card
    top=490*SS
    names=v["names"]; card_h=90*SS*len(names)+120*SS
    d.rounded_rectangle([MARGIN,top,W-MARGIN,top+card_h], radius=28*SS, fill=CARD)
    d.text((MARGIN+40*SS, top+55*SS), "AI's answer:", font=font(FB,30*SS), fill=MUTE, anchor="lm")
    y=top+130*SS
    for i,n in enumerate(names,1):
        d.text((MARGIN+40*SS, y), f"{i}.", font=font(FB,40*SS), fill=MINT, anchor="lm")
        d.text((MARGIN+110*SS, y), n, font=font(FB,40*SS), fill=WHITE, anchor="lm"); y+=90*SS
    # missing note
    note=v.get("note","— your practice isn't on the list.")
    lines,nf,lh=fit(d, note, W-2*MARGIN, FB, 46*SS, 34*SS)
    yy=top+card_h+70*SS
    for l in lines: d.text((W/2,yy),l,font=nf,fill=CORAL,anchor="mm"); yy+=lh
    footer(d, idx, total); return img

def slide_compare(v, idx, total):
    img,d=base(); eyebrow_top(d, v.get("eyebrow","the difference"))
    midx=W//2; top=320*SS; bot=H-260*SS
    d.line([(midx,top),(midx,bot)], fill=(40,54,66), width=3*SS)
    def col(cx, title, items, accent):
        d.text((cx, top+30*SS), title, font=font(FB,52*SS), fill=accent, anchor="mm")
        y=top+150*SS
        for it in items:
            for l in wrap_lines(d, it, font(FR,40*SS), (W//2)-2*MARGIN):
                d.text((cx, y), l, font=font(FR,40*SS), fill=WHITE, anchor="mm"); y+=62*SS
            y+=28*SS
    col(W//4+20*SS, v["left"]["title"], v["left"]["items"], MUTE)
    col(3*W//4-20*SS, v["right"]["title"], v["right"]["items"], MINT)
    footer(d, idx, total); return img

def slide_bars(v, idx, total):
    img,d=base(); eyebrow_top(d, v.get("eyebrow","what moves the needle"))
    d.text((MARGIN, 300*SS), v["title"], font=font(FB,54*SS), fill=WHITE, anchor="lm")
    bars=v["bars"]; y=460*SS; bar_w=W-2*MARGIN
    for b in bars:
        d.text((MARGIN, y-10*SS), b["label"], font=font(FB,38*SS), fill=WHITE, anchor="ls")
        by=y+30*SS
        d.rounded_rectangle([MARGIN,by,MARGIN+bar_w,by+46*SS], radius=14*SS, fill=CARD)
        w=int(bar_w*max(0.12,min(1.0,b["value"])))
        d.rounded_rectangle([MARGIN,by,MARGIN+w,by+46*SS], radius=14*SS, fill=MINT)
        y+=180*SS
    footer(d, idx, total); return img

def slide_flow(v, idx, total):
    img,d=base(); eyebrow_top(d, v.get("eyebrow","how it works"))
    steps=v["steps"]; n=len(steps)
    top=340*SS; gap=(H-560*SS)//n
    for i,s in enumerate(steps):
        cy=top+i*gap+gap//2
        d.rounded_rectangle([MARGIN,cy-70*SS,W-MARGIN,cy+70*SS], radius=24*SS, fill=CARD)
        d.ellipse([MARGIN+30*SS,cy-34*SS,MARGIN+98*SS,cy+34*SS], fill=MINT)
        d.text((MARGIN+64*SS, cy), str(i+1), font=font(FB,40*SS), fill=BG, anchor="mm")
        for j,l in enumerate(wrap_lines(d, s, font(FB,38*SS), W-2*MARGIN-200*SS)[:2]):
            d.text((MARGIN+140*SS, cy-24*SS+j*48*SS), l, font=font(FB,38*SS), fill=WHITE, anchor="lm")
        if i<n-1:
            ax=W//2
            d.line([(ax,cy+70*SS),(ax,cy+gap-70*SS)], fill=MINT, width=4*SS)
    footer(d, idx, total); return img

VISUAL={"chat":slide_chat,"compare":slide_compare,"bars":slide_bars,"flow":slide_flow}

def render(post):
    slides=[]
    slides.append(post)  # placeholder to count; build real list below
    seq=["cover"]
    if post.get("visual"): seq.append("visual")
    seq += ["point"]*len(post.get("points",[]))
    seq.append("cta")
    total=len(seq)
    imgs=[]; n=0; pi=0
    for kind in seq:
        n+=1
        if kind=="cover": imgs.append(slide_cover(post,n,total))
        elif kind=="visual": imgs.append(VISUAL[post["visual"]["type"]](post["visual"],n,total))
        elif kind=="point": imgs.append(slide_point(pi+1, post["points"][pi], n, total)); pi+=1
        elif kind=="cta": imgs.append(slide_cta(post.get("cta","theaeoloop.com"), n, total))
    outdir=os.path.join(OUTROOT, post["slug"]); os.makedirs(outdir, exist_ok=True)
    # clear old slides so counts stay correct
    for f in os.listdir(outdir):
        if f.startswith("slide-"): os.remove(os.path.join(outdir,f))
    for i,img in enumerate(imgs,1):
        img.resize((1080,1350), Image.LANCZOS).convert("RGB").save(os.path.join(outdir,f"slide-{i}.jpg"),"JPEG",quality=92)
    return len(imgs)

if __name__=="__main__":
    posts=json.load(open(SPEC,encoding="utf-8"))
    for post in posts:
        c=render(post); print(f"{post['slug']}: {c} slides")
    print("done")
