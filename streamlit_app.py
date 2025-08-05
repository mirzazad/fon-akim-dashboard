import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

@st.cache_data
def load_data():
    # Google Drive dosya ID
    file_id = "1ZptN78nnE4i-YTDvcy0DiUtTQ5SWDJJ7"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Dosya indirilemedi.")
        return None
    
    return pd.read_pickle(io.BytesIO(response.content))

main_df = load_data()
if main_df is None:
    st.stop()

# 🔍 Filtreler
main_df["Tarih"] = pd.to_datetime(main_df["Tarih"])
asset_columns = [col for col in main_df.columns if col.endswith("_TL")]
asset_columns_clean = [col.replace("_TL", "") for col in asset_columns]

pysh_list = sorted(main_df["PYŞ"].dropna().unique())
range_dict = {
    "1 Hafta": 5,
    "1 Ay": 22,
    "3 Ay": 66,
    "6 Ay": 126,
    "1 Yıl": 252
}

# 🧭 Sidebar
st.sidebar.header("Filtreler")
selected_pysh = st.sidebar.selectbox("PYŞ seçin", pysh_list)
selected_range = st.sidebar.selectbox("Zaman aralığı", list(range_dict.keys()))
day_count = range_dict[selected_range]

# 📊 Veri Hazırlığı
last_dates = main_df["Tarih"].drop_duplicates().sort_values(ascending=False).head(day_count)
pysh_df = main_df[(main_df["PYŞ"] == selected_pysh) & (main_df["Tarih"].isin(last_dates))]
total_flows = pysh_df[asset_columns].sum()

summary_df = pd.DataFrame({
    "Varlık Sınıfı": asset_columns_clean,
    "Toplam Flow (mn)": total_flows.values / 1e6
}).sort_values(by="Toplam Flow (mn)", ascending=False)
total_sum_mn = summary_df["Toplam Flow (mn)"].sum()

# 📈 Grafik
fig = px.bar(
    summary_df,
    x="Varlık Sınıfı",
    y="Toplam Flow (mn)",
    title=f"{selected_pysh} - {selected_range} Net Fon Akımı (Toplam: {total_sum_mn:,.1f} mn TL)",
    color_discrete_sequence=["#191970"]
)

fig.update_layout(
    title_font=dict(size=20, family="Segoe UI Semibold", color="black"),
    xaxis_title="Varlık Sınıfı",
    yaxis_title="Toplam Flow (mn)",
    yaxis_tickformat=",.0f",
    xaxis=dict(
        tickfont=dict(size=13, family="Segoe UI Semibold", color="black")
    ),
    yaxis=dict(
        tickfont=dict(size=13, family="Segoe UI Semibold", color="black")
    ),
    font=dict(
        size=13,
        family="Segoe UI",
        color="black"
    ),
    plot_bgcolor="#f7f7f7",
    paper_bgcolor="#ffffff"
)

# 🖥️ Göster
st.title("Fon Akımları Dashboard")
st.plotly_chart(fig, use_container_width=True)

