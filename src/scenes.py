"""Escenas del Short. Cada escena es f(canvas, T) con T = tiempo global (s) del audio.
Los tiempos clave provienen de la transcripción palabra a palabra (transcript_raw.json)."""
import math
import random

import skia

from lib import *

# ------------------------------------------------------------------ helpers
PAL = {
    "day": dict(sky=("#8fcdf0", "#e6f5ff"), far="#a9c2de", mid="#7f9fc4", tree="#2e5e52",
                gr=("#f4f9ff", "#cfe1f3")),
    "storm": dict(sky=("#7189a8", "#c3d1e0"), far="#9fb1c7", mid="#6f86a6", tree="#2a4d47",
                  gr=("#eef4fb", "#bfd0e3")),
    "dusk": dict(sky=("#262a58", "#b5687a"), far="#4f5384", mid="#363a66", tree="#17283a",
                 gr=("#b4bedf", "#7682ad")),
    "night": dict(sky=("#0b0f2c", "#2a3566"), far="#28305c", mid="#1d2349", tree="#0f1a2a",
                  gr=("#8a99c6", "#4a5888")),
}


def camera(c, cx, cy, z=1.0, rot=0.0, shake=0.0, T=0.0):
    c.translate(W / 2 + noise(T * 30, 1) * shake, H / 2 + noise(T * 30, 2) * shake)
    c.rotate(rot)
    c.scale(z, z)
    c.translate(-cx, -cy)


def landscape(c, T, cam, pal="day", ground_y=1400, seed=1, trees=True, tree_xs=None, far_y=None,
              sway=0.0, sun=None, mid=True):
    """cielo en pantalla + capas con parallax. cam=(cx,cy,z,rot,shake)"""
    p = PAL[pal]
    sky(c, *p["sky"])
    if sun:
        glow(c, sun[0], sun[1], sun[2] * 3, "#fff6c8", 0.5)
        circle(c, sun[0], sun[1], sun[2], "#fff3b0", 0)
    cx, cy, z, rot, shk = cam
    fy = far_y if far_y is not None else ground_y - 260
    # capa lejana
    c.save()
    camera(c, cx * 0.35 + 540 * 0.65, cy * 0.5 + 960 * 0.5, 1 + (z - 1) * 0.3, rot, shk * 0.3, T)
    mountains(c, seed, fy + 60, 640, p["far"], peaks=6, ow=6)
    c.restore()
    if mid:
        c.save()
        camera(c, cx * 0.65 + 540 * 0.35, cy * 0.75 + 960 * 0.25, 1 + (z - 1) * 0.6, rot, shk * 0.6, T)
        mountains(c, seed + 7, fy + 170, 420, p["mid"], peaks=9, ow=6)
        c.restore()
    c.save()
    camera(c, cx, cy, z, rot, shk, T)
    if trees:
        xs = tree_xs if tree_xs is not None else [-300, -60, 120, 760, 980, 1250, 1500]
        rnd = random.Random(seed)
        for x in xs:
            h = rnd.uniform(300, 430)
            pine(c, x, ground_y + 10, h, p["tree"], sway=sway * math.sin(T * 2 + x))
    ground(c, ground_y, *p["gr"], seed=seed)
    return c  # canvas queda con la cámara aplicada; el llamador debe c.restore()


def auto_blink(T, seed=0.0):
    ph = (T + seed) % 3.3
    return 1 - abs(ph - 0.07) / 0.07 if ph < 0.14 else 0.0


def hip_y(ground_y, s, style="hero"):
    st = STYLES[style]
    return ground_y - (st["thigh"] + st["shin"] + 16) * s


def red_flash(c, a, color="#ff2030"):
    if a > 0:
        vignette(c, color, a, H * 0.7)


def white_flash(c, a):
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), P("#ffffff", alpha=a))


def arrow(c, x, y, ang, ln, col="#ffe14a"):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    pth = path([(-18, -ln), (18, -ln), (18, -40), (44, -40), (0, 0), (-44, -40), (-18, -40)])
    shape(c, pth, col, 8)
    c.restore()


# ================================================================== 1. despertar
def s01_wake(c, T):
    hipx, hipy = 620, 1300
    lean = -90 + 90 * ease_out_back(pr(T, 1.55, 2.3), 1.2)
    cx = lerp(380, 560, smooth(pr(T, 0.9, 2.1)))
    cy = lerp(1270, 1080, smooth(pr(T, 0.9, 2.1)))
    z = lerp(2.4, 1.0, smooth(pr(T, 0.9, 2.1))) + 0.04 * T
    cam = (cx, cy, z, 0, 0)
    landscape(c, T, cam, "day", ground_y=1345, tree_xs=[-200, 80, 950, 1180])
    # nieve acumulada junto al cuerpo
    ellipse(c, hipx - 300, 1350, 120, 30, "#ffffff", 0)
    eyes_closed = T < 0.26
    blink = 1 - pr(T, 0.26, 0.42) if T < 0.42 else auto_blink(T, 1.2)
    look = (0, 0)
    if 0.5 < T < 0.85:
        look = (-1, -0.3)
    elif 0.85 <= T < 1.2:
        look = (1, -0.3)
    elif T >= 1.2:
        look = (0.2, -0.6)
    mouth = "o" if T > 1.85 else "neutral"
    person(c, hipx, hipy, 1.0, lean=lean, legA=(88, 92), legB=(92, 96), armA=(-10, -4), armB=(10, 4),
           look=look, blink=blink, eyes_closed=eyes_closed, mouth=mouth, mouth_open=pr(T, 1.85, 2.1),
           brows=pr(T, 1.8, 2.0), T=T, cold=0.25)
    # copos sobre el cuerpo que caen al sentarse
    for i, (dx, dy) in enumerate([(-120, -60), (-40, -70), (60, -60)]):
        fall = ease_in(pr(T, 1.6, 2.1)) * 90
        circle(c, hipx + dx, hipy + dy + fall, 14, "#ffffff", 4, alpha=1 - pr(T, 1.9, 2.2))
    c.restore()
    snowfall(c, T, n=70, wind=0.25, speed=110, size=(3, 8))
    # contador de años
    if T > 0.85:
        n = int(20000 * ease_out(pr(T, 1.0, 1.85)))
        s = pop(T, 0.85)
        text(c, "HACE", W / 2, 260, 80, "#ffffff", scale=s, rot=-3)
        text(c, "{:,}".format(n).replace(",", ".") + " AÑOS", W / 2, 380, 130, "#ffe14a", scale=s, rot=-3)
    if T < 0.3:
        c.drawRect(skia.Rect.MakeWH(W, H), P("#000000", alpha=1 - pr(T, 0.0, 0.3)))
    # párpados (POV)


# ================================================================== 2. ropa
def s02_clothes(c, T):
    z = 1.0 + 0.02 * (T - 2.55)
    cx, cy = 540, 1060
    zp = ease_out(pr(T, 3.5, 3.95))
    z = lerp(z, 1.75, zp)
    cy = lerp(cy, 1130, zp)
    shk = 20 * (1 - pr(T, 5.0, 5.6)) if T > 5.0 else 0
    cam = (cx, cy, z, 0, shk)
    landscape(c, T, cam, "day", ground_y=1530, tree_xs=[-150, 90, 1000, 1220], seed=2)
    hy = hip_y(1530, 1.25)
    tug = math.sin(T * 9) * 6 if 3.0 < T < 4.9 else 0
    scared = T > 4.95
    person(c, 540, hy, 1.25, armA=(-10 + tug * 0.3, 60), armB=(10 - tug * 0.3, -60),
           look=(0, 1) if not scared else (0, 0), head_tilt=0, mouth="scream" if scared else "worried",
           mouth_open=0.8, brows=1 if T > 3.5 else 0.3, blink=auto_blink(T), T=T, cold=0.3,
           sweat=1 if scared else 0)
    # flecha a la ropa
    if 3.52 < T < 4.95:
        a = pop(T, 3.52)
        c.save()
        c.translate(780, hy - 120)
        c.scale(a, a)
        arrow(c, 0, 0, 60 + math.sin(T * 10) * 4, 150)
        c.restore()
    if scared:
        s = pop(T, 5.0, 0.35)
        c.save()
        c.translate(540, hy - 95)
        c.scale(s, s)
        glow(c, 0, 0, 160, "#ff2a3d", 0.5)
        skull(c, 0, 0, 55)
        c.restore()
    c.restore()
    snowfall(c, T, n=60, wind=0.3, speed=120)
    if T > 3.52:
        callout(c, T, 3.52, "TU ROPA", W / 2, 330, 120, "#ffe14a", t1=4.9)
    if scared:
        red_flash(c, 0.55 + 0.2 * math.sin(T * 18))
        callout(c, T, 5.0, "¡PELIGRO!", W / 2, 330, 140, "#ff3b4a")


