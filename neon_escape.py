"""
Neon Escape_Cyberpunk Arcade Survival
"""
import pygame, sys, math, random, os
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

W, H=1200, 600
FPS= 60
THIS_DIR=os.path.dirname(os.path.abspath(__file__))

BG =(3,   0,  12)
CYAN   =(0,  220, 255)
CYAN2 =(0,  150, 200)
PURPLE  =(170,  0, 255)
PURPLE2=(100,  0, 180)
RED=(255,  20,  60)
ORANGE= (255, 110,   0)
YELLOW=(255, 230,   0)
WHITE=(255, 255, 255)
BLUE =(0,   80,  255)
DKWALL=(6,   0,   22)
MIDWALL= (14,  0,   40)
GREEN=(0,  255,  100)
PINK=(255,  0,  180)

canvas =pygame.display.set_mode((W, H))
pygame.display.set_caption("NEON ESCAPE  ·  Cyberpunk Arcade Survival")
CLOCK=pygame.time.Clock()

try:
    font_big=pygame.font.Font(None, 72)
    font_mid=pygame.font.Font(None, 42)
    font_hud=pygame.font.Font(None, 28)
    font_small= pygame.font.Font(None, 22)
    font_tiny= pygame.font.Font(None, 18)
except:
    font_big=pygame.font.SysFont("couriernew",52,bold=True)
    font_mid=pygame.font.SysFont("couriernew",28,bold=True)
    font_hud=pygame.font.SysFont("couriernew",18,bold=True)
    font_small= pygame.font.SysFont("couriernew",14)
    font_tiny= pygame.font.SysFont("couriernew",12)

#Easy,Medium and Hard
DIFF={
    "EASY": {
        "spawn_start": 110, #frames between spawns when starting
        "spawn_min": 70, #spawning 
        "proj_spd_start":3.8,
        "proj_spd_max":5.5,
        "laser_interval":420,
        "emp_interval":500,
        "max_projs_on_screen": 4,
        "constrict_max":120,  #px each wall closes in
        "constrict_spd":0.06, #pxper frame
        "phase2_score":40,
        "phase2_survive":600,  #frames required to survive after full constriction
        "dmg_proj":14, "dmg_laser":20, "dmg_emp":12,
        "boss_speed": 3,
    },
    "MEDIUM": {
        "spawn_start": 80,
        "spawn_min":   45,
        "proj_spd_start": 5.0,
        "proj_spd_max": 8.5,
        "laser_interval": 280,
        "emp_interval":320,
        "max_projs_on_screen": 6,
        "constrict_max":140,
        "constrict_spd":0.09,
        "phase2_score":35,
        "phase2_survive":480,
        "dmg_proj":20, "dmg_laser":30, "dmg_emp":18,
        "boss_speed": 5,
    },
    "HARD": {
        "spawn_start": 55,
        "spawn_min":28,
        "proj_spd_start": 7.0,
        "proj_spd_max":13.0,
        "laser_interval":180,
        "emp_interval":200,
        "max_projs_on_screen": 9,
        "constrict_max":155,
        "constrict_spd":0.14,
        "phase2_score": 30,
        "phase2_survive":360,
        "dmg_proj":28, "dmg_laser":40, "dmg_emp":25,
        "boss_speed": 7,
    },
}
chosen_diff="MEDIUM"  
VOL_MASTER=0.7   

# SOUND ENGINE
import numpy as np
SR =44100
#tiny DSP helpers 
def _env_adsr(n, a=0.01, d=0.05, s_level=0.7, r=0.15):
    """Attack-decay-sustain-release envelope, all as fraction of total length."""
    env=np.zeros(n)
    ai=min(int(a*n), n)
    di=min(int(d*n), n-ai)
    ri=min(int(r*n), n-ai-di)
    si=max(0, n - ai - di - ri)
    if ai>0: env[:ai]=np.linspace(0,1,ai)
    if di>0: env[ai:ai+di]=np.linspace(1,s_level,di)
    if si>0: env[ai+di:ai+di+si]=s_level
    if ri>0: env[n-ri:n]=np.linspace(s_level,0,ri)
    return env

def _osc(freq, n, wave="sine", detune=0.0):
    t=np.linspace(0,n/SR,n,False)
    f=freq * (1+detune)
    if wave=="sine":  
         return np.sin(2*np.pi*f*t)
    if wave=="saw":  
          return 2*(t*f - np.floor(t*f+0.5))
    if wave=="square": 
        return np.sign(np.sin(2*np.pi*f*t))
    if wave=="tri":    
        return 2*np.abs(2*(t*f - np.floor(t*f+0.5)))-1
    return np.sin(2*np.pi*f*t)

def _noise(n): return np.random.uniform(-1,1,n)

def _sweep_osc(f1, f2, n, wave="sine"):
    freq=np.linspace(f1, f2, n)
    phi =2*np.pi*np.cumsum(freq)/SR
    if wave=="sine":  return np.sin(phi)
    if wave=="saw":   return 2*(phi/(2*np.pi) - np.floor(phi/(2*np.pi)+0.5))
    if wave=="square": return np.sign(np.sin(phi))
    return np.sin(phi)

def _reverb(s, delay_ms=40, decay=0.35, n_taps=4):
    """Simple multi-tap delay reverb."""
    out=s.copy()
    delay_s=delay_ms/1000.0
    for tap in range(1, n_taps+1):
        d=int(delay_s * tap * SR)
        if d >= len(s): break
        gain=decay**(tap)
        out[d:] += s[:-d]*gain if d>0 else s*gain
    return out

def _distort(s, amount=2.0):
    return np.tanh(s * amount) / np.tanh(amount)

def _to_sound(buf, vol=0.5):
    buf=np.clip(buf, -1, 1)
    s16=(buf * vol * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([s16, s16]))

#SOund Builders

def snd_player_hit():
    n=int(SR*0.28)
    body=_sweep_osc(520, 55, n, "saw")
    body=_distort(body, 3.5)
    body *= _env_adsr(n, 0.005, 0.12, 0.0, 0.88)
  #crack
    nc=int(SR*0.06)
    crack=_noise(nc) * np.exp(-np.linspace(0,12,nc))
    body[:nc] += crack * 0.9
    thud=_osc(60, n, "sine") * _env_adsr(n, 0.002, 0.3, 0.0, 0.7)
    body += thud * 0.6
    body=_reverb(body, 25, 0.25, 3)
    return _to_sound(body, 0.72)

def snd_laser_beam():
    n=int(SR*0.35)
    charge=_sweep_osc(300, 1800, n, "sine")
    charge += _sweep_osc(600, 3600, n, "sine") * 0.4
    charge += _sweep_osc(150, 900, n, "saw") * 0.2
    env_c=_env_adsr(n, 0.05, 0.05, 0.8, 0.1)
    charge *= env_c
  #final zap,noise burst in last 20%
    zi=int(n*0.8)
    charge[zi:] += _noise(n-zi) * np.exp(-np.linspace(0,8,n-zi)) * 0.8
    charge=_reverb(charge, 35, 0.3, 3)
    return _to_sound(charge, 0.65)

def snd_emp_blast():
  #deep booming electromagnetic pulse with reverb tail
    n=int(SR*0.55)
    low=_sweep_osc(180, 30, n, "sine") * 0.8
    low += _sweep_osc(360, 60, n, "sine") * 0.4
    low += _sweep_osc(90, 20, n, "saw") * 0.3
  #mid crunch
    mid=_sweep_osc(800, 200, n, "square") * 0.3
  #noise tail
    tail_start=int(n*0.1)
    noise_tail=np.zeros(n)
    noise_tail[tail_start:]=_noise(n-tail_start) * np.exp(-np.linspace(0,5,n-tail_start))
    body=low + mid + noise_tail*0.4
    body *= _env_adsr(n, 0.005, 0.15, 0.4, 0.44)
    body=_reverb(body, 60, 0.45, 5)
    return _to_sound(body, 0.68)

def snd_death_explosion():
  #massive explosion 
    n=int(SR*1.1)
  #sub boom: very low pitch drops fast
    sub=_sweep_osc(80, 18, n, "sine") * 1.2
    sub *= np.exp(-np.linspace(0, 3, n))
    mid_n=int(SR*0.4)
    mid=_noise(mid_n) * np.exp(-np.linspace(0, 6, mid_n))
    mid=_distort(mid, 4.0)
    body=sub.copy()
    body[:mid_n] += mid * 0.9
    hc=int(SR*0.05)
    body[:hc] += _noise(hc) * np.exp(-np.linspace(0,20,hc)) * 1.4
    for h in [110, 220, 330, 440]:
        henv=np.exp(-np.linspace(0, 4+h/110, n))
        body += _osc(h, n, "sine") * henv * 0.15
    body=_reverb(body, 80, 0.55, 6)
    return _to_sound(body, 0.80)

def snd_phase_change():
  #dramatic alarm 
    n=int(SR*0.65)
  # two sweeping sines
    alarm =_sweep_osc(220, 1100, n, "square") * 0.5
    alarm += _sweep_osc(233, 1166, n, "square") * 0.5  #slightly detuned
    alarm *= _env_adsr(n, 0.01, 0.1, 0.7, 0.19)
  #impact at end
    imp_start=int(n*0.75)
    imp=_noise(n-imp_start) * np.exp(-np.linspace(0,10,n-imp_start))
    alarm[imp_start:] += imp * 0.8
    sub=_sweep_osc(100, 30, n, "sine") * np.exp(-np.linspace(0,5,n))
    alarm += sub * 0.6
    alarm=_reverb(alarm, 45, 0.4, 4)
    return _to_sound(alarm, 0.70)

def snd_escape_win():
    n=int(SR*1.0)
    notes=[261, 329, 392, 523, 659, 784, 1046]
    body=np.zeros(n)
    step=n // len(notes)
    for i, freq in enumerate(notes):
        ns=min(step*2, n - i*step)
        if ns <= 0: break
        chunk=_osc(freq, ns, "sine")
        chunk += _osc(freq*2, ns, "sine") * 0.3
        chunk += _osc(freq*0.5, ns, "saw") * 0.15
        env=_env_adsr(ns, 0.02, 0.1, 0.7, 0.18)
        body[i*step:i*step+ns] += chunk * env * 0.5
  #whoosh underneath
    whoosh=_sweep_osc(80, 2000, n, "saw") * 0.3
    whoosh *= np.linspace(0, 1, n)
    body += whoosh
    body=_reverb(body, 55, 0.5, 5)
    return _to_sound(body, 0.65)

