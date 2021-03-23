import streamlit as st
import numpy as np
import pandas as pd
from zipfile import ZipFile
import altair as alt
from vega_datasets import data
import geopandas as gpd
from io import BytesIO
from urllib.request import urlopen
from hdx.utilities.easy_logging import setup_logging
from hdx.hdx_configuration import Configuration
Configuration.create(hdx_site='prod', hdx_read_only=True,user_agent='WBG')
from hdx.data.dataset import Dataset
# or: requests.get(url).content

# ----------READING FACEBOOK DATA--------------------
@st.cache
def facebook_data_reader():
    resp = urlopen(Dataset.get_resources(Dataset.read_from_hdx('movement-range-maps'))[1]['download_url'])
    zipfile = ZipFile(BytesIO(resp.read()))
    file = [i for i in zipfile.namelist() if 'movement' in i][0]
    df = pd.read_csv(zipfile.open(file),sep='\t')
    df['ds'] = pd.to_datetime(df['ds'])
    df['all_day_bing_tiles_visited_relative_change'] = df['all_day_bing_tiles_visited_relative_change']*100
    df['all_day_ratio_single_tile_users'] = df['all_day_ratio_single_tile_users']*100
    return df
data = facebook_data_reader()

# ----------INTRODUCTION-----------------------------

''' # Can big data be used to monitor human mobility disruptions in real time?'''
"More than ever, 2020 highlighted that the incidence and aftermath of geographic and public health crises can result in widespread disruptions to human movement. With emerging sources of big data comes the promise of informing response, recovery, and ultimate resilience to these risks in near-real-time. Using location data derived from smartphones, we provide a comparative cross-border visualization of human movement in the face of such challenges in selected Pacific countries."

# st.title(f'Country {country}')    
# st.header('Start by selecting a country.')
country = st.radio('Start by selecting a country from the following Pacific countries.',
    options=('Vietnam','the Philippines','Timor Leste'))
metric = st.radio('What metric are you interested in monitoring?',
    options=('Mobility change','Staying put/sheltering in place'))

if country=='Vietnam':
    prov_column = 'VARNAME_1'
    city_column = 'VARNAME_2'
elif country == 'Timor Leste':
    prov_column = 'polygon_name'
    city_column = 'polygon_name'
else:
    prov_column = 'NAME_1'
    city_column = 'NAME_2'

# ----------COUNTRY & DEFAULT DICTIONARIES----------
c_dict = {'Vietnam':'VNM','the Philippines':'PHL','Timor Leste':'TLS'}
default_provinces = {'Vietnam':['Ha Noi','Ho Chi Minh','Da Nang'],'the Philippines':'Metropolitan Manila','Timor Leste':'Dili Barat'} 
default_cities = {'Vietnam':['Ha Giang','Quang Binh'],'the Philippines':['Quezon City','Tuguegarao City'],'Timor Leste':'Dili Barat'} 
metric_dict = {'Mobility change':'all_day_bing_tiles_visited_relative_change','Staying put/sheltering in place':'all_day_ratio_single_tile_users'}
metric_ylabel = {'Mobility change':'Change in Mobility (%)','Staying put/sheltering in place':'Facebook users staying put (%)'}
analysis_label = {'Provincial level':'Provinces','City/municipality level':'Cities/municipalities','Custom':'Affected'}
analysis_level = {'Provincial level':prov_column,'City/municipality level':city_column,'Custom':None}

# ----------FILTERING DATA-----------------------------
@st.cache  
def facebook_data_filter(df,country):
    df = df[df['country']==c_dict[country]]
    if country!='Timor Leste':
        adm1 = gpd.read_file(f'boundaries/{c_dict[country]}/gadm36_{c_dict[country]}_1.shp')
        adm2 = gpd.read_file(f'boundaries/{c_dict[country]}/gadm36_{c_dict[country]}_2.shp')
        df = pd.merge(df,adm2[['GID_1','GID_2','VARNAME_2','NAME_1','NAME_2']],left_on='polygon_id',right_on='GID_2')\
        .merge(adm1[['GID_1','VARNAME_1']],on='GID_1')
    else:
        adm1 = gpd.read_file(f'boundaries/tls/tls_admbnda_adm1_who_ocha_20200911.shp')
        adm2 = gpd.read_file(f'boundaries/tls/tls_admbnda_adm2_who_ocha_20200911.shp')
        # df = pd.merge(df,adm2[['GID_1','GID_2','VARNAME_2','NAME_1','NAME_2']],left_on='polygon_id',right_on='GID_2')\
        # .merge(adm1[['GID_1','VARNAME_1']],on='GID_1')
    return df
df = facebook_data_filter(data,country)

# ----------SELECTION OF LEVEL OF ANALYSIS----------------------
st.header(f'Analysis of mobility changes in {country}.')

