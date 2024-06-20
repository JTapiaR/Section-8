import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

# Configuración de la página
st.set_page_config(
    page_title="Section-8 Properties Map",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título visible en la aplicación
st.title("Section-8 Properties Map 🏂")

# Función para cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('Datos/Data_Final.csv')

    # Asegurarse de que 'FMR' y 'rent_estimate' son numéricos

    return df

@st.cache_data
def get_filtered_data(state, counties, home_types):
    df = load_data()
    if state:
        df = df[df['state'] == state]
    if counties:
        df = df[df['County'].isin(counties)]
    #if home_types:
    #    df = df[df['homeType'].isin(home_types)]
    return df

# Cargar los datos completos
df = load_data()

# Verificar las columnas en el DataFrame
#st.write("Columnas disponibles en el DataFrame:", df.columns)

# Filtrar por estado
states = df['state'].unique()
selected_state = st.selectbox('Select a State', states)

# Filtrar por condados
filtered_df_state = get_filtered_data(selected_state, None, None)
counties = filtered_df_state['County'].unique()
selected_counties = st.multiselect('Select Counties', counties)

# Filtrar por tipo de vivienda (homeType)
home_types = df['homeType'].unique()
selected_home_types = st.multiselect('Select Home Types', home_types, default=home_types)

# Mostrar un mensaje de carga
st.text('Loading data...done!')

# Crear tarjetas y mapas para cada condado seleccionado
if selected_counties:
    filtered_df_county_and_homeType = get_filtered_data(selected_state, selected_counties, selected_home_types)
    for county in selected_counties:
        county_df = filtered_df_county_and_homeType[filtered_df_county_and_homeType['County'] == county]
        
        # Obtener valores únicos de 'bedrooms'
        bedrooms = county_df['bedrooms'].unique()
        bedrooms = sorted(bedrooms)
        bedrooms.insert(0, 'All')  # Agregar la opción 'All' al principio

        st.write(f"## {county} County")

        # Mostrar métricas
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Section 8 Properties", value=county_df[county_df['Section_8'] == 1].shape[0])
        with col2:
            st.metric(label="Total Non-Section 8 Properties", value=county_df[county_df['Section_8'] == 0].shape[0])

        # Control de selección de número de cuartos
        selected_bedrooms = st.radio(f'Select Bedrooms for {county}', bedrooms, index=0, key=f'bedrooms_{county}', horizontal=True)
        
        # Aplicar filtro de dormitorios si no es 'All'
        if selected_bedrooms != 'All':
            county_df = county_df[county_df['bedrooms'] == selected_bedrooms]

        # Control de selección de tipo de vivienda
        selected_home_types = st.radio(f'Select Home Types for {county}', home_types, index=0, key=f'hometypes_{county}', horizontal=True)
        
        # Aplicar filtro de tipo de vivienda
        if selected_home_types != 'All':
            county_df = county_df[county_df['homeType'] == selected_home_types]

        # Verificar que hay datos en el DataFrame filtrado
        if county_df.empty:
            st.warning(f"No data available for {county} County with the selected filters.")
            continue

        # Crear el mapa interactivo con Plotly y Mapbox
        mapbox_token = os.getenv("MAPBOX_API_KEY")  # Reemplaza con tu API Key de Mapbox
        
        try:
            fig = px.scatter_mapbox(
                county_df,
                lat="latitude",
                lon="longitude",
                color="Section_8",
                #size="sizediff",
                color_continuous_scale=["red", "green"],
                hover_data={
                    #"prices_sq_foot": True,
                    "latitude": False,
                    "longitude": False,
                    "Section_8": False,
                    "zpid": True,
                    "detailUrl_InfoTOD": True
                },
                mapbox_style="carto-positron",
                zoom=10,
                height=600
            )
        except ValueError as e:
            st.error(f"Error creating the map for {county}: {e}")
            continue
        
        fig.update_layout(
            mapbox=dict(
                accesstoken=mapbox_token,
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            coloraxis_colorbar=dict(
                title="Section 8",
                tickvals=[0, 1],
                ticktext=["No", "Yes"]
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Filtrar propiedades Section 8
        section_8_properties = county_df[county_df['Section_8'] == 1]
        
        # Mostrar tabla con propiedades Section 8
        st.write("### Section 8 Properties")
        st.dataframe(section_8_properties[[
            "zpid",
            "detailUrl_InfoTOD",
            "price_sq_foot",
            "bedrooms",
            "FRM",
            "yearBuilt",
            "SCHOOLSMeandistance",
            "price_to_rent_ratio_InfoTOD",
            "livingArea",
            "lastSoldPrice",
            "description"
        ]])
else:
    st.write("Please select at least one county to view the data.")
