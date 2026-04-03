import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os
from datetime import datetime
import io

# --- สีที่คุณ Mu เลือก p_clr = (0.2, 0.5, 1) ---
P_CLR = (0.2, 0.5, 1)

def thai_baht(num):
    try:
        num = float(num)
        baht, satang = int(num), int(round((num - int(num)) * 100))
        def read(n):
            units = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
            pos = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]
            s, n_str = "", str(n)[::-1]
            for i, d in enumerate(n_str):
                d = int(d)
                if d != 0:
                    if i == 1 and d == 1: s = "สิบ" + s
                    elif i == 1 and d == 2: s = "ยี่สิบ" + s
                    elif i == 0 and d == 1 and len(n_str) > 1: s = "เอ็ด" + s
                    else: s = units[d] + pos[i] + s
            return s
        res = read(baht) + "บาท"
        return res + (read(satang) + "สตางค์" if satang != 0 else "ถ้วน")
    except: return ""

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ใบเสนอราคาโรงกลึง", layout="centered")

st.title("🛠️ ระบบออกใบเสนอราคา")

# ส่วนหัวข้อมูล
customer_name = st.text_input("ชื่อลูกค้า", placeholder="พิมพ์หรือใช้ไมค์พูดชื่อบริษัท...")
date_str = st.date_input("วันที่", datetime.now()).strftime("%d/%m/%Y")

# --- จุดที่แก้ Error: ตรวจสอบและสร้างรายการเริ่มต้น ---
if 'items' not in st.session_state:
    st.session_state.items = [{"name": "", "qty": 1.0, "unit": "ชุด", "price": 0.0}]

st.subheader("📦 รายการสินค้า")

# แสดงรายการที่มีอยู่
for i, item in enumerate(st.session_state.items):
    with st.container(border=True):
        st.session_state.items[i]["name"] = st.text_input(f"รายการที่ {i+1}", value=item["name"], key=f"name_{i}")
        c1, c2, c3 = st.columns([1, 1, 1])
        st.session_state.items[i]["qty"] = c1.number_input("จำนวน", min_value=0.0, value=float(item["qty"]), key=f"qty_{i}")
        st.session_state.items[i]["unit"] = c2.text_input("หน่วย", value=item["unit"], key=f"unit_{i}")
        st.session_state.items[i]["price"] = c3.number_input("ราคา/หน่วย", min_value=0.0, value=float(item["price"]), key=f"price_{i}")

# ปุ่มเพิ่มรายการ
if st.button("➕ เพิ่มแถวรายการ"):
    st.session_state.items.append({"name": "", "qty": 1.0, "unit": "ชุด", "price": 0.0})
    st.rerun()

# คำนวณเงิน
total_all = sum(it["qty"] * it["price"] for it in st.session_state.items)
st.divider()
st.write(f"### รวมเงินทั้งสิ้น: **{total_all:,.2f}** บาท")
st.write(f"({thai_baht(total_all)})")

# ปุ่มสร้าง PDF
if st.button("📄 สร้างไฟล์ PDF และดาวน์โหลด", type="primary"):
    if not customer_name:
        st.error("⚠️ กรุณาพิมพ์ชื่อลูกค้าก่อนครับ")
    else:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # ฟอนต์และรูปพื้นหลัง
        try:
            pdfmetrics.registerFont(TTFont('Sarabun', 'Sarabun-Regular.ttf'))
            font_main = 'Sarabun'
        except:
            font_main = 'Helvetica'
            
        if os.path.exists("template.jpg"):
            c.drawImage("template.jpg", 0, 0, 595, 842)
        
        c.setFont(font_main, 10)
        c.setFillColorRGB(*P_CLR)
        
        # เขียนข้อมูลลง PDF (พิกัดเดียวกับในคอม)
        c.drawString(82, 696.3, customer_name)
        c.drawString(455, 696.3, date_str)
        
        styleN = getSampleStyleSheet()["Normal"]
        styleN.fontName, styleN.fontSize, styleN.textColor, styleN.leading = font_main, 10, P_CLR, 14
        
        y_pos = 600
        for i, it in enumerate(st.session_state.items):
            if not it["name"]: continue
            p = Paragraph(it["name"], styleN)
            w, h = p.wrap(300, 100)
            p.drawOn(c, 60, y_pos - h + 10)
            c.drawCentredString(29, y_pos, str(i+1))
            c.drawCentredString(389, y_pos, str(it["qty"]))
            c.drawCentredString(432.2, y_pos, it["unit"])
            c.drawRightString(513.6, y_pos, f"{it['price']:,.2f}")
            c.drawRightString(580, y_pos, f"{it['qty']*it['price']:,.2f}")
            y_pos -= max(h, 20)
            
        c.drawRightString(580, 191, f"{total_all:,.2f}")
        c.drawRightString(580, 170, thai_baht(total_all))
        
        c.save()
        buffer.seek(0)
        st.download_button(
            label="📥 กดที่นี่เพื่อบันทึกไฟล์ลงมือถือ",
            data=buffer,
            file_name=f"ใบเสนอราคา_{customer_name}.pdf",
            mime="application/pdf"
        )
        st.success("สร้าง PDF เรียบร้อย! กดปุ่มดาวน์โหลดแล้วแชร์เข้า LINE ได้เลยครับ")