def snd_powerup():
  #sparkling ascending chime
    n=int(SR*0.45)
    body=np.zeros(n)
    freqs=[523, 659, 784, 1047, 1319]
    for i, f in enumerate(freqs):
        start=i * (n//6)
        ns=n - start
        if ns <= 0: break
        chunk=_osc(f, ns, "sine") + _osc(f*2, ns, "sine")*0.3
        env=_env_adsr(ns, 0.01, 0.05, 0.6, 0.34)
        body[start:] += chunk * env * 0.35
    body += _noise(n) * np.exp(-np.linspace(0,8,n)) * 0.08
    body=_reverb(body, 30, 0.4, 4)
    return _to_sound(body, 0.58)

def snd_player_shoot():
  #sharp plasma zap
    n=int(SR*0.14)
    body =_sweep_osc(1400, 600, n, "saw") * 0.7
    body += _sweep_osc(700, 300, n, "square") * 0.3
    body *= _env_adsr(n, 0.003, 0.08, 0.2, 0.72)
    body[:int(n*0.1)] += _noise(int(n*0.1)) * 0.5
    body=_reverb(body, 18, 0.2, 2)
    return _to_sound(body, 0.52)

def snd_boss_hit():
  #deep metallic sound
    n=int(SR*0.40)
  #metallic body: slightly inharmonic series
    body=_osc(180, n, "sine") * 0.7
    body += _osc(380, n, "sine") * 0.5 #slightly inharmonic
    body += _osc(620, n, "sine") * 0.3
    body += _osc(900, n, "sine") * 0.15
    body *= np.exp(-np.linspace(0, 7, n))
    pn=int(SR*0.04)
    body[:pn] += _noise(pn) * np.exp(-np.linspace(0,15,pn)) * 1.1
    body=_distort(body, 1.8)
    body=_reverb(body, 40, 0.38, 4)
    return _to_sound(body, 0.72)

def snd_net_fire():
    n=int(SR*0.22)
    body=_noise(n) * 0.5
    body += _sweep_osc(400, 200, n, "square") * 0.4
    body += _sweep_osc(800, 400, n, "sine") * 0.3
    for _ in range(8):
        pos=random.randint(0, n-100)
        cl=random.randint(40,100)
        body[pos:pos+cl] += _noise(cl) * 1.5
    body *= _env_adsr(n, 0.01, 0.15, 0.3, 0.54)
    body=_reverb(body, 22, 0.3, 3)
    return _to_sound(body, 0.55)

def snd_boost_jump():
    n=int(SR*0.10)
    body =_sweep_osc(200, 800, n, "sine") * 0.6
    body += _sweep_osc(100, 400, n, "saw")  * 0.3
    body *= _env_adsr(n, 0.005, 0.05, 0.5, 0.45)
    return _to_sound(body, 0.38)

# BGM
def make_synthwave_bgm(bpm=125, bars=8, intensity=1.0):
    """
    Rich layered synthwave loop.
    bass + lead arpeggio + pad + kick + snare + hihat + fx
    """
    spb  =60.0/bpm
    beats=bars * 4
    total=int(SR * spb * beats)
    buf  =np.zeros(total, dtype=np.float64)

    bass_seq =[55, 55, 65, 55, 55, 65, 55, 73]   
    arp_seq  =[220,261,293,329,220,261,349,329]  

    note_dur=int(SR * spb * 0.48)
    for i, note in enumerate(bass_seq * bars):
        pos=int(i * SR * spb * 0.5)
        if pos + note_dur >= total: break
        t2=np.linspace(0,note_dur/SR,note_dur,False)
        bass_note =0.6*np.sin(2*np.pi*note*t2)
        bass_note += 0.3*np.sin(2*np.pi*note*2*t2)
        bass_note += 0.15*(2*(t2*note - np.floor(t2*note+0.5))) 
        bass_env=np.ones(note_dur)
        bass_env[-note_dur//5:]=np.linspace(1,0,note_dur//5)
        buf[pos:pos+note_dur] += bass_note * bass_env * 0.45

    arp_step=int(SR * spb * 0.25) 
    for i, note in enumerate(arp_seq * (bars*2)):
        pos=int(i * arp_step)
        ns=min(arp_step, total-pos)
        if ns <= 0 or pos >= total: break
        t2=np.linspace(0,ns/SR,ns,False)
        arp_note =0.35*np.sin(2*np.pi*note*t2)
        arp_note += 0.15*np.sin(2*np.pi*note*1.5*t2)  #fifth
        arp_env=np.exp(-np.linspace(0,6,ns))
        buf[pos:pos+ns] += arp_note * arp_env * 0.4 * intensity

    pad_notes=[110, 138, 165, 185]  
    pad_chunk=int(SR * spb * 4)   #one bar at a time
    for bar_i in range(bars):
        pos=int(bar_i * SR * spb * 4)
        ns=min(pad_chunk, total-pos)
        if ns <= 0: break
        t2=np.linspace(0,ns/SR,ns,False)
        pad=np.zeros(ns)
        for pn in pad_notes:
            pad += 0.18*np.sin(2*np.pi*pn*t2)
            pad += 0.06*np.sin(2*np.pi*pn*2*t2)
        pad_env=np.ones(ns); pad_env[:ns//10]=np.linspace(0,1,ns//10); pad_env[-ns//8:]=np.linspace(1,0,ns//8)
        buf[pos:pos+ns] += pad * pad_env * 0.28

  # drums 
    kick_n=int(SR*0.12)
    snare_n= int(SR*0.10)
    hat_n =int(SR*0.04)

    for beat_i in range(beats):
        beat_pos=int(beat_i * SR * spb)

      #kick on every beat
        if beat_pos + kick_n < total:
            kt=np.linspace(0,kick_n/SR,kick_n,False)
            kick =0.9*np.sin(2*np.pi*np.linspace(160,30,kick_n)*kt)
            kick += 0.3*np.random.uniform(-1,1,kick_n)*np.exp(-kt*60)
            kick *= np.exp(-kt*28)
            buf[beat_pos:beat_pos+kick_n] += kick * 0.55

      #snare on 2 and 4
        if beat_i%4 in (1,3) and beat_pos+snare_n < total:
            sn_t=np.linspace(0,snare_n/SR,snare_n,False)
            snare =0.5*np.random.uniform(-1,1,snare_n)*np.exp(-sn_t*40)
            snare += 0.3*np.sin(2*np.pi*200*sn_t)*np.exp(-sn_t*30)
            buf[beat_pos:beat_pos+snare_n] += snare * 0.40

        for sub in range(2):
            hp=beat_pos + int(sub * SR * spb * 0.5)
            if hp + hat_n < total:
                hat=0.25*np.random.uniform(-1,1,hat_n)*np.exp(-np.linspace(0,25,hat_n))
                buf[hp:hp+hat_n] += hat * 0.22
#reverb
    delay=int(0.06*SR)
    if delay < len(buf):
        buf[delay:] += buf[:-delay]*0.18
    delay2=int(0.12*SR)
    if delay2 < len(buf):
        buf[delay2:] += buf[:-delay2]*0.10

    buf=np.clip(buf,-1,1)
    s16=(buf*32767*0.62).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([s16,s16]))

def make_boss_bgm():
    """Heavier, faster, more dissonant than normal BGM."""
    return make_synthwave_bgm(bpm=148, bars=8, intensity=1.3)

has_audio=False
SFX_HIT=SFX_LASER=SFX_EMP=SFX_SPAWN=SFX_DIE=None
SFX_PHASE=SFX_ESCAPE=SFX_BOOST=SFX_POWERUP=SFX_SHOOT=None
SFX_BULLET_HIT=SFX_BOSS_HIT=SFX_NET=BGM=BOSS_BGM=None

try:
    if pygame.mixer.get_init():
        pygame.mixer.quit()
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    pygame.mixer.set_num_channels(16)
    has_audio=True
except Exception as _se:
    has_audio=False

if has_audio:
    def _safe(fn, *a, **k):
        try: return fn(*a,**k)
        except: return None

    SFX_HIT      =_safe(snd_player_hit)
    SFX_LASER    =_safe(snd_laser_beam)
    SFX_EMP      =_safe(snd_emp_blast)
    SFX_DIE      =_safe(snd_death_explosion)
    SFX_PHASE    =_safe(snd_phase_change)
    SFX_ESCAPE   =_safe(snd_escape_win)
    SFX_POWERUP  =_safe(snd_powerup)
    SFX_SHOOT    =_safe(snd_player_shoot)
    SFX_BOSS_HIT =_safe(snd_boss_hit)
    SFX_NET      =_safe(snd_net_fire)
    SFX_BOOST    =_safe(snd_boost_jump)
    SFX_SPAWN    =_safe(snd_net_fire) #reuse net for generic spawn
    SFX_BULLET_HIT= _safe(snd_boss_hit)  #reuse for bullet hit variation
    try:
        BGM=make_synthwave_bgm(bpm=125, bars=8)
        BGM.set_volume(0.42)
    except: BGM=None
    try:
        BOSS_BGM=make_boss_bgm()
        BOSS_BGM.set_volume(0.46)

    except: BOSS_BGM=None

# audio helper

def play(sfx):
    if has_audio and sfx is not None:
        try: sfx.play()
        except: pass

def play_ui(sfx):
    """play on a specific channel so ui clicks never cut game sounds"""
    if has_audio and sfx is not None:
        try:
            ch=pygame.mixer.Channel(14)
            ch.play(sfx)
        except: pass

def start_bgm():
    if has_audio and BGM is not None:
        try:
            pygame.mixer.Channel(15).play(BGM, loops=-1)
        except: pass

def stop_bgm():
    if has_audio:
        try:
            pygame.mixer.Channel(15).stop()
        except: pass

def start_boss_bgm():
    if has_audio and BOSS_BGM is not None:
        try:
            pygame.mixer.Channel(15).play(BOSS_BGM, loops=-1)
        except: pass

def apply_volume():
    """Apply master volume to all sounds."""
    global VOL_MASTER
    v=VOL_MASTER
    for sfx in [SFX_HIT,SFX_LASER,SFX_EMP,SFX_DIE,SFX_PHASE,SFX_ESCAPE,
                SFX_POWERUP,SFX_SHOOT,SFX_BOSS_HIT,SFX_NET,SFX_BOOST,
                SFX_UI_CLICK,SFX_UI_SELECT,SFX_BULLET_HIT,SFX_SPAWN]:
        if sfx: sfx.set_volume(v * 0.9)
    if BGM:      BGM.set_volume(v * 0.42)
    if BOSS_BGM: BOSS_BGM.set_volume(v * 0.46)

def start_menu_bgm():
    """slightly quieter, calmer version of bgm for main menu"""
    if has_audio and BGM is not None:
        try:
            ch=pygame.mixer.Channel(15)
            BGM.set_volume(0.28)
            ch.play(BGM, loops=-1)
        except: pass

#ui click sound 
def _make_ui_click():
    try:
        n=int(44100 * 0.06)
        t=np.linspace(0, n/44100, n, False)
        s=np.sin(2*np.pi*880*t) * 0.5 + np.sin(2*np.pi*1320*t) * 0.3
        env=np.exp(-np.linspace(0, 12, n))
        s=(s * env * 0.4 * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack([s, s]))
    except: return None

def _make_ui_select():
    """slightly more musical tone for confirming a selection"""
    try:
        n=int(44100 * 0.12)
        t=np.linspace(0, n/44100, n, False)
        s=np.sin(2*np.pi*660*t) * 0.5 + np.sin(2*np.pi*990*t) * 0.4 + np.sin(2*np.pi*1320*t)*0.2
        env=np.exp(-np.linspace(0, 8, n))
        s=(s * env * 0.45 * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack([s, s]))
    except: return None

SFX_UI_CLICK =_make_ui_click()  if has_audio else None
SFX_UI_SELECT=_make_ui_select() if has_audio else None
#apply default volume once everything is loaded

# SPRITES


# PLAYER 
def make_player(thrust=0):
    """
    96×58 surface. Player faces RIGHT (away from boss who is on the left).
    thrust: 0=glide  1=boost-up  2=falling
    """
    sw, sh=96, 58
    s=pygame.Surface((sw, sh), pygame.SRCALPHA)

  # jet-bike 
    body=[(20,29),(26,18),(72,16),(82,24),(82,34),(72,42),(26,40)]
    pygame.draw.polygon(s,(16,6,38),body)
    pygame.draw.polygon(s,(80,0,160),body,2)
  #top-side 
    pygame.draw.line(s,CYAN,(28,17),(70,16),2)
  #bottom-side strip
    pygame.draw.line(s,PURPLE,(28,40),(70,41),1)
  #chassis panel lines
    pygame.draw.line(s,(50,0,110),(40,18),(40,40),1)
    pygame.draw.line(s,(50,0,110),(56,17),(56,41),1)

  # rider body 

    pygame.draw.rect(s,(22,8,50),(55,10,18,22),border_radius=4)
    pygame.draw.rect(s,(80,0,160),(55,10,18,22),1,border_radius=4)
  #arms
    pygame.draw.rect(s,(18,6,42),(64,14,14,8),border_radius=3)  #fwd arm
    pygame.draw.rect(s,(18,6,42),(50,18,10,6),border_radius=2)  #back arm
  #flight suit glowing
    pygame.draw.line(s,CYAN,(57,12),(70,12),1)
    pygame.draw.line(s,CYAN,(57,20),(70,20),1)

  # helmet
    pygame.draw.circle(s,(24,8,55),(72,16),10) #skull
    pygame.draw.circle(s,(14,4,35),(72,16),10,1) #outline
  #visor 
    visor_s=pygame.Surface((14,8),pygame.SRCALPHA)
    pygame.draw.ellipse(visor_s,(0,200,255,180),(0,0,14,8))
    s.blit(visor_s,(66,12))
  #visor reflection
    pygame.draw.line(s,(180,240,255),(68,13),(72,13),1)

  # engine block 
    pygame.draw.rect(s,(12,4,30),(14,22,18,14),border_radius=3)
    pygame.draw.rect(s,(100,0,180),(14,22,18,14),1,border_radius=3)
  #exhaust nozzle
    pygame.draw.ellipse(s,(8,2,20),(8,24,10,10))
    pygame.draw.ellipse(s,(120,0,200),(8,24,10,10),1)

  # JET FLAME 
    fl=32 + thrust*18 if thrust==1 else (18 if thrust==2 else 24)
    for i in range(6):
        t2=i/5
        fc=(int(t2*255), int(100+t2*80), 255)
        fa=int(210 - t2*180)
        flen=int(fl*(1 - t2*0.5))
        fw  =max(1, int((1-t2)*7))
        fy  =29 + int((t2-0.5)*5)
        fs  =pygame.Surface((flen+2,fw*2+2),pygame.SRCALPHA)
        pygame.draw.ellipse(fs,(*fc,fa),(0,0,flen,fw*2))
        s.blit(fs,(8-flen, fy-fw))

  # wing fin
    fin=[(26,40),(14,48),(30,50),(36,42)]
    pygame.draw.polygon(s,(28,0,70),fin)
    pygame.draw.polygon(s,PURPLE,fin,1)
  #top stabiliser
    st=[(26,18),(14,10),(30,8),(36,16)]
    pygame.draw.polygon(s,(28,0,70),st)
    pygame.draw.polygon(s,CYAN2,st,1)

    return s

player_frames=[make_player(0), make_player(1), make_player(2)]

# BOSS 
def make_boss_body():
    """110×110 static base."""
    bw,bh=110,110
    s=pygame.Surface((bw,bh),pygame.SRCALPHA)
    cx,cy=bw//2,bh//2
    for r,c in [(48,(20,0,55)),(45,(35,0,90)),(42,(15,0,45))]:
        pygame.draw.circle(s,c,(cx,cy),r)
    pygame.draw.circle(s,PURPLE2,(cx,cy),48,2)
    pygame.draw.circle(s,(40,0,100),(cx,cy),30)
    pygame.draw.circle(s,PURPLE,(cx,cy),30,2)
  #pupil
    for r,c in [(18,(160,0,0)),(13,(220,20,20)),(8,(255,70,70))]:
        pygame.draw.circle(s,c,(cx,cy),r)
  #specular
    pygame.draw.circle(s,(255,190,190),(cx-5,cy-5),4)
  #gear notches around shell
    for ad in range(0,360,30):
        a =math.radians(ad)
        x1=cx+int(math.cos(a)*30); y1=cy+int(math.sin(a)*30)
        x2=cx+int(math.cos(a)*44); y2=cy+int(math.sin(a)*44)
        pygame.draw.line(s,(70,0,150),(x1,y1),(x2,y2),1)
  #cannons pointing right
    for dy in (-20,20):
        pygame.draw.rect(s,(12,0,35),(cx+20,cy+dy-5,32,10),border_radius=3)
        pygame.draw.rect(s,CYAN2,    (cx+20,cy+dy-5,32,10),1,border_radius=3)
        pygame.draw.rect(s,CYAN,     (cx+48,cy+dy-2,12,4))
    return s

boss_body=make_boss_body()

def draw_boss(surf, bx, by, ring_a, wing_t, pulse, mal=False):
    cx,cy=bx+55, by+55
    gc   =ORANGE if mal else PURPLE
    rc   =ORANGE if mal else CYAN
  #glow
    for r in (85,68,52):
        a =max(0,int(25+pulse*12))
        gs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*gc,a),(r,r),r)
        surf.blit(gs,(cx-r,cy-r))
  #outer ring
    for i in range(8):
        a =ring_a + i*(math.tau/8)
        rx=cx+int(math.cos(a)*64); ry=cy+int(math.sin(a)*64)
        pygame.draw.circle(surf,rc,(rx,ry),4)
        if i%2==0: pygame.draw.circle(surf,WHITE,(rx,ry),2)
    rs=pygame.Surface((134,134),pygame.SRCALPHA)
    pygame.draw.circle(rs,(*rc,35),(67,67),64,2)
    surf.blit(rs,(cx-67,cy-67))
  #inner ring
    for i in range(6):
        a =-ring_a*1.5+i*(math.tau/6)
        rx=cx+int(math.cos(a)*50); ry=cy+int(math.sin(a)*50)
        pygame.draw.circle(surf,PURPLE,(rx,ry),3)
  #animated wings
    wf=int(wing_t*14)
    for sgn,dy in [(-1,-22),(1,22)]:
        wpts=[(cx+12,cy+dy),(cx+58,cy+sgn*45+wf*sgn),(cx+68,cy+sgn*30+wf*sgn//2),(cx+52,cy+dy*0.8)]
        wpts=[(int(x),int(y)) for x,y in wpts]
        pygame.draw.polygon(surf,(20,0,50),wpts)
        wc=ORANGE if mal else PURPLE2
        pygame.draw.polygon(surf,wc,wpts,1)
        for pt in wpts[1:3]:
            pygame.draw.line(surf,(*( CYAN if not mal else ORANGE),90),(cx+12,cy),pt,1)
  #body
    surf.blit(boss_body,(bx,by))
  #eye pulse glow
    eg=pygame.Surface((52,52),pygame.SRCALPHA)
    ea=int(100+pulse*55)
    pygame.draw.circle(eg,(255,0,0,min(255,ea)),(26,26),22)
    surf.blit(eg,(cx-26,cy-26))
  #cannon charge
    cc=ORANGE if mal else CYAN
    cr=int(3+abs(pulse)*2)
    for dy in (-20,20):
        pygame.draw.circle(surf,cc,(cx+50,cy+dy),cr)

# PROJECTILES
def make_plasma_net(sz=50):
    s=pygame.Surface((sz,sz),pygame.SRCALPHA)
    c=sz//2; r=sz//2-4
    for i in range(6):
        a=i*(math.tau/6)
        pygame.draw.line(s,(0,210,255,160),(c,c),(c+int(math.cos(a)*r),c+int(math.sin(a)*r)),1)
    for ri in [1,2]:
        rr=r*ri//2
        rs2=pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
        pygame.draw.circle(rs2,(0,190,255,110),(rr+2,rr+2),rr,1)
        s.blit(rs2,(c-rr-2,c-rr-2))
    pygame.draw.circle(s,(0,240,255,200),(c,c),r,2)
    for i in range(6):
        a=i*(math.tau/6)
        pygame.draw.circle(s,CYAN,(c+int(math.cos(a)*r),c+int(math.sin(a)*r)),3)
    return s

def make_bullet(w=38,h=14):
    s=pygame.Surface((w,h),pygame.SRCALPHA)
    pts=[(0,h//2),(5,2),(w-5,2),(w,h//2),(w-5,h-2),(5,h-2)]
    pygame.draw.polygon(s,(0,50,110),pts)
    pygame.draw.polygon(s,CYAN,pts,1)
    pygame.draw.ellipse(s,(150,230,255,190),(4,h//2-2,w-10,4))
    gs=pygame.Surface((18,18),pygame.SRCALPHA)
    pygame.draw.circle(gs,(0,210,255,130),(9,9),8)
    s.blit(gs,(w-14,h//2-9))
    return s

def make_mine(sz=40):
    s=pygame.Surface((sz,sz),pygame.SRCALPHA)
    c=sz//2; r=sz//2-5
    pygame.draw.circle(s,(28,8,0),(c,c),r)
    pygame.draw.circle(s,ORANGE,(c,c),r,2)
    for i in range(6):
        a=i*(math.tau/6)
        ix=c+int(math.cos(a)*r); iy=c+int(math.sin(a)*r)
        ex=c+int(math.cos(a)*(r+6)); ey=c+int(math.sin(a)*(r+6))
        pygame.draw.line(s,ORANGE,(ix,iy),(ex,ey),2)
    pygame.draw.circle(s,(255,140,0),(c,c),7)
    pygame.draw.circle(s,YELLOW,(c,c),4)
    return s

NET_SURF =make_plasma_net(50)
BULLET_SURF= make_bullet(38,14)
MINE_SURF =make_mine(40)

def make_emp_ring(r, alpha):
    sz=r*2+6
    s=pygame.Surface((sz,sz),pygame.SRCALPHA)
    c=sz//2
    pygame.draw.circle(s,(160,0,255,alpha),(c,c),r,3)
    pygame.draw.circle(s,(200,80,255,alpha//2),(c,c),max(1,r-9),1)
    for i in range(10):
        a=i*(math.tau/10)
        nx=c+int(math.cos(a)*r); ny=c+int(math.sin(a)*r)
        pygame.draw.circle(s,(210,90,255,alpha),(nx,ny),2)
    return s

# CITY BACKGROUND
def make_city(seed, tw, max_h, far=True):
    surf=pygame.Surface((tw,max_h),pygame.SRCALPHA)
    rng=random.Random(seed)
    bc=(10,0,25) if far else (18,0,42)
    wcs=[(0,200,255,85),(160,0,255,75),(0,130,190,55)]
    x=0
    while x<tw:
        bw=rng.randint(34,115); bh=rng.randint(55,max_h-18)
        by=max_h-bh
        pygame.draw.rect(surf,bc,(x,by,bw,bh))
        tc=rng.choice(wcs)
        pygame.draw.rect(surf,tc[:3]+(45,),(x,by,bw,2))
        for wy in range(by+8,max_h-10,15):
            for wx in range(x+4,x+bw-4,11):
                if rng.random()>0.44:
                    wc=rng.choice(wcs)
                    pygame.draw.rect(surf,wc,(wx,wy,5,8))
        x+=bw+rng.randint(2,14)
    return surf

CW=2400
city_far =make_city(7,  CW,290,True)
city_near=make_city(13, CW,200,False)
cfx=0.0; cnx=0.0

star_surf=pygame.Surface((W,H),pygame.SRCALPHA)
for _ in range(200):
    sx=random.randint(0,W-1); sy=random.randint(0,H//2)
    sa=random.randint(50,180); sz=random.uniform(0.5,2.0)
    pygame.draw.circle(star_surf,(255,255,255,sa),(sx,sy),int(sz))

rain=[{"x":random.randint(0,W),"y":random.randint(0,H),
       "s":random.uniform(6,13),"a":random.randint(22,65)} for _ in range(160)]

def draw_bg(surf, tval):
    global cfx, cnx
    surf.fill(BG)
    surf.blit(star_surf,(0,0))
    cfx=(cfx-0.3)%(-CW)
    surf.blit(city_far,(int(cfx),H-city_far.get_height()))
    surf.blit(city_far,(int(cfx)+CW,H-city_far.get_height()))
    cnx=(cnx-0.95)%(-CW)
    surf.blit(city_near,(int(cnx),H-city_near.get_height()))
    surf.blit(city_near,(int(cnx)+CW,H-city_near.get_height()))
    for rd in rain:
        pygame.draw.line(surf,(45,0,100,rd["a"]),
            (int(rd["x"]),int(rd["y"])),(int(rd["x"])-2,int(rd["y"])+int(rd["s"]*1.3)),1)
        rd["y"]+=rd["s"]; rd["x"]-=1.1
        if rd["y"]>H: rd["y"]=-8; rd["x"]=random.randint(0,W)


# HAZARD WALLS
top_wall=60  #bottom edge 
bot_wall=H-60  #top edge 

def draw_top_wall(surf, tval):
    pygame.draw.rect(surf,DKWALL,(0,0,W,top_wall))
  #glow fringe
    for i in range(10):
        a=max(0,38-i*4)
        gs=pygame.Surface((W,2),pygame.SRCALPHA)
        gs.fill((0,200,255,a))
        surf.blit(gs,(0,top_wall-i*2))
  #spikes
    for sx in range(0,W,22):
        sh2=11+int(math.sin(sx*0.07+tval*3)*4)
        pts=[(sx,top_wall),(sx+11,top_wall+sh2),(sx+22,top_wall)]
        pygame.draw.polygon(surf,MIDWALL,pts)
        pygame.draw.polygon(surf,(0,170,255),pts,1)
  #live glow line
    for x in range(0,W,3):
        y=top_wall+int(math.sin(x*0.05+tval*4)*4)
        pygame.draw.line(surf,(0,200,255,160),(x,y),(x,y),1)
    for cx2 in range(40,W,80):
        sw2=math.sin(tval*1.3+cx2*0.012)*8
        pts2=[(int(cx2+sw2*math.sin(j*0.8)),int(j/5*top_wall*0.8)) for j in range(6)]
        if len(pts2)>=2: pygame.draw.lines(surf,(0,110,150,90),False,pts2,1)

def draw_bot_wall(surf, tval):
    pygame.draw.rect(surf,DKWALL,(0,bot_wall,W,H-bot_wall))
    for i in range(10):
        a=max(0,38-i*4)
        gs=pygame.Surface((W,2),pygame.SRCALPHA)
        gs.fill((255,20,55,a))
        surf.blit(gs,(0,bot_wall+i*2))
    for sx in range(0,W,22):
        sh2=10+int(math.sin(sx*0.07-tval*3)*4)
        pts=[(sx,bot_wall),(sx+11,bot_wall-sh2),(sx+22,bot_wall)]
        pygame.draw.polygon(surf,MIDWALL,pts)
        pygame.draw.polygon(surf,(255,25,55),pts,1)
    for wave in range(3):
        for x in range(0,W,3):
            y=bot_wall+4+wave*6+int(math.sin(x*0.025+tval*5+wave)*3)
            pygame.draw.line(surf,(255,0,55,max(0,150-wave*30)),(x,y),(x,y),1)

# PARTICLES
particles=[]

def spawn_p(x,y,col,n=8,spd=3.5,sz=3,life=28):
    for _ in range(n):
        a=random.uniform(0,math.tau); v=random.uniform(0.3,spd)
        particles.append([float(x),float(y),math.cos(a)*v,math.sin(a)*v,
                          list(col[:3]),life,life,sz])

def update_particles(surf):
    dead=[]
    for p in particles:
        p[0]+=p[2]; p[1]+=p[3]; p[3]+=0.05
        p[2]*=0.97; p[3]*=0.97; p[5]-=1
        if p[5]<=0: dead.append(p); continue
        a=int(255*p[5]/p[6]); sz=max(1,int(p[7]*p[5]/p[6]))
        ps=pygame.Surface((sz*2,sz*2),pygame.SRCALPHA)
        pygame.draw.circle(ps,(*p[4][:3],a),(sz,sz),sz)
        surf.blit(ps,(int(p[0])-sz,int(p[1])-sz))
    for p in dead:
        try: particles.remove(p)
        except: pass

# SCREEN FX
shake_t=0; shake_mag=0; flash_col=RED; flash_a=0; glitch_t=0

def do_shake(mag=8,dur=10):
    global shake_t,shake_mag
    shake_t=max(shake_t,dur); shake_mag=max(shake_mag,mag)

def get_shake():
    global shake_t,shake_mag
    if shake_t>0:
        shake_t-=1
        ox=random.randint(-shake_mag,shake_mag)
        oy=random.randint(-shake_mag//2,shake_mag//2)
        if shake_t==0: shake_mag=0
        return ox,oy
    return 0,0

def do_flash(col=None,a=130):
    global flash_col,flash_a
    flash_col=col or RED; flash_a=max(flash_a,a)

def draw_flash(surf):
    global flash_a
    if flash_a<=0: return
    fs=pygame.Surface((W,H),pygame.SRCALPHA)
    fs.fill((*flash_col[:3],int(flash_a)))
    surf.blit(fs,(0,0)); flash_a=max(0,flash_a-8)

def do_glitch(dur=18):
    global glitch_t
    glitch_t=max(glitch_t,dur)

def draw_glitch(surf):
    global glitch_t
    if glitch_t<=0: return
    glitch_t-=1
    if random.random()>0.55:
        sw2=random.randint(80,500); sh2=random.randint(2,9)
        sx2=random.randint(0,W-sw2); sy2=random.randint(0,H-sh2)
        try:
            sl=surf.subsurface((sx2,sy2,sw2,sh2)).copy()
            surf.blit(sl,(sx2+random.randint(-16,16),sy2))
        except: pass
    sl2=pygame.Surface((W,random.randint(1,3)),pygame.SRCALPHA)
    sl2.fill((0,255,255,random.randint(6,24)))
    surf.blit(sl2,(0,random.randint(0,H-3)))




def draw_hud(surf, score, hi, shield, phase_name, diff_name, phase2_progress=0.0, combo=0, ghost_t=0, boost_t=0):
  #dark strip behind the hud
    tb=pygame.Surface((W,top_wall),pygame.SRCALPHA)
    tb.fill((0,0,8,215))
    surf.blit(tb,(0,0))
    pygame.draw.line(surf,CYAN,(0,top_wall),(W,top_wall),1)

  #row 1 (y=8)
    sc=font_hud.render(f"SCORE  {score:05d}", True, CYAN)
    surf.blit(sc, (12, 8))

    hi_s=font_hud.render(f"HI  {hi:05d}  [{diff_name}]", True, CYAN)
    surf.blit(hi_s, (W - hi_s.get_width() - 12, 8))

  #row 2 (y=32)
    ph=font_tiny.render(phase_name, True, PURPLE)
    surf.blit(ph, (W//2 - ph.get_width()//2, 32))

  #row 3 (y=50)
    bar_y=52; bw_bar=120; bh_bar=8

    sl3=font_tiny.render("SHIELD", True, CYAN)
    surf.blit(sl3, (12, bar_y - 13))
    pygame.draw.rect(surf, (30,0,20), (12, bar_y, bw_bar, bh_bar))
    fw=max(0, int(bw_bar * shield/100))
    bc=(0,210,80) if shield>60 else (255,170,0) if shield>30 else RED
    if fw>0:
        pygame.draw.rect(surf, bc, (12, bar_y, fw, bh_bar))
    pygame.draw.rect(surf, CYAN, (12, bar_y, bw_bar, bh_bar), 1)

  #constriction bar right side
    if phase2_progress > 0:
        prog=min(1.0, phase2_progress)
        cx2=W - 132; cw2=120
        clbl=font_tiny.render("WALLS", True, PURPLE)
        surf.blit(clbl, (cx2, bar_y - 13))
        pygame.draw.rect(surf, (20,0,30), (cx2, bar_y, cw2, bh_bar))
        pygame.draw.rect(surf, PURPLE, (cx2, bar_y, int(cw2*prog), bh_bar))
        pygame.draw.rect(surf, PURPLE, (cx2, bar_y, cw2, bh_bar), 1)

    if combo >= 2:
        cc=ORANGE if combo >= 5 else YELLOW
        cs=font_hud.render(f"COMBO  x{combo}", True, cc)
        surf.blit(cs, (W - cs.get_width() - 50, top_wall + 28))
    pb_x=W-36; pb_y=(top_wall-10)//2; pb_w=28; pb_h=28
    pygame.draw.rect(surf, (20,0,50), (pb_x, pb_y, pb_w, pb_h), border_radius=4)
    pygame.draw.rect(surf, (80,0,160), (pb_x, pb_y, pb_w, pb_h), 1, border_radius=4)
    bw2=5; bh2=14; bx0=pb_x+6; by0=pb_y+7
    pygame.draw.rect(surf, CYAN, (bx0, by0, bw2, bh2))
    pygame.draw.rect(surf, CYAN, (bx0+bw2+4, by0, bw2, bh2))

  #bottom bar
    bb=pygame.Surface((W, H-bot_wall), pygame.SRCALPHA)
    bb.fill((8,0,0,200))
    surf.blit(bb,(0,bot_wall))
    pygame.draw.line(surf, RED, (0,bot_wall),(W,bot_wall), 1)
    active_pups=[]
    if ghost_t > 0:
        active_pups.append(("GHOST MODE", ghost_t, 240, CYAN))
    if boost_t > 0:
        active_pups.append(("PWR BOOST", boost_t, 180, YELLOW))
    if active_pups:
        pill_w=130; pill_h=18; pill_gap=8
        total_w=len(active_pups)*(pill_w+pill_gap) - pill_gap
        px0=W//2 - total_w//2
        py0=top_wall + 4
        for name, timer, max_t, col in active_pups:
            pygame.draw.rect(surf, (10,0,25), (px0, py0, pill_w, pill_h), border_radius=5)
          #progress bar fill
            prog=timer / max_t
            bar_w=int((pill_w-4) * prog)
            if bar_w > 0:
                pygame.draw.rect(surf, (*col[:3], 160), (px0+2, py0+2, bar_w, pill_h-4), border_radius=4)
            pygame.draw.rect(surf, col, (px0, py0, pill_w, pill_h), 1, border_radius=5)
          #label
            secs=max(1, timer//60 + (1 if timer%60>0 else 0))
            lbl=font_tiny.render(f"{name} {secs}s", True, col)
            surf.blit(lbl, (px0 + pill_w//2 - lbl.get_width()//2, py0 + pill_h//2 - lbl.get_height()//2))
            px0 += pill_w + pill_gap

    pup_x=12; pup_y=bot_wall + 6
    if ghost_t > 0:
        secs=ghost_t//60 + 1
        gt=font_tiny.render(f"GHOST  {secs}s", True, CYAN)
        surf.blit(gt, (pup_x, pup_y)); pup_x += gt.get_width()+18
    if boost_t > 0:
        secs=boost_t//60 + 1
        bt2=font_tiny.render(f"BOOST  {secs}s", True, YELLOW)
        surf.blit(bt2, (pup_x, pup_y))


#TOPScore 
hi_scores={"EASY": 0, "MEDIUM": 0, "HARD": 0}

def get_hi():
    return hi_scores.get(chosen_diff, 0)

def update_hi(score):
    if score > hi_scores.get(chosen_diff, 0):
        hi_scores[chosen_diff]=score
SCORE=0


#Game Objects
class Boss:
    """Replaces Dragon — bounces up/down on left side."""
    def __init__(self, speed):
        self.velocity=speed
        self.rect =pygame.Rect(18, H//2-55, 110, 110)
        self.up   =True; self.down=False
        self.ring_a= 0.0; self.wing_t= 0.0; self.wing_d= 1
        self.pulse=0.0; self.alive=True
        self.malfunction=False; self.mal_t=0

    def update(self):
        if not self.alive: return
        if self.rect.top  <= top_wall:   self.up=False;  self.down=True
        if self.rect.bottom >= bot_wall: self.up=True;   self.down=False
        if self.up:   self.rect.top -= self.velocity
        else:         self.rect.top += self.velocity
        self.ring_a += 0.022
        self.pulse  =math.sin(pygame.time.get_ticks()*0.005)
        self.wing_t += 0.055*self.wing_d
        if abs(self.wing_t)>1.0: self.wing_d*=-1
        if self.malfunction:
            self.mal_t+=1
            if self.mal_t%4==0:
                spawn_p(self.rect.centerx+random.randint(-40,40),
                        self.rect.centery+random.randint(-35,35),
                        ORANGE,n=3,spd=4,sz=3,life=18)

    def draw(self, surf):
        if not self.alive: return
        draw_boss(surf,self.rect.left,self.rect.top,
                  self.ring_a,self.wing_t,self.pulse,self.malfunction)


class Projectile:
    """Fires from boss (LEFT) toward player (RIGHT). Speed increases over time."""
    def __init__(self, boss_rect, speed, ptype=None):
        types=["net","bullet","bullet","mine"]
        self.ptype=ptype or random.choice(types)
        self.angle=0.0; self.pulse=random.uniform(0,math.tau); self.alive=True
        self.vx=speed + random.uniform(-0.5,0.5)
        if   self.ptype=="net":    self.img=NET_SURF;    self.vx*=0.85
        elif self.ptype=="bullet": self.img=BULLET_SURF; self.vx*=1.1
        elif self.ptype=="mine":   self.img=MINE_SURF;   self.vx*=0.7
        self.rect=self.img.get_rect()
        self.rect.left=boss_rect.right+6
        cy=boss_rect.centery+random.randint(-30,30)
        self.rect.centery=max(top_wall+18,min(bot_wall-18,cy))

    def update(self): self.rect.left+=int(self.vx); self.pulse+=0.12; self.angle+=0.07

    def draw(self, surf):
        gc=CYAN if self.ptype=="bullet" else (PURPLE if self.ptype=="net" else ORANGE)
        glo=pygame.Surface((56,56),pygame.SRCALPHA)
        ga=int(45+math.sin(self.pulse)*14)
        pygame.draw.circle(glo,(*gc,ga),(28,28),24)
        surf.blit(glo,(self.rect.centerx-28,self.rect.centery-28))
        if self.ptype=="net":
            rot=pygame.transform.rotate(self.img,math.degrees(self.angle))
            surf.blit(rot,rot.get_rect(center=self.rect.center))
        else:
            surf.blit(self.img,self.rect)


class LaserBeam:
    WARN=52; BEAM=26
    def __init__(self):
        self.y    =random.randint(top_wall+48,bot_wall-48)
        self.timer=0; self.phase="warn"; self.alive=True

    def update(self):
        self.timer+=1
        if self.phase=="warn" and self.timer>=self.WARN:
            self.phase="beam"; self.timer=0
            do_shake(5,7); do_flash(RED,75); play(SFX_LASER)
        elif self.phase=="beam" and self.timer>=self.BEAM:
            self.alive=False
            play(SFX_LASER)

    def draw(self, surf):
        if self.phase=="warn":
            if (self.timer//6)%2==0:
                ws=pygame.Surface((W,14),pygame.SRCALPHA); ws.fill((255,0,55,48))
                surf.blit(ws,(0,self.y-7))
                wt=font_small.render("  ⚡ LASER WARNING ⚡  ",True,(255,70,70))
                surf.blit(wt,(W//2-wt.get_width()//2,self.y-22))
        elif self.phase=="beam":
            for bw2 in (32,20,9,3):
                ba=38 if bw2>9 else (90 if bw2>3 else 220)
                bs=pygame.Surface((W,bw2),pygame.SRCALPHA); bs.fill((255,0,55,ba))
                surf.blit(bs,(0,self.y-bw2//2))
            pygame.draw.line(surf,(255,200,200),(0,self.y),(W,self.y),2)

    def hit_rect(self): return pygame.Rect(0,self.y-7,W,14)


class EMPRing:
    def __init__(self, boss_rect):
        self.cx=float(boss_rect.right); self.cy=float(boss_rect.centery)
        self.r=8.0; self.spd=5.0; self.life=90; self.alive=True

    def update(self):
        self.r+=self.spd; self.life-=1
        if self.life<=0 or self.r>max(W,H): self.alive=False

    def draw(self, surf):
        ir=int(self.r)
        if ir<3: return
        a=int(170*self.life/90)
        rs=make_emp_ring(ir,a)
        surf.blit(rs,(int(self.cx)-ir-3,int(self.cy)-ir-3))

    def collides(self, rect):
        return abs(math.hypot(self.cx-rect.centerx,self.cy-rect.centery)-self.r)<17


class Player:
    """Replaces Mario — same up/down attrs, gravity based."""
    velocity=10
    def __init__(self):
        self.rect=player_frames[0].get_rect()
        self.rect.right=W-28; self.rect.centery=H//2
        self.up=False; self.down=True
        self.vy=0.0; self.alive=True
        self.shield=100; self.invinc=0
        self.mario_score=0
        self.frame=0; self.ftimer=0
        self.tilt=0.0; self.trail=[]
        self.boost_frame=0

    def update(self):
        if not self.alive: return
        boost_force=-1.05 if getattr(self,"super_boost",False) else -0.62
        if self.up:   self.vy+=boost_force
        self.vy+=0.30; self.vy=max(-9,min(9,self.vy)); self.vy*=0.90
        self.rect.top+=int(self.vy)
        if self.rect.top<top_wall:
            self.rect.top=top_wall; self.vy=abs(self.vy)*0.25
            self._die()
        if self.rect.bottom>bot_wall:
            self.rect.bottom=bot_wall; self.vy=-abs(self.vy)*0.25
            self._die()
        if self.invinc>0: self.invinc-=1
        self.ftimer+=1
        if self.ftimer>=7: self.ftimer=0; self.frame=(self.frame+1)%3
        self.boost_frame=1 if self.up else (2 if self.vy>1 else 0)
        tgt=-self.vy*2.6
        self.tilt+=(tgt-self.tilt)*0.16; self.tilt=max(-28,min(28,self.tilt))
        if self.ftimer%2==0:
            spawn_p(self.rect.left+4,self.rect.centery+10,BLUE,n=2,spd=2.5,sz=3,life=14)
        self.trail.append((self.rect.centerx,self.rect.centery))
        if len(self.trail)>8: self.trail.pop(0)

    def _die(self):
        if self.alive:
            self.alive=False
            game_over_flag[0]=True
            game_over_flag[1]=self.rect.centerx
            game_over_flag[2]=self.rect.centery

    def draw(self, surf):
        if not self.alive: return
        for i,(tx,ty) in enumerate(self.trail):
            a=int(40*(i/max(1,len(self.trail))))
            gh=player_frames[self.boost_frame].copy(); gh.set_alpha(a)
            surf.blit(gh,gh.get_rect(center=(tx,ty)))
        if self.invinc>0 and (self.invinc//4)%2==1: return
        fi=player_frames[self.boost_frame]
        if abs(self.tilt)>1: fi=pygame.transform.rotate(fi,self.tilt)
        surf.blit(fi,fi.get_rect(center=self.rect.center))

    def hit(self, dmg):
        if self.invinc>0: return
        self.shield=max(0,self.shield-dmg)
        self.invinc=50
        do_shake(7,10); do_flash(RED,100); do_glitch(12); play(SFX_HIT)
        spawn_p(self.rect.centerx,self.rect.centery,CYAN,n=14,spd=5,sz=4,life=26)
        if self.shield<=0: self._die()


#Death Animation
def run_death_anim(player_cx, player_cy):
    """Full-screen death explosion over ~2 seconds."""
    play(SFX_DIE); do_shake(20,40); do_glitch(60)
    tval=pygame.time.get_ticks()*0.001
    for frame in range(120):
        CLOCK.tick(FPS)
        draw_bg(canvas,tval+frame*0.016)
        draw_top_wall(canvas,tval+frame*0.016)
        draw_bot_wall(canvas,tval+frame*0.016)
        for ring_i in range(1,4):
            r=int((frame+ring_i*15)*2.2)
            if r>0 and r<600:
                a=max(0,int(200-frame*2.5))
                rs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
                col=(255,100,0) if ring_i%2==0 else CYAN
                pygame.draw.circle(rs,(*col,a),(r,r),r,max(1,6-frame//20))
                canvas.blit(rs,(player_cx-r,player_cy-r))
        if frame<40:
            for _ in range(6):
                col=random.choice([RED,ORANGE,CYAN,YELLOW])
                spawn_p(player_cx,player_cy,col,n=3,spd=random.uniform(2,8),sz=4,life=40)
      #flash overlay
        a=max(0,int(180-frame*3))
        if a>0:
            fl=pygame.Surface((W,H),pygame.SRCALPHA); fl.fill((255,60,0,a))
            canvas.blit(fl,(0,0))
      #text
        if frame>50:
            ta=min(255,int((frame-50)*6))
            txt=font_big.render("CAPTURED",True,RED)
            ts=txt.copy(); ts.set_alpha(ta)
            canvas.blit(ts,(W//2-txt.get_width()//2,H//2-40))
        update_particles(canvas)
        draw_glitch(canvas)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()



#World 1

def world1_exit_transition(player_x, player_y):
    """Player zooms right off screen, brief dark, boss appears from right."""
    play(SFX_ESCAPE)
    px=float(player_x)
    py=float(player_y)
    spd=5.0
    tval_base=pygame.time.get_ticks() * 0.001

  #phase A
    for frame in range(80):
        CLOCK.tick(FPS)
        tv=tval_base + frame*0.016
        draw_bg(canvas, tv)
        draw_top_wall(canvas, tv)
        draw_bot_wall(canvas, tv)
        spd=min(spd + 1.8, 60)
      #speed lines
        for _ in range(int(spd * 0.6)):
            lx=random.randint(0, W)
            ly=random.randint(top_wall+6, bot_wall-6)
            pygame.draw.line(canvas, (0,200,255,random.randint(40,130)),
                             (lx,ly), (max(0,lx-random.randint(30,120)),ly), 1)
        px += spd
        if px < W + 200:
            fi=pygame.transform.rotate(player_frames[1], -22)
            canvas.blit(fi, (int(px)-48, int(py)-29))
            spawn_p(int(px)-30, int(py)+10, BLUE, n=4, spd=4, sz=3, life=16)
            spawn_p(int(px)-15, int(py)+6,  CYAN, n=2, spd=2, sz=2, life=10)
        da=min(255, frame * 4)
        ov=pygame.Surface((W,H), pygame.SRCALPHA)
        ov.fill((0,0,0,da))
        canvas.blit(ov, (0,0))
        update_particles(canvas)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()

  #phase B
    for frame in range(80):
        CLOCK.tick(FPS)
        canvas.fill((0,0,0))
        blink=(frame//8) % 2
        msgs=[
            (font_big,  "WARNING",            RED,    H//2-80),
            (font_mid,  "HUNTER CORE AI",     RED,    H//2-10),
            (font_mid,  "FINAL  FORM  ONLINE",PURPLE, H//2+40),
            (font_small,"[ Z ] to shoot    [ SPACE / ↑ ] to dodge", CYAN, H//2+100),
        ]
        for fnt, txt, col, y2 in msgs:
            if col == RED and not blink and frame < 50:
                continue
            a=min(255, frame * 5)
            s2=fnt.render(txt, True, col)
            s2.set_alpha(a)
            canvas.blit(s2, (W//2-s2.get_width()//2, y2))
        if frame > 30:
            do_flash(RED, 30)
        draw_flash(canvas)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()

  #phase C
    boss_enter_x=float(W + 200)
    boss_enter_y=float(H // 2)
    boss_enter_spd=30.0
    ring_enter=0.0
    for frame in range(80):
        CLOCK.tick(FPS)
        tv=tval_base + (160+frame)*0.016
        draw_bg(canvas, tv)
        draw_top_wall(canvas, tv)
        draw_bot_wall(canvas, tv)
        boss_enter_spd=max(2.0, boss_enter_spd * 0.88)
        boss_enter_x -= boss_enter_spd
        ring_enter += 0.04
      #boss entering from right
        bsurf=pygame.Surface((160,160), pygame.SRCALPHA)
        draw_monstrous_boss(bsurf, 80, 80, ring_enter, math.sin(frame*0.06),
                            math.sin(frame*0.05), False, boss_hp_frac=1.0)
        canvas.blit(bsurf, (int(boss_enter_x)-80, int(boss_enter_y)-80))
        if boss_enter_spd < 5 and frame > 40:
            do_shake(int(boss_enter_spd+3), 4)
        if frame > 40:
            a=min(255, (frame-40)*8)
            t1=font_big.render("WORLD  2", True, RED)
            t1.set_alpha(a); canvas.blit(t1, (W//2-t1.get_width()//2, H//2-60))
        update_particles(canvas)
        draw_flash(canvas)
        do_glitch(2) if frame > 55 else None
        draw_glitch(canvas)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()



#Boss Sprite

def draw_monstrous_boss(surf, cx, cy, ring_a, wing_t, pulse, enraged=False, boss_hp_frac=1.0):
    """
    Much larger and meaner than the world-1 boss.
    surf: surface to draw on
    cx,cy: centre on that surface
    enraged: True when HP < 30%
    """
    base_col  =(200,0,80)   if enraged else (130,0,200)
    accent_col=(255,60,0)   if enraged else (0,200,255)
    eye_col   =(255,0,0)
    glow_col  =(255,40,0)   if enraged else (170,0,255)

  #outer glow
    for r in (88,72,56,42):
        ga=int((18 + abs(pulse)*14) * (r/88))
        gs=pygame.Surface((r*2,r*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*glow_col, ga), (r,r), r)
        surf.blit(gs, (cx-r, cy-r))

  #large armoured outer shell 
    shell_pts=[]
    for i in range(16):
        ang=i*(math.tau/16) + ring_a*0.3
        rad=58 + (10 if i%2==0 else -6)
        shell_pts.append((cx+int(math.cos(ang)*rad), cy+int(math.sin(ang)*rad)))
    pygame.draw.polygon(surf, (18,0,40), shell_pts)
    pygame.draw.polygon(surf, base_col, shell_pts, 2)

  #top spikes
    for si in range(-2, 3):
        spike_ang=math.pi*1.5 + si*(math.pi/8) + math.sin(ring_a+si)*0.12
        spike_len=40 + abs(si)*6 + int(abs(pulse)*8)
        tip_x=cx + int(math.cos(spike_ang)*spike_len)
        tip_y=cy + int(math.sin(spike_ang)*spike_len)
        base_l=cx + int(math.cos(spike_ang+0.18)*30)
        base_ly=cy + int(math.sin(spike_ang+0.18)*30)
        base_r=cx + int(math.cos(spike_ang-0.18)*30)
        base_ry=cy + int(math.sin(spike_ang-0.18)*30)
        pygame.draw.polygon(surf, accent_col, [(tip_x,tip_y),(base_l,base_ly),(base_r,base_ry)])
        pygame.draw.polygon(surf, (200,200,255), [(tip_x,tip_y),(base_l,base_ly),(base_r,base_ry)], 1)

  # wings 
    for side, sy in [(-1,-1),(1,1)]:
        wf=int(wing_t * 18 * side)
      #main wing blade
        wing=[
            (cx-14, cy+side*18),
            (cx-75, cy+side*(52+wf)),
            (cx-95, cy+side*(38+wf)),
            (cx-85, cy+side*(22+wf//2)),
            (cx-50, cy+side*12),
        ]
        pygame.draw.polygon(surf, (20,0,45), wing)
        pygame.draw.polygon(surf, base_col, wing, 2)
      #neon lines on wing
        for ni in range(3):
            t_blend=ni/2
            ex=cx-14 + int(t_blend*(wing[1][0]-wing[0][0]))
            ey=cy+side*18 + int(t_blend*(wing[1][1]-cy-side*18))
            pygame.draw.line(surf, (*accent_col, 120), (cx-14,cy+side*18), wing[2], 1)
      #secondary small blade
        mini=[
            (cx-14, cy+side*8),
            (cx-55, cy+side*(68+wf)),
            (cx-45, cy+side*(78+wf)),
        ]
        pygame.draw.polygon(surf, (14,0,30), mini)
        pygame.draw.polygon(surf, (80,0,160), mini, 1)

  #three cannon barrels pointing towards left
    for di in (-22, 0, 22):
        pygame.draw.rect(surf, (14,0,35), (cx-68, cy+di-5, 42, 10), border_radius=3)
        pygame.draw.rect(surf, accent_col, (cx-68, cy+di-5, 42, 10), 1, border_radius=3)
        pygame.draw.rect(surf, accent_col, (cx-80, cy+di-2, 14, 4))
        mg=pygame.Surface((18,18), pygame.SRCALPHA)
        ma=int(100 + abs(pulse)*80)
        pygame.draw.circle(mg, (*accent_col, ma), (9,9), 8)
        surf.blit(mg, (cx-80-2, cy+di-9))

  #rotating outer ring 
    for rr, rc, rspd in [(72, accent_col, 1.0), (80, base_col, -0.7)]:
        for i in range(12):
            a=ring_a*rspd + i*(math.tau/12)
            rx=cx + int(math.cos(a)*rr)
            ry=cy + int(math.sin(a)*rr)
            pygame.draw.circle(surf, rc, (rx,ry), 3 if rr==72 else 2)
        rsurf=pygame.Surface((rr*2+4,rr*2+4), pygame.SRCALPHA)
        pygame.draw.circle(rsurf, (*rc,30), (rr+2,rr+2), rr, 1)
        surf.blit(rsurf, (cx-rr-2, cy-rr-2))

  #inner body core
    pygame.draw.circle(surf, (22,0,55), (cx,cy), 36)
    pygame.draw.circle(surf, base_col, (cx,cy), 36, 2)
    pygame.draw.circle(surf, (40,0,100), (cx,cy), 26)

    eye_r=18 + int(abs(pulse)*4)
    eg=pygame.Surface((eye_r*2+8,eye_r*2+8), pygame.SRCALPHA)
    pygame.draw.circle(eg, (*eye_col, int(100+abs(pulse)*100)), (eye_r+4,eye_r+4), eye_r+4)
    surf.blit(eg, (cx-eye_r-4, cy-eye_r-4))
    pygame.draw.circle(surf, (200,0,0), (cx,cy), eye_r)
    pygame.draw.circle(surf, (255,60,60), (cx,cy), eye_r-6)
    pygame.draw.circle(surf, (255,160,160), (cx-4,cy-4), 6)

    for i in range(12):
        a=ring_a*2 + i*(math.tau/12)
        x1=cx+int(math.cos(a)*28); y1=cy+int(math.sin(a)*28)
        x2=cx+int(math.cos(a)*36); y2=cy+int(math.sin(a)*36)
        pygame.draw.line(surf, (80,0,160), (x1,y1),(x2,y2), 2)

  #enraged visuals
    if enraged:
        for i in range(6):
            a=ring_a*3 + i*(math.tau/6)
            x1=cx+int(math.cos(a)*36); y1=cy+int(math.sin(a)*36)
            x2=cx+int(math.cos(a)*62); y2=cy+int(math.sin(a)*62)
            pygame.draw.line(surf, (255,0,60,160), (x1,y1),(x2,y2), 2)



#World 2

_boss_going_up=True

def run_boss_level(carry_score, diff_name):
    global top_wall, bot_wall, _boss_going_up
    top_wall=80; bot_wall=H - 80
    _boss_going_up=True
    d=DIFF[diff_name]

    boss_hp_max={"EASY":35,"MEDIUM":55,"HARD":90}[diff_name]
    boss_hp=boss_hp_max

    pl_x=float(-100) #sliding in
    pl_y=float(H//2)
    pl_vy=0.0
    pl_shield=100
    pl_invinc=0
    pl_up=False
    pl_shoot_cd=0
    pl_entering=True  

    bs_x=float(W - 160)
    bs_y=float(H//2)
    ring_a=0.0
    wing_t=0.0
    wing_d=1
    bs_pulse=0.0
    bs_atk_timer=60 
    bs_atk_cd={"EASY":38,"MEDIUM":26,"HARD":18}[diff_name]
    bs_bullet_spd={"EASY":7.5,"MEDIUM":9.5,"HARD":12.0}[diff_name]
    bs_speed=d["boss_speed"] * 0.85
    bs_rage_cd=0    #cool down

    player_bullets=[]
    boss_projs=[]
    emp_rings_bl=[]

    particles_bl=[]

    def spawn_bl(x,y,col,n=6,spd=4,sz=3,life=24):
        for _ in range(n):
            a=random.uniform(0,math.tau); v=random.uniform(0.3,spd)
            particles_bl.append([float(x),float(y),math.cos(a)*v,math.sin(a)*v,
                                  list(col[:3]),life,life,sz])

    def update_bl(surf):
        dead=[]
        for p in particles_bl:
            p[0]+=p[2]; p[1]+=p[3]; p[3]+=0.05
            p[2]*=0.97; p[3]*=0.97; p[5]-=1
            if p[5]<=0: dead.append(p); continue
            a=int(255*p[5]/p[6]); sz2=max(1,int(p[7]*p[5]/p[6]))
            ps=pygame.Surface((sz2*2,sz2*2),pygame.SRCALPHA)
            pygame.draw.circle(ps,(*p[4][:3],a),(sz2,sz2),sz2)
            surf.blit(ps,(int(p[0])-sz2,int(p[1])-sz2))
        for p in dead:
            try: particles_bl.remove(p)
            except: pass

    def fire_boss_proj(btype):
        fire_x=bs_x - 80 
        fire_y=bs_y
      #aim directly at player 
        dx=pl_x - fire_x 
        dy=pl_y - fire_y
        dist=max(1, math.hypot(dx,dy))
        base_spd=bs_bullet_spd * (1.0 if btype=="bullet" else 0.65 if btype=="net" else 0.8)
        spread=random.uniform(-0.15, 0.15)
        vx=(dx/dist) * base_spd * (1+spread)
        vy=(dy/dist) * base_spd * (1+random.uniform(-0.2,0.2))
        boss_projs.append({
            "x": float(fire_x), "y": float(fire_y),
            "vx": vx, "vy": vy,
            "type": btype, "rot": 0.0, "life": 200
        })

    def draw_boss_proj(surf, p):
        col=ORANGE if p["type"]=="mine" else (RED if p["type"]=="laser_ball" else PURPLE)
        glo=pygame.Surface((56,56),pygame.SRCALPHA)
        pygame.draw.circle(glo,(*col,55),(28,28),26)
        surf.blit(glo,(int(p["x"])-28,int(p["y"])-28))
        pygame.draw.circle(surf,col,(int(p["x"]),int(p["y"])),10,0)
        if p["type"]=="net":
            for i in range(6):
                a=i*(math.tau/6)+p["rot"]
                pygame.draw.line(surf,col,
                    (int(p["x"]),int(p["y"])),
                    (int(p["x"]+math.cos(a)*14),int(p["y"]+math.sin(a)*14)),1)
            pygame.draw.circle(surf,col,(int(p["x"]),int(p["y"])),14,1)
        elif p["type"]=="laser_ball":
          #spinning cross laser ball
            for i in range(4):
                a=i*(math.tau/4)+p["rot"]*2
                pygame.draw.line(surf,col,
                    (int(p["x"]),int(p["y"])),
                    (int(p["x"]+math.cos(a)*18),int(p["y"]+math.sin(a)*18)),2)

    def draw_player_bullet(surf, b):
        glo=pygame.Surface((52,18),pygame.SRCALPHA)
        pygame.draw.ellipse(glo,(0,220,255,80),(0,0,52,18))
        surf.blit(glo,(int(b["x"])-26,int(b["y"])-9))
        pygame.draw.rect(surf,PURPLE,(int(b["x"])-20,int(b["y"])-3,40,6))
        pygame.draw.rect(surf,(200,255,255),(int(b["x"])-10,int(b["y"])-2,20,4))
        ng=pygame.Surface((16,16),pygame.SRCALPHA)
        pygame.draw.circle(ng,(0,255,255,160),(8,8),7)
        surf.blit(ng,(int(b["x"])+18,int(b["y"])-8))

    def draw_pl(surf, x, y, invinc, up, vy):
        if invinc>0 and (invinc//4)%2==1: return
        tilt=-vy*2.5; tilt=max(-25,min(25,tilt))
        fi=player_frames[1 if up else (2 if vy>1 else 0)]
        if abs(tilt)>1: fi=pygame.transform.rotate(fi,tilt)
        surf.blit(fi,fi.get_rect(center=(int(x),int(y))))

    start_boss_bgm()

    game_running=True
    result="captured"
    frame_count=0

    while game_running:
        CLOCK.tick(FPS)
        tval=pygame.time.get_ticks() * 0.001
        frame_count += 1

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: pygame.quit();sys.exit()
                if ev.key in (pygame.K_UP,pygame.K_SPACE):
                    pl_up=True
                if ev.key==pygame.K_z and pl_shoot_cd<=0:
                    player_bullets.append({
                        "x": pl_x+50, "y": pl_y-5,
                        "vx": 16+random.uniform(0,2)
                    })
                    play(SFX_SHOOT)
                    pl_shoot_cd=16
            if ev.type==pygame.KEYUP:
                if ev.key in (pygame.K_UP,pygame.K_SPACE):
                    pl_up=False
        if pl_entering:
            pl_x=min(pl_x+14, 130.0)
            if pl_x >= 130.0:
                pl_entering=False
            pl_vy=0.0
        else:
          #normal gravity
            if pl_up: pl_vy += -0.62
            pl_vy += 0.30; pl_vy=max(-9,min(9,pl_vy)); pl_vy*=0.90
            pl_y += pl_vy
            if pl_y-29 < top_wall:
                pl_y=top_wall+29; pl_vy=abs(pl_vy)*0.25
                result="captured"; game_running=False
            if pl_y+29 > bot_wall:
                pl_y=bot_wall-29; pl_vy=-abs(pl_vy)*0.25
                result="captured"; game_running=False
        if pl_invinc>0: pl_invinc-=1
        if pl_shoot_cd>0: pl_shoot_cd-=1

      #boss vertically
        bs_y += -bs_speed if _boss_going_up else bs_speed
        if bs_y-70 <= top_wall+5:
            _boss_going_up=False; bs_y=top_wall+75
        if bs_y+70 >= bot_wall-5:
            _boss_going_up=True;  bs_y=bot_wall-75
      #boss also tracks player a bit
        bs_y += (pl_y - bs_y) * 0.008

        ring_a+=0.028
        bs_pulse=math.sin(tval*7)
        wing_t+=0.06*wing_d
        if abs(wing_t)>1.0: wing_d*=-1

      #boss attacks 
        enraged=boss_hp < boss_hp_max * 0.40
        bs_atk_timer+=1
        effective_cd=bs_atk_cd // 2 if enraged else bs_atk_cd
        if bs_atk_timer >= effective_cd:
            bs_atk_timer=0
            if enraged:
              #rage mode
                for spread in (-0.35, 0.0, 0.35):
                    dx=pl_x - (bs_x-80); dy=pl_y - bs_y
                    dist=max(1,math.hypot(dx,dy))
                    spd3=bs_bullet_spd * 1.15
                    boss_projs.append({
                        "x":float(bs_x-80),"y":float(bs_y),
                        "vx":(dx/dist)*spd3,
                        "vy":(dy/dist)*spd3 + spread*spd3,
                        "type":"laser_ball","rot":0.0,"life":180
                    })
                do_shake(3,4); do_flash(RED,50)
                spawn_bl(bs_x,bs_y,RED,n=8,spd=3,sz=2,life=18)
            else:
                atype=random.choice(["bullet","bullet","bullet","net","net","emp","laser_ball"])
                if atype in ("bullet","net","laser_ball"):
                    fire_boss_proj(atype)
                  #medium and hard also fire a second angled shot
                    if diff_name in ("MEDIUM","HARD") and atype=="bullet":
                        old_pl_y=pl_y
                      #temporarily aim slightly above
                        import types
                        fire_boss_proj("laser_ball")
                elif atype=="emp":
                    emp_rings_bl.append({
                        "cx":float(bs_x-80),"cy":float(bs_y),
                        "r":8.0,"spd":6.0,"life":85
                    })
            play(SFX_SPAWN)

      #update player bullets
        for b in player_bullets[:]:
            b["x"]+=b["vx"]
            if b["x"]>W+30:
                player_bullets.remove(b); continue
          #hit boss
            if abs(b["x"]-bs_x)<75 and abs(b["y"]-bs_y)<75:
                player_bullets.remove(b)
                boss_hp-=1
                play(SFX_BOSS_HIT)
                spawn_bl(bs_x-30+random.randint(-20,20),
                         bs_y+random.randint(-20,20),
                         ORANGE,n=10,spd=6,sz=4,life=28)
                do_shake(5,6)
                do_flash(ORANGE,55)
                if boss_hp<=0:
                  #Boss Destroyed
                    stop_bgm()
                    play(SFX_DIE)
                    do_shake(22,50); do_glitch(60); do_flash(ORANGE,220)
                  #destruction loop
                    for dframe in range(180):
                        CLOCK.tick(FPS)
                        dtval=pygame.time.get_ticks()*0.001
                        draw_bg(canvas,dtval)
                        draw_top_wall(canvas,dtval); draw_bot_wall(canvas,dtval)
                      #draw player 
                        draw_pl(canvas,pl_x,pl_y,0,False,0)
                      #exploding boss
                        for ring_i in range(1,5):
                            rr=int((dframe*2.5+ring_i*25))
                            if rr<400:
                                a_ring=max(0,int(200-dframe*1.8))
                                rs2=pygame.Surface((rr*2,rr*2),pygame.SRCALPHA)
                                rcol=(255,100,0) if ring_i%2==0 else (255,0,80)
                                pygame.draw.circle(rs2,(*rcol,a_ring),(rr,rr),rr,max(1,5-dframe//40))
                                canvas.blit(rs2,(int(bs_x)-rr,int(bs_y)-rr))
                      #debris particles
                        if dframe < 80:
                            for _ in range(8):
                                dcol=random.choice([ORANGE,RED,YELLOW,(255,200,0)])
                                spawn_bl(bs_x+random.randint(-60,60),
                                         bs_y+random.randint(-50,50),
                                         dcol,n=2,spd=random.uniform(3,9),sz=random.randint(2,5),life=40)
                      #flickering broken boss
                        if dframe<100:
                            scale=max(0.1, 1.0-dframe/100)
                            bsize=int(200*scale)
                            if bsize>10:
                                bsurf2=pygame.Surface((bsize,bsize),pygame.SRCALPHA)
                                cx2=bsize//2; cy2=bsize//2
                                if (dframe//6)%2==0:
                                    pygame.draw.circle(bsurf2,(200,50,0),( cx2,cy2),bsize//3)
                                    pygame.draw.circle(bsurf2,(255,100,0),(cx2,cy2),bsize//5)
                                    pygame.draw.circle(bsurf2,(255,200,0),(cx2,cy2),bsize//8)
                                canvas.blit(bsurf2,(int(bs_x)-bsize//2,int(bs_y)-bsize//2))
                        if dframe<40:
                            fa2=max(0,int(180-dframe*5))
                            fl2=pygame.Surface((W,H),pygame.SRCALPHA)
                            fl2.fill((255,80,0,fa2)); canvas.blit(fl2,(0,0))
                        if dframe>60:
                            ta=min(255,int((dframe-60)*5))
                            bt=font_big.render("BOSS  DESTROYED",True,ORANGE)
                            bt.set_alpha(ta)
                            canvas.blit(bt,(W//2-bt.get_width()//2,H//2-50))
                        update_bl(canvas)
                        draw_glitch(canvas)
                        do_shake(max(0,14-dframe//8),4)
                        ox2,oy2=get_shake()
                        if ox2 or oy2:
                            cp2=canvas.copy(); canvas.fill(BG); canvas.blit(cp2,(ox2,oy2))
                        pygame.display.update()
                        for ev in pygame.event.get():
                            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                    result="escaped"; game_running=False
                continue

        for p in boss_projs[:]:
            p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["life"]-=1
            p["rot"]+=0.09
            if p["life"]<=0 or p["x"]<-30 or p["y"]<top_wall-20 or p["y"]>bot_wall+20:
                boss_projs.remove(p); continue
            if pl_invinc<=0 and abs(p["x"]-pl_x)<34 and abs(p["y"]-pl_y)<34:
                boss_projs.remove(p)
                pl_shield=max(0,pl_shield-d["dmg_proj"])
                pl_invinc=55
                do_shake(7,9); do_flash(RED,100); play(SFX_HIT)
                spawn_bl(pl_x,pl_y,RED,n=12,spd=5,sz=3,life=26)
                if pl_shield<=0:
                    result="captured"; game_running=False

        for er in emp_rings_bl[:]:
            er["r"]+=er["spd"]; er["life"]-=1
            if er["life"]<=0 or er["r"]>max(W,H): emp_rings_bl.remove(er); continue
            if pl_invinc<=0:
                dist=math.hypot(er["cx"]-pl_x,er["cy"]-pl_y)
                if abs(dist-er["r"])<18:
                    pl_shield=max(0,pl_shield-d["dmg_emp"])
                    pl_invinc=55
                    do_shake(5,8); do_flash(PURPLE,90); play(SFX_EMP)
                    if pl_shield<=0:
                        result="captured"; game_running=False

      #draw
        draw_bg(canvas, tval)
      #red glow behind boss
        bga=pygame.Surface((W,H),pygame.SRCALPHA)
        bga.fill((60,0,0, int(20+abs(bs_pulse)*15)))
        canvas.blit(bga,(0,0))

        draw_top_wall(canvas, tval)
        draw_bot_wall(canvas, tval)

        for er in emp_rings_bl:
            ir=int(er["r"])
            if ir>2:
                a=int(155*er["life"]/85)
                rs=pygame.Surface((ir*2+6,ir*2+6),pygame.SRCALPHA)
                pygame.draw.circle(rs,(170,0,255,a),(ir+3,ir+3),ir,3)
                canvas.blit(rs,(int(er["cx"])-ir-3,int(er["cy"])-ir-3))

      #boss projectiles
        for p in boss_projs:
            draw_boss_proj(canvas,p)

      #player bullets
        for b in player_bullets:
            draw_player_bullet(canvas,b)

        bsurf=pygame.Surface((200,200),pygame.SRCALPHA)
        draw_monstrous_boss(bsurf, 100, 100, ring_a, wing_t, bs_pulse, enraged, boss_hp/boss_hp_max)
        canvas.blit(bsurf,(int(bs_x)-100,int(bs_y)-100))

        draw_pl(canvas, pl_x, pl_y, pl_invinc, pl_up, pl_vy)
      #player engine trail
        if not pl_entering:
            spawn_bl(int(pl_x)+42, int(pl_y)+10, BLUE, n=2,spd=2,sz=2,life=12)

        update_bl(canvas)

        tb=pygame.Surface((W,top_wall),pygame.SRCALPHA); tb.fill((0,0,8,220))
        canvas.blit(tb,(0,0))
        pygame.draw.line(canvas,RED,(0,top_wall),(W,top_wall),1)

        sc=font_hud.render("SHIELD",True,CYAN); canvas.blit(sc,(12,8))
        shw=130; pygame.draw.rect(canvas,(30,0,20),(12,30,shw,8))
        sfw=max(0,int(shw*pl_shield/100))
        sbc=(0,210,80) if pl_shield>60 else (255,170,0) if pl_shield>30 else RED
        if sfw>0: pygame.draw.rect(canvas,sbc,(12,30,sfw,8))
        pygame.draw.rect(canvas,CYAN,(12,30,shw,8),1)

      #boss HP 
        bhlbl=font_hud.render("BOSS HP",True,RED); canvas.blit(bhlbl,(W-155,8))
        bhw=130; seg=bhw//boss_hp_max
        pygame.draw.rect(canvas,(25,0,10),(W-155,30,bhw,8))
        for i in range(boss_hp):
            sc2=RED if boss_hp<boss_hp_max*0.3 else (255,80,0) if boss_hp<boss_hp_max*0.6 else (255,200,0)
            pygame.draw.rect(canvas,sc2,(W-155+i*seg,30,max(1,seg-1),8))
        pygame.draw.rect(canvas,RED,(W-155,30,bhw,8),1)

        wl=font_tiny.render("WORLD 2  —  FINAL BOSS  —  Z to shoot  UP/SPACE to dodge",True,
                             (255,60,60) if enraged else PURPLE)
        canvas.blit(wl,(W//2-wl.get_width()//2,18))
        if enraged:
            blink2=(frame_count//6)%2
            if blink2:
                er_txt=font_hud.render("⚠ ENRAGED ⚠",True,RED)
                canvas.blit(er_txt,(W//2-er_txt.get_width()//2,top_wall+8))

        bb=pygame.Surface((W,H-bot_wall),pygame.SRCALPHA); bb.fill((8,0,0,200))
        canvas.blit(bb,(0,bot_wall))
        pygame.draw.line(canvas,RED,(0,bot_wall),(W,bot_wall),1)

        draw_flash(canvas)
        ox,oy=get_shake()
        if ox or oy:
            cp=canvas.copy(); canvas.fill(BG); canvas.blit(cp,(ox,oy))
        pygame.display.update()

    stop_bgm()
    top_wall=80; bot_wall=H-80

    if result=="captured":
        game_over_flag[0]=True
        game_over_flag[1]=int(pl_x); game_over_flag[2]=int(pl_y)
        game_over()
    return result



# escape animation

def run_escape_anim(score, start_x=None, start_y=None):
    play(SFX_ESCAPE)
    do_shake(18, 25)
    do_glitch(40)
    do_flash(CYAN, 160)

    px=float(start_x if start_x else W*0.8)
    py=float(start_y if start_y else H//2)
    spd=4.0
    tval_base=pygame.time.get_ticks()*0.001

    for frame in range(260):
        CLOCK.tick(FPS)
        tval=tval_base + frame*0.016
        draw_bg(canvas, tval)
        draw_top_wall(canvas, tval)
        draw_bot_wall(canvas, tval)

        spd=min(spd + 1.4, 55)

      #horizontal speed lines 
        line_count=int(spd * 0.7)
        for _ in range(line_count):
            lx=random.randint(0, W)
            ly=random.randint(top_wall+8, bot_wall-8)
            le=random.randint(30, 140)
            la=random.randint(50, 160)
            pygame.draw.line(canvas,(0,200,255,la),(lx,ly),(max(0,lx-le),ly),1)

        px += spd
        if px < W + 150:
            fi=pygame.transform.rotate(player_frames[1], -22)
            canvas.blit(fi, (int(px)-48, int(py)-29))
          #big jet trail behind it
            spawn_p(int(px)-30, int(py)+10, BLUE, n=4, spd=4, sz=4, life=18)
            spawn_p(int(px)-20, int(py)+6,  CYAN, n=2, spd=2, sz=2, life=10)
        if frame < 50:
            for _ in range(3):
                spawn_p(random.randint(0,W), random.choice([top_wall,bot_wall]),
                        CYAN, n=4, spd=5, sz=3, life=22)
        if frame < 80:
            spawn_p(random.randint(18,130), random.randint(top_wall+10,bot_wall-10),
                    ORANGE, n=2, spd=6, sz=3, life=16)

        if frame > 80:
            oa=min(200, int((frame-80)*3.2))
            ov=pygame.Surface((W,H), pygame.SRCALPHA)
            ov.fill((0,0,5,oa))
            canvas.blit(ov,(0,0))

      #escaped successfully
        if frame > 95:
            ta=min(255, int((frame-95)*5))
            gw=pygame.Surface((700,90), pygame.SRCALPHA)
            gw.fill((0,180,255, min(60, ta//4)))
            canvas.blit(gw, (W//2-350, H//2-80))
            t1=font_big.render("ESCAPED  SUCCESSFULLY", True, CYAN)
            t1s=t1.copy(); t1s.set_alpha(ta)
            canvas.blit(t1s, (W//2-t1.get_width()//2, H//2-68))

        if frame > 130:
            ta2=min(255, int((frame-130)*5))
            t2=font_mid.render("HUNTER  CORE  DESTROYED", True, PURPLE)
            t2s=t2.copy(); t2s.set_alpha(ta2)
            canvas.blit(t2s, (W//2-t2.get_width()//2, H//2+2))

        if frame > 160:
            ta3=min(255, int((frame-160)*6))
            t3=font_hud.render(f"FINAL  SCORE  :  {score:05d}", True, GREEN)
            t3s=t3.copy(); t3s.set_alpha(ta3)
            canvas.blit(t3s, (W//2-t3.get_width()//2, H//2+58))

        if frame > 200:
            ta4=min(255, int((frame-200)*8))
            t4=font_small.render("PRESS  ANY  KEY  TO  PLAY  AGAIN", True, (150,150,160))
            t4s=t4.copy(); t4s.set_alpha(ta4)
            canvas.blit(t4s, (W//2-t4.get_width()//2, H//2+105))

        update_particles(canvas)
        draw_flash(canvas)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
    while True:
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: pygame.quit();sys.exit()
                main_menu(); return
        pygame.time.wait(16)

#intro
def run_intro(boss_obj, player_obj):
    for t in range(300):
        CLOCK.tick(FPS)
        tval=pygame.time.get_ticks()*0.001
        draw_bg(canvas,tval)
        boss_obj.rect.left=max(18,boss_obj.rect.left-max(1,int((boss_obj.rect.left-18)*0.04)))
        boss_obj.pulse=math.sin(t*0.05); boss_obj.ring_a+=0.02
        boss_obj.wing_t=math.sin(t*0.04)
        boss_obj.draw(canvas)
        player_obj.vy=0; player_obj.boost_frame=0; player_obj.draw(canvas)
        if t<90:
            a=min(255,t*3)
            m=font_mid.render("HUNTER  CORE  AI  —  ONLINE",True,CYAN)
            ms=m.copy(); ms.set_alpha(a)
            canvas.blit(ms,(W//2-m.get_width()//2,H//2-50))
        elif t<190:
            a=min(255,(t-90)*3)
            m1=font_mid.render("THREAT LEVEL :  MAXIMUM",True,PURPLE)
            m2=font_small.render("SURVIVAL PROBABILITY :  2.4 %",True,RED)
            for m,dy in [(m1,-40),(m2,12)]:
                mc=m.copy(); mc.set_alpha(a); canvas.blit(mc,(W//2-m.get_width()//2,H//2+dy))
        else:
            if (t//8)%2:
                al=font_big.render("⚠  ALARM  ACTIVATED  ⚠",True,RED)
                canvas.blit(al,(W//2-al.get_width()//2,H//2-34))
            do_flash(RED,28)
        draw_top_wall(canvas,tval); draw_bot_wall(canvas,tval)
        draw_hud(canvas,0,get_hi(),100,"PHASE 1 — SPEED SURVIVAL",chosen_diff)
        draw_flash(canvas)
        pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                pygame.quit();sys.exit()
    do_shake(16,22); do_glitch(35); do_flash(RED,200)


#Game Over

game_over_flag=[False, W-80, H//2] 

def game_over():
    global SCORE, top_wall, bot_wall
    stop_bgm(); update_hi(SCORE)
    px=game_over_flag[1]; py=game_over_flag[2]
    top_wall=80
    bot_wall=H - 80
    run_death_anim(px,py)
    while True:
        CLOCK.tick(FPS)
        tval=pygame.time.get_ticks()*0.001
        draw_bg(canvas,tval)
        draw_top_wall(canvas,tval); draw_bot_wall(canvas,tval)
        ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,175)); canvas.blit(ov,(0,0))
        t1=font_big.render("CAPTURED",True,RED)
        t2=font_mid.render(f"SCORE  {SCORE:05d}      HI  {get_hi():05d}",True,CYAN)
        t3=font_small.render("[ R ]  Retry     [ M ]  Main Menu     [ ESC ]  Quit",True,(170,170,170))
        canvas.blit(t1,(W//2-t1.get_width()//2,H//2-90))
        canvas.blit(t2,(W//2-t2.get_width()//2,H//2-10))
        canvas.blit(t3,(W//2-t3.get_width()//2,H//2+55))
        draw_glitch(canvas); pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: pygame.quit();sys.exit()
                if ev.key==pygame.K_r: game_loop()
                if ev.key==pygame.K_m: main_menu()
        pygame.time.wait(16)


#Instructions Screen

def instructions_screen():
    lines=[
        ("NEON ESCAPE  —  HOW TO PLAY", font_mid, CYAN, 0),
        ("", font_small, WHITE, 14),
        ("CONTROLS", font_hud, PURPLE, 0),
        ("   Arrow / SPACE  —  Jet boost upward", font_small, WHITE, 0),
        ("  Release          —  Fall (gravity always on)", font_small, WHITE, 0),
        ("  ESC              —  Quit", font_small, (150,150,150), 10),
        ("PHASE 1  —  SPEED SURVIVAL", font_hud, CYAN, 0),
        ("  The Hunter Core AI fires projectiles from the LEFT.", font_small, WHITE, 0),
        ("  Projectiles start slow, grow faster as your score rises.", font_small, WHITE, 0),
        ("  Survive long enough and the boss enters PHASE 2.", font_small, WHITE, 10),
        ("PHASE 2  —  CONSTRICTION", font_hud, PURPLE, 0),
        ("  The ceiling drops and the floor rises — space shrinks!", font_small, WHITE, 0),
        ("  Walls stop at a safe minimum — it stays beatable.", font_small, WHITE, 0),
        ("  Survive the final assault phase to ESCAPE.", font_small, WHITE, 10),
        ("ATTACKS", font_hud, CYAN, 0),
        ("  Plasma Net  — rotating hex grid, hard to dodge", font_small, WHITE, 0),
        ("  Energy Bullet — fast cyan dart (Phase 1 main attack)", font_small, WHITE, 0),
        ("  Energy Mine — slow but explosive on contact", font_small, WHITE, 0),
        ("  Laser Beam  — full-width, warned in advance (Phase 2+)", font_small, WHITE, 0),
        ("  EMP Ring    — expanding shockwave ring (Phase 2+)", font_small, WHITE, 10),
        ("DIFFICULTY", font_hud, PURPLE, 0),
        ("  EASY   — slow projectiles, low max speed, shallow constriction", font_small, (100,255,100), 0),
        ("  MEDIUM — balanced challenge, moderate speed ramp", font_small, YELLOW, 0),
        ("  HARD   — fast from the start, deep constriction, high damage", font_small, (255,80,80), 10),
        ("[ BACKSPACE ]  or  [ ESC ]  to return", font_small, (150,150,150), 0),
    ]
    scroll=0; target_scroll=0
    while True:
        CLOCK.tick(FPS)
        tval=pygame.time.get_ticks()*0.001
        draw_bg(canvas,tval)
        ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,15,220)); canvas.blit(ov,(0,0))
        y=60+scroll
        for text,font2,col,extra_pad in lines:
            if text:
                s=font2.render(text,True,col)
                canvas.blit(s,(W//2-s.get_width()//2,y))
                y+=s.get_height()+6
            else:
                y+=12
            y+=extra_pad
      #fade at top and bottom
        for edge,edy in [(0,0),(H-60,H)]:
            fd=pygame.Surface((W,60),pygame.SRCALPHA)
            for row in range(60):
                a=int(200*(1-row/60)) if edy==0 else int(200*row/60)
                fd.fill((0,0,0,a),(0,row,W,1))
            canvas.blit(fd,(0,edge))
        pg=font_small.render("SCROLL  ↑ ↓  or  MOUSE WHEEL",True,(80,80,80))
        canvas.blit(pg,(W//2-pg.get_width()//2,H-22))
        draw_glitch(canvas); pygame.display.update()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE,pygame.K_BACKSPACE): return
                if ev.key==pygame.K_UP: scroll+=30
                if ev.key==pygame.K_DOWN: scroll-=30
            if ev.type==pygame.MOUSEWHEEL: scroll+=ev.y*22


#Main Menu

def draw_menu_btn(surf, rect, label, col, selected, hovered, t_pulse=0):
    """Draw a polished neon button with glow on select/hover."""
    bx2,by2,bw2,bh2=rect.x,rect.y,rect.w,rect.h
    glow_a=int(70+40*abs(math.sin(t_pulse*0.06))) if selected else (35 if hovered else 0)
    if glow_a>0:
        gs=pygame.Surface((bw2+16,bh2+16),pygame.SRCALPHA)
        pygame.draw.rect(gs,(*col,glow_a),(0,0,bw2+16,bh2+16),border_radius=10)
        surf.blit(gs,(bx2-8,by2-8))
    pygame.draw.rect(surf,(14,4,35),rect,border_radius=7)
    border_col=col if (selected or hovered) else tuple(max(0,c//3) for c in col)
    bw_px=2 if selected else (1 if hovered else 1)
    pygame.draw.rect(surf,border_col,rect,bw_px,border_radius=7)
    txt_col=WHITE if selected else (col if hovered else tuple(max(60,c//2+40) for c in col))
    bt=font_mid.render(label,True,txt_col)
    surf.blit(bt,(bx2+bw2//2-bt.get_width()//2, by2+bh2//2-bt.get_height()//2))

def main_menu():
    global chosen_diff, top_wall, bot_wall, VOL_MASTER
  #reset walls
    top_wall=80
    bot_wall=H - 80
    diff_options=["EASY","MEDIUM","HARD"]
    diff_cols={"EASY":(60,220,80),"MEDIUM":(255,210,0),"HARD":(255,70,70)}
    diff_sel=diff_options.index(chosen_diff)

    NAV=6; nav_sel=diff_sel 

    t=0
    mouse_pos=(0,0)
    start_menu_bgm()
  #default rect for vol bar 
    vbar_x=W//2-160; vbar_w=320
    vol_bar_rect=pygame.Rect(vbar_x, 0, vbar_w, 20) 

    while True:
        CLOCK.tick(FPS)
        tval=t * 0.016

        draw_bg(canvas, tval)
        draw_top_wall(canvas, tval)
        draw_bot_wall(canvas, tval)

        cy=H // 2 

        panel_w=540; panel_h=420
        panel_x=W//2 - panel_w//2
        panel_y=cy - panel_h//2
        panel=pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 12, 175))
        pygame.draw.rect(panel, (60, 0, 120, 180), (0,0,panel_w,panel_h), 1)
        canvas.blit(panel, (panel_x, panel_y))

        hue=int(100 + 155*abs(math.sin(t*0.025)))
        ti=font_big.render("NEON  ESCAPE", True, (hue, 0, 255))
        canvas.blit(ti, (W//2 - ti.get_width()//2, panel_y + 18))

        su=font_mid.render("CYBERPUNK  ARCADE  SURVIVAL", True, CYAN)
        canvas.blit(su, (W//2 - su.get_width()//2, panel_y + 76))

        div_y=panel_y + 110
        pygame.draw.line(canvas, (60, 0, 130), (W//2-200, div_y), (W//2+200, div_y), 1)

        hs_y=div_y + 10
        for di, dn in enumerate(diff_options):
            dc=diff_cols[dn]
            hi_val=hi_scores.get(dn, 0)
            active=di == diff_sel
            hs_s=font_tiny.render(f"{dn}  HI:{hi_val:05d}", True,
                                    dc if active else tuple(c//3 for c in dc))
            hsx=W//2 + (di-1)*170 - hs_s.get_width()//2
            canvas.blit(hs_s, (hsx, hs_y))

        DBW=158; DBH=46; DB_GAP=12
        db_total=3*DBW + 2*DB_GAP
        db_x0=W//2 - db_total//2
        db_y=hs_y + 24
        diff_rects=[]
        for i, opt in enumerate(diff_options):
            col=diff_cols[opt]
            r=pygame.Rect(db_x0 + i*(DBW+DB_GAP), db_y, DBW, DBH)
            diff_rects.append(r)
            draw_menu_btn(canvas, r, opt, col, i==diff_sel, r.collidepoint(mouse_pos), t)

      #thin divider
        div2_y=db_y + DBH + 14
        pygame.draw.line(canvas, (60, 0, 130), (W//2-200, div2_y), (W//2+200, div2_y), 1)

      # action buttons 
        ABW=300; ABH=46; ab_gap=10
        ab_y0=div2_y + 12
        start_rect=pygame.Rect(W//2-ABW//2, ab_y0,                  ABW, ABH)
        instr_rect=pygame.Rect(W//2-ABW//2, ab_y0 + ABH + ab_gap,   ABW, ABH)
        quit_rect =pygame.Rect(W//2-ABW//2, ab_y0 + (ABH+ab_gap)*2, ABW, ABH)
        action_rects =[start_rect, instr_rect, quit_rect]
        action_labels=["START  GAME", "INSTRUCTIONS", "QUIT"]
        action_cols  =[GREEN, CYAN, (120,120,120)]

        for ai, (ar, al, ac) in enumerate(zip(action_rects, action_labels, action_cols)):
            draw_menu_btn(canvas, ar, al, ac, nav_sel==(3+ai), ar.collidepoint(mouse_pos), t)

        vol_y=panel_y + panel_h - 30
        vl=font_tiny.render("VOL", True, (100,100,120))
        canvas.blit(vl, (W//2-190, vol_y+2))
      #volume bar
        vbar_x=W//2-160; vbar_w=320; vbar_h=10
        pygame.draw.rect(canvas,(15,0,35),(vbar_x,vol_y,vbar_w,vbar_h),border_radius=4)
        vfill=int(vbar_w*VOL_MASTER)
        pygame.draw.rect(canvas,CYAN,(vbar_x,vol_y,vfill,vbar_h),border_radius=4)
        pygame.draw.rect(canvas,(60,0,130),(vbar_x,vol_y,vbar_w,vbar_h),1,border_radius=4)
      #knob
        knob_x=vbar_x+vfill; knob_y=vol_y+vbar_h//2
        pygame.draw.circle(canvas,WHITE,(knob_x,knob_y),6)
        pygame.draw.circle(canvas,CYAN,(knob_x,knob_y),6,2)
      #- and + labels
        vm=font_hud.render("-",True,(80,80,100)); canvas.blit(vm,(W//2-182,vol_y-2))
        vp=font_hud.render("+",True,(80,80,100)); canvas.blit(vp,(W//2+168,vol_y-2))
        vval=font_tiny.render(f"{int(VOL_MASTER*100)}%",True,WHITE)
        canvas.blit(vval,(W//2+4,vol_y-10))
        vol_bar_rect=pygame.Rect(vbar_x,vol_y-4,vbar_w,vbar_h+8)
        boss_cx=panel_x - 90
        boss_cy=cy + int(math.sin(t*0.04)*12)
        draw_boss(canvas, boss_cx-55, boss_cy-55, t*0.022, math.sin(t*0.04), math.sin(t*0.05))

        pf=player_frames[1 if (t//22)%2==0 else 0]
        player_x=panel_x + panel_w + 30
        player_y=cy - pf.get_height()//2 + int(math.sin(t*0.04 + 1)*8)
        canvas.blit(pf, (player_x, player_y))

        if t%80<5: do_glitch(4)
        draw_glitch(canvas)
        pygame.display.update()
        t += 1

      # handle mouse cursor
        all_clickable=diff_rects+action_rects
        if any(r.collidepoint(mouse_pos) for r in all_clickable):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.MOUSEMOTION:
                mouse_pos=ev.pos
                if ev.buttons[0] and vol_bar_rect.collidepoint(ev.pos):
                    VOL_MASTER=max(0.0,min(1.0,(ev.pos[0]-vbar_x)/vbar_w))
                    apply_volume()
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                mp=ev.pos
              #volume bar click
                if vol_bar_rect.collidepoint(mp):
                    VOL_MASTER=max(0.0,min(1.0,(mp[0]-vbar_x)/vbar_w))
                    apply_volume(); play_ui(SFX_UI_CLICK)

                for i,dr in enumerate(diff_rects):
                    if dr.collidepoint(mp):
                        diff_sel=i; chosen_diff=diff_options[i]; nav_sel=i
                        play_ui(SFX_UI_CLICK)
                if start_rect.collidepoint(mp):
                    play_ui(SFX_UI_SELECT)
                    chosen_diff=diff_options[diff_sel]; stop_bgm(); game_loop(); return
                if instr_rect.collidepoint(mp):
                    play_ui(SFX_UI_CLICK); instructions_screen()
                if quit_rect.collidepoint(mp):
                    pygame.quit(); sys.exit()

            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: pygame.quit();sys.exit()
              #[ and ] keys adjust volume
                if ev.key==91:  #[
                    VOL_MASTER=max(0.0,VOL_MASTER-0.1); apply_volume(); play_ui(SFX_UI_CLICK)
                if ev.key==93:  #]
                    VOL_MASTER=min(1.0,VOL_MASTER+0.1); apply_volume(); play_ui(SFX_UI_CLICK)
                if ev.key in (pygame.K_LEFT,pygame.K_a):
                    diff_sel=(diff_sel-1)%3; chosen_diff=diff_options[diff_sel]; nav_sel=diff_sel
                    play_ui(SFX_UI_CLICK)
                if ev.key in (pygame.K_RIGHT,pygame.K_d):
                    diff_sel=(diff_sel+1)%3; chosen_diff=diff_options[diff_sel]; nav_sel=diff_sel
                    play_ui(SFX_UI_CLICK)
                if ev.key in (pygame.K_UP,pygame.K_w):
                    nav_sel=(nav_sel-1)%NAV
                    if nav_sel<3: diff_sel=nav_sel; chosen_diff=diff_options[diff_sel]
                    play_ui(SFX_UI_CLICK)
                if ev.key in (pygame.K_DOWN,pygame.K_s):
                    nav_sel=(nav_sel+1)%NAV
                    if nav_sel<3: diff_sel=nav_sel; chosen_diff=diff_options[diff_sel]
                    play_ui(SFX_UI_CLICK)
                if ev.key in (pygame.K_RETURN,pygame.K_SPACE):
                    play_ui(SFX_UI_SELECT)
                    if nav_sel<3:
                        chosen_diff=diff_options[diff_sel]; stop_bgm(); game_loop(); return
                    elif nav_sel==3:
                        chosen_diff=diff_options[diff_sel]; stop_bgm(); game_loop(); return
                    elif nav_sel==4:
                        instructions_screen()
                    elif nav_sel==5:
                        pygame.quit(); sys.exit()


#Main Game Loop

def game_loop():
    global SCORE, top_wall, bot_wall
    d=DIFF[chosen_diff]

    SCORE=0
    top_wall=80; bot_wall=H-80
    particles.clear()
    game_over_flag[0]=False; game_over_flag[1]=W-80; game_over_flag[2]=H//2

  #addictive hooks 
    combo=0; combo_timer=0; COMBO_WINDOW=130
    streak=0
  #power-up timers
    ghost_timer=0  
    boost_timer=0   
    used_combos=set()  
    popups=[] 
    milestones={10,25,50,100,200,500}
    fired_milestones=set()
    best_run_score=get_hi()

    def add_popup(text, x, y, col=CYAN, size=26, life=70):
        popups.append({"t":text,"x":float(x),"y":float(y),
                        "vy":-1.4,"life":life,"ml":life,"col":col,"sz":size})

    def draw_popups(surf):
        dead=[]
        for p in popups:
            p["y"]+=p["vy"]; p["life"]-=1
            if p["life"]<=0: dead.append(p); continue
            a=int(255*min(1, p["life"]/p["ml"]*2))
            try:
                f2=pygame.font.Font(None,p["sz"])
                ts2=f2.render(p["t"],True,p["col"])
                ts2.set_alpha(a)
                surf.blit(ts2,(int(p["x"])-ts2.get_width()//2,int(p["y"])))
            except: pass
        for p in dead:
            try: popups.remove(p)
            except: pass

    boss =Boss(d["boss_speed"])
    player= Player()

    flames_list          =[]
    add_new_flame_counter=0

    laser_beams=[]; emp_rings=[]
    laser_t=0; emp_t=0

  #Phase 1 state
    phase=1
    phase_name="PHASE 1 — SPEED SURVIVAL"

  #Speed ramp for phase1
    proj_speed=d["proj_spd_start"]

  #Spawn rate ramp(frames between spawns, starts slow, decreases)
    spawn_interval=d["spawn_start"]

  #Phase 2 state
    phase2_started=False
    constrict_amount=0.0       
    constrict_done=False
    phase2_survive_timer=0       
    phase2_progress=0.0         

    paused=False
    if BGM: BGM.set_volume(0.42)
    start_bgm()
    run_intro(boss, player)

    while True:
        CLOCK.tick(FPS)
        tval=pygame.time.get_ticks()*0.001

      # events 
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit();sys.exit()
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
              #check pause button click 
                if ev.pos[0] > W-42 and ev.pos[1] < 80:
                    paused=not paused
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: pygame.quit();sys.exit()
                if ev.key in (pygame.K_p, pygame.K_PAUSE):
                    paused=not paused
                if ev.key in (pygame.K_UP,pygame.K_SPACE) and not paused:
                    player.up=True; player.down=False; play(SFX_BOOST)
            if ev.type==pygame.KEYUP:
                if ev.key in (pygame.K_UP,pygame.K_SPACE):
                    player.up=False; player.down=True

      #pause screen
        if paused:
            draw_bg(canvas, pygame.time.get_ticks()*0.001)
            draw_top_wall(canvas, pygame.time.get_ticks()*0.001)
            draw_bot_wall(canvas, pygame.time.get_ticks()*0.001)
            boss.draw(canvas)
            player.draw(canvas)
            draw_hud(canvas, SCORE, get_hi(), player.shield,
                     phase_name, chosen_diff, phase2_progress if phase>=2 else 0.0, combo)
            ov=pygame.Surface((W,H), pygame.SRCALPHA)
            ov.fill((0,0,0,155))
            canvas.blit(ov, (0,0))
            pt=font_big.render("PAUSED", True, CYAN)
            canvas.blit(pt, (W//2 - pt.get_width()//2, H//2 - 55))
            ph2=font_small.render("P  to resume     M  for main menu     ESC  quit", True, (170,170,170))
            canvas.blit(ph2, (W//2 - ph2.get_width()//2, H//2 + 14))
          #check M 
            for ev2 in pygame.event.get():
                if ev2.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev2.type==pygame.KEYDOWN:
                    if ev2.key==pygame.K_ESCAPE: pygame.quit();sys.exit()
                    if ev2.key in (pygame.K_p, pygame.K_PAUSE): paused=False
                    if ev2.key==pygame.K_m:
                        stop_bgm(); main_menu(); return
            pygame.display.update()
            CLOCK.tick(FPS)
            continue

      # check game-over flag 
        if game_over_flag[0]:
            game_over(); return

      # phase 1
        if phase==1:
          #speed ramp
            ramp_t=pygame.time.get_ticks() / 1000.0
            ramp_f=min(1.0, ramp_t / 180.0)  #full speed after 180s 
            proj_speed   =d["proj_spd_start"] + ramp_f*(d["proj_spd_max"]-d["proj_spd_start"])
            spawn_interval= max(d["spawn_min"], int(d["spawn_start"] - ramp_f*(d["spawn_start"]-d["spawn_min"])))

          #transition to phase 2
            if SCORE >= d["phase2_score"]:
                phase=2; phase_name="PHASE 2 — CONSTRICTION"
                do_flash(PURPLE,180); do_shake(14,18); do_glitch(30); play(SFX_PHASE)

      # phase 2: constriction 
        if phase==2:
            boss.malfunction=True
            if not constrict_done:
                constrict_amount=min(constrict_amount+d["constrict_spd"], d["constrict_max"])
                top_wall =60  + int(constrict_amount)
                bot_wall =H-60 - int(constrict_amount)
                phase2_progress=constrict_amount / d["constrict_max"]
                if constrict_amount >= d["constrict_max"]:
                    constrict_done=True
                    phase_name="PHASE 3 — FINAL ASSAULT"
                    do_flash(RED,200); do_shake(16,20); do_glitch(40); play(SFX_PHASE)
            else:
                phase2_survive_timer+=1
                if phase2_survive_timer >= d["phase2_survive"]:
                  #world 1 done 
                    stop_bgm()
                    play(SFX_PHASE)
                    world1_exit_transition(player.rect.centerx, player.rect.centery)
                    result=run_boss_level(SCORE, chosen_diff)
                    if result == "escaped":
                        update_hi(SCORE)
                        run_escape_anim(SCORE, W//2, H//2)
                    return

        combo_timer+=1
        if combo_timer>COMBO_WINDOW:
            combo=0; combo_timer=0; used_combos=set()

        streak+=1

        for ms in list(milestones):
            if SCORE>=ms and ms not in fired_milestones:
                fired_milestones.add(ms)
                add_popup(f"★ {ms} POINTS! ★",W//2,H//2-60,CYAN,34,90)
                do_flash(CYAN,60); do_shake(5,6)

      #power-up timers
        if ghost_timer>0:
            ghost_timer-=1
            player.invinc=max(player.invinc,1)  
            gs=pygame.Surface((120,80),pygame.SRCALPHA)
            ga=int(60+40*math.sin(pygame.time.get_ticks()*0.01))
            pygame.draw.ellipse(gs,(0,220,255,ga),(0,0,120,80))
            canvas.blit(gs,(player.rect.centerx-60,player.rect.centery-40))
        if boost_timer>0:
            boost_timer-=1

        boss.update()

      # spawn projectile 
        add_new_flame_counter+=1
        cap=d["max_projs_on_screen"]
        if add_new_flame_counter>=spawn_interval and len(flames_list)<cap:
            add_new_flame_counter=0
            flames_list.append(Projectile(boss.rect, proj_speed))
            play(SFX_SPAWN)

      # laser 
        laser_t+=1; emp_t+=1
        li=d["laser_interval"]; ei=d["emp_interval"]
        if phase>=2 and laser_t>=li:
            laser_t=0; laser_beams.append(LaserBeam())
        if phase>=2 and emp_t>=ei:
            emp_t=0; emp_rings.append(EMPRing(boss.rect))

      #update everything 
        for f in flames_list[:]:
            f.update()
            if not f.rect.colliderect(player.rect):
                if abs(f.rect.centery - player.rect.centery) < 60 and abs(f.rect.centerx - player.rect.centerx) < 80:
                    SCORE+=2
                    add_popup("+2 CLOSE!", player.rect.centerx, player.rect.top-10,
                              YELLOW,22,50)
                    spawn_p(player.rect.right,player.rect.centery,YELLOW,n=4,spd=3,sz=2,life=18)
            if f.rect.left>=W:        
                flames_list.remove(f)
              #combo
                combo_timer2=pygame.time.get_ticks()
                SCORE+=1
                combo+=1
                combo_timer=0
                if combo>=3:
                    bonus=combo-2
                    SCORE+=bonus
                    add_popup(f"COMBO  x{combo}  +{bonus}!",
                              player.rect.centerx, player.rect.top-30,
                              ORANGE,28,65)
                    spawn_p(player.rect.centerx,player.rect.centery,ORANGE,n=6,spd=4,sz=3,life=22)
              #combo rewards(ghost mode,high jump,increase health)
                if combo==4 and 4 not in used_combos:
                    used_combos.add(4)
                    ghost_timer=240
                    play(SFX_POWERUP)
                    player.invinc=240
                    add_popup("GHOST  MODE!  4s",player.rect.centerx,player.rect.top-55,CYAN,30,90)
                    do_flash(CYAN,80)
                    spawn_p(player.rect.centerx,player.rect.centery,CYAN,n=20,spd=6,sz=4,life=40)
                if combo==5 and 5 not in used_combos:
                    used_combos.add(5)
                    player.shield=min(100,player.shield+20)
                    play(SFX_POWERUP)
                    add_popup("+20  SHIELD  RECHARGE!",player.rect.centerx,player.rect.top-55,GREEN,28,90)
                    do_flash(GREEN,70)
                    spawn_p(player.rect.centerx,player.rect.centery,GREEN,n=16,spd=5,sz=4,life=35)
                if combo==7 and 7 not in used_combos:
                    used_combos.add(7)
                    boost_timer=180
                    play(SFX_POWERUP)
                    add_popup("POWER  BOOST!  3s",player.rect.centerx,player.rect.top-55,YELLOW,28,90)
                    do_flash(YELLOW,70)
                    spawn_p(player.rect.centerx,player.rect.centery,YELLOW,n=16,spd=5,sz=4,life=35)
        for lb in laser_beams[:]:
            lb.update()
            if not lb.alive: laser_beams.remove(lb)
        for er in emp_rings[:]:
            er.update()
            if not er.alive: emp_rings.remove(er)

        player.super_boost=boost_timer > 0
        player.update()
        if game_over_flag[0]: game_over(); return

      #collisions 
        for f in flames_list[:]:
            if f.rect.colliderect(player.rect):
                flames_list.remove(f)
                player.hit(d["dmg_proj"])
                combo=0; combo_timer=0; streak=0; used_combos=set()
                spawn_p(player.rect.centerx,player.rect.centery,PURPLE,n=10,spd=4,sz=4,life=22)
                if game_over_flag[0]: game_over(); return
        for lb in laser_beams:
            if lb.phase=="beam" and lb.hit_rect().colliderect(player.rect):
                player.hit(d["dmg_laser"])
                combo=0; combo_timer=0; streak=0; used_combos=set()
                if game_over_flag[0]: game_over(); return
        for er in emp_rings:
            if er.collides(player.rect):
                player.hit(d["dmg_emp"])
                combo=0; combo_timer=0; streak=0; used_combos=set()
                if game_over_flag[0]: game_over(); return

        draw_bg(canvas,tval)
        for er in emp_rings: er.draw(canvas)
        for lb in laser_beams: lb.draw(canvas)
        for f in flames_list: f.draw(canvas)
        draw_top_wall(canvas,tval)
        draw_bot_wall(canvas,tval)
        boss.draw(canvas)
        player.draw(canvas)
        update_particles(canvas)
        draw_hud(canvas,SCORE,get_hi(),player.shield,phase_name,chosen_diff,
                 phase2_progress if phase>=2 else 0.0, combo)
        draw_popups(canvas)
        draw_flash(canvas); draw_glitch(canvas)

        ox,oy=get_shake()
        if ox or oy:
            cp=canvas.copy(); canvas.fill(BG); canvas.blit(cp,(ox,oy))

        pygame.display.update()
if __name__=="__main__":
    apply_volume()
    main_menu()
