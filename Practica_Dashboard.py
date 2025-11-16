import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings
import numpy as np  # Necesario para seleccionar columnas numéricas
from pathlib import Path

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Superstore!!!", page_icon=":bar_chart:", layout="wide")

# --- 1. INICIALIZAR EL ESTADO DE LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- 2. FUNCIÓN DE LOGIN ---
def check_login(user, password):
    return (
        user == st.secrets["mi_usuario"]
        and password == st.secrets["mi_password"]
    )

# --- 3. MOSTRAR EL LOGIN SI NO ESTÁ LOGUEADO ---
if not st.session_state.logged_in:
    st.sidebar.title("Login")
    user_input = st.sidebar.text_input("User", key="login_user")
    password_input = st.sidebar.text_input("Password", type="password", key="login_pass")
    
    if st.sidebar.button("Entrar", key="login_button"):
        if check_login(user_input, password_input):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.sidebar.error("Incorrect User or Password. Please Try Again")
    
    elif not user_input and not password_input:
        st.warning("Please introduce login credentials on the sidebar to access the dashboard.")

    # Detiene la app aquí. El resto del código no se ejecutará.
    st.stop() 

# --- 4. SI LLEGAS AQUÍ, ES PORQUE SÍ ESTÁS LOGUEADO ---

st.title(" :bar_chart: Sample SuperStore EDA")
fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "xlsx", "txt", "xls"]))

# --- 5. LÓGICA DE CARGA DE DATOS (CORREGIDA PARA GITHUB) ---
APP_DIR = Path(__file__).parent 
DEFAULT_FILE_PATH = APP_DIR / "Sample - Superstore.xls"

if fl is not None:
    # Si se sube un archivo...
    filename = fl.name
    st.write(filename)
    
    file_extension = filename.split('.')[-1].lower()

    if file_extension in ["xls", "xlsx"]:
        df = pd.read_excel(fl) 
    elif file_extension == "csv":
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    else:
        st.error("Formato de archivo no soportado. Sube un CSV o Excel.")
        df = pd.DataFrame() # Creamos un df vacío
else:
    # Carga por defecto si no se sube nada
    try:
        df = pd.read_excel(DEFAULT_FILE_PATH)
    except FileNotFoundError:
        st.error(f"Archivo por defecto no encontrado en: {DEFAULT_FILE_PATH}")
        st.info("Asegúrate de que 'Sample - Superstore.xls' está en tu repositorio de GitHub.")
        df = pd.DataFrame()
    except Exception as e:
        st.error(f"Error al leer el archivo por defecto: {e}")
        df = pd.DataFrame()


# --- VALIDACIÓN ---
if df.empty:
    st.warning("No hay datos para analizar. Sube un archivo válido.")
    st.stop() # Detiene el script para evitar errores

# --- 6. FILTROS DEL SIDEBAR ---
# Ahora que 'df' existe, creamos los filtros.
st.sidebar.header("Choose your filter: ")
region = st.sidebar.multiselect("Pick your Region", df["Region"].unique(), key="region_filter")
if not region:
    df2 = df.copy()
else:
    df2 = df[df["Region"].isin(region)]

state = st.sidebar.multiselect("Pick the State", df2["State"].unique(), key="state_filter")
if not state:
    df3 = df2.copy()
else:
    df3 = df2[df2["State"].isin(state)]

city = st.sidebar.multiselect("Pick the City", df3["City"].unique(), key="city_filter")

# Botón de Logout
if st.sidebar.button("Logout", key="logout_button"):
    st.session_state.logged_in = False # Olvida que estaba logueado
    st.rerun() # Vuelve a correr (y mostrará el login)


# --- 7. EL RESTO DE TU DASHBOARD (Página principal) ---

col1, col2 = st.columns((2))
df["Order Date"] = pd.to_datetime(df["Order Date"])

#Getting the min and max date 
startDate = pd.to_datetime(df["Order Date"]).min()
endDate = pd.to_datetime(df["Order Date"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))  

df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)]

