# -*- coding: utf-8 -*-
"""The AEO Loop — Instagram carousel generator (1080x1350 4:5 slides).
Reads carousels.json (list of posts) and renders each slide PNG into content/carousels/<slug>/.
Run:  python tools/carousel_generator.py
Post shape: { "slug","eyebrow","hook","points":[..],"cta" }  -> cover + N point slides + CTA slide."""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "content", "carousels.json")
OUTROOT = os.path.join(HERE, "content", "posts")   # publisher reads posts/<slug>/slide-N.jpg

SS = 2
W, H = 1080*SS, 1350*SS
BG   = (10, 14, 21)      # #0A0E15
MINT = (26, 214, 160)    # #1AD6A0
WHITE= (238, 241, 238)
MUTE = (120, 134, 128)
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
    mf=font(FB,26*SS)
    d.text((W-90*SS, 92*SS), f"{idx}/{total}", font=mf, fill=MUTE, anchor="rm")
    hf=font(FB,30*SS); handle="theaeoloop.com"
    d.text((W/2, H-120*SS), handle, font=hf, fill=MINT, anchor="mm")

def slide_cover(spec, idx, total):
    img,d=base()
    glyph(d, W//2, 250*SS, 11*SS)
    ef=font(FB,30*SS); eye="  ".join(list(spec["eyebrow"].upper()))
    d.text((W/2, 375*SS), eye, font=ef, fill=MINT, anchor="mm")
    lines,hf,lh=fit(d, spec["hook"], W-2*MARGIN, FB, 100*SS, 56*SS)
    y=(H-lh*len(lines))//2+20*SS
    for l in lines: d.text((W/2,y),l,font=hf,fill=WHITE,anchor="mm"); y+=lh
    d.text((W/2, H-215*SS), "swipe →", font=font(FR,30*SS), fill=MUTE, anchor="mm")
    footer(d, idx, total); return img

def slide_point(num, text, idx, total):
    img,d=base()
    nf=font(FB,120*SS)
    d.text((MARGIN, 300*SS), str(num), font=nf, fill=MINT, anchor="lm")
    d.line([(MARGIN, 400*SS),(MARGIN+70*SS,400*SS)], fill=MINT, width=5*SS)
    lines,tf,lh=fit(d, text, W-2*MARGIN, FB, 82*SS, 48*SS)
    y=520*SS
    for l in lines: d.text((MARGIN,y),l,font=tf,fill=WHITE,anchor="lm"); y+=lh
    footer(d, idx, total); return img

def slide_cta(text, idx, total):
    img,d=base()
    glyph(d, W//2, 320*SS, 11*SS)
    lines,tf,lh=fit(d, text, W-2*MARGIN, FB, 76*SS, 44*SS)
    y=(H-lh*len(lines))//2+30*SS
    for l in lines: d.text((W/2,y),l,font=tf,fill=WHITE,anchor="mm"); y+=lh
    footer(d, idx, total); return img

def render(post):
    slides=[]
    points=post.get("points",[])
    total = 2 + len(points)   # cover + points + cta
    slides.append(("cover", slide_cover(post,1,total)))
    for i,p in enumerate(points):
        slides.append((f"p{i+1}", slide_point(i+1, p, 2+i, total)))
    slides.append(("cta", slide_cta(post.get("cta","Free scan — link in bio."), total, total)))
    outdir=os.path.join(OUTROOT, post["slug"]); os.makedirs(outdir, exist_ok=True)
    paths=[]
    for n,(_,img) in enumerate(slides,1):
        p=os.path.join(outdir, f"slide-{n}.jpg")   # Instagram Graph API requires JPEG
        img.resize((1080,1350), Image.LANCZOS).convert("RGB").save(p,"JPEG",quality=92); paths.append(p)
    return paths

if __name__=="__main__":
    posts=json.load(open(SPEC,encoding="utf-8"))
    for post in posts:
        ps=render(post); print(f"{post['slug']}: {len(ps)} slides")
    print("done")
