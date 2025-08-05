import streamlit as st
import pandas as pd
import plotly.express as px  # 🔧 eksik olan bu
import gdown
import os


@st.cache_data
def load_data():
    url_id = "1ZptN78nnE4i-YTDvcy0DiUtTQ5SWDJJ7"  # kendi dosya ID'ni buraya yaz
    url = f"https://drive.google.com/uc?id={url_id}"
    output = "main_df.pkl"

    if not os.path.exists(output):  # sadece ilk sefer indirir
        gdown.download(url, output, quiet=False)
    return pd.read_pickle(output)

main_df = load_data()


# --------------------------
# 🔍 Filtreleme ayarları
# --------------------------
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

# --------------------------
# 🧭 Sidebar
# --------------------------
st.sidebar.header("Filtreler")
selected_pysh = st.sidebar.selectbox("PYŞ seçin", pysh_list)
selected_range = st.sidebar.selectbox("Zaman aralığı", list(range_dict.keys()))
day_count = range_dict[selected_range]

# --------------------------
# 📊 Veri Hazırlığı
# --------------------------
last_dates = main_df["Tarih"].drop_duplicates().sort_values(ascending=False).head(day_count)
pysh_df = main_df[(main_df["PYŞ"] == selected_pysh) & (main_df["Tarih"].isin(last_dates))]
total_flows = pysh_df[asset_columns].sum()

summary_df = pd.DataFrame({
    "Varlık Sınıfı": asset_columns_clean,
    "Toplam Flow (mn)": total_flows.values / 1e6
}).sort_values(by="Toplam Flow (mn)", ascending=False)
total_sum_mn = summary_df["Toplam Flow (mn)"].sum()




# --------------------------
# 📈 Grafik
# --------------------------
fig = px.bar(
    summary_df,
    x="Varlık Sınıfı",
    y="Toplam Flow (mn)",
    title=f"{selected_pysh} - {selected_range} Net Fon Akımı (Toplam: {total_sum_mn:.1f} mn TL)",
    color_discrete_sequence=["#8cc5e3"]
)

fig.update_layout(
    xaxis_title="Varlık Sınıfı",
    yaxis_title="Toplam Flow (mn)",
    yaxis_tickformat=",.0f",
    plot_bgcolor="#f7f7f7",
    paper_bgcolor="#ffffff"
)

# --------------------------
# 🖥️ Sayfa Gösterimi
# --------------------------
st.title("Fon Akımları Dashboard")
st.plotly_chart(fig, use_container_width=True)