# ----------PROVINCE VISUALIZATION----------------------
if country!='Timor Leste':
    analysis = st.radio('At what level would you like to conduct your analysis?',
    options=('Provincial level','City/municipality level','Custom'))
    analyis_level_default = {'Provincial level':default_provinces,'City/municipality level':default_cities,'Custom':None}
    if analysis!='Custom':
        column = analysis_level[analysis]
        area = st.multiselect(
        f'Select as many {analysis_label[analysis].lower()} as you would like to visualize and/or compare.',
        options=tuple((df[column].sort_values().unique()).reshape(1, -1)[0]),default=analyis_level_default[analysis][country])
        df_p = df[df[column].isin(area)].groupby([column,'ds']).mean().reset_index()
        pr = alt.Chart(df_p).mark_line().encode(x=alt.X('ds', axis=alt.Axis(title='Date')),
            y=alt.Y(metric_dict[metric], axis=alt.Axis(title=metric_ylabel[metric])),
            color=alt.Color(column,legend=alt.Legend(title=analysis_label[analysis]))).properties(width=800).interactive( bind_y = False) #, size='c', color='c', tooltip=['a', 'b', 'c'])
        st.write(pr)
    else:
        ## COMPARISON GROUP 1
        default_prov1 = {'Vietnam':['Da Nang'],'the Philippines':'Metropolitan Manila','Timor Leste':'Dili Barat'} 
        default_cities1 = {'Vietnam':['Ha Giang'],'the Philippines':['Quezon City','Tuguegarao City'],'Timor Leste':'Dili Barat'} 

        st.subheader(f'Comparison Group 1.')
        prov1 = st.multiselect(
        f'Select provinces/centrally-controlled municipalities to include in comparison group 1.',
        options=tuple((df[analysis_level['Provincial level']].sort_values().unique()).reshape(1, -1)[0]),default = default_prov1[country])
        cities_in = st.multiselect(
        f'Select cities/muncipalities to include in comparison group 1.',
        options=tuple((df[analysis_level['City/municipality level']].sort_values().unique()).reshape(1, -1)[0]),default = None)
        
        ## COMPARISON GROUP 2
        default_prov2 = {'Vietnam':['Ha Noi','Ho Chi Minh'],'the Philippines':'Catanduanes','Timor Leste':'Dili Barat'} 
        default_cities2 = {'Vietnam':['Quang Binh'],'the Philippines':['Quezon City','Tuguegarao City'],'Timor Leste':'Dili Barat'} 

        st.subheader(f'Comparison Group 2.')
        prov2_default = ['Ha Noi','Ho Chi Minh']
        prov2 = st.multiselect(
        f'Select provinces/centrally-controlled municipalities to include in comparison group 2.',
            options=tuple((df[analysis_level['Provincial level']].sort_values().unique()).reshape(1, -1)[0]),default = default_prov2[country])
        cities_ex = st.multiselect(
        f'Select cities/muncipalities to include in comparison group 2.',
        options=tuple((df[analysis_level['City/municipality level']].sort_values().unique()).reshape(1, -1)[0]),default = None)

        
        df1 = df[(df[analysis_level['Provincial level']].isin(prov1)) | (df[analysis_level['City/municipality level']].isin(cities_in))].set_index('ds')\
            .resample('1D').mean().reset_index()#.set_index('ds').resample('7D').mean().reset_index()
        df1['status'] = 'Group 1'
        
        df2 = df[~((df[analysis_level['Provincial level']].isin(prov2)) | (df[analysis_level['City/municipality level']].isin(cities_in)))].set_index('ds')\
            .resample('1D').mean().reset_index()#.set_index('ds').resample('7D').mean().reset_index()
        df2['status'] = 'Group 2'
        df_c = pd.concat([df1,df2])
        pr = alt.Chart(df_c).mark_line().encode(x=alt.X('ds', axis=alt.Axis(title='Date')),
            y=alt.Y(metric_dict[metric], axis=alt.Axis(title=metric_ylabel[metric])),
            color=alt.Color('status',legend=alt.Legend(title='Comparison groups'))).properties(width=800).interactive( bind_y = False) #, size='c', color='c', tooltip=['a', 'b', 'c'])
        st.write(pr)
else: 
    st.write(f'For {country}, data is only available for Dili Timur and Dili Barat.')
    analysis = st.multiselect('Select your area of interest',
        options=['Dili Barat','Dili Timur'],
        default=['Dili Barat','Dili Timur'])
    df_t = df[df['polygon_name'].isin(analysis)].groupby(['polygon_name','ds']).mean().reset_index()
    tls = alt.Chart(df_t).mark_line().encode(x=alt.X('ds', axis=alt.Axis(title='Date')),
        y=alt.Y(metric_dict[metric], axis=alt.Axis(title=metric_ylabel[metric])),
        color=alt.Color('polygon_name',legend=alt.Legend(title='Area'))).properties(width=800).interactive( bind_y = False) #, size='c', color='c', tooltip=['a', 'b', 'c'])
    st.write(tls)