# ================================================================== 3-4. tela
_fabric = {}


def fabric_image():
    if "img" not in _fabric:
        s = skia.Surface(1400, 2400)
        cc = s.getCanvas()
        cc.clear(hexc("#ece6d8"))
        st = 26
        pa = P("#e0d8c6")
        pl = P("#cfc6b1", 2)
        for j in range(0, 2400 // st + 1):
            for i in range(0, 1400 // st + 1):
                x, y = i * st, j * st
                if (i + j) % 2:
                    cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 2, y + 6, st - 4, st - 12), 6, 6), pa)
                else:
                    cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 6, y + 2, st - 12, st - 4), 6, 6), pa)
        for j in range(0, 2400, st):
            cc.drawLine(0, j, 1400, j, pl)
        _fabric["img"] = s.makeImageSnapshot()
    return _fabric["img"]


DROPS = [(640, 560, 6.6, 120), (300, 820, 6.78, 140), (760, 1060, 6.95, 130), (420, 1260, 7.1, 150),
         (720, 1500, 7.3, 120), (260, 1580, 7.45, 110), (880, 780, 7.6, 100)]


def _fabric_scene(c, T, freeze):
    c.drawImage(fabric_image(), -160, -240)
    for i, (x, y, tl, r) in enumerate(DROPS):
        if T < tl - 0.35:
            continue
        if T < tl:
            k = pr(T, tl - 0.35, tl)
            drop(c, x, lerp(y - 700, y, ease_in(k)), 34, "#8fd3ff", 6)
            continue
        g = ease_out(pr(T, tl, tl + 0.7))
        rr = r * g
        col = mixh("#c4b99f", "#cfeaff", freeze)
        c.drawCircle(x, y, rr * 1.05, blur_paint(14, col, 0.95))
        c.drawCircle(x, y, rr * 0.7, blur_paint(10, mixh("#b8ad92", "#e8f7ff", freeze), 0.7))
        if T < tl + 0.15:
            puff(c, x, y, 60, pr(T, tl, tl + 0.3), "#8fd3ff")
        if freeze > 0:
            rnd = random.Random(i)
            for k in range(5):
                fx, fy = x + rnd.uniform(-rr * 0.6, rr * 0.6), y + rnd.uniform(-rr * 0.6, rr * 0.6)
                snowflake(c, fx, fy, rnd.uniform(18, 34) * freeze, "#ffffff", 5, rot=rnd.uniform(0, 60))
            # grietas de hielo
            for k in range(6):
                a = k / 6 * math.tau + i
                c.drawLine(x, y, x + math.cos(a) * rr * freeze, y + math.sin(a) * rr * freeze, P("#ffffff", 3, alpha=0.8))


def s03_cotton(c, T):
    z = 1.0 + 0.06 * (T - 5.9)
    c.save()
    camera(c, 540, 960, z, 2, 0, T)
    _fabric_scene(c, T, 0)
    # etiqueta
    if T > 6.25:
        s = pop(T, 6.25, 0.35)
        c.save()
        c.translate(330, 330)
        c.rotate(-8 + math.sin(T * 3) * 2)
        c.scale(s, s)
        rrect(c, -230, -120, 460, 240, 18, "#ffffff", 8)
        rrect(c, -205, -95, 410, 190, 10, None, 4, "#c9c3b3")
        text(c, "100%", 0, -40, 90, "#3d5f96", shadow=False, sw=0)
        text(c, "ALGODÓN", 0, 50, 80, "#1c1a2e", shadow=False, sw=0)
        c.restore()
    c.restore()
    callout(c, T, 6.74, "¡ABSORBE!", W / 2 + 120, 1200 - 600, 110, "#8fd3ff", rot=4)


def s04_freeze(c, T):
    zf = ease_out_back(pr(T, 9.08, 9.4))
    z = 1.14 + 0.15 * zf + 0.03 * (T - 8.2)
    shk = 14 * (1 - pr(T, 9.08, 9.6)) if T > 9.08 else 0
    c.save()
    camera(c, 540, 960, z, 2 - 3 * zf, shk, T)
    _fabric_scene(c, T + 2.0, smooth(pr(T, 9.08, 9.7)))
    c.restore()
    if T > 9.08:
        a = pr(T, 9.08, 9.5)
        c.drawRect(skia.Rect.MakeWH(W, H), P("#bfe6ff", alpha=0.25 * a))
        vignette(c, "#7fc4ff", 0.5 * a)
    callout(c, T, 9.08, "¡SE CONGELA!", W / 2, 330, 120, "#bfe6ff")
    if T > 9.64:
        callout(c, T, 9.64, "CONTRA TU PIEL", W / 2, 470, 80, "#ffffff", rot=3)


# ================================================================== 5. frío
def s05_cold(c, T):
    z = lerp(1.0, 1.15, smooth(pr(T, 10.0, 13.2)))
    cx, cy = lerp(540, 470, pr(T, 10, 13.2)), lerp(1000, 1060, pr(T, 10, 13.2))
    zz = ease_in(pr(T, 13.25, 13.55))
    z = lerp(z, 2.0, zz)
    cy = lerp(cy, 1180, zz)
    cx = lerp(cx, 430, zz)
    cam = (cx, cy, z, 0, 3)
    landscape(c, T, cam, "storm", ground_y=1480, seed=4, tree_xs=[-120, 80, 1010, 1250], sway=1.5)
    hy = hip_y(1480, 1.15)
    cold = lerp(0.4, 0.95, pr(T, 10.0, 11.5))
    person(c, 430, hy, 1.15, armA=(-20, 100), armB=(20, -100), shiver=1, cold=cold, frost=0.9,
           mouth="grit", brows=1, blink=auto_blink(T, 0.5), T=T, look=(0.3, 0))
    # vaho
    for k in range(3):
        ph = ((T * 0.9 + k / 3) % 1)
        circle(c, 470 + ph * 90, hy - 290 - ph * 40, 14 + ph * 30, "#ffffff", 0, alpha=0.5 * (1 - ph))
    v = lerp(0, -40, ease_out(pr(T, 10.05, 11.0)))
    thermometer(c, 860, 980, 0.8, v, T=T)
    c.restore()
    snowfall(c, T, n=110, wind=1.4, speed=260, size=(3, 9))
    wind_lines(c, T, n=9)
    callout(c, T, 11.4, "EL FRÍO...", W / 2, 300, 120, "#bfe6ff")
    callout(c, T, 11.9, "NO ES TU PEOR ENEMIGO", W / 2, 430, 74, "#ffffff", rot=2)


# ================================================================== 6. hambre
def s06_hunger(c, T):
    shk = 16 * (1 - pr(T, 14.1, 14.6)) if T > 14.1 else 2
    z = lerp(1.0, 1.12, smooth(pr(T, 13.55, 14.85)))
    cam = (540, 1220, z, 0, shk)
    landscape(c, T, cam, "storm", ground_y=1900, seed=5, tree_xs=[60, 1020], sway=1)
    hy = 1560
    person(c, 540, hy, 1.55, armA=(-5, 75), armB=(5, -75), mouth="worried", brows=1, look=(0, 0.8),
           T=T, cold=0.5, frost=0.4, shiver=0.3, blink=auto_blink(T))
    bx, by = 540, hy - 70
    for k in range(3):
        ph = ((T * 2.2 + k / 3) % 1)
        r = 150 + ph * 160
        a = (1 - ph) * 0.9
        pth = skia.Path()
        pth.addArc(skia.Rect.MakeLTRB(bx - r, by - r * 0.7, bx + r, by + r * 0.7), -30, 60)
        c.drawPath(pth, P("#ffffff", 10, alpha=a))
        pth = skia.Path()
        pth.addArc(skia.Rect.MakeLTRB(bx - r, by - r * 0.7, bx + r, by + r * 0.7), 150, 60)
        c.drawPath(pth, P("#ffffff", 10, alpha=a))
    c.restore()
    snowfall(c, T, n=60, wind=1.0, speed=200)
    for t0, x, y in ((13.75, 210, 1180), (14.25, 860, 1100)):
        if T > t0:
            text(c, "GRRR", x + noise(T * 40, x) * 6, y + noise(T * 40, y) * 6, 80, "#ffd166", scale=pop(T, t0),
                 rot=-10 if x < 500 else 10)
    if T > 14.1:
        red_flash(c, 0.45)
    callout(c, T, 14.05, "EL HAMBRE", W / 2, 330, 160, "#ff4d4d")