#Filter the dataframe based on Region, State and City
if not city:
    filtered_df = df3.copy()
else:
    filtered_df = df3[df3["City"].isin(city)]

category_df = filtered_df.groupby(by = ["Category"], as_index= False)["Sales"].sum()

with col1:
    st.subheader("Sales by Category")
    fig = px.bar(category_df, x = "Category", y = "Sales", text = ["${:,.2f}".format(x) for x in category_df["Sales"]],
                template = "seaborn")
    # --- HOVER FIX ---
    fig.update_traces(hovertemplate="<b>Categoría</b>: %{x}<br><b>Ventas</b>: %{y:$,.2f}")
    st.plotly_chart(fig, use_container_width= True, height= 200)

with col2:
    st.subheader("Sales by Region")
    fig = px.pie(filtered_df, values = "Sales", names = "Region", hole = 0.5)
    # --- HOVER FIX ---
    fig.update_traces(text = filtered_df["Region"], textposition = "outside",
                      hovertemplate="<b>Región</b>: %{label}<br><b>Ventas</b>: %{value:$,.2f}<br><b>Porcentaje</b>: %{percent}")
    st.plotly_chart(fig, use_container_width=True)

cl1 , cl2 = st.columns(2)
with cl1:
    with st.expander("Category_ViewData"):
        st.write(category_df.style.background_gradient(cmap = "Blues"))
        csv = category_df.to_csv(index = False).encode("utf-8")
        st.download_button("Download Data", data = csv, file_name="Category.csv", mime = "text/csv",
                            help = "Click here to Download the Data as a CSV file", key="csv_category")
    
with cl2:
    with st.expander("Region_ViewData"):
        region_df = filtered_df.groupby(by = "Region", as_index = False)["Sales"].sum()
        st.write(region_df.style.background_gradient(cmap = "Oranges"))
        csv = region_df.to_csv(index = False).encode("utf-8")
        st.download_button("Download Data", data = csv, file_name="Region.csv", mime = "text/csv",
                            help = "Click here to Download the Data as a CSV file", key="csv_region")

filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")

# --- CAMBIO 1: TIME SERIES DINÁMICO ---
st.subheader("Time-Series Analysis")

# 1. Lista de columnas numéricas
numeric_cols = filtered_df.select_dtypes(include=np.number).columns.tolist()

# 2. Selector para la métrica (Y-axis)
time_y_var = st.selectbox(
    "Elige la métrica para la serie de tiempo:", 
    numeric_cols, 
    index=numeric_cols.index('Sales') if 'Sales' in numeric_cols else 0, 
    key="time_y"
)

# 3. Gráfico dinámico
linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))[time_y_var].sum()).reset_index()
# --- HOVER FIX: Quitado el 'labels' que creaba "Monto Total" ---
fig2 = px.line(linechart, x = "month_year", y = time_y_var, height = 500, width = 1000, template = "gridon")

# 4. Arreglo del Hover (Formato) - Ahora usa la variable dinámica 'time_y_var'
fig2.update_traces(hovertemplate=f"<b>Mes</b>: %{{x}}<br><b>{time_y_var}</b>: %{{y:$,.2f}}")
st.plotly_chart(fig2, use_container_width= True)
# --- FIN CAMBIO 1 ---

with st.expander("View TimeSeries Data: "):
    st.write(linechart.style.background_gradient(cmap = "Blues"))
    csv = linechart.to_csv(index = False).encode("utf-8")
    st.download_button("Download Data", data = csv, file_name="TimeSeries.csv", mime = "text/csv",
                        help = "Click here to Download the Data as a CSV file", key="csv_timeseries")
    
#Create a tree map based on Region, Category, and sub-Category
st.subheader("Hierarchical View of Sales using TreeMap")
fig3 = px.treemap(filtered_df, path = ("Region", "Category", "Sub-Category"), values = "Sales", hover_data=["Sales"],
                color = "Sub-Category")
