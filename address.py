import streamlit as st
import pandas as pd
import base64
import io
from difflib import get_close_matches
from vobject import readOne  # for parsing vCard

st.set_page_config(page_title="📱 Contact Manager", layout="centered")
st.title("📲 Contact Import & Export Tool")

st.markdown("""
This app helps you **import/export contact data** from mobile or Gmail (CSV or vCard format), and apply value-added features like deduplication, domain tagging, and formatting.
""")

# ----------------------- INPUT -----------------------
uploaded_file = st.file_uploader("Upload contact CSV or vCard (.vcf) file", type=["csv", "vcf"])

if uploaded_file:
    file_name = uploaded_file.name

    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif file_name.endswith(".vcf"):
        contacts = []
        content = uploaded_file.read().decode("utf-8")
        for block in content.strip().split("END:VCARD"):
            if block.strip():
                try:
                    v = readOne(block + "END:VCARD\n")
                    name = v.fn.value if hasattr(v, 'fn') else ""
                    phone = v.tel.value if hasattr(v, 'tel') else ""
                    email = v.email.value if hasattr(v, 'email') else ""
                    contacts.append({"Name": name, "Phone": phone, "Email": email})
                except Exception:
                    pass
        df = pd.DataFrame(contacts)

    st.success("✅ File loaded successfully!")
    st.write("### Preview of Uploaded Data")
    st.dataframe(df.head())

    # ----------------------- VALUE ADDITIONS -----------------------
    st.subheader("🔍 Value-Added Options")

    if st.checkbox("Remove duplicates by Name & Phone"):
        df = df.drop_duplicates(subset=["Name", "Phone"], keep="first")
        st.info(f"Duplicate contacts removed. {len(df)} remaining.")

    if st.checkbox("Tag contacts with Gmail/Yahoo/Other"):
        def tag_domain(email):
            if pd.isna(email): return "Unknown"
            if "gmail" in email: return "Gmail"
            elif "yahoo" in email: return "Yahoo"
            else: return "Other"

        df["EmailProvider"] = df["Email"].apply(tag_domain)
        st.success("Tagged email domains.")
        st.dataframe(df[["Name", "Email", "EmailProvider"]])

    if st.checkbox("Format phone numbers"):
        def format_phone(phone):
            phone = str(phone).replace(" ", "").replace("-", "")
            if phone.startswith("+91"):
                return phone
            elif phone.startswith("0"):
                return "+91" + phone[1:]
            elif len(phone) == 10:
                return "+91" + phone
            return phone

        df["Phone"] = df["Phone"].apply(format_phone)
        st.success("Phone numbers formatted.")

    if st.checkbox("Suggest possible merges (fuzzy match)"):
        st.write("Possible duplicates based on similar names:")
        suggestions = []
        names = df["Name"].dropna().unique().tolist()
        for name in names:
            matches = get_close_matches(name, names, n=3, cutoff=0.85)
            if len(matches) > 1:
                suggestions.append(matches)

        if suggestions:
            for group in suggestions:
                st.warning(f"Similar contacts: {', '.join(group)}")
        else:
            st.success("No fuzzy duplicates found.")

    # ----------------------- EXPORT -----------------------
    st.subheader("⬇️ Export Processed Data")
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="contacts_cleaned.csv">📅 Download CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

    # -------- Export as vCard --------
    def create_vcard(row):
        vcard = "BEGIN:VCARD\n"
        vcard += "VERSION:3.0\n"
        vcard += f"FN:{row.get('Name','')}\n"
        vcard += f"TEL:{row.get('Phone','')}\n"
        if pd.notna(row.get('Email')):
            vcard += f"EMAIL:{row.get('Email')}\n"
        vcard += "END:VCARD\n"
        return vcard

    if st.button("📇 Export as vCard"):
        vcard_data = "".join(df.apply(create_vcard, axis=1).tolist())
        b64_vcf = base64.b64encode(vcard_data.encode()).decode()
        href_vcf = f'<a href="data:text/vcard;base64,{b64_vcf}" download="contacts.vcf">📄 Download vCard (.vcf)</a>'
        st.markdown(href_vcf, unsafe_allow_html=True)

else:
    st.info("👈 Upload a contact file to begin.")