# ================================================================== 7. energía
def s07_energy(c, T):
    rect = skia.Rect.MakeWH(W, H)
    vgrad(c, rect, "#1b3d66", "#0c1b33")
    gp = P("#2a527f", 2)
    for i in range(0, W, 90):
        c.drawLine(i, 0, i, H, gp)
    for j in range(0, H, 90):
        c.drawLine(0, j, W, j, gp)
    k = smooth(pr(T, 15.2, 15.9))
    cx, cy, z = lerp(420, 560, k), lerp(1200, 1080, k), lerp(1.7, 1.0, k)
    c.save()
    camera(c, cx, cy, z, 0, 3 if T > 17.6 else 0, T)
    hx, hy = 400, 1330
    person(c, hx, hy, 1.15, armA=(-25, 30), armB=(25, -30), T=T, cold=lerp(0.2, 0.7, pr(T, 16, 18.5)),
           frost=pr(T, 17.6, 18.4) * 0.6, shiver=pr(T, 17.3, 17.8), mouth="worried" if T > 16.3 else "neutral",
           brows=pr(T, 16.0, 16.4), blink=auto_blink(T, 2), look=(0.6, 0))
    # ventana al pecho con el "horno"
    wx, wy, wr = hx, hy - 105, 78
    clip = skia.Path()
    clip.addCircle(wx, wy, wr)
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    c.drawCircle(wx, wy, wr, P("#2a0f0f"))
    inten = 0.55 + 0.6 * ease_out(pr(T, 15.46, 16.0))
    fire(c, wx, wy + 55, 0.28 + 0.06 * inten, T, logs=False, intensity=inten)
    c.restore()
    circle(c, wx, wy, wr, None, 10)
    glow(c, wx, wy, 200 * inten, "#ff8a3d", 0.25)
    if T > 15.96:
        text(c, "x2", wx + 150, wy - 120, 150, "#ff9a2e", scale=pop(T, 15.96), rot=-10)
    lvl = 1.0 - 0.88 * smooth(pr(T, 16.3, 18.6))
    battery(c, 850, 1040, 0.85, lvl, T)
    if T > 16.48:
        text(c, "ENERGÍA", 850, 790, 70, "#ffe14a", scale=pop(T, 16.48))
    text(c, "%d%%" % round(lvl * 100), 850, 1300, 70, "#ffffff")
    c.restore()
    if T > 17.62:
        snowfall(c, T, n=50, wind=0.8, speed=180, alpha=pr(T, 17.6, 18.0))
    callout(c, T, 15.4, "QUEMAS EL DOBLE", W / 2, 300, 100, "#ff9a2e", t1=18.6)


# ================================================================== 8. grasa
def s08_fat(c, T):
    z = lerp(1.0, 1.08, pr(T, 18.9, 20.75))
    cam = (540, 960, z, 0, 0)
    landscape(c, T, cam, "day", ground_y=1980, seed=6, tree_xs=[880, 1080])
    hy = 1760
    happy = T > 19.82
    person(c, 330, hy, 1.7, armA=(-15, -5), armB=(15, 5), look=(0.8, -0.8), mouth="smile" if happy else "o",
           mouth_open=0.4, brows=-0.2 if happy else 0.5, blink=auto_blink(T, 1), T=T, cold=0.3, head_tilt=6)
    if happy:
        dk = ((T - 19.9) * 1.4) % 1
        drop(c, 360 + 30, hy - 1.7 * 168 - 1.7 * 69 + 70 + dk * 70, 10, "#bfe8ff", 4)
    c.restore()
    bp = ease_out_back(pr(T, 19.0, 19.35))
    bubble(c, 700, 620, 330, 270, bp, tail=(470, 1150))
    if bp > 0.2:
        bobv = math.sin(T * 4) * 12
        meat(c, 690, 600 + bobv, 1.25 * bp, rot=-10 + math.sin(T * 3) * 6)
        for k in range(4):
            a = T * 2 + k * math.pi / 2
            snowflake(c, 700 + math.cos(a) * 250, 600 + math.sin(a) * 180, 14, "#ffe14a", 4, rot=T * 90)
    if T > 19.82:
        text(c, "GRASA", 700, 820, 120, "#ffe14a", scale=pop(T, 19.82), rot=-4 + math.sin(T * 5) * 2)
    snowfall(c, T, n=40, wind=0.2, speed=100)


# ================================================================== 9. mamut
def s09_mammoth(c, T):
    mx = lerp(1450, 830, smooth(pr(T, 20.75, 22.9)) * 0.3 + pr(T, 20.75, 22.9) * 0.7)
    phase = (1450 - mx) / 45
    walking = T < 22.9
    thud = (abs(math.cos(phase)) ** 14) * 9 if walking else 0
    drop_t = 24.15
    land = pr(T, drop_t, drop_t + 0.4)
    shk = thud + (24 * (1 - land) if T > drop_t else 0)
    cx = lerp(470, 660, smooth(pr(T, 20.9, 22.2)))
    z = lerp(0.95, 1.0, smooth(pr(T, 23.9, 24.6)))
    cam = (cx, 1080, z, 0, shk)
    gy = 1430
    landscape(c, T, cam, "day", ground_y=gy, seed=8, tree_xs=[-260, -40, 1300, 1550])
    hs = 0.5
    surprised = T > 21.1
    person(c, 150, hip_y(gy, hs), hs, look=(1, -0.6) if surprised else (1, 0), mouth="o" if surprised else "neutral",
           mouth_open=0.7, brows=1 if T > 23.98 else 0.3, blink=auto_blink(T), T=T, cold=0.3,
           armA=(-25, -15) if surprised else (-14, -6), armB=(25, 15) if surprised else (14, 6), shiver=0.2)
    if 21.1 < T < 22.2:
        text(c, "!", 150, hip_y(gy, hs) - 330, 120, "#ffe14a", scale=pop(T, 21.1))
    squash = 1 - 0.07 * math.sin(land * math.pi) if T > drop_t else 1
    c.save()
    c.translate(mx, gy)
    c.scale(1, squash)
    c.translate(-mx, -gy)
    mammoth(c, mx, gy, 1.0, phase, facing=-1, T=T, sway=0.4 if not walking else 0)
    c.restore()
    # 4 patas
    if T > 22.1:
        for k, (lx, t0) in enumerate(((mx - 170, 22.16), (mx - 135, 22.28), (mx + 110, 22.40), (mx + 150, 22.52))):
            if T < 23.6:
                text(c, str(k + 1), lx, gy - 300 + 330 * 0.0 + 180, 70, "#ffe14a", scale=pop(T, t0) * (1 - pr(T, 23.3, 23.6)))
    # pesa
    if T > 23.9:
        fy = lerp(-200, gy - 560 * squash, ease_in(pr(T, 23.9, drop_t))) if T < drop_t else gy - 560 * squash
        kettle_weight(c, mx + 40, fy, 0.75)
        if T > drop_t:
            puff(c, mx + 40, gy - 520, 120, pr(T, drop_t, drop_t + 0.5))
    c.restore()
    snowfall(c, T, n=50, wind=0.3, speed=120)
    callout(c, T, 22.16, "4 PATAS", W / 2, 330, 110, "#ffffff", t1=23.85)
    callout(c, T, 24.15, "6 TONELADAS", W / 2, 330, 130, "#ffe14a")


