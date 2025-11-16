import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings
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

    # Detiene la app aquí si no estás logueado.
    st.stop() 

# --- 4. SI LLEGAS AQUÍ, ES PORQUE SÍ ESTÁS LOGUEADO ---
# Ahora cargamos los datos PRIMERO.

st.title(" :bar_chart: Sample SuperStore EDA")

fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "xlsx", "txt", "xls"]))

# --- Lógica de Carga de Datos ---
if fl is not None:
    filename = fl.name
    st.write(filename)
    
    file_extension = filename.split('.')[-1].lower()

    if file_extension in ["xls", "xlsx"]:
        df = pd.read_excel(fl) 
    elif file_extension == "csv":
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    else:
        st.error("Formato de archivo no soportado. Sube un CSV o Excel.")
        df = pd.DataFrame()

else:
    # Carga por defecto
    os.chdir("/Users/alecab/Documents/PYTHON/")
    df = pd.read_excel("Sample - Superstore.xls")

# --- VALIDACIÓN ---
# Si el df está vacío (ej: se subió un .txt), paramos aquí.
if df.empty:
    st.warning("No hay datos para analizar. Sube un archivo válido.")
    st.stop()

# --- 5. AHORA SÍ, CREAMOS LOS FILTROS DEL SIDEBAR ---
# (Porque 'df' ya existe)

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
    st.session_state.logged_in = False
    st.rerun()

# --- 6. EL RESTO DE TU DASHBOARD (Página principal) ---

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
    st.plotly_chart(fig, use_container_width= True, height= 200)

with col2:
    st.subheader("Sales by Region")
    fig = px.pie(filtered_df, values = "Sales", names = "Region", hole = 0.5)
    fig.update_traces(text = filtered_df["Region"], textposition = "outside")
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
st.subheader("Time Series Analysis")

linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))["Sales"].sum()).reset_index()
fig2 = px.line(linechart, x = "month_year", y = "Sales", labels = {"Sales": "Amount"}, height = 500, width = 1000, template = "gridon")
st.plotly_chart(fig2, use_container_width= True)

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
st.plotly_chart(fig3, use_container_width= True)

chart1, chart2 = st.columns(2)
with chart1:
    st.subheader("Sales by Segment")
    fig = px.pie(filtered_df, values = "Sales", names = "Segment", template = "plotly_dark")
    fig.update_traces(text = filtered_df["Segment"], textposition = "inside")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("Sales by Category")
    fig = px.pie(filtered_df, values = "Sales", names = "Category", template = "gridon")
    fig.update_traces(text = filtered_df["Category"], textposition = "inside")
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

# Create a Scatterplot
data1 = px.scatter(filtered_df, x = "Sales", y = "Profit", size = "Quantity")
data1["layout"].update(
    title = dict(
        text = "Relationship between Sales and Profit using Scatterplot.",
        font = dict(size = 20)
    ),
    xaxis = dict(
        title = dict(
            text = "Sales",
            font = dict(size = 19)
        )
    ),
    yaxis = dict(
        title = dict(
            text = "Profit",
            font = dict(size = 19)
        )
    )
)
st.plotly_chart(data1, use_container_width= True)

with st.expander("View Data"):
    st.write(filtered_df.iloc[:500,1:20:2].style.background_gradient(cmap = "Oranges"))

#Download original Data
csv = df.to_csv(index = False).encode("utf-8")
st.download_button("Download Data", data = csv, file_name= "Data.csv", mime = "text/csv/", key="csv_main")