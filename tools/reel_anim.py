# -*- coding: utf-8 -*-
"""Animated 9:16 reel: TYPEWRITER cover (hook types out + blinking cursor) then
fades through the chart slides. Frame-based (Pillow) -> ffmpeg. Silent.

Run:  python tools/reel_anim.py <slug>
"""
import os, sys, glob, shutil, subprocess, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920
BG=(10,14,21); MINT=(26,214,160); WHITE=(238,241,238); MUTE=(120,134,128)
FB="C:/Windows/Fonts/segoeuib.ttf"; FR="C:/Windows/Fonts/segoeui.ttf"
FPS=30; TYPE_T=2.0; COVER_HOLD=1.3; SLIDE_HOLD=2.2; XF=0.4
def font(p,s): return ImageFont.truetype(p,int(s))

def glyph(d,cx,cy,scale):
    segs=[((16,16),(12,8),(5,8),(5,16)),((5,16),(5,24),(12,24),(16,16)),
          ((16,16),(20,8),(27,8),(27,16)),((27,16),(27,24),(20,24),(16,16))]
    r=2.9*scale/2
    for p0,p1,p2,p3 in segs:
        for i in range(101):
            t=i/100;u=1-t
            x=u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0]
            y=u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]
            d.ellipse([cx+(x-16)*scale-r,cy+(y-16)*scale-r,cx+(x-16)*scale+r,cy+(y-16)*scale+r],fill=MINT)

def wrap(d,text,f,maxw):
    out=[];cur=""
    for w in text.split():
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)<=maxw: cur=t
        else:
            if cur:out.append(cur)
            cur=w
    if cur:out.append(cur)
    return out

def fit(d,text,maxw,start,mins):
    s=start
    while s>=mins:
        f=font(FB,s);lines=wrap(d,text,f,maxw)
        if all(d.textlength(l,font=f)<=maxw for l in lines):
            a,de=f.getmetrics();return lines,f,int((a+de)*1.16)
        s-=4
    a,de=f.getmetrics();return lines,f,int((a+de)*1.16)

def cover_base(eyebrow):
    img=Image.new("RGB",(W,H),BG);d=ImageDraw.Draw(img)
    glyph(d,W//2,360,15)
    d.text((W/2,540),"  ".join(list(eyebrow.upper())),font=font(FB,34),fill=MINT,anchor="mm")
    d.text((W/2,H-150),"theaeoloop.com",font=font(FB,34),fill=MINT,anchor="mm")
    return img

def pad(src):
    im=Image.open(src).convert("RGB");c=Image.new("RGB",(W,H),BG)
    if im.width!=W: im=im.resize((W,int(im.height*W/im.width)),Image.LANCZOS)
    c.paste(im,(0,(H-im.height)//2));return c

def build(slug):
    posts=os.path.join(HERE,"content","posts",slug)
    slides=sorted(glob.glob(os.path.join(posts,"slide-*.jpg")))
    spec={c["slug"]:c for c in json.load(open(os.path.join(HERE,"content","carousels.json"),encoding="utf-8"))}[slug]
    base=cover_base(spec["eyebrow"])
    d0=ImageDraw.Draw(base); X=90; YTOP=760
    lines,hf,lh=fit(d0,spec["hook"],W-180,84,46)
    nchars=sum(len(l) for l in lines)
    tmp=os.path.join(HERE,"content","reels","_af",slug)
    if os.path.exists(tmp):shutil.rmtree(tmp)
    os.makedirs(tmp)
    fi=[0]
    def save(img):
        fi[0]+=1; img.save(os.path.join(tmp,f"{fi[0]:04d}.jpg"),"JPEG",quality=90)
    def draw_hook(img,k,cursor):
        d=ImageDraw.Draw(img); rem=k; y=YTOP; cpos=None
        for line in lines:
            show=line if rem>=len(line) else line[:max(0,rem)]
            d.text((X,y),show,font=hf,fill=WHITE,anchor="la")
            if rem<len(line): cpos=(X+d.textlength(show,font=hf),y); rem=-1
            else: rem-=len(line)
            y+=lh
            if rem<0: break
        if cursor:
            if cpos is None: cpos=(X+d.textlength(lines[-1],font=hf), YTOP+lh*(len(lines)-1))
            cx,cy=cpos; d.rectangle([cx+7,cy+10,cx+15,cy+int(hf.size*0.86)],fill=MINT)
    # COVER — typewriter then hold with blinking cursor
    ntype=int(TYPE_T*FPS); nhold=int(COVER_HOLD*FPS)
    for fr in range(ntype+nhold):
        k=nchars if fr>=ntype else int(fr/ntype*nchars)
        img=base.copy(); draw_hook(img,k, fr%(FPS//2)<(FPS//4)); save(img)
    full=base.copy(); draw_hook(full,nchars,False)
    # SLIDES — crossfade + hold
    prev=full
    for s in slides[1:]:
        im=pad(s)
        for fr in range(int(XF*FPS)): save(Image.blend(prev,im,fr/int(XF*FPS)))
        for fr in range(int(SLIDE_HOLD*FPS)): save(im)
        prev=im
    out=os.path.join(HERE,"content","reels",f"{slug}.mp4")
    ff=shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()
    subprocess.run([ff,"-y","-framerate",str(FPS),"-i",os.path.join(tmp,"%04d.jpg"),
                    "-c:v","libx264","-pix_fmt","yuv420p","-r",str(FPS),"-movflags","+faststart",out],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp,ignore_errors=True)
    print(f"{slug}: {fi[0]} frames -> {out}")

if __name__=="__main__":
    build(sys.argv[1])