# ================================================================== 10. sin lanza / fuego / tribu
CARDS = [(200, 25.15, 25.95, "LANZA"), (540, 26.70, 26.95, "FUEGO"), (880, 27.56, 27.80, "TRIBU")]


def s10_without(c, T):
    shk = 0
    for _, _, tx, _ in CARDS:
        if tx < T < tx + 0.25:
            shk = 10 * (1 - pr(T, tx, tx + 0.25))
    cam = (540, 1000, 1.0 + 0.02 * (T - 25), 0, shk)
    landscape(c, T, cam, "storm", ground_y=1560, seed=9, tree_xs=[-100, 1150], sway=1)
    hy = hip_y(1560, 1.15)
    person(c, 540, hy + 200, 1.15, look=(0, -1), mouth="worried", brows=1, blink=auto_blink(T), T=T, cold=0.6,
           frost=0.5, shiver=0.6, armA=(-25, 30), armB=(25, -30))
    c.restore()
    snowfall(c, T, n=70, wind=1.0, speed=200)
    for x, t0, tx, label in CARDS:
        if T < t0:
            continue
        s = pop(T, t0, 0.35)
        c.save()
        c.translate(x, 720)
        c.rotate((-4 if x < 540 else 4 if x > 540 else 0) + math.sin(T * 3 + x) * 1.5)
        c.scale(s, s)
        rrect(c, -150, -190, 300, 380, 34, "#ffffff", 9)
        if label == "LANZA":
            spear(c, -95, 90, 200, 135)
        elif label == "FUEGO":
            fire(c, 0, 70, 0.42, T)
        else:
            tribe_icon(c, 0, 80, 0.85, T)
        text(c, label, 0, 140, 58, "#1c1a2e", shadow=False, sw=0)
        if T > tx:
            red_x(c, 0, -20, 110, pr(T, tx, tx + 0.18), 34)
        c.restore()
    callout(c, T, 25.04, "SIN...", W / 2, 330, 120, "#ffffff")


def s10b_nothing(c, T):
    gy = 1420
    mxp = pr(T, 28.3, 30.0)
    mx = lerp(700, 1050, mxp)
    cam = (lerp(560, 700, mxp), 1090, 0.95, 0, 0)
    landscape(c, T, cam, "day", ground_y=gy, seed=10, tree_xs=[-200, 1600])
    hs = 0.62
    hy = hip_y(gy, hs)
    throw = pr(T, 28.38, 28.75)
    shrug = smooth(pr(T, 29.25, 29.5))
    if T < 28.75:
        armB = (lerp(20, 160, smooth(throw * 2)), lerp(30, 175, smooth(throw * 2)))
        if throw > 0.5:
            k = (throw - 0.5) * 2
            armB = (lerp(160, 70, k), lerp(175, 60, k))
    else:
        armB = (lerp(70, 60, shrug), lerp(60, 160, shrug))
    armA = (lerp(-14, -60, shrug), lerp(-6, -160, shrug))
    person(c, 300, hy, hs, armA=armA, armB=armB, look=(1, 0), mouth="sad" if T > 29.25 else "grit",
           brows=1 if T > 29.2 else -0.6, T=T, cold=0.5, blink=auto_blink(T), lean=lerp(0, 8, throw))
    mammoth(c, mx, gy, 0.75, (mx - 700) / 45, facing=1, T=T)
    # bola de nieve
    hit_x, hit_y = mx - 0.75 * 270, gy - 0.75 * 330
    if 28.7 < T < 29.05:
        k = pr(T, 28.7, 29.05)
        sx, sy = 300 + 70, hy - 230
        bx = lerp(sx, hit_x, k)
        by = lerp(sy, hit_y, k) - math.sin(k * math.pi) * 220
        circle(c, bx, by, 18, "#ffffff", 5)
    if 29.05 < T < 29.6:
        puff(c, hit_x, hit_y, 70, pr(T, 29.05, 29.5))
        text(c, "¡PAF!", hit_x, hit_y - 120, 70, "#ffffff", scale=pop(T, 29.05) * (1 - pr(T, 29.4, 29.6)))
    c.restore()
    snowfall(c, T, n=45, wind=0.3, speed=120)
    callout(c, T, 29.3, "NADA", W / 2, 330, 170, "#ff4d4d")


# ================================================================== 11. río
def _river(c, T, cam_override=None):
    hxp = pr(T, 30.0, 30.95)
    hx = lerp(120, 470, hxp)
    zp = smooth(pr(T, 31.55, 31.95))
    cam = cam_override or (lerp(420, 520, hxp) + zp * -60, lerp(1150, 1080, zp), lerp(1.05, 1.5, zp), 0, 0)
    gy = 1330
    landscape(c, T, cam, "day", ground_y=gy, seed=12, tree_xs=[-250, 60, 900, 1150])
    # río
    ry0, ry1 = 1400, 1700
    rp = curve([(-1500, ry0), (0, ry0 + 20), (800, ry0 - 10), (2500, ry0 + 10)], close=False)
    rp.lineTo(2500, ry1)
    rp.lineTo(-1500, ry1)
    rp.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(0, ry0), skia.Point(0, ry1)], [hexc("#6cc3f0"), hexc("#2f7fc0")])
    c.drawPath(rp, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawPath(curve([(-1500, ry0), (0, ry0 + 20), (800, ry0 - 10), (2500, ry0 + 10)], close=False), P(OUT, OW))
    rnd = random.Random(4)
    for i in range(16):
        ly = rnd.uniform(ry0 + 40, ry1 - 30)
        lx = (rnd.uniform(-600, 1800) + T * 260 * rnd.uniform(0.8, 1.3)) % 2400 - 600
        c.drawLine(lx, ly, lx + rnd.uniform(60, 140), ly, P("#ffffff", 6, alpha=0.7))
    for i in range(5):
        ix = (rnd.uniform(-400, 1600) + T * 200) % 2200 - 400
        iy = rnd.uniform(ry0 + 60, ry1 - 60)
        shape(c, path([(ix - 50, iy), (ix - 20, iy - 26), (ix + 46, iy - 18), (ix + 56, iy + 10), (ix - 10, iy + 18)]),
              "#eaf6ff", 5)
    ground(c, ry1 + 60, "#f4f9ff", "#cfe1f3", seed=3)
    # personaje
    hs = 0.85
    kneel = smooth(pr(T, 30.95, 31.3))
    hy = lerp(hip_y(ry0 - 10, hs), ry0 - 10 - 110 * hs, kneel)
    if T < 30.95:
        ph = T * 10
        wp = walk(ph)
        person(c, hx, hy + bob(ph), hs, look=(1, 0), T=T, cold=0.4, blink=auto_blink(T), **wp)
    else:
        dip = smooth(pr(T, 31.15, 31.4))
        lift = smooth(pr(T, 31.45, 31.7))
        aA = (lerp(-14, -10, dip), lerp(-6, 10, dip))
        aA = (lerp(aA[0], -20, lift), lerp(aA[1], 147, lift))
        aB = (lerp(14, 10, dip), lerp(6, -10, dip))
        aB = (lerp(aB[0], 20, lift), lerp(aB[1], -147, lift))
        drinking = T > 31.6
        person(c, hx, hy, hs, legA=(lerp(-5, -80, kneel), lerp(-3, -5, kneel)),
               legB=(lerp(5, 80, kneel), lerp(3, 5, kneel)), armA=aA, armB=aB, look=(0, 1),
               eyes_closed=drinking, mouth="o" if drinking else "smile", mouth_open=0.3, T=T, cold=0.4,
               blink=auto_blink(T), lean=lerp(0, 6, kneel))
        if drinking:
            for k in range(3):
                ph = ((T * 2 + k / 3) % 1)
                drop(c, hx + (k - 1) * 18, hy - 230 * hs + ph * 160, 7, "#8fd3ff", 3)
    return hx


def s11_river(c, T):
    _river(c, T)
    c.restore()
    snowfall(c, T, n=40, wind=0.2, speed=100)
    if T > 30.98:
        callout(c, T, 30.98, "UN RÍO", W / 2, 330, 110, "#8fd3ff", t1=32.3)


def s12_error(c, T):
    rnd = random.Random(int(T * 30))
    bands = [0, 520, 700, 1180, 1300, H]
    shk = 16 * (1 - pr(T, 32.5, 33.0))
    for i in range(len(bands) - 1):
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0, bands[i], W, bands[i + 1]))
        c.translate(rnd.uniform(-40, 40) * (1 - pr(T, 32.5, 33.1)) + noise(T * 30, 3) * shk, 0)
        _river(c, 31.95)
        c.restore()
        c.restore()
    # tinte rojo y scanlines
    c.drawRect(skia.Rect.MakeWH(W, H), P("#ff1030", alpha=0.32))
    gray = skia.Paint(Color=hexc("#000000", 40))
    for j in range(0, H, 8):
        c.drawRect(skia.Rect.MakeXYWH(0, j, W, 3), gray)
    vignette(c, "#4a0010", 0.8)
    s = pop(T, 32.52, 0.25)
    c.save()
    c.translate(W / 2 + noise(T * 40, 9) * 10, 760)
    c.scale(s, s)
    circle(c, 0, 0, 150, "#ff2a3d", 12)
    red_x(c, 0, 0, 70, 1, 0)
    c.drawLine(-60, -60, 60, 60, P("#ffffff", 34))
    c.drawLine(60, -60, -60, 60, P("#ffffff", 34))
    c.restore()
    text(c, "ERROR", W / 2 + rnd.uniform(-6, 6), 1050, 230, "#ff2a3d", stroke="#ffffff", sw=36, scale=s)
    text(c, "ERROR", W / 2, 1050, 230, "#ff2a3d", scale=s, shadow=False)


