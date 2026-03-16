"""Generate the Logical Component Architecture diagram as a JPEG image."""

from PIL import Image, ImageDraw, ImageFont
import math, os

# ── Canvas ──────────────────────────────────────────────────────────────
W, H = 2600, 1900
BG = "#F8F9FA"
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ── Fonts ───────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    names = (["arialbd.ttf", "calibrib.ttf"] if bold
             else ["arial.ttf", "calibri.ttf"])
    for n in names:
        for d in ["C:/Windows/Fonts", "/usr/share/fonts/truetype/dejavu"]:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F_TITLE = load_font(30, bold=True)
F_HEAD  = load_font(24, bold=True)
F_SUB   = load_font(20, bold=True)
F_BODY  = load_font(17)
F_SMALL = load_font(15)
F_LABEL = load_font(16, bold=True)

# ── Colours ─────────────────────────────────────────────────────────────
C_CC_BG, C_CC_BD       = "#E3F2FD", "#1565C0"
C_CRM_BG, C_CRM_BD     = "#E8F5E9", "#2E7D32"
C_BILL_BG, C_BILL_BD   = "#FFF3E0", "#E65100"
C_AGENT_BG, C_AGENT_BD = "#FFFFFF", "#90A4AE"
C_OLLAMA_BG, C_OLLAMA_BD = "#FCE4EC", "#C62828"
C_GUI_BG, C_GUI_BD     = "#F3E5F5", "#6A1B9A"
C_ARROW = "#37474F"
C_A2A   = "#1565C0"

# ── Drawing helpers ─────────────────────────────────────────────────────
def rrect(x0, y0, x1, y1, fill, outline, r=12, w=2):
    draw.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=fill, outline=outline, width=w)

