import streamlit as st
import numpy as np
import pandas as pd
from zipfile import ZipFile
import requests
import altair as alt
import base64
import io
import datetime
from vega_datasets import data
import geopandas as gpd
from io import BytesIO
from urllib.request import urlopen
from hdx.utilities.easy_logging import setup_logging
from hdx.hdx_configuration import Configuration
try:
    Configuration.create(hdx_site='prod', hdx_read_only=True,user_agent='WBG')
except:
    pass
from hdx.data.dataset import Dataset
# or: requests.get(url).content

# ----------READING FACEBOOK DATA--------------------

def download_from_hdx():
    '''
    Function to download latest movement range maps from HDX.
    '''
    url = Dataset.get_resources(Dataset.read_from_hdx('movement-range-maps'))[1]['download_url']
    return url

@st.cache
def government_response_reader():
    url = ('https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest.csv')
    s=requests.get(url).content
    c=pd.read_csv(io.StringIO(s.decode('utf-8')))
    c = c[['CountryName', 'CountryCode',  'Date',  'StringencyIndex']]
    c.columns = ['CountryName', 'country', 'ds', 'Policy Stringency']
    c['ds'] = pd.to_datetime(c['ds'],format = '%Y%m%d')
    c['Stringency Metric'] = 'Oxford University Stringency Index'
    return c

@st.cache
def facebook_data_reader():
    # govt = government_response_reader()
    resp = urlopen(download_from_hdx())
    zipfile = ZipFile(BytesIO(resp.read()))
    file = [i for i in zipfile.namelist() if 'movement' in i][0]
    df = pd.read_csv(zipfile.open(file),sep='\t')
    df['ds'] = pd.to_datetime(df['ds'])
    df['all_day_bing_tiles_visited_relative_change'] = df['all_day_bing_tiles_visited_relative_change']*100
    df['all_day_ratio_single_tile_users'] = df['all_day_ratio_single_tile_users']*100
    # df = pd.merge(df,govt,on=['ds','country'])
    return df
fb = facebook_data_reader()

# ----------INTRODUCTION-----------------------------

''' # Can big data be used to monitor human mobility disruptions in real time?'''
st.markdown("More than ever, 2020 highlighted that the incidence and aftermath of climate-related and public health crises can result in widespread disruptions to human movement. With emerging sources of big data comes the promise of informing response, recovery, and ultimate resilience to these risks in near-real-time. Using location data derived from Facebook's [_Movement Range Maps_](https://data.humdata.org/dataset/movement-range-maps), we provide a comparative cross-border visualization of human movement in the face of such challenges in selected Pacific countries. [_Raw data can be found here_](https://data.humdata.org/dataset/movement-range-maps).")
country = st.sidebar.radio('Start by selecting a country from the following Pacific countries.',
    options=('Vietnam','the Philippines','Timor Leste'))