# ================================================================== 13. calor robado
def s13_inside(c, T):
    rect = skia.Rect.MakeWH(W, H)
    vgrad(c, rect, "#0d2140", "#06101f")
    gp = P("#15345a", 2)
    for i in range(0, W, 80):
        c.drawLine(i, 0, i, H, gp)
    for j in range(0, H, 80):
        c.drawLine(0, j, W, j, gp)
    z = lerp(1.0, 1.12, pr(T, 33.3, 36.4))
    c.save()
    camera(c, 540, 1240, z, 0, 0, T)
    hx, hy, s = 470, 1420, 1.5
    cold_k = smooth(pr(T, 34.3, 35.9))
    # brillo interior cálido -> frío
    glow(c, hx, hy - 120 * s, 420, mixh("#ff8a3d", "#3aa0ff", cold_k), 0.55)
    flash = 0.5 + 0.5 * math.sin(T * 14) if T > 35.5 else 0
    person(c, hx, hy, s, style="xray", T=T, armA=(-14, -6), armB=(14, 6))
    # garganta y estómago
    mouth_y = hy - s * (168 + 69) + s * 40
    stom_y = hy - 60 * s
    fl = ease_out(pr(T, 33.72, 34.3))
    line(c, [(hx, mouth_y), (hx, lerp(mouth_y, stom_y - 40, fl))], 26, "#58c2ff", 5, "#bff1ff")
    if T > 34.2:
        sp = ease_out_back(pr(T, 34.2, 34.6))
        ellipse(c, hx + 20, stom_y, 85 * sp, 60 * sp, "#58c2ff", 6, "#bff1ff")
        for k in range(3):
            wy = stom_y + math.sin(T * 6 + k) * 8
            c.drawLine(hx - 40 + k * 30, wy - 10, hx - 20 + k * 30, wy - 10, P("#ffffff", 5, alpha=0.7))
    # frío que se expande
    if cold_k > 0:
        glow(c, hx + 20, stom_y, 120 + 420 * cold_k, "#7fd0ff", 0.55 * cold_k)
    # partículas de calor que escapan
    if T > 34.6:
        rnd = random.Random(5)
        for i in range(26):
            st = 34.6 + rnd.uniform(0, 1.4)
            if T < st:
                continue
            k = ((T - st) * rnd.uniform(0.6, 1.0)) % 1.2
            a = rnd.uniform(0, math.tau)
            d = 60 + k * 520
            px, py = hx + math.cos(a) * d, hy - 140 * s + math.sin(a) * d * 1.3
            circle(c, px, py, 16 * (1 - k / 1.2), "#ffb347", 0, alpha=1 - k / 1.2)
            glow(c, px, py, 40, "#ff8a3d", 0.4 * (1 - k / 1.2))
    if flash:
        glow(c, hx, hy - 150 * s, 500, "#bff1ff", 0.25 * flash)
    v = lerp(37, 35, smooth(pr(T, 34.6, 36.0)))
    c.restore()
    c.save()
    thermometer(c, 900, 1000, 0.62, v, vmin=30, vmax=40, label=False, T=T)
    text(c, "%.1f°C" % v, 900, 1110, 70, "#ffd1a1" if v > 36 else "#bfe6ff")
    if T > 35.6:
        text(c, "HIPOTERMIA", 900, 1200, 46, "#ff6b6b", scale=pop(T, 35.6))
    c.restore()
    callout(c, T, 34.6, "TE ROBA CALOR", W / 2, 330, 120, "#ffb347")
    callout(c, T, 35.5, "DESDE ADENTRO", W / 2, 460, 80, "#bfe6ff", rot=2)


# ================================================================== 14. bosque oscuro
EYES = [(150, 1120, 38.5), (900, 1150, 38.75), (680, 1010, 39.0), (330, 1030, 39.25), (1000, 980, 39.45),
        (60, 960, 39.6)]


def s14_forest(c, T):
    hxp = pr(T, 36.45, 40.05)
    hx = lerp(250, 600, hxp)
    z = lerp(1.0, 1.12, smooth(hxp))
    cam = (lerp(480, 560, hxp), 1120, z, 0, 0)
    gy = 1420
    landscape(c, T, cam, "dusk", ground_y=gy, seed=14, tree_xs=[], mid=True)
    rnd = random.Random(14)
    for x in range(-300, 1500, 170):
        pine(c, x + rnd.uniform(-40, 40), gy - 60, rnd.uniform(420, 560), "#121d2c", snow=True)
    c.drawRect(skia.Rect.MakeLTRB(-2000, 600, 3000, gy), P("#0b1020", alpha=0.35))
    for ex, ey, t0 in EYES:
        a = smooth(pr(T, t0, t0 + 0.3))
        eyes_pair(c, ex, ey, 0.9, a, auto_blink(T, ex / 300))
    for x in (-150, 160, 820, 1150):
        pine(c, x, gy + 20, 520, "#1a2a3d", snow=True)
    ground(c, gy, *PAL["dusk"]["gr"], seed=14)
    bush(c, 880, gy + 30, 110, "#1e3a3a", shake=1 if 37.9 < T < 38.5 else 0, T=T)
    hs = 0.75
    ph = T * 8
    wp = walk(ph, 20)
    wp["armA"], wp["armB"] = (-20, 100), (20, -100)
    person(c, hx, hip_y(gy, hs) + bob(ph, 5), hs, look=(1, 0), T=T, cold=0.6, frost=0.3, shiver=0.3,
           mouth="worried", brows=0.6, blink=auto_blink(T), **wp)
    if 37.9 < T < 38.6:
        for k in range(5):
            pk = pr(T, 37.9 + k * 0.05, 38.5)
            circle(c, 880 + (k - 2) * 40 + pk * 30 * (k - 2), gy - 80 - pk * 120 + pk * pk * 160, 8, "#2e5e52", 3,
                   alpha=1 - pk)
    c.restore()
    snowfall(c, T, n=40, wind=0.4, speed=90, alpha=0.6)
    vignette(c, "#000000", 0.75)
    callout(c, T, 37.9, "UN DETALLE...", W / 2, 330, 100, "#ffd23f")


