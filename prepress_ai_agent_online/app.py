import io, csv
import fitz
import streamlit as st
from PIL import Image
import numpy as np

st.set_page_config(page_title="Prepress AI Agent", page_icon="🖨️", layout="wide")
st.title("🖨️ Prepress AI Agent")
st.caption("Online prototype for preliminary PDF artwork checks. Human verification is required before production.")

with st.sidebar:
    st.header("SKU specifications")
    width_mm = st.number_input("Trim/artboard width (mm)", min_value=1.0, value=90.0, step=1.0)
    height_mm = st.number_input("Trim/artboard height (mm)", min_value=1.0, value=50.0, step=1.0)
    bleed_mm = st.number_input("Required bleed per edge (mm)", min_value=0.0, value=3.0, step=0.5)
    min_dpi = st.number_input("Minimum effective image DPI", min_value=1, value=300, step=25)
    edge_band_mm = st.number_input("Edge inspection band (mm)", min_value=0.5, value=1.0, step=0.5)
    white_threshold = st.slider("White-pixel threshold", 200, 255, 245)
    white_percent = st.slider("Flag edge if white pixels exceed (%)", 10, 100, 80)

st.warning("Privacy: this app runs on its hosting provider. Do not upload confidential client artwork until your employer approves this hosting arrangement. Use sample files for testing.")
st.info("Checks page size, placed raster-image effective DPI, possible white edge gaps, and likely PDF spot-color definitions. It does not automatically modify artwork or guarantee print readiness.")
uploaded = st.file_uploader("Upload a non-confidential sample PDF", type=["pdf"])

def mm_to_pt(mm): return mm * 72 / 25.4

def spot_scan(doc):
    found = []
    for xref in range(1, doc.xref_length()):
        try: obj = doc.xref_object(xref, compressed=False)
        except Exception: continue
        if "/Separation" in obj or "/DeviceN" in obj:
            found.append({"PDF object": xref, "Definition": "Separation" if "/Separation" in obj else "DeviceN", "Snippet": " ".join(obj.split())[:240]})
    return found

def edge_scan(page):
    pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72), alpha=False)
    arr = np.asarray(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))
    h, w, _ = arr.shape
    bx = max(1, int(mm_to_pt(edge_band_mm) * 150 / 72))
    by = max(1, int(mm_to_pt(edge_band_mm) * 150 / 72))
    regions = {"Top": arr[:by,:,:], "Bottom": arr[max(0,h-by):,:,:], "Left": arr[:,:bx,:], "Right": arr[:,max(0,w-bx):,:]}
    out = []
    for name, region in regions.items():
        pct = float(np.all(region >= white_threshold, axis=2).mean() * 100) if region.size else 0
        out.append({"Edge": name, "White pixels (%)": round(pct,1), "Result": "Warning: possible white/uncovered edge" if pct >= white_percent else "No obvious white-edge warning"})
    return out

def inspect(data):
    doc = fitz.open(stream=data, filetype="pdf")
    pages, images, edges = [], [], []
    ew, eh, eb = mm_to_pt(width_mm), mm_to_pt(height_mm), mm_to_pt(bleed_mm)
    try:
        for pn, page in enumerate(doc, 1):
            r = page.rect
            wmm, hmm = r.width*25.4/72, r.height*25.4/72
            expected = [(ew,eh),(eh,ew)]
            expected_bleed = [(w+2*eb,h+2*eb) for w,h in expected]
            fits = any(abs(r.width-x)<=mm_to_pt(.5) and abs(r.height-y)<=mm_to_pt(.5) for x,y in expected_bleed)
            pages.append({"Page":pn,"PDF width (mm)":round(wmm,2),"PDF height (mm)":round(hmm,2),"Expected artboard (mm)":f"{width_mm:g} × {height_mm:g}","Bleed (mm/edge)":bleed_mm,"Result":"Pass: page matches artboard + bleed" if fits else "Warning: page size differs from expected artboard + bleed"})
            seen=set()
            for info in page.get_images(full=True):
                xref=info[0]
                try:
                    im=doc.extract_image(xref); pw,ph=im["width"],im["height"]
                    for ir in page.get_image_rects(xref):
                        key=(xref,round(ir.x0,2),round(ir.y0,2),round(ir.x1,2),round(ir.y1,2))
                        if key in seen: continue
                        seen.add(key)
                        dx=pw/max(ir.width/72,1e-6); dy=ph/max(ir.height/72,1e-6)
                        images.append({"Page":pn,"Image xref":xref,"Pixels":f"{pw} × {ph}","Effective DPI (X)":round(dx),"Effective DPI (Y)":round(dy),"Result":"Pass" if min(dx,dy)>=min_dpi else "Warning: below minimum DPI"})
                except Exception as e:
                    images.append({"Page":pn,"Image xref":xref,"Pixels":"Unknown","Effective DPI (X)":"N/A","Effective DPI (Y)":"N/A","Result":f"Could not inspect image: {str(e)[:80]}"})
            edges.extend([{"Page":pn,**x} for x in edge_scan(page)])
        spots=spot_scan(doc)
    finally: doc.close()
    return pages,images,edges,spots

if uploaded:
    if uploaded.size > 50*1024*1024:
        st.error("This prototype accepts files up to 50 MB. Use a smaller non-confidential test PDF.")
    else:
        try:
            pages,images,edges,spots=inspect(uploaded.getvalue())
            a,b,c,d=st.columns(4)
            a.metric("Pages inspected",len(pages)); b.metric("Placed images",len(images))
            c.metric("Possible edge warnings",sum("Warning" in x["Result"] for x in edges)); d.metric("Spot definitions flagged",len(spots))
            st.subheader("1. Artboard / bleed"); st.dataframe(pages,use_container_width=True)
            st.subheader("2. Image resolution")
            if images: st.dataframe(images,use_container_width=True)
            else: st.write("No placed raster images detected; vector artwork may not need image-DPI checks.")
            st.subheader("3. Possible white edges")
            st.caption("Heuristic only: intentional white artwork can trigger warnings, and some defects may be missed.")
            st.dataframe(edges,use_container_width=True)
            st.subheader("4. Spot colors")
            if spots:
                st.warning("Possible Separation/DeviceN definitions found. Verify colorant names and conversion requirements in an approved prepress tool.")
                st.dataframe(spots,use_container_width=True)
            else: st.success("No obvious Separation/DeviceN definitions found by this heuristic. This does not prove there are no spot colors.")
            buf=io.StringIO(); writer=csv.writer(buf); writer.writerow(["Section","Details"])
            for x in pages: writer.writerow(["Page dimensions",x])
            for x in images: writer.writerow(["Image resolution",x])
            for x in edges: writer.writerow(["Edge check",x])
            for x in spots: writer.writerow(["Spot color",x])
            st.download_button("Download validation report (CSV)",buf.getvalue().encode(), "prepress_validation_report.csv","text/csv")
            st.warning("This prototype reports issues only. It does not export a corrected PDF; verify findings manually.")
        except Exception as e: st.error(f"Could not inspect this PDF: {e}")