metric = st.sidebar.radio('What metric are you interested in monitoring?',
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
default_provinces = {'Vietnam':['Ha Noi','Ho Chi Minh','Da Nang'],'the Philippines':['Metropolitan Manila','Catanduanes'],'Timor Leste':'Dili Barat'} 
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
        adm1 = gpd.read_file(f'boundaries/TLS/tls_admbnda_adm1_who_ocha_20200911.shp')
        adm2 = gpd.read_file(f'boundaries/TLS/tls_admbnda_adm2_who_ocha_20200911.shp')
    return df
df = facebook_data_filter(fb,country)

# ----------DEFINING A FUNCTION FOR ROLLING TOOLTIP-----------------------------  
def rolling(data,metric,column=None,color=None,date_df=None):
    base = alt.Chart(data).encode(x=alt.X('ds:T', axis=alt.Axis(title='Date'))).properties(width=800,height=250)
    pr = base.mark_line(interpolate='basis').encode(y=alt.Y(metric_dict[metric], axis=alt.Axis(title=metric_ylabel[metric])),color=color)
    circle = base.mark_circle(opacity=.5).encode(alt.Y('Policy Stringency', axis=alt.Axis(title='COVID-19 Policy Stringency')),tooltip=['Policy Stringency:N'],color=alt.Color('Stringency Metric',scale=alt.Scale(scheme='Pastel2')))
    rules = alt.Chart(date_df).mark_rule(strokeWidth=5,opacity=.5).encode(
    x='Date:T',y=alt.Y('y',axis=None),
    color=alt.Color('color:N', scale=None), tooltip='Event')
    chart = alt.layer(circle,pr).resolve_scale(y = 'independent',color='independent').interactive(bind_y=False)

    return chart
g = government_response_reader()

# ----------SELECTION OF LEVEL OF ANALYSIS----------------------
st.header(f'Analysis of mobility changes in {country}.')
# ----------PROVINCE VISUALIZATION----------------------
if country!='Timor Leste':
  
    analysis = st.sidebar.radio('At what level would you like to conduct your analysis?',
    options=('Provincial level','City/municipality level','Custom'))
    analyis_level_default = {'Provincial level':default_provinces,'City/municipality level':default_cities,'Custom':None}
    
    if analysis!='Custom':
        column = analysis_level[analysis]
        area = st.sidebar.multiselect(
        f'Select as many {analysis_label[analysis].lower()} as you would like to visualize and/or compare.',
        options=tuple((df[column].sort_values().unique()).reshape(1, -1)[0]),default=analyis_level_default[analysis][country])
        data = df[df[column].isin(area)].groupby([column,'ds']).mean().reset_index()
        data = pd.merge(data,g[g['country']==c_dict[country]],on='ds')
        color=alt.Color(column,legend=alt.Legend(title=metric_ylabel[metric]))
        # d = st.sidebar.date_input("Enter a key date where a crisis-related event took place.",datetime.date(2020, 7, 6))
        # d = [d]
        date_df = pd.DataFrame({
            'Date': ['2020-10-18'],
            'Event': ['Flooding'],
            })
        date_df['Date'] = pd.to_datetime(date_df['Date'])
        date_df['y']=100
        date_df['color']='tomato'
        st.write(rolling(data,metric,column=column,color=color,date_df=date_df))
        # st.write(rules)

    else:
        ## COMPARISON GROUP 1
        default_prov1 = {'Vietnam':['Da Nang'],'the Philippines':'Metropolitan Manila','Timor Leste':'Dili Barat'} 
        default_cities1 = {'Vietnam':['Ha Giang'],'the Philippines':['Quezon City','Tuguegarao City'],'Timor Leste':'Dili Barat'} 

        st.subheader(f'Comparison Group 1.')
        prov1 = st.sidebar.multiselect(
        f'Select provinces/centrally-controlled municipalities to include in comparison group 1.',
        options=tuple((df[analysis_level['Provincial level']].sort_values().unique()).reshape(1, -1)[0]),default = default_prov1[country])
        cities_in = st.sidebar.multiselect(
        f'Select cities/muncipalities to include in comparison group 1.',
        options=tuple((df[analysis_level['City/municipality level']].sort_values().unique()).reshape(1, -1)[0]),default = None)
        
        ## COMPARISON GROUP 2
        default_prov2 = {'Vietnam':['Ha Noi','Ho Chi Minh'],'the Philippines':'Catanduanes','Timor Leste':'Dili Barat'} 
        default_cities2 = {'Vietnam':['Quang Binh'],'the Philippines':['Quezon City','Tuguegarao City'],'Timor Leste':'Dili Barat'} 

        st.subheader(f'Comparison Group 2.')
        prov2_default = ['Ha Noi','Ho Chi Minh']
        prov2 = st.sidebar.multiselect(
        f'Select provinces/centrally-controlled municipalities to include in comparison group 2.',
            options=tuple((df[analysis_level['Provincial level']].sort_values().unique()).reshape(1, -1)[0]),default = default_prov2[country])
        cities_ex = st.sidebar.multiselect(
        f'Select cities/muncipalities to include in comparison group 2.',
        options=tuple((df[analysis_level['City/municipality level']].sort_values().unique()).reshape(1, -1)[0]),default = None)

        
        df1 = df[(df[analysis_level['Provincial level']].isin(prov1)) | (df[analysis_level['City/municipality level']].isin(cities_in))].set_index('ds')\
            .resample('1D').mean().reset_index()#.set_index('ds').resample('7D').mean().reset_index()
        df1['status'] = 'Group 1'
        
        df2 = df[~((df[analysis_level['Provincial level']].isin(prov2)) | (df[analysis_level['City/municipality level']].isin(cities_in)))].set_index('ds')\
            .resample('1D').mean().reset_index()#.set_index('ds').resample('7D').mean().reset_index()
        df2['status'] = 'Group 2'
        data = pd.concat([df1,df2])
        data = pd.merge(data,g[g['country']==c_dict[country]],on='ds')
        color = alt.Color('status',legend=alt.Legend(title='Comparison groups'))

        
        st.write(rolling(data,metric,color=color))

else: 
    st.write(f'For {country}, data is only available for Dili Timur and Dili Barat.')
    analysis = st.multiselect('Select your area of interest',
        options=['Dili Barat','Dili Timur'],
        default=['Dili Barat','Dili Timur'])
    data = df[df['polygon_name'].isin(analysis)].groupby(['polygon_name','ds']).mean().reset_index()
    data = pd.merge(data,g[g['country']==c_dict[country]],on='ds')

    color = alt.Color('polygon_name',legend=alt.Legend(title='Area'))
    st.write(rolling(data,metric,color=color))





# ----------DOWNLOADING DATA----------------------

def get_table_download_link_csv(df):
    csv = df.to_csv(index=False).encode()
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="facebook_export.csv" target="_blank">here.</a>'
    return href

st.subheader('Export data')
st.markdown(f'Download the data used to generate this plot in a csv file by clicking {get_table_download_link_csv(data)}', unsafe_allow_html=True)
