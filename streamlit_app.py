import streamlit as st
import pandas as pd
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
# 🎛️ Sidebar Ayarları
# --------------------------
st.sidebar.header("📅 Takasbank Veri Seçimi")
selected_date = st.sidebar.date_input("Tarih seç", value=datetime.today())
start = st.sidebar.button("📥 Veriyi Getir ve Göster")

# --------------------------
# 🚀 Başla Butonuna Basıldıysa
# --------------------------
if start:
    st.write(f"⏳ {selected_date.strftime('%Y-%m-%d')} için veriler indiriliyor...")
    t_df, t7_df, t28_df = download_takasbank_excel(selected_date)

    # --------------------------
    # 🔎 Filtrele & Hazırla
    # --------------------------
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

    # --------------------------
    # 📈 Grafik
    # --------------------------
    plot_data = df_percent[["Haftalık Değişim", "Aylık Değişim"]]
    t_amount_billion = df.drop("TOPLAM")["t"] / 1e9

    fig, ax1 = plt.subplots(figsize=(12, 10))
    plot_data.plot(
        kind="barh",
        ax=ax1,
        width=0.6,
        color={"Haftalık Değişim": "#162336", "Aylık Değişim": "#cc171d"}
    )

    ax1.set_title(f"Varlık Sınıfında Değişim ({selected_date.strftime('%d %B %Y')})", fontsize=16)
    ax1.set_xlabel("Değişim (bps)", fontsize=12)
    ax1.set_ylabel("Varlık Sınıfı", fontsize=12)
    ax1.grid(axis="x", linestyle="--", alpha=0.6)
    ax1.legend(loc="lower right")
    ax1.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f'))
    ax1.invert_yaxis()

    # 🔵 Noktalar: Varlık büyüklüğü
    ax2 = ax1.twiny()
    ax2.scatter(t_amount_billion.values, range(len(t_amount_billion)), color="royalblue", marker="o")
    ax2.set_xlabel("Büyüklük (Milyar TL)", fontsize=12)
    ax2.set_xlim(0, t_amount_billion.max() * 1.3)
    ax2.set_yticks(range(len(t_amount_billion)))
    ax2.set_yticklabels(df_percent.index.tolist())

    for i, value in enumerate(t_amount_billion.values):
        label = f"{int(round(value)):,}".replace(",", ".")
        ax2.text(
            value * 1.05,
            i,
            label,
            va='center',
            fontsize=11,
            color="#355765",
            bbox=dict(boxstyle="round,pad=0.1", facecolor="#FFFFFF90", edgecolor="none")
        )

    st.pyplot(fig)