# ================================================================== 15. no estás solo
def s15_notalone(c, T):
    zk = ease_out_back(pr(T, 40.15, 40.45))
    z = lerp(1.0, 1.28, zk)
    cam = (540, 1330, z, -2 * zk, 4)
    gy = 1950
    landscape(c, T, cam, "dusk", ground_y=gy, seed=15, tree_xs=[], mid=False)
    rnd = random.Random(15)
    for x in range(-200, 1400, 200):
        pine(c, x, gy - 300, rnd.uniform(600, 760), "#121d2c")
    c.drawRect(skia.Rect.MakeLTRB(-2000, 0, 3000, gy), P("#0b1020", alpha=0.45))
    pts = [(170, 1050), (880, 980), (330, 820), (760, 760), (980, 1250), (90, 1300), (560, 700)]
    for i, (ex, ey) in enumerate(pts):
        eyes_pair(c, ex, ey, 1.3, smooth(pr(T, 40.05 + i * 0.08, 40.4 + i * 0.08)), auto_blink(T, i))
    turn = smooth(pr(T, 40.1, 40.3))
    person(c, 540, 1920, 1.9, look=(lerp(0.3, -1, turn), -0.1), head_tilt=lerp(0, -8, turn), mouth="o",
           mouth_open=0.9, brows=1, sweat=1, shiver=0.5, T=T, cold=0.6, armA=(-25, 30), armB=(25, -30))
    c.restore()
    vignette(c, "#000000", 0.8)
    callout(c, T, 40.46, "NO ESTÁS SOLO", W / 2, 330, 130, "#ff4d4d")


# ================================================================== 16. lobos
def s16_wolves(c, T):
    k = smooth(pr(T, 41.7, 42.9))
    cam = (lerp(500, 540, k), lerp(1400, 1160, k), lerp(1.6, 1.0, k), 0, 0)
    gy = 1260
    landscape(c, T, cam, "night", ground_y=gy, seed=16, tree_xs=[-300, 980, 1200])
    moon(c, 860, 520, 70)
    # colina lejana con el humano
    hill = curve([(-200, gy + 10), (60, 1110), (300, 1130), (480, gy + 10)], close=False)
    hill.close()
    shape(c, hill, "#9fb0d8", 6)
    person(c, 180, 1130 - 213 * 0.22, 0.22, T=T, armA=(-20, 100), armB=(20, -100), shiver=0.5, cold=0.6)
    # rastro de olor
    wx, wy, ws = 830, 1660, 1.6
    sn = 0.5 + 0.5 * math.sin(T * 9)
    nose = (wx - ws * 200, wy - ws * 145 + sn * 20)
    reveal = ease_out(pr(T, 42.4, 43.2))
    for j in range(3):
        pts = []
        for i in range(30):
            u = i / 29
            if u > reveal:
                break
            x = lerp(200, nose[0], u)
            y = lerp(1060, nose[1], u) + math.sin(u * 14 - T * 6 + j) * 26 + (j - 1) * 22
            pts.append((x, y))
        if len(pts) > 2:
            p = P("#d9f99d", 7, alpha=0.75)
            p.setPathEffect(skia.DashPathEffect.Make([26, 22], -T * 120))
            c.drawPath(curve(pts, close=False), p)
    for i in range(6):
        u = ((T * 0.4 + i / 6) % 1) * reveal
        circle(c, lerp(200, nose[0], u), lerp(1060, nose[1], u) + math.sin(u * 14 - T * 6) * 26, 14, "#d9f99d", 0,
               alpha=0.5)
    wolf(c, 520, 1430, 0.7, facing=-1, T=T, sniff=0.5 + 0.5 * math.sin(T * 7 + 1), glow_eyes=True)
    wolf(c, 1050, 1380, 0.6, facing=-1, T=T, sniff=0.5 + 0.5 * math.sin(T * 8 + 2), glow_eyes=True)
    wolf(c, wx, wy, ws, facing=-1, T=T, sniff=sn, glow_eyes=True, color="#7d879a")
    for i in range(3):
        ph = ((T * 3 + i / 3) % 1)
        c.drawPath(curve([(nose[0] - 30 - ph * 40, nose[1] - 30 + i * 30), (nose[0] - 60 - ph * 40, nose[1] - 20 + i * 30),
                          (nose[0] - 90 - ph * 40, nose[1] - 30 + i * 30)]), P("#ffffff", 6, alpha=1 - ph))
    c.restore()
    snowfall(c, T, n=40, wind=0.3, speed=90, alpha=0.7)
    if T > 43.1:
        a = pop(T, 43.1)
        c.save()
        c.translate(W / 2, 470)
        c.scale(a, a)
        c.drawLine(-380, 0, 380, 0, P("#ffffff", 8))
        for sx in (-1, 1):
            shape(c, path([(sx * 400, 0), (sx * 360, -26), (sx * 360, 26)]), "#ffffff", 4)
        c.restore()
        text(c, "KILÓMETROS", W / 2, 400, 90, "#d9f99d", scale=a)
    callout(c, T, 42.04, "LOBOS", W / 2, 280, 120, "#ffffff", t1=43.0)


# ================================================================== 17. oso
def s17_bear(c, T):
    rise = pr(T, 45.6, 46.3)
    roar = smooth(pr(T, 47.0, 47.2))
    shk = 22 * (1 - pr(T, 47.05, 47.6)) if T > 47.05 else 0
    cy = lerp(1210, 1060, smooth(rise))
    cam = (580, cy, lerp(0.95, 0.9, rise), 0, shk)
    gy = 1440
    landscape(c, T, cam, "storm", ground_y=gy, seed=17, tree_xs=[-220, 1350], sway=0.5)
    cave_arch(c, 620, gy, 380, 560)
    emerge = smooth(pr(T, 44.35, 45.1))
    bs = 0.82
    c.save()
    c.translate(620, gy)
    c.scale(lerp(0.85, 1, emerge), lerp(0.85, 1, emerge))
    c.translate(-620, -gy)
    bear(c, 620, gy, bs, rise=rise, roar=roar, T=T)
    c.restore()
    if emerge < 1:
        c.drawPath(curve([(620 - 190, gy + 8), (620 - 200, gy - 300), (620, gy - 480), (620 + 200, gy - 300),
                          (620 + 190, gy + 8)], close=True), P("#14121f", alpha=1 - emerge))
    hs = 0.5
    scared = T > 45.6
    person(c, 190, hip_y(gy, hs), hs, look=(1, -1 if scared else 0), mouth="o" if scared else "neutral",
           mouth_open=0.9, brows=1 if scared else 0, T=T, cold=0.5, shiver=0.4 + 0.6 * roar, sweat=1 if scared else 0,
           armA=(-25, 30), armB=(25, -30))
    # regla
    top = gy - bs * 615
    if T > 46.0:
        g = ease_out(pr(T, 46.0, 46.4))
        rx = 930
        yt = lerp(gy, top, g)
        rrect(c, rx - 22, yt, 44, gy - yt, 10, "#ffe14a", 6)
        n = int((gy - yt) / 34)
        for i in range(n):
            c.drawLine(rx - 22, gy - i * 34, rx - (2 if i % 3 else -8), gy - i * 34, P(OUT, 4))
        if T > 46.44:
            text(c, "3 M", rx - 10, top - 60, 100, "#ffe14a", scale=pop(T, 46.44))
            c.drawLine(rx - 30, top, 760, top, P("#ffffff", 5, alpha=0.8))
        if T > 46.7:
            ht = gy - 0.5 * 525
            text(c, "1,7 M", 190, ht - 60, 60, "#ffffff", scale=pop(T, 46.7))
            dp = P("#ffffff", 4, alpha=0.8)
            dp.setPathEffect(skia.DashPathEffect.Make([16, 12], 0))
            c.drawLine(120, ht, 900, ht, dp)
    if roar > 0:
        for i in range(4):
            ph = ((T * 3 + i / 4) % 1)
            r = 150 + ph * 300
            pth = skia.Path()
            pth.addArc(skia.Rect.MakeLTRB(620 - r, top + 40 - r * 0.6, 620 + r, top + 40 + r * 0.6), -60, 120)
            c.drawPath(pth, P("#ffffff", 8, alpha=(1 - ph) * roar))
            pth = skia.Path()
            pth.addArc(skia.Rect.MakeLTRB(620 - r, top + 40 - r * 0.6, 620 + r, top + 40 + r * 0.6), 120, 120)
            c.drawPath(pth, P("#ffffff", 8, alpha=(1 - ph) * roar))
    c.restore()
    snowfall(c, T, n=60, wind=0.8, speed=180)
    callout(c, T, 44.64, "OSO CAVERNARIO", W / 2, 300, 100, "#ffffff", t1=46.3)
    callout(c, T, 47.1, "¡GRRAAAH!", W / 2, 330, 140, "#ff4d4d")