fig3.update_layout(width = 800, height = 650)
# --- HOVER FIX ---
fig3.update_traces(hovertemplate="<b>%{label}</b><br><b>Ventas</b>: %{value:$,.2f}<br><b>Padre</b>: %{parent}")
st.plotly_chart(fig3, use_container_width= True)

chart1, chart2 = st.columns(2)
with chart1:
    st.subheader("Sales by Segment")
    fig = px.pie(filtered_df, values = "Sales", names = "Segment", template = "plotly_dark")
    # --- HOVER FIX ---
    fig.update_traces(text = filtered_df["Segment"], textposition = "inside",
                      hovertemplate="<b>Segmento</b>: %{label}<br><b>Ventas</b>: %{value:$,.2f}<br><b>Porcentaje</b>: %{percent}")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("Sales by Category")
    fig = px.pie(filtered_df, values = "Sales", names = "Category", template = "gridon")
    # --- HOVER FIX ---
    fig.update_traces(text = filtered_df["Category"], textposition = "inside",
                      hovertemplate="<b>Categoría</b>: %{label}<br><b>Ventas</b>: %{value:$,.2f}<br><b>Porcentaje</b>: %{percent}")
    st.plotly_chart(fig, use_container_width=True)

import plotly.figure_factory as ff
st.subheader(":point_right: Month Wise Sub-Category Sales Summary")
with st.expander("Summary_Table"):
    df_sample = df[0:5][["Region", "State", "City", "Category", "Sub-Category", "Sales", "Profit", "Quantity"]]
    fig = ff.create_table(df_sample, colorscale="cividis")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("Month wise Sub-Category Table")
    filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
    sub_category_Year = pd.pivot_table(data = filtered_df, values = "Sales", index = ["Sub-Category"], columns = "month")
    st.write(sub_category_Year.style.background_gradient(cmap = "Blues"))

# --- CAMBIO 2: SCATTER PLOT DINÁMICO Y CON HOVER LIMPIO ---
st.subheader("Scatter Plot")

# 1. Selectores de variables (usamos 'numeric_cols' que ya definimos)
col_x, col_y, col_size = st.columns(3)
with col_x:
    x_var = st.selectbox("Elige la variable X:", numeric_cols, index=numeric_cols.index('Sales') if 'Sales' in numeric_cols else 0, key="scatter_x")
with col_y:
    y_var = st.selectbox("Elige la variable Y:", numeric_cols, index=numeric_cols.index('Profit') if 'Profit' in numeric_cols else 0, key="scatter_y")
with col_size:
    size_var = st.selectbox("Elige la variable de Tamaño:", numeric_cols, index=numeric_cols.index('Quantity') if 'Quantity' in numeric_cols else 0, key="scatter_size")

# 2. Gráfico dinámico
data1 = px.scatter(filtered_df, x = x_var, y = y_var, size = size_var, custom_data=[x_var, y_var, size_var])

# 3. Arreglo del Hover (Formato)
# --- HOVER FIX --- (Mantenemos el formato bueno, con etiquetas y formato de moneda)
data1.update_traces(hovertemplate=f"<b>{x_var}</b>: %{{x:$,.2f}}<br><b>{y_var}</b>: %{{y:$,.2f}}<br><b>{size_var}</b>: %{{customdata[2]:,.0f}}")

# 4. Actualización del layout (títulos dinámicos)
data1.update_layout(
    title=dict(
        text=f"Relación entre {x_var} y {y_var}",
        font=dict(size=20)
    ),
    xaxis=dict(
        title=dict(
            text=x_var,
            font=dict(size=19)
        )
    ),
    yaxis=dict(
        title=dict(
            text=y_var,
            font=dict(size=19)
        )
    )
)
st.plotly_chart(data1, use_container_width= True)
# --- FIN CAMBIO 2 ---

with st.expander("View Data"):
    st.write(filtered_df.iloc[:500,1:20:2].style.background_gradient(cmap = "Oranges"))

#Download original Data
csv = df.to_csv(index = False).encode("utf-8")
st.download_button("Download Data", data = csv, file_name= "Data.csv", mime = "text/csv/", key="csv_main")