def tc(x, y, txt, font, fill="#212121"):
    bb = draw.textbbox((0, 0), txt, font=font)
    draw.text((x - (bb[2] - bb[0]) // 2, y), txt, font=font, fill=fill)

def tl(x, y, txt, font, fill="#424242"):
    draw.text((x, y), txt, font=font, fill=fill)

def arr(x0, y0, x1, y1, c=C_ARROW, w=2, h=10):
    draw.line((x0, y0, x1, y1), fill=c, width=w)
    a = math.atan2(y1-y0, x1-x0)
    draw.polygon([(x1,y1),
                  (x1-h*math.cos(a-math.pi/6), y1-h*math.sin(a-math.pi/6)),
                  (x1-h*math.cos(a+math.pi/6), y1-h*math.sin(a+math.pi/6))], fill=c)

def darr(x0, y0, x1, y1, c=C_A2A, w=2, dash=12, gap=8, h=10):
    dx, dy = x1-x0, y1-y0
    L = math.hypot(dx, dy)
    ux, uy = dx/L, dy/L
    d = 0
    while d < L - h:
        e = min(d + dash, L - h)
        draw.line((x0+ux*d, y0+uy*d, x0+ux*e, y0+uy*e), fill=c, width=w)
        d = e + gap
    a = math.atan2(dy, dx)
    draw.polygon([(x1,y1),
                  (x1-h*math.cos(a-math.pi/6), y1-h*math.sin(a-math.pi/6)),
                  (x1-h*math.cos(a+math.pi/6), y1-h*math.sin(a+math.pi/6))], fill=c)

def inner_box(x, y, w, h, title, lines):
    rrect(x, y, x+w, y+h, "#E8EAF6", C_AGENT_BD, r=6)
    tl(x+8, y+5, title, F_SMALL, "#283593")
    for i, l in enumerate(lines):
        tl(x+12, y+26+i*19, l, F_SMALL, "#444")


# ═══════════════════════════════════════════════════════════════════════
#  TITLE
# ═══════════════════════════════════════════════════════════════════════
tc(W//2, 18, "A2A Inter-System Business Flow — Logical Architecture", F_TITLE, "#0D47A1")

# ═══════════════════════════════════════════════════════════════════════
#  CC REGION
# ═══════════════════════════════════════════════════════════════════════
CC = (40, 65, 2520, 650)  # x, y, w, h
rrect(CC[0], CC[1], CC[0]+CC[2], CC[1]+CC[3], C_CC_BG, C_CC_BD, r=16, w=3)
tl(CC[0]+16, CC[1]+8, "CC  (Call Center)", F_HEAD, C_CC_BD)

# ── CC-client ─────────────────────────────────────────────────────
cx, cy, cw, ch = 70, 110, 450, 340
rrect(cx, cy, cx+cw, cy+ch, C_AGENT_BG, C_CC_BD, r=10)
tc(cx+cw//2, cy+8, "CC-client  :5172", F_SUB, C_CC_BD)
tl(cx+14, cy+38, "Customer Caller (Vue 3)", F_BODY, "#555")
tl(cx+14, cy+70, "Components:", F_SMALL, "#666")
for i, t in enumerate(["DialerView  (page root)",
                        "DialPad  (3×4 keypad + input)",
                        "CallStatus  (state indicator)",
                        "VideoStream  (local + remote)"]):
    tl(cx+26, cy+92+i*21, f"• {t}", F_SMALL)
tl(cx+14, cy+182, "Composables / Stores:", F_SMALL, "#666")
for i, t in enumerate(["useWebRTC  (RTCPeerConnection)",
                        "signaling.ts  (WebSocket client)",
                        "callStore  (Pinia state)"]):
    tl(cx+26, cy+204+i*21, f"• {t}", F_SMALL)
tl(cx+14, cy+278, "No REST calls — WS signaling only", F_SMALL, "#999")

# ── CC-server ─────────────────────────────────────────────────────
sx, sy, sw, sh = 640, 110, 820, 560
rrect(sx, sy, sx+sw, sy+sh, C_AGENT_BG, C_CC_BD, r=10)
tc(sx+sw//2, sy+8, "CC-server  :8001", F_SUB, C_CC_BD)
tl(sx+14, sy+38, "Orchestrator + Signaling (FastAPI)", F_BODY, "#555")

inner_box(sx+16, sy+70, 380, 90,
          "WebSocket Signaling  /ws/signal",
          ["Relay: offer / answer / ice-candidate",
           "Events: call-start / call-end",
           "Push: progress / business_payload / error"])

inner_box(sx+412, sy+70, 390, 90,
          "A2A Orchestrator  (flow sequencer)",
          ["Sequential A2A calls to CRM & Billing",
           "Aggregates results → business_payload",
           "Graceful degradation on A2A failure"])

inner_box(sx+16, sy+178, 380, 68,
          "Communication Agent  /communication",
          ["skill: send_notification  (TMF681)",
           "Channel: sms | email | push"])

inner_box(sx+412, sy+178, 390, 68,
          "REST Endpoint",
          ["POST /order/create",
           "(verify_identity → create_order → notify)"])

inner_box(sx+16, sy+264, 786, 44,
          "a2a-python SDK",
          ["Client: outbound A2A calls  ·  Server: Communication Agent card + JSON-RPC dispatch"])

# ── CC-gui ────────────────────────────────────────────────────────
gx, gy, gw, gh = 1580, 110, 500, 380
rrect(gx, gy, gx+gw, gy+gh, C_AGENT_BG, C_CC_BD, r=10)
tc(gx+gw//2, gy+8, "CC-gui  :5173", F_SUB, C_CC_BD)
tl(gx+14, gy+38, "Agent Dashboard (Vue 3 + Element Plus)", F_BODY, "#555")
tl(gx+14, gy+70, "Panels:", F_SMALL, "#666")
for i, t in enumerate(["CustomerInfo  (profile card)",
                        "BillSummary  (balance + usage)",
                        "NBO List  (ranked offers + fallback tag)",
                        "OrderConfirmation  (id + state)",
                        "NotificationStatus  (sent / failed)"]):
    tl(gx+26, gy+92+i*21, f"• {t}", F_SMALL)
tl(gx+14, gy+206, "Composables / Stores:", F_SMALL, "#666")
for i, t in enumerate(["useWebRTC  (answer incoming calls)",
                        "signaling.ts  (WebSocket client)",
                        "callStore  (Pinia state)"]):
    tl(gx+26, gy+228+i*21, f"• {t}", F_SMALL)

# ── Connector zone (below boxes, inside CC region) ────────────────
conn_y = 520  # y for arrows — in the open space below CC-client & CC-gui

# CC-client ──► CC-server
arr(cx+cw, conn_y, sx, conn_y, C_CC_BD, 3)
tc((cx+cw+sx)//2, conn_y-22, "WebSocket signaling", F_LABEL, C_CC_BD)

# CC-server ──► CC-gui
arr(sx+sw, conn_y, gx, conn_y, C_CC_BD, 3)
tc((sx+sw+gx)//2, conn_y-22, "WS push (progress, payload)", F_LABEL, C_CC_BD)

# CC-gui ──► CC-server (return)
arr(gx, conn_y+40, sx+sw, conn_y+40, "#C62828", 2)
tc((gx+sx+sw)//2, conn_y+44, "POST /order/create", F_LABEL, "#C62828")


# ═══════════════════════════════════════════════════════════════════════
#  A2A ZONE  (gap between CC and servers)
# ═══════════════════════════════════════════════════════════════════════
a2a_top = CC[1] + CC[3]       # 715
a2a_bot = a2a_top + 100       # 815

# Left: CC-server → CRM
ax1 = sx + sw//3
darr(ax1, a2a_top, ax1, a2a_bot, C_A2A, 3)
tc(ax1+6, a2a_top+10, "A2A  (JSON-RPC 2.0)", F_LABEL, C_A2A)
tl(ax1+16, a2a_top+32, "query_customer · query_bill · get_nbo", F_SMALL, C_A2A)
tl(ax1+16, a2a_top+52, "verify_identity · create_order · get_ai_model_status", F_SMALL, C_A2A)

# Right: CC-server → Billing
bx_a2a = 1830
darr(sx+sw-60, a2a_top, bx_a2a, a2a_bot, C_BILL_BD, 3)
tl(bx_a2a-20, a2a_top+10, "A2A", F_LABEL, C_BILL_BD)
tl(bx_a2a-40, a2a_top+32, "query_bill", F_SMALL, C_BILL_BD)


# ═══════════════════════════════════════════════════════════════════════
#  CRM-server
# ═══════════════════════════════════════════════════════════════════════
crm_x, crm_y, crm_w, crm_h = 40, a2a_bot, 1420, 850

rrect(crm_x, crm_y, crm_x+crm_w, crm_y+crm_h, C_CRM_BG, C_CRM_BD, r=16, w=3)
tl(crm_x+16, crm_y+10, "CRM-server  :8002", F_HEAD, C_CRM_BD)

def agent_box(x, y, w, h, name, prefix, skills, tmf, bd=C_CRM_BD):
    rrect(x, y, x+w, y+h, C_AGENT_BG, bd, r=8)
    tl(x+10, y+6, name, F_SUB, bd)
    tl(x+10, y+32, prefix, F_SMALL, "#666")
    for i, s in enumerate(skills):
        tl(x+14, y+56+i*22, f"• {s}", F_SMALL, "#333")
    tl(x+10, y+h-24, tmf, F_SMALL, "#888")

agent_box(crm_x+24, crm_y+48, 400, 170,
          "Profiling Agent", "/profiling",
          ["query_customer", "verify_identity"],
          "TMF629 · TMF637 · TMF720")

agent_box(crm_x+24, crm_y+234, 400, 170,
          "Recommendation Agent", "/recommendation",
          ["get_nbo  (LLM ranking + fallback)"],
          "TMF701 · TMF620 · TMF637")

agent_box(crm_x+24, crm_y+420, 400, 140,
          "Order Agent", "/order",
          ["create_order"],
          "TMF622")

agent_box(crm_x+24, crm_y+576, 400, 140,
          "AI Management Agent", "/ai-management",
          ["get_ai_model_status"],
          "TMF915")

# ── Ollama ────────────────────────────────────────────────────────
ox, oy, ow, oh = crm_x+470, crm_y+234, 220, 110
rrect(ox, oy, ox+ow, oy+oh, C_OLLAMA_BG, C_OLLAMA_BD, r=8)
tc(ox+ow//2, oy+12, "Ollama", F_SUB, C_OLLAMA_BD)
tc(ox+ow//2, oy+44, "qwen2.5:7b", F_BODY, "#333")
tc(ox+ow//2, oy+70, "(LLM inference)", F_SMALL, "#888")

arr(crm_x+424, crm_y+320, ox, crm_y+290, C_OLLAMA_BD, 2)
tl(crm_x+432, crm_y+280, "httpx async", F_SMALL, C_OLLAMA_BD)

# ── SQLite + SDK ──────────────────────────────────────────────────
inner_box(crm_x+470, crm_y+390, 440, 90,
          "SQLite databases",
          ["customers · product_offerings · orders",
           "identities · ai_models",
           "seed.py  (auto-init at startup)"])

inner_box(crm_x+470, crm_y+496, 440, 54,
          "a2a-python SDK server",
          ["4 Agent Cards + JSON-RPC 2.0 dispatch"])

# ── CRM-gui ───────────────────────────────────────────────────────
cgx, cgy, cgw, cgh = crm_x+470, crm_y+580, 320, 110
rrect(cgx, cgy, cgx+cgw, cgy+cgh, C_GUI_BG, C_GUI_BD, r=8)
tc(cgx+cgw//2, cgy+10, "CRM-gui  :5174", F_SUB, C_GUI_BD)
tl(cgx+14, cgy+40, "Customer 360 view", F_BODY, "#333")
tl(cgx+14, cgy+64, "(profile + order history)", F_SMALL, "#666")
tl(cgx+14, cgy+86, "Vue 3 + Element Plus", F_SMALL, "#888")

arr(cgx, cgy+55, crm_x+424+16, crm_y+510, C_GUI_BD, 2)


# ═══════════════════════════════════════════════════════════════════════
#  Billing-server
# ═══════════════════════════════════════════════════════════════════════
bx, by, bw, bh = 1580, a2a_bot, 560, 520

rrect(bx, by, bx+bw, by+bh, C_BILL_BG, C_BILL_BD, r=16, w=3)
tl(bx+16, by+10, "Billing-server  :8003", F_HEAD, C_BILL_BD)

agent_box(bx+24, by+48, 500, 140,
          "Usage Agent", "/usage",
          ["query_bill"],
          "TMF677 · TMF678",
          bd=C_BILL_BD)

inner_box(bx+24, by+210, 500, 62,
          "SQLite: bills",
          ["seed.py  (auto-init at startup)"])

inner_box(bx+24, by+290, 500, 54,
          "a2a-python SDK server",
          ["1 Agent Card + JSON-RPC 2.0 dispatch"])

# ── Billing-gui ───────────────────────────────────────────────────
bgx, bgy, bgw, bgh = bx+24, by+370, 360, 100
rrect(bgx, bgy, bgx+bgw, bgy+bgh, C_GUI_BG, C_GUI_BD, r=8)
tc(bgx+bgw//2, bgy+10, "Billing-gui  :5175", F_SUB, C_GUI_BD)
tl(bgx+14, bgy+40, "Bill details & consumption", F_BODY, "#333")
tl(bgx+14, bgy+64, "Vue 3 + Element Plus", F_SMALL, "#888")

arr(bgx+bgw//2, bgy, bx+bw//2, by+356, C_GUI_BD, 2)


# ═══════════════════════════════════════════════════════════════════════
#  Legend
# ═══════════════════════════════════════════════════════════════════════
lx, ly = 2200, a2a_bot + 30
rrect(lx, ly, lx+380, ly+200, "#FAFAFA", "#BDBDBD", r=8)
tl(lx+12, ly+8, "Legend", F_SUB, "#333")
# solid line
draw.line((lx+20, ly+44, lx+60, ly+44), fill=C_CC_BD, width=3)
tl(lx+70, ly+36, "WebSocket / REST", F_SMALL, "#444")
# dashed line
for i in range(5):
    draw.line((lx+20+i*10, ly+74, lx+26+i*10, ly+74), fill=C_A2A, width=3)
tl(lx+70, ly+66, "A2A  (JSON-RPC 2.0 over HTTP)", F_SMALL, "#444")
# swatches
for i, (c, label) in enumerate([
    (C_CC_BG, "CC subsystem"), (C_CRM_BG, "CRM subsystem"),
    (C_BILL_BG, "Billing subsystem"), (C_GUI_BG, "GUI frontend"),
]):
    draw.rectangle((lx+20, ly+100+i*24, lx+44, ly+118+i*24), fill=c, outline="#999")
    tl(lx+52, ly+100+i*24, label, F_SMALL, "#444")


# ═══════════════════════════════════════════════════════════════════════
#  Save
# ═══════════════════════════════════════════════════════════════════════
out = os.path.join(os.path.dirname(__file__), "architecture.jpg")
img.save(out, "JPEG", quality=95)
print(f"Saved: {out}  ({W}x{H})")