# ================================================================== 18. presa lenta
def s18_chase(c, T):
    t = T - 47.65
    camx = 540 + 520 * t
    gy = 1450
    cam = (camx, 1180, 1.05, 0, 3)
    landscape(c, T, cam, "day", ground_y=gy, seed=18, tree_xs=[])
    base = int((camx - 1200) // 420)
    rnd_trees = [(i * 420 + (i * 137) % 160, 330 + (i * 53) % 120) for i in range(base, base + 8)]
    for x, h in rnd_trees:
        pine(c, x, gy + 10, h, PAL["day"]["tree"])
    ground(c, gy, *PAL["day"]["gr"], x0=camx - 1400, x1=camx + 1400, seed=1)
    hx = camx + 140
    hs = 0.6
    ph = T * 13
    rp = run(ph)
    person(c, hx, hip_y(gy, hs) + bob(ph, 10), hs, look=(-1, 0), mouth="scream", mouth_open=0.8, brows=1, sweat=1,
           T=T, cold=0.3, **rp)
    # reno que se escapa
    dx = camx + lerp(330, 1100, ease_in(pr(T, 47.8, 48.8)))
    wolf(c, dx, gy + 5, 0.75, phase=T * 18, mode="run", facing=1, T=T, deer=True, color="#9a6a42", belly="#e8d3b5")
    # lobos que alcanzan
    gap = lerp(560, 330, smooth(pr(T, 47.65, 51.0)))
    wolf(c, hx - gap, gy + 10, 0.8, phase=T * 16, mode="run", facing=1, T=T, glow_eyes=False)
    wolf(c, hx - gap - 230, gy + 15, 0.7, phase=T * 16 + 1.3, mode="run", facing=1, T=T)
    for k in range(3):
        pk = ((T * 3 + k / 3) % 1)
        circle(c, hx - 60 - pk * 140, gy - 10 - pk * 40, 22 * (1 - pk), "#ffffff", 0, alpha=1 - pk)
    tags = [(dx, gy - 300, 47.9, "80 KM/H", "#9fe8a0"), (hx - gap, gy - 230, 48.25, "60 KM/H", "#ffd166"),
            (hx, gy - 400, 48.02, "TÚ: 15 KM/H", "#ff6b6b")]
    for x, y, t0, s, col in tags:
        if T > t0:
            text(c, s, x, y, 54, col, scale=pop(T, t0))
    c.restore()
    snowfall(c, T, n=50, wind=-1.6, speed=150)
    wind_lines(c, T, n=6, speed=-1400, alpha=0.4)
    callout(c, T, 48.84, "LA PRESA", W / 2, 280, 110, "#ffffff")
    callout(c, T, 49.4, "MÁS LENTA", W / 2, 410, 130, "#ff4d4d", rot=3)


# ================================================================== 19. neandertales
def s19_neander(c, T):
    z = lerp(1.0, 1.1, smooth(pr(T, 51.05, 54.15)))
    c.drawRect(skia.Rect.MakeWH(W, H), P("#2a1c17"))
    c.save()
    camera(c, 560, 1180, z, 0, 0, T)
    gy = 1470
    # boca de la cueva con tormenta
    mouthp = curve([(-200, gy), (-180, 760), (60, 560), (230, 760), (260, gy)], close=True)
    c.save()
    c.clipPath(mouthp, doAntiAlias=True)
    vgrad(c, skia.Rect.MakeLTRB(-300, 400, 400, gy), "#5b6f8c", "#a9bad0")
    rnd = random.Random(19)
    for i in range(60):
        x = (rnd.uniform(-300, 400) + T * 500) % 700 - 300
        y = (rnd.uniform(400, gy) + T * 300) % (gy - 400) + 400
        c.drawCircle(x, y, rnd.uniform(3, 7), P("#ffffff"))
    c.restore()
    # pared de roca
    wall = skia.Path()
    wall.addRect(skia.Rect.MakeLTRB(-600, -400, 1800, gy + 600))
    hole = mouthp
    wall = skia.Op(wall, hole, skia.PathOp.kDifference_PathOp)
    sh = skia.GradientShader.MakeRadial(skia.Point(560, gy - 120), 900, [hexc("#8a5a3c"), hexc("#3a2620")])
    c.drawPath(wall, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawPath(mouthp, P(OUT, OW))
    # arcos de roca
    for (x, y, rx, ry) in ((300, 300, 600, 260), (1000, 520, 420, 300)):
        c.drawPath(curve([(x - rx, y + ry), (x, y - ry * 0.2), (x + rx, y + ry)]), P("#2a1a15", 14))
    # pinturas rupestres
    c.save()
    c.translate(820, 760)
    c.scale(0.38, 0.38)
    p = P("#c2552e", 10, alpha=0.8)
    c.drawPath(curve([(-280, -300), (-260, -470), (60, -525), (270, -400), (300, -250)]), p)
    for lx in (-180, -100, 120, 200):
        c.drawLine(lx, -280, lx, -60, p)
    c.drawPath(curve([(300, -380), (380, -300), (390, -150), (350, -100)]), p)
    c.restore()
    hand_print(c, 960, 960, 0.7)
    hand_print(c, 1040, 1040, 0.6, alpha=0.5)
    # suelo
    c.drawRect(skia.Rect.MakeLTRB(-600, gy, 1800, gy + 800), P("#4a3328"))
    c.drawLine(-600, gy, 1800, gy, P(OUT, OW))
    glow(c, 560, gy - 120, 650, "#ff9a3c", 0.35 + 0.05 * math.sin(T * 9))
    ns = 0.85
    person(c, 300, hip_y(gy, ns, "neander"), ns, style="neander", T=T, armA=(-14, -6), armB=(30, 170),
           holding=(1, lambda cc, x, y, a1, a2: spear(cc, x, y + 200, 470, 180)), look=(1, 0), mouth="neutral",
           blink=auto_blink(T, 1))
    person(c, 830, hip_y(gy, 0.8, "neander"), 0.8, style="neander", facing=-1, T=T, armA=(50, 80), armB=(40, 75),
           look=(1, 0.3), mouth="smile", blink=auto_blink(T, 2))
    person(c, 700, hip_y(gy, 0.55, "neander") + 10, 0.55, style="neander", facing=-1, T=T, armA=(60, 100),
           armB=(50, 90), look=(1, 0), mouth="smile", blink=auto_blink(T, 0.4))
    fire(c, 560, gy + 10, 0.7, T)
    c.restore()
    vignette(c, "#000000", 0.6)
    callout(c, T, 51.54, "NEANDERTALES", W / 2, 300, 115, "#ffd166")
    callout(c, T, 53.3, "MILENIOS", W / 2, 440, 120, "#ffffff", rot=3)


# ================================================================== 20. comparación
def s20_compare(c, T):
    a = ease_out(pr(T, 54.15, 54.5))
    # panel superior: neandertal
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 0, W, 960))
    c.translate(-W * (1 - a), 0)
    vgrad(c, skia.Rect.MakeLTRB(0, 0, W, 960), "#5a3524", "#b06a3c")
    glow(c, 140, 880, 420, "#ff9a3c", 0.4)
    fire(c, 130, 905, 0.42, T)
    c.drawRect(skia.Rect.MakeLTRB(0, 900, W, 960), P("#4a3328"))
    ns = 0.9
    person(c, 400, hip_y(900, ns, "neander"), ns, style="neander", T=T, armA=(-14, -6), armB=(30, 170),
           holding=(1, lambda cc, x, y, a1, a2: spear(cc, x, y + 200, 470, 180)), mouth="smile", look=(1, 0),
           blink=auto_blink(T))
    c.restore()
    # panel inferior: tú
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 960, W, H))
    c.translate(W * (1 - a), 0)
    vgrad(c, skia.Rect.MakeLTRB(0, 960, W, H), "#6f86a6", "#d6e2ee")
    mountains(c, 3, 1600, 300, "#8ea3bf", ow=6)
    ground(c, 1840, seed=2)
    hs = 0.9
    person(c, 330, hip_y(1840, hs), hs, T=T, armA=(-20, 100), armB=(20, -100), shiver=1, cold=0.9, frost=0.8,
           mouth="grit", brows=1, blink=auto_blink(T, 1), look=(-0.4, -1) if T < 54.9 else (1, 0))
    c.restore()
    snowfall(c, T, n=35, wind=1.2, speed=200)
    # divisor
    pts = [(0, 950)]
    for i in range(13):
        pts.append((i * 90 + 45, 960 + (14 if i % 2 else -14)))
    pts.append((W, 950))
    pts += [(W, 970), (0, 970)]
    shape(c, path(pts), "#ffffff", 6)
    vs = pop(T, 54.3)
    c.save()
    c.translate(W / 2, 960)
    c.scale(vs, vs)
    circle(c, 0, 0, 78, "#ff4d4d", 8)
    c.restore()
    text(c, "VS", W / 2, 960, 80, "#ffffff", scale=vs, shadow=False)
    text(c, "NEANDERTAL", W / 2, 90, 70, "#ffd166", scale=pop(T, 54.2))
    text(c, "TÚ", W / 2 + 260, 1060, 80, "#ffffff", scale=pop(T, 54.88))
    rows = [(55.84, "CUERPO"), (57.08, "SABER")]
    for i, (t0, lbl) in enumerate(rows):
        if T < t0:
            continue
        s = pop(T, t0)
        text(c, lbl, 770, 330 + i * 160, 74, "#ffffff", scale=s)
        check(c, 990, 330 + i * 160, 38, pr(T, t0 + 0.1, t0 + 0.4), 22)
        text(c, lbl, 770, 1200 + i * 160, 74, "#ffffff", scale=s)
        red_x(c, 990, 1200 + i * 160, 34, pr(T, t0 + 0.15, t0 + 0.45), 22)


