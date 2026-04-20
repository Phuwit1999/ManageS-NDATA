import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(
    page_title="S/N Checker",
    page_icon="🔍",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; color: #1e3a5f; margin-bottom: 0; }
    .sub-title  { color: #6b7280; margin-top: 0; margin-bottom: 1.5rem; }
    .found-box  { background: #ecfdf5; border-left: 4px solid #10b981;
                  padding: 1rem 1.2rem; border-radius: 6px; margin-top: 1rem; }
    .not-found  { background: #fef2f2; border-left: 4px solid #ef4444;
                  padding: 1rem 1.2rem; border-radius: 6px; margin-top: 1rem; }
    .info-row   { display: flex; gap: 2rem; flex-wrap: wrap; margin-top: 0.5rem; }
    .info-item  { min-width: 150px; }
    .info-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase;
                  letter-spacing: 0.05em; }
    .info-value { font-size: 1rem; font-weight: 600; color: #111827; }
    .stat-card  { background: #f9fafb; border: 1px solid #e5e7eb;
                  border-radius: 8px; padding: 1rem; text-align: center; }
    .stat-num   { font-size: 2rem; font-weight: 700; color: #1e3a5f; }
    .stat-lbl   { font-size: 0.8rem; color: #6b7280; }
    .diff-card-red   { background: #fef2f2; border-left: 4px solid #ef4444;
                       padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 0.5rem; }
    .diff-card-orange{ background: #fff7ed; border-left: 4px solid #f97316;
                       padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 0.5rem; }
    .diff-card-green { background: #ecfdf5; border-left: 4px solid #10b981;
                       padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 0.5rem; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #1e3a5f; margin: 1.5rem 0 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🔍 S/N Checker</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ตรวจสอบ Serial Number อุปกรณ์จากไฟล์ Excel (รองรับการค้นหาและเปรียบเทียบไฟล์)</p>', unsafe_allow_html=True)

# --- Session State ---
for key in ["df", "sn_col", "file_name", "display_cols"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ------------------------------------------------------------------ #
#  Helper: read any supported file
# ------------------------------------------------------------------ #
def read_file(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext == "csv":
        return pd.read_csv(uploaded_file)
    elif ext == "xlsx":
        return pd.read_excel(uploaded_file, engine="openpyxl")
    elif ext == "xls":
        try:
            return pd.read_excel(uploaded_file, engine="xlrd")
        except Exception:
            uploaded_file.seek(0)
            raw_bytes = uploaded_file.read()
            dfs = pd.read_html(io.BytesIO(raw_bytes), encoding="utf-8")
            return dfs[0] if dfs else pd.DataFrame()
    return pd.DataFrame()


# ------------------------------------------------------------------ #
#  SIDEBAR — Upload & Settings
# ------------------------------------------------------------------ #
with st.sidebar:
    st.header("📂 โหลดฐานข้อมูล")

    uploaded = st.file_uploader(
        "อัปโหลดไฟล์หลัก (ฐานข้อมูล)",
        type=["xlsx", "xls", "csv"],
        help="รองรับ .xlsx, .xls, .csv",
        key="main_upload"
    )

    if uploaded:
        try:
            df_raw = read_file(uploaded)
            if not df_raw.empty:
                st.session_state.df = df_raw.copy()
                st.session_state.file_name = uploaded.name
                st.success(f"✅ โหลดสำเร็จ: {len(df_raw):,} รายการ")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

    # Column mapping
    if st.session_state.df is not None:
        st.divider()
        st.subheader("⚙️ ตั้งค่าคอลัมน์")
        cols = list(st.session_state.df.columns)

        default_sn = 0
        sn_keywords = ["serial", "s/n", "sn", "serialno", "serial_no", "serial number"]
        for i, c in enumerate(cols):
            if any(kw in str(c).lower() for kw in sn_keywords):
                default_sn = i
                break

        st.session_state.sn_col = st.selectbox(
            "คอลัมน์ Serial Number (S/N)",
            cols,
            index=default_sn
        )

        display_cols = st.multiselect(
            "คอลัมน์ที่ต้องการแสดงผล",
            [c for c in cols if c != st.session_state.sn_col],
            default=[c for c in cols if c != st.session_state.sn_col][:6]
        )
        st.session_state.display_cols = display_cols

        st.divider()
        st.caption(f"📄 ไฟล์: `{st.session_state.file_name}`")
        st.caption(f"📊 {len(st.session_state.df):,} แถว | {len(cols)} คอลัมน์")


# ------------------------------------------------------------------ #
#  MAIN
# ------------------------------------------------------------------ #
if st.session_state.df is None:
    st.info("👈 กรุณาอัปโหลดไฟล์ Excel หรือ CSV ทางด้านซ้ายก่อน")
    st.markdown("**รูปแบบไฟล์ที่รองรับ:** `.xlsx` · `.xls` · `.csv`")
    st.stop()

df = st.session_state.df
sn_col = st.session_state.sn_col
display_cols = st.session_state.display_cols or [c for c in df.columns if c != sn_col]

# Stats row
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num">{len(df):,}</div>
        <div class="stat-lbl">รายการทั้งหมด</div>
    </div>""", unsafe_allow_html=True)
with col2:
    unique_sn = df[sn_col].dropna().nunique()
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num">{unique_sn:,}</div>
        <div class="stat-lbl">S/N ไม่ซ้ำ</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="stat-card">
        <div class="stat-num">{len(df.columns)}</div>
        <div class="stat-lbl">จำนวนคอลัมน์</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ================================================================== #
#  TABS
# ================================================================== #
tab1, tab2 = st.tabs(["🔎 ค้นหา S/N", "📊 เปรียบเทียบไฟล์"])


# ------------------------------------------------------------------ #
#  TAB 1 — Search
# ------------------------------------------------------------------ #
with tab1:
    st.subheader("🔎 ค้นหา Serial Number")
    search_input = st.text_area(
        "พิมพ์ S/N ที่ต้องการค้นหา (สามารถใส่ได้หลายค่าโดยแยกด้วยบรรทัดใหม่ หรือ เว้นวรรค)",
        placeholder="เช่น\nSN12345678\nSN87654321",
        height=150,
        label_visibility="collapsed"
    )

    col_search, col_clear = st.columns([4, 1])
    with col_search:
        do_search = st.button("ค้นหา", type="primary", use_container_width=True, key="btn_search")
    with col_clear:
        if st.button("ล้าง", use_container_width=True, key="btn_clear"):
            st.rerun()

    if search_input and do_search:
        queries = [q.strip().upper() for q in re.split(r'[\n,\s]+', search_input) if q.strip()]

        if not queries:
            st.warning("กรุณากรอก S/N ที่ต้องการค้นหา")
        else:
            mask = df[sn_col].astype(str).str.strip().str.upper().isin(queries)
            results = df[mask]
            found_sns = results[sn_col].astype(str).str.strip().str.upper().unique()
            not_found_sns = [q for q in queries if q not in found_sns]

            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.success(f"✅ พบข้อมูล: {len(found_sns)} จาก {len(queries)} รายการ")
            with col_res2:
                if not_found_sns:
                    st.error(f"❌ ไม่พบข้อมูล: {len(not_found_sns)} รายการ")

            if not results.empty:
                st.markdown(f'<div class="found-box">✅ <b>พบข้อมูลทั้งหมด {len(results)} แถว</b></div>',
                            unsafe_allow_html=True)
                st.markdown("")
                show_cols = [sn_col] + [c for c in display_cols if c in df.columns]
                st.dataframe(results[show_cols].reset_index(drop=True), use_container_width=True)

                csv = results.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 ดาวน์โหลดผลการค้นหาเป็น CSV",
                    data=csv,
                    file_name="search_results.csv",
                    mime="text/csv",
                )

            if not_found_sns:
                with st.expander("🔍 รายการที่ไม่พบในฐานข้อมูล", expanded=True):
                    for sn in not_found_sns:
                        st.write(f"• `{sn}`")

                    if len(not_found_sns) <= 5:
                        st.markdown("---")
                        st.markdown("💡 **ผลการค้นหาใกล้เคียงสำหรับรายการที่ไม่พบ:**")
                        for sn in not_found_sns:
                            partial = df[df[sn_col].astype(str).str.upper().str.contains(sn, na=False)]
                            if not partial.empty:
                                st.write(f"ใกล้เคียงสำหรับ `{sn}`:")
                                st.dataframe(partial[[sn_col] + display_cols].head(3), use_container_width=True)

    elif not search_input and do_search:
        st.warning("กรุณากรอก S/N ที่ต้องการค้นหา")


# ------------------------------------------------------------------ #
#  TAB 2 — File Comparison
# ------------------------------------------------------------------ #
with tab2:
    st.subheader("📊 เปรียบเทียบกับไฟล์อ้างอิง")
    st.markdown("อัปโหลดไฟล์ที่ต้องการเปรียบเทียบกับฐานข้อมูลหลัก เพื่อหาความแตกต่างของ S/N")

    compare_file = st.file_uploader(
        "อัปโหลดไฟล์เปรียบเทียบ",
        type=["xlsx", "xls", "csv"],
        help="รองรับ .xlsx, .xls, .csv",
        key="compare_upload"
    )

    if compare_file:
        try:
            df_cmp = read_file(compare_file)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
            st.stop()

        if df_cmp.empty:
            st.warning("ไฟล์เปรียบเทียบว่างเปล่า")
            st.stop()

        # Select SN column from compare file
        cmp_cols = list(df_cmp.columns)
        default_cmp_sn = 0
        sn_keywords = ["serial", "s/n", "sn", "serialno", "serial_no", "serial number"]
        for i, c in enumerate(cmp_cols):
            if any(kw in str(c).lower() for kw in sn_keywords):
                default_cmp_sn = i
                break

        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            st.markdown(f"**ไฟล์หลัก:** `{st.session_state.file_name}` ({len(df):,} รายการ)")
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;คอลัมน์ S/N: **`{sn_col}`**")
        with col_cfg2:
            st.markdown(f"**ไฟล์เปรียบเทียบ:** `{compare_file.name}` ({len(df_cmp):,} รายการ)")
            cmp_sn_col = st.selectbox(
                "คอลัมน์ S/N (ไฟล์เปรียบเทียบ)",
                cmp_cols,
                index=default_cmp_sn,
                key="cmp_sn_col"
            )

        if st.button("▶️ เริ่มเปรียบเทียบ", type="primary", use_container_width=True):

            # Normalize both sets
            set_main = set(df[sn_col].dropna().astype(str).str.strip().str.upper())
            set_cmp  = set(df_cmp[cmp_sn_col].dropna().astype(str).str.strip().str.upper())

            only_in_main = set_main - set_cmp   # มีในหลัก แต่ไม่มีในไฟล์เทียบ
            only_in_cmp  = set_cmp  - set_main  # มีในไฟล์เทียบ แต่ไม่มีในหลัก
            in_both       = set_main & set_cmp  # ตรงกันทั้งคู่

            st.markdown("---")

            # Summary cards
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="stat-card">
                    <div class="stat-num" style="color:#10b981">{len(in_both):,}</div>
                    <div class="stat-lbl">✅ ตรงกัน (Match)</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="stat-card">
                    <div class="stat-num" style="color:#ef4444">{len(only_in_main):,}</div>
                    <div class="stat-lbl">🔴 มีในหลัก แต่ไม่มีในไฟล์เทียบ</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="stat-card">
                    <div class="stat-num" style="color:#f97316">{len(only_in_cmp):,}</div>
                    <div class="stat-lbl">🟠 มีในไฟล์เทียบ แต่ไม่มีในหลัก</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("")

            # ---- Section 1: Match ----
            with st.expander(f"✅ รายการที่ตรงกัน ({len(in_both):,} รายการ)", expanded=False):
                df_matched = df[df[sn_col].astype(str).str.strip().str.upper().isin(in_both)]
                show_cols = [sn_col] + [c for c in display_cols if c in df.columns]
                st.dataframe(df_matched[show_cols].reset_index(drop=True), use_container_width=True, height=300)
                csv_matched = df_matched.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 ดาวน์โหลดรายการที่ตรงกัน", csv_matched,
                                   "matched.csv", "text/csv", key="dl_matched")

            # ---- Section 2: Only in Main ----
            with st.expander(f"🔴 มีในฐานข้อมูลหลัก แต่ไม่พบในไฟล์เปรียบเทียบ ({len(only_in_main):,} รายการ)", expanded=True):
                if only_in_main:
                    df_only_main = df[df[sn_col].astype(str).str.strip().str.upper().isin(only_in_main)]
                    show_cols = [sn_col] + [c for c in display_cols if c in df.columns]
                    st.dataframe(df_only_main[show_cols].reset_index(drop=True), use_container_width=True, height=300)
                    csv_only_main = df_only_main.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 ดาวน์โหลดรายการนี้", csv_only_main,
                                       "only_in_main.csv", "text/csv", key="dl_only_main")
                else:
                    st.success("ไม่มีรายการที่หายไป — S/N ทุกตัวในฐานข้อมูลหลักอยู่ในไฟล์เปรียบเทียบ")

            # ---- Section 3: Only in Compare ----
            with st.expander(f"🟠 มีในไฟล์เปรียบเทียบ แต่ไม่พบในฐานข้อมูลหลัก ({len(only_in_cmp):,} รายการ)", expanded=True):
                if only_in_cmp:
                    df_only_cmp = df_cmp[df_cmp[cmp_sn_col].astype(str).str.strip().str.upper().isin(only_in_cmp)]
                    st.dataframe(df_only_cmp.reset_index(drop=True), use_container_width=True, height=300)
                    csv_only_cmp = df_only_cmp.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 ดาวน์โหลดรายการนี้", csv_only_cmp,
                                       "only_in_compare.csv", "text/csv", key="dl_only_cmp")
                else:
                    st.success("ไม่มีรายการส่วนเกิน — S/N ทุกตัวในไฟล์เปรียบเทียบมีอยู่ในฐานข้อมูลหลัก")

            # ---- Download Full Report ----
            st.markdown("---")
            st.markdown("### 📦 ดาวน์โหลดรายงานเต็ม (Excel)")

            output = io.BytesIO()
            show_main_cols = [sn_col] + [c for c in display_cols if c in df.columns]

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Sheet 1: Matched
                df_matched_full = df[df[sn_col].astype(str).str.strip().str.upper().isin(in_both)]
                df_matched_full[show_main_cols].reset_index(drop=True).to_excel(
                    writer, sheet_name="✅ ตรงกัน", index=False)

                # Sheet 2: Only in Main
                df_only_main_full = df[df[sn_col].astype(str).str.strip().str.upper().isin(only_in_main)]
                df_only_main_full[show_main_cols].reset_index(drop=True).to_excel(
                    writer, sheet_name="🔴 มีแค่ในฐานข้อมูลหลัก", index=False)

                # Sheet 3: Only in Compare
                df_only_cmp_full = df_cmp[df_cmp[cmp_sn_col].astype(str).str.strip().str.upper().isin(only_in_cmp)]
                df_only_cmp_full.reset_index(drop=True).to_excel(
                    writer, sheet_name="🟠 มีแค่ในไฟล์เปรียบเทียบ", index=False)

            output.seek(0)
            st.download_button(
                label="📥 ดาวน์โหลดรายงาน Excel (3 Sheet)",
                data=output.getvalue(),
                file_name="comparison_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    else:
        st.info("👆 อัปโหลดไฟล์เปรียบเทียบเพื่อเริ่มต้น")
        st.markdown("""
        **วิธีใช้งาน:**
        1. อัปโหลดไฟล์หลัก (ฐานข้อมูล) ทางแถบด้านซ้าย
        2. อัปโหลดไฟล์เปรียบเทียบในแท็บนี้
        3. เลือกคอลัมน์ S/N ของแต่ละไฟล์
        4. กด **เริ่มเปรียบเทียบ**

        **ผลลัพธ์ที่จะได้:**
        - ✅ รายการที่ตรงกันทั้งสองไฟล์
        - 🔴 S/N ที่มีในฐานข้อมูลหลัก **แต่ไม่มี**ในไฟล์เปรียบเทียบ
        - 🟠 S/N ที่มีในไฟล์เปรียบเทียบ **แต่ไม่มี**ในฐานข้อมูลหลัก
        """)

# ------------------------------------------------------------------ #
#  Data Preview
# ------------------------------------------------------------------ #
st.markdown("---")
with st.expander("📋 ดูข้อมูลทั้งหมด (ฐานข้อมูลหลัก)", expanded=False):
    filter_text = st.text_input("กรองข้อมูล (พิมพ์เพื่อกรองทุกคอลัมน์)", key="filter_all")
    if filter_text:
        mask_all = df.astype(str).apply(
            lambda col: col.str.upper().str.contains(filter_text.upper(), na=False)
        ).any(axis=1)
        filtered_df = df[mask_all]
        st.caption(f"แสดง {len(filtered_df):,} จาก {len(df):,} รายการ")
        st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True, height=400)
    else:
        st.caption(f"แสดงทั้งหมด {len(df):,} รายการ")
        st.dataframe(df.reset_index(drop=True), use_container_width=True, height=400)