import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import requests
import io
from datetime import datetime, timedelta

# --------------------------
# 🧠 Fonksiyon: Veri indir
# --------------------------
@st.cache_data
def download_takasbank_excel(t_date: datetime):
    fon_grubu = "F"
    fon_turu = "99999"
    key = "rT4AQ2R2lXyX-Ys9LzTkPbJ8szIKc4w1xwMbqV-1v984zpEau4bixJOrFrmS9sM_0"

    dates = {
        "t": t_date,
        "t7": t_date - timedelta(days=7),
        "t28": t_date - timedelta(days=28)
    }

    dfs = {}
    for label, date in dates.items():
        date_str = date.strftime("%Y%m%d")
        url = f"https://www.takasbank.com.tr/plugins/ExcelExportPortfoyStatistics?reportType=P&type={fon_grubu}&fundType={fon_turu}&endDate={date_str}&startDate={date_str}&key={key}&lang=T&language=tr"
        response = requests.get(url)
        dfs[label] = pd.read_excel(io.BytesIO(response.content))

    return dfs["t"], dfs["t7"], dfs["t28"]

# --------------------------
# 📦 PYŞ fon akım verisi
# --------------------------
@st.cache_data
def load_main_data():
    url_id = "1ZptN78nnE4i-YTDvcy0DiUtTQ5SWDJJ7"
    url = f"https://drive.google.com/uc?id={url_id}"
    output = "main_df.pkl"

    if not os.path.exists(output):
        import gdown
        gdown.download(url, output, quiet=False)
    return pd.read_pickle(output)

# --------------------------
# 🎛️ Sidebar
# --------------------------
st.sidebar.header("Filtreler")

# PYŞ Dashboard için filtreler
main_df = load_main_data()
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

selected_pysh = st.sidebar.selectbox("PYŞ seçin", pysh_list)
selected_range = st.sidebar.selectbox("Zaman aralığı", list(range_dict.keys()))
day_count = range_dict[selected_range]

# Takasbank için tarih
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Takasbank Tarih Seçimi")
selected_date = st.sidebar.date_input("Tarih seç", value=datetime.today())
start = st.sidebar.button("📥 Veriyi Getir ve Göster")

# --------------------------
# 🖥️ Sayfa Başlığı
# --------------------------
st.title("Fon Akımları Dashboard")

# --------------------------
# PYŞ Grafiği
# --------------------------
last_dates = main_df["Tarih"].drop_duplicates().sort_values(ascending=False).head(day_count)
pysh_df = main_df[(main_df["PYŞ"] == selected_pysh) & (main_df["Tarih"].isin(last_dates))]
total_flows = pysh_df[asset_columns].sum()

summary_df = pd.DataFrame({
    "Varlık Sınıfı": asset_columns_clean,
    "Toplam Flow (mn)": total_flows.values / 1e6
}).sort_values(by="Toplam Flow (mn)", ascending=False)

total_sum_mn = summary_df["Toplam Flow (mn)"].sum()
fig1 = px.bar(
    summary_df,
    x="Varlık Sınıfı",
    y="Toplam Flow (mn)",
    title=f"{selected_pysh} - {selected_range} Net Fon Akımı (Toplam: {total_sum_mn:,.0f} mn TL)",
    color_discrete_sequence=["#8cc5e3"]
)
fig1.update_layout(
    xaxis_title="Varlık Sınıfı",
    yaxis_title="Toplam Flow (mn)",
    yaxis_tickformat=",.0f",
    plot_bgcolor="#f7f7f7",
    paper_bgcolor="#ffffff",
    xaxis_tickfont=dict(weight="bold"),
    title_font=dict(size=18)
)
st.plotly_chart(fig1, use_container_width=True)

# --------------------------
# Takasbank Grafiği
# --------------------------
if start:
    st.write(f"⏳ {selected_date.strftime('%Y-%m-%d')} için veriler indiriliyor...")
    t_df, t7_df, t28_df = download_takasbank_excel(selected_date)

    main_items = [
        "Hisse Senedi", "Devlet Tahvili", "Finansman Bonosu", "Kamu Dış Borçlanma Araçları",
        "Özel Sektör Dış Borçlanma Araçları", "Takasbank Para Piyasası İşlemleri",
        "Kamu Kira Sertifikaları (Döviz)", "Özel Sektör Kira Sertifikaları", "Özel Sektör Yurt Dışı Kira Sertifikaları",
        "Vadeli Mevduat (Döviz)", "Katılma Hesabı (Döviz)", "Repo Islemleri", "Kıymetli Madenler",
        "Yabancı Borsa Yatırım Fonları", "Borsa Yatırım Fonları Katılma Payları", "Vadeli İşlemler Nakit Teminatları",
        "Diğer", "TOPLAM"
    ]

    def prepare(df):
        return df[df[df.columns[0]].isin(main_items)].set_index(df.columns[0])[df.columns[1]]

    data = {
        "t": prepare(t_df),
        "t7": prepare(t7_df),
        "t28": prepare(t28_df)
    }

    df = pd.concat(data.values(), axis=1)
    df.columns = data.keys()
    total = df.loc["TOPLAM"]

    df_percent = df.drop("TOPLAM").div(total, axis=1)
    df_percent["Haftalık Değişim"] = (df_percent["t"] - df_percent["t7"]) * 10000
    df_percent["Aylık Değişim"] = (df_percent["t"] - df_percent["t28"]) * 10000
    df_percent = df_percent.round(1)

    plot_data = df_percent[["Haftalık Değişim", "Aylık Değişim"]].reset_index().melt(id_vars=df_percent.index.name, var_name="Dönem", value_name="bps")
    fig2 = px.bar(
        plot_data,
        x="bps",
        y=df_percent.index.name,
        color="Dönem",
        orientation="h",
        title=f"Takasbank Varlık Dağılımı Değişimi - {selected_date.strftime('%d %B %Y')}",
        color_discrete_map={"Haftalık Değişim": "#162336", "Aylık Değişim": "#cc171d"}
    )
    fig2.update_layout(
        xaxis_title="Değişim (bps)",
        yaxis_title="Varlık Sınıfı",
        plot_bgcolor="#f7f7f7",
        paper_bgcolor="#ffffff",
        title_font=dict(size=18),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig2, use_container_width=True)