# ================================================================== 21. ventisca nocturna
def s21_blizzard(c, T):
    z = lerp(0.95, 1.1, smooth(pr(T, 58.25, 61.15)))
    cam = (540, 1150, z, 0, 3)
    gy = 1380
    landscape(c, T, cam, "night", ground_y=gy, seed=21, tree_xs=[-200, 1300], sway=2)
    cave_arch(c, 930, gy - 20, 90, 140, rock="#3d4566")
    hs = 0.45
    person(c, 540, hip_y(gy, hs), hs, T=T, armA=(-20, 100), armB=(20, -100), shiver=1, cold=0.9, frost=0.9,
           mouth="grit", brows=1)
    c.restore()
    c.drawRect(skia.Rect.MakeWH(W, H), P("#0a1030", alpha=0.25))
    snowfall(c, T, n=160, wind=1.8, speed=320, size=(3, 10))
    wind_lines(c, T, n=12, alpha=0.5)
    if T > 59.38:
        s = pop(T, 59.38)
        c.save()
        c.translate(460, 440)
        c.scale(s, s)
        stopwatch(c, 0, 0, 120, (T - 59.38) * 900)
        c.restore()
        text(c, "?", 700, 440, 220, "#ffe14a", scale=s, rot=10 + math.sin(T * 4) * 5)
    callout(c, T, 59.84, "¿CUÁNTO DURARÍAS?", W / 2, 700, 86, "#ffffff", rot=-2)


def s21b_closeup(c, T):
    z = lerp(1.0, 1.15, smooth(pr(T, 61.15, 63.95)))
    cam = (540, 1250, z, 0, 3)
    landscape(c, T, cam, "night", ground_y=1950, seed=22, tree_xs=[-100, 1150], sway=2, mid=False)
    person(c, 540, 1790, 1.5, T=T, armA=(-20, 100), armB=(20, -100), shiver=1, cold=1.0, frost=1.0,
           mouth="grit", brows=1, blink=0.45 + 0.1 * math.sin(T * 2), look=(0, 0.3))
    for k in range(3):
        ph = ((T * 0.8 + k / 3) % 1)
        circle(c, 540 + ph * 60, 1790 - 1.5 * 200 - ph * 80, 20 + ph * 40, "#ffffff", 0, alpha=0.5 * (1 - ph))
    c.restore()
    snowfall(c, T, n=150, wind=1.8, speed=320, size=(3, 10))
    wind_lines(c, T, n=10, alpha=0.5)
    vignette(c, "#000820", 0.7)
    callout(c, T, 61.2, "SIN REFUGIO", W / 2, 330, 120, "#bfe6ff", t1=62.5)
    if T > 62.66:
        s = pop(T, 62.66)
        c.save()
        c.translate(250, 360)
        c.scale(s, s)
        moon(c, 0, 0, 80)
        c.restore()
        text(c, "1 NOCHE", 640, 360, 130, "#fff3c4", scale=s, rot=-3 + math.sin(T * 4) * 1.5)


# ================================================================== 22. atardecer
def s22_dusk(c, T):
    k = smooth(pr(T, 64.0, 66.6))
    top = mixh("#3a3f7a", "#05081a", k)
    bot = mixh("#ff9a5a", "#1a1f45", k)
    mid = mixh("#c2607a", "#0e1433", k)
    sky(c, top, bot, mid)
    stars(c, pr(T, 65.2, 66.6))
    z = lerp(1.15, 1.0, smooth(pr(T, 63.95, 67.0)))
    c.save()
    camera(c, 540, 1150, z, 0, 0, T)
    sy = lerp(1000, 1420, smooth(pr(T, 64.0, 66.4)))
    glow(c, 540, sy, 520, "#ffb347", 0.6 * (1 - k * 0.7))
    circle(c, 540, sy, 140, mixh("#ffd27a", "#ff6a3a", k), 0)
    mountains(c, 41, 1350, 520, mixh("#5b4a7a", "#141933", k), peaks=6, ow=6)
    mountains(c, 42, 1470, 330, mixh("#3d3563", "#0d1128", k), peaks=8, ow=6)
    ground(c, 1520, mixh("#9ea3cf", "#2a3157", k), mixh("#6a6f9e", "#151a36", k), seed=5)
    for x in (120, 950):
        pine(c, x, 1530, 380, "#0f1424")
    hs = 0.6
    person(c, 540, hip_y(1520, hs), hs, style="shadow", T=T, armA=(-20, 100), armB=(20, -100), shiver=0.6)
    c.restore()
    snowfall(c, T, n=50, wind=0.6, speed=110, alpha=0.6)
    vignette(c, "#000000", 0.5 + 0.4 * k)
    callout(c, T, 64.44, "ESA NOCHE...", W / 2, 330, 110, "#ffd27a")
    if T > 66.75:
        c.drawRect(skia.Rect.MakeWH(W, H), P("#000000", alpha=smooth(pr(T, 66.75, 67.0))))


# ================================================================== línea de tiempo
# (inicio, función, transición de entrada, y de subtítulos)
SCENES = [
    (0.00, s01_wake, "cut"),
    (2.55, s02_clothes, "punch"),
    (5.90, s03_cotton, "whip"),
    (8.20, s04_freeze, "cut"),
    (10.00, s05_cold, "punch"),
    (13.55, s06_hunger, "punch"),
    (14.85, s07_energy, "whip"),
    (18.90, s08_fat, "punch"),
    (20.75, s09_mammoth, "whip"),
    (25.00, s10_without, "punch"),
    (28.30, s10b_nothing, "cut"),
    (30.00, s11_river, "whip"),
    (32.45, s12_error, "cut"),
    (33.30, s13_inside, "punch"),
    (36.45, s14_forest, "fade"),
    (40.05, s15_notalone, "punch"),
    (41.65, s16_wolves, "whip"),
    (44.30, s17_bear, "punch"),
    (47.65, s18_chase, "whip"),
    (51.05, s19_neander, "iris"),
    (54.15, s20_compare, "cut"),
    (58.25, s21_blizzard, "wipe"),
    (61.15, s21b_closeup, "punch"),
    (63.95, s22_dusk, "fade"),
]
DURATION = 67.0
CAPTION_Y = {s20_compare: 1800}
