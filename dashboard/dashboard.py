import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

# Helper function
def create_sum_casual_user_df(df):
    sum_casual_user_df = df.groupby("dteday").casual.sum().sort_values(ascending=False).reset_index()
    return sum_casual_user_df

def create_sum_registered_user_df(df):
    sum_registered_user_df = df.groupby("dteday").registered.sum().sort_values(ascending=False).reset_index()
    return sum_registered_user_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("dteday").cnt.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_byweather_df(df):
    byweather_df = df.groupby("weathersit").cnt.sum().sort_values(ascending=False).reset_index()
    return byweather_df

def create_byseason_df(df):
    byseason_df = df.groupby("season").cnt.sum().sort_values(ascending=False).reset_index()
    return byseason_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="dteday", as_index=False).agg({
        "dteday": "max",         # Mengambil tanggal terakhir untuk recency
        "instant": "nunique",    # Menghitung frekuensi unik pengguna
        "cnt": "sum"             # Menghitung total jumlah pengguna
    })
    rfm_df.columns = ["dteday", "max_order_timestamp", "monetary"]
    
    # Mengonversi max_order_timestamp menjadi datetime
    rfm_df["max_order_timestamp"] = pd.to_datetime(rfm_df["max_order_timestamp"])
    
    # Menghitung recency (jarak hari dari transaksi terakhir)
    recent_date = df["dteday"].max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    
    # Menghapus kolom max_order_timestamp
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

def create_daily_orders_df(df):
    df['dteday'] = pd.to_datetime(df['dteday'])
    daily_orders_df = df.resample('M', on='dteday').sum()
    return daily_orders_df

# Prepare dataframe
day_df = pd.read_csv("dashboard/main_data.csv")

# Ensure the date column is of type datetime
datetime_columns = ["dteday"]  # Menggunakan kolom dteday sesuai dengan dataset
day_df.sort_values(by="dteday", inplace=True)  # diurutkan berdasarkan tanggal
day_df.reset_index(drop=True, inplace=True)  # Reset index

# Mengubah setiap kolom di datetime_columns menjadi tipe datetime
for column in datetime_columns:
    day_df[column] = pd.to_datetime(day_df[column])

# Create filter components
min_date = day_df["dteday"].min()  # Mengambil tanggal minimum dari kolom dteday
max_date = day_df["dteday"].max()  # Mengambil tanggal maksimum dari kolom dteday

with st.sidebar:
    st.image("dashboard/bike.jpg")  # Menampilkan gambar di sidebar
    start_date, end_date = st.date_input(
        label='Range of Time', 
        min_value=min_date,      # Tanggal minimum sebagai batas bawah
        max_value=max_date,      # Tanggal maksimum sebagai batas atas
        value=[min_date, max_date]  # Rentang waktu awal dan akhir default
    )

# Memfilter dataframe berdasarkan rentang tanggal yang dipilih
main_df = day_df[(day_df["dteday"] >= pd.to_datetime(start_date)) &
                 (day_df["dteday"] <= pd.to_datetime(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_casual_user_df = create_sum_casual_user_df(main_df)
sum_registered_user_df = create_sum_registered_user_df(main_df)
byweather_df = create_byweather_df(main_df)
byseason_df = create_byseason_df(main_df)
rfm_df = create_rfm_df(main_df)

# Cek apakah perubahan berhasil
print(_df[['season', 'weathersit']].head())
# Create dashboard
st.header('Bike Sharing Dashboard :bar_chart:')

# 1. Persentase Total Pengguna Berdasarkan Musim
st.subheader("Persentase Total Pengguna Berdasarkan Musim")

total_users_per_season = byseason_df['cnt'].sum() # Hitung total pengguna per musim
byseason_df['percent'] = (byseason_df['cnt'] / total_users_per_season) * 100 # Hitung persentase pengguna per musim

# Visualisasi dengan pie chart
fig, ax = plt.subplots(figsize=(10, 6))
ax.pie(byseason_df['percent'], labels=byseason_df['season'], autopct='%1.1f%%', startangle=90, colors=sns.color_palette("coolwarm", len(byseason_df)))
ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
plt.title("Persentase Total Pengguna Berdasarkan Musim", fontsize=20)
st.pyplot(fig)

# 2. Persentase Pengguna Terdaftar Per Bulan
st.subheader("Tren Pengguna Terdaftar Per Bulan")

# Ambil data per bulan untuk pengguna terdaftar
monthly_registered_users = main_df.resample('M', on='dteday')['registered'].sum().reset_index()

# Hitung persentase perubahan dari bulan ke bulan
monthly_registered_users['percent_change'] = monthly_registered_users['registered'].pct_change() * 100

# Visualisasi tren pengguna terdaftar
plt.figure(figsize=(10, 6))
plt.plot(monthly_registered_users['dteday'], monthly_registered_users['registered'], marker='o', color='#A5C0DD')
plt.title('Tren Pengguna Terdaftar Per Bulan', fontsize=20)
plt.xlabel('Bulan')
plt.ylabel('Jumlah Pengguna Terdaftar')
plt.xticks(rotation=45)
plt.grid(True)
st.pyplot(plt)

# 3. Distribusi Pengguna Biasa dan Tetap Berdasarkan Cuaca dan Musim
st.subheader("Distribusi Pengguna Biasa dan Tetap Berdasarkan Cuaca dan Musim")

# Gabungkan data cuaca dan musim
weather_season_df = main_df.groupby(['season', 'weathersit']).agg({
    'casual': 'sum',
    'registered': 'sum'
}).reset_index()

# Plot distribusi pengguna kasual dan terdaftar berdasarkan cuaca dan musim
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

# Visualisasi pengguna kasual berdasarkan cuaca dan musim
sns.barplot(x="casual", y="season", hue="weathersit", data=weather_season_df, palette='coolwarm', ax=ax[0])
ax[0].set_title("Pengguna Kasual Berdasarkan Cuaca dan Musim", fontsize=20)
ax[0].set_xlabel("Jumlah Pengguna Kasual")
ax[0].set_ylabel("Musim")
ax[0].tick_params(axis='x', labelsize=15)
ax[0].tick_params(axis='y', labelsize=15)

# Visualisasi pengguna terdaftar berdasarkan cuaca dan musim
sns.barplot(x="registered", y="season", hue="weathersit", data=weather_season_df, palette='coolwarm', ax=ax[1])
ax[1].set_title("Pengguna Terdaftar Berdasarkan Cuaca dan Musim", fontsize=20)
ax[1].set_xlabel("Jumlah Pengguna Terdaftar")
ax[1].set_ylabel("Musim")
ax[1].tick_params(axis='x', labelsize=15)
ax[1].tick_params(axis='y', labelsize=15)

st.pyplot(fig)

# RFM Analysis
# Mempersiapkan figure untuk dua bar chart
fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(21, 6))

# Bar chart untuk Recency
sns.barplot(ax=axes[0], x='dteday', y='recency', data=rfm_df, color='b')
axes[0].set_title('Recency per Day')
axes[0].set_ylabel('Recency (Days)')
axes[0].set_xlabel('Day')
axes[0].tick_params(axis='x', rotation=45)  # Rotate x labels for better readability

# Bar chart untuk Monetary
sns.barplot(ax=axes[1], x='dteday', y='monetary', data=rfm_df, color='g')
axes[1].set_title('Monetary per Day')
axes[1].set_ylabel('Monetary')
axes[1].set_xlabel('Day')
axes[1].tick_params(axis='x', rotation=45)  # Rotate x labels for better readability

st.pyplot(fig)
