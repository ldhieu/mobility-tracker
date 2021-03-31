import streamlit as st
import numpy as np
import pandas as pd
from zipfile import ZipFile
import requests
import altair as alt
import base64
import io
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
def read_pacific_typhoons():
    r = requests.get('https://docs.google.com/spreadsheets/d/e/2PACX-1vRFJfCoAhf_no2vxzaTLMgqAqcx9XpNmX5HQOY2sX5BsNdopYsSZUoAV7lc5mCfnWTpmc5IN_4QNXBW/pub?output=csv')
    pac = r.content
    pac = pd.read_csv(BytesIO(pac), index_col=0,parse_dates=['start_date','end_date'])
    return pac

def download_from_hdx(show_spinner=False):
    '''
    Function to download latest movement range maps from HDX.
    '''
    url = Dataset.get_resources(Dataset.read_from_hdx('movement-range-maps'))[1]['download_url']
    return url

@st.cache(suppress_st_warning=True,show_spinner=False)
def government_response_reader():
    url = ('https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest.csv')
    s=requests.get(url).content
    c=pd.read_csv(io.StringIO(s.decode('utf-8')))
    c = c[['CountryName', 'CountryCode',  'Date',  'StringencyIndex']]
    c.columns = ['CountryName', 'country', 'ds', 'Policy Stringency']
    c['ds'] = pd.to_datetime(c['ds'],format = '%Y%m%d')
    c['Stringency Metric'] = 'Oxford Stringency Index'
    return c

@st.cache(suppress_st_warning=True,show_spinner=False)
def facebook_data_reader():
    resp = urlopen(download_from_hdx())
    zipfile = ZipFile(BytesIO(resp.read()))
    file = [i for i in zipfile.namelist() if 'movement' in i][0]
    df = pd.read_csv(zipfile.open(file),sep='\t')
    df['ds'] = pd.to_datetime(df['ds'])
    df['Change in Mobility'] = (df['all_day_bing_tiles_visited_relative_change']*100).round(2)
    df['Staying Put'] = (df['all_day_ratio_single_tile_users']*100).round(2)
    return df

fb = facebook_data_reader()
pac = read_pacific_typhoons().reset_index()
pac['_y'] = -100
pac['y'] = 100

# ----------INTRODUCTION-----------------------------

html = " <a href='covid-19observatory.com'> <img src='https://covid-19observatory.com/static/assets/images/logo-covid.png' height=150> </a>"
st.sidebar.markdown(html, unsafe_allow_html=True)
''' # Can big data be used to monitor human mobility disruptions in near-real time?'''
st.markdown("2020 highlighted that the climate-related and public health crises can result in widespread disruptions to human movement. With emerging sources of big data comes the promise of informing response, recovery, and ultimate resilience to these risks in near-real-time. Using location data derived from Facebook's [_Movement Range Maps_](https://dataforgood.fb.com/tools/movement-range-maps/), we provide a comparative cross-border visualization of human movement in the face of such challenges in selected Pacific countries.")
st.subheader("Let's begin.")
'\n\nYou can change what is visualized in the plot below by using the form in the **sidebar on the left.** Scroll to zoom in and out of the plot.'
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
metric_dict = {'Mobility change':'Change in Mobility','Staying put/sheltering in place':'Staying Put'}
metric_ylabel = {'Mobility change':'Change in Mobility (%)','Staying put/sheltering in place':'Facebook users staying put (%)'}
analysis_label = {'Provincial level':'Provinces','City/municipality level':'Cities/municipalities','Custom':'Affected'}
analysis_level = {'Provincial level':prov_column,'City/municipality level':city_column,'Custom':None}
typhoon_dict = {'Vietnam':pd.DataFrame({'Date': ['2020-10-05','2020-10-09', '2020-10-11','2020-10-13','2020-10-24','2020-10-27','2020-11-5','2020-11-9','2020-11-14'],'Event': ['Tropical Depression','Tropical Storm Linfa', 'Tropical Storm Nangka','Tropical Depression Ofel','Typhoon Saudel','Typhoon Molave','Typhoon Goni','Tropical Storm Etau','Typhoon Vamco']}),
                'the Philippines':pd.DataFrame({'Date': ['2020-5-8','2020-6-10', '2020-7-11','2020-7-30','2020-7-31','2020-8-6','2020-8-9','2020-8-9','2020-8-16','2020-8-20','2020-8-27','2020-8-30','2020-9-10','2020-9-15','2020-9-19','2020-9-25','2020-10-4','2020-10-6','2020-10-11','2020-10-13','2020-10-18','2020-10-19','2020-10-22','2020-10-26','2020-10-30','2020-11-6','2020-11-8','2020-12-18'],'Event': ['Typhoon Vonggong (Ango)','Tropical Storm Nuri (Butchoy)', 'Tropical Depression Carina','Typhoon Hagupit (Dindo)','Tropical Storm Sinlaki','Tropical Storm Jangmi (Enteng)','Tropical Depression 06W','Severe Tropical Storm Mekkhala (Ferdie)','Severe Tropical Storm Higos (Helen)','Typhoon Bavi (Igme)','Typhoon Maysak (Julian)','Typhoon Haishen (Kristine)','Tropical Depression 12W','Tropical Storm Noul (Leon)','Severe Tropical Storm Dolphin (Marce)','Severe Tropical Storm Kujira','Typhoon Chan-hom','Tropical Storm Linfa','Tropical Storm Nangka (Nika)','Tropical Depression Ofel','Typhoon Saudel (Pepito)','Tropical Depression 20W','Typhoon Molave (Quinta)','Typhoon Goni (Rolly)','Severe Tropical Storm Atsani (Siony)','Tropical Storm Etau (Tonyo)','Typhoon Vamco (Ulysses)','Tropical Storm Krovanh (Vicky)']}),
                'Timor Leste':pd.DataFrame({'Date':['2020-3-13'],'Event':['Dili Flooding']
                })
                }
# ----------FILTERING DATA-----------------------------
@st.cache(suppress_st_warning=True,show_spinner=False)
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

# ----------DEFINING A FUNCTION FOR PLOTTING TOOLTIP-----------------------------  
def plotting(data,metric,column=None,color=None,date_df=None,viz=None,country=None,pac=None):
    date_df = typhoon_dict[country]
    date_df['y'] = 100
    base = alt.Chart(data).encode(x=alt.X('ds:T', axis=alt.Axis(title='Date'))).properties(width=800,height=250)
    pr = base.mark_line(interpolate='basis',strokeWidth=2).encode(y=alt.Y(metric_dict[metric], axis=alt.Axis(title=metric_ylabel[metric])),color=color,tooltip=[metric_dict[metric]])
    circle = base.mark_circle(opacity=.5,size=15).encode(alt.Y('Policy Stringency', axis=alt.Axis(title='COVID-19 Policy Stringency')),tooltip=['Policy Stringency:N'],color=alt.Color('Stringency Metric',scale=alt.Scale(scheme='Pastel2')))
    try:
        rules = alt.Chart(pac.reset_index()).mark_rect(opacity=0.3,color='tomato').encode(tooltip=['Province','Event'],x='start_date',x2='end_date',y2='y',y='_y')
    except:
        pass
    
    if set(viz) == set(['COVID-19 Restrictions']):
        chart = alt.layer(circle,pr).interactive(bind_y=False).resolve_scale(y = 'independent',color='independent').configure_axis(grid=False).configure_view(strokeOpacity=0)
    if set(viz)==set(['Pacific Typhoons']):
        chart = alt.layer(pr,rules).interactive(bind_y=False).resolve_scale(color='independent').configure_axis(
    grid=False).configure_view(strokeOpacity=0)
    if set(viz)==set(['COVID-19 Restrictions','Pacific Typhoons']):
        chart = alt.layer(circle,rules).interactive(bind_y=False).resolve_scale(color='independent')#.configure_axis(grid=False)#.configure_view(strokeOpacity=0)
        chart = alt.layer(chart,pr).resolve_scale(color='independent',y='independent').configure_axis(
    grid=False).configure_view(strokeOpacity=0)
    return chart

g = government_response_reader()
# ----------SELECTION OF LEVEL OF ANALYSIS----------------------
st.header(f'Analysis of mobility changes in {country}.')
# ----------ALL BUT TIMOR LESTE----------------------
if country!='Timor Leste':
    viz = st.multiselect('Select the type of disruption to human mobility you would like to visualize.',options=['COVID-19 Restrictions','Pacific Typhoons'],default=['COVID-19 Restrictions','Pacific Typhoons'])
    analysis = st.sidebar.radio('At what level would you like to conduct your analysis?',
    options=('Provincial level','City/municipality level','Custom'))
    analysis_level_default = {'Provincial level':default_provinces,'City/municipality level':default_cities,'Custom':None}
    analysis_flooding_default = {'Vietnam':['Thua Thien Hue','Quang Binh','Quang Ngai'],'the Philippines':['Catanduanes','Metropolitan Manila']}
    if analysis!='Custom':
        column = analysis_level[analysis]
        if analysis=='Provincial level':
            flood_provinces = st.sidebar.radio('List only provinces that were affected by 2020 Pacific floods?',options = ('Yes','No'),index=1)
            if flood_provinces=='Yes':
                area = pac[pac['Country']==country]['Province'].sort_values().unique().reshape(1,-1)[0]
                area = st.sidebar.multiselect(
                f'Only showing {analysis_label[analysis].lower()} that were affected by Pacific typhoons. Select as many of these as you would like to visualize and/or compare.',
            options=tuple(area),default=analysis_flooding_default[country])
            else:
                area = st.sidebar.multiselect(
                f'Select as many {analysis_label[analysis].lower()} as you would like to visualize and/or compare.',
                options=tuple((df[column].sort_values().unique()).reshape(1, -1)[0]),default=analysis_level_default[analysis][country])
        else:
                area = st.sidebar.multiselect(
                f'Select as many {analysis_label[analysis].lower()} as you would like to visualize and/or compare.',
                options=tuple((df[column].sort_values().unique()).reshape(1, -1)[0]),default=analysis_level_default[analysis][country])
        data = df[df[column].isin(area)]
        pac = pac[pac['Province'].apply(lambda x: x in data['VARNAME_1'].unique())]
        data =data.groupby([column,'ds']).mean().reset_index()
        data = pd.merge(data,g[g['country']==c_dict[country]],on='ds')
        color=alt.Color(column,legend=alt.Legend(title=metric_ylabel[metric]))
        st.write(plotting(data,metric,column=column,color=color,viz=viz,country=country,pac=pac))
            # st.write(rules)
    else:
## -----------COMPARISON GROUP 1--------------------
        default_prov1 = {'Vietnam':['Da Nang'],'the Philippines':'Metropolitan Manila','Timor Leste':'Dili Barat'} 
        default_cities1 = {'Vietnam':['Ha Giang'],'the Philippines':['Quezon City','Tuguegarao City'],'Timor Leste':'Dili Barat'} 
        st.sidebar.subheader(f'Comparison Group 1.')
        prov1 = st.sidebar.multiselect(
        f'Select provinces/centrally-controlled municipalities to include in comparison group 1.',
        options=tuple((df[analysis_level['Provincial level']].sort_values().unique()).reshape(1, -1)[0]),default = default_prov1[country])
        cities_in = st.multiselect(
        f'Select cities/muncipalities to include in comparison group 1.',
        options=tuple((df[analysis_level['City/municipality level']].sort_values().unique()).reshape(1, -1)[0]),default = None)
## -----------COMPARISON GROUP 2--------------------
        default_prov2 = {'Vietnam':['Ha Noi','Ho Chi Minh'],'the Philippines':'Catanduanes','Timor Leste':'Dili Barat'} 
        default_cities2 = {'Vietnam':['Quang Binh'],'the Philippines':['Quezon City','Tuguegarao City'],'Timor Leste':'Dili Barat'} 
        st.sidebar.subheader(f'Comparison Group 2.')
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
            .resample('1D').mean().reset_index()
        df2['status'] = 'Group 2'
        data = pd.concat([df1,df2])
        data = pd.merge(data,g[g['country']==c_dict[country]],on='ds')
        base = alt.Chart(data).encode(x='ds') 
        line = base.mark_line(color='red').encode(y='PolicyValue:Q')
        color = alt.Color('status',legend=alt.Legend(title='Comparison groups'))
        st.write(plotting(data,metric,color=color,country=country,viz=viz))
## -----------TIMOR LESTE--------------------
else: 
    viz = ['COVID-19 Restrictions']
    st.write(f'For {country}, data is only available for Dili Timur and Dili Barat.')
    analysis = st.multiselect('Select your area of interest',
        options=['Dili Barat','Dili Timur'],
        default=['Dili Barat','Dili Timur'])
    data = df[df['polygon_name'].isin(analysis)].groupby(['polygon_name','ds']).mean().reset_index()
    data = pd.merge(data,g[g['country']==c_dict[country]],on='ds')

    color = alt.Color('polygon_name',legend=alt.Legend(title='Area'))
    st.write(plotting(data,metric,color=color,country=country,viz=viz))

# ----------DOWNLOADING DATA----------------------

def get_table_download_link_csv(df):
    csv = df.to_csv(index=False).encode()
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="facebook_export.csv" target="_blank">here.</a>'
    return href

st.subheader('Export data')
st.markdown(f'Download the data visualized in the plot above by clicking {get_table_download_link_csv(data)}', unsafe_allow_html=True)

"""
### Data Sources
- Raw data for Facebook's Movement Range maps can be found [on the Humanitarian Data Exchange](https://data.humdata.org/dataset/movement-range-maps).
- Province and city/municipality names used are taken from the [Database of Global Administrative Areas (GADM)](https://gadm.org/download_country_v3.html).
- A spreadsheet containing all the weather events used in this app can be found [here](https://docs.google.com/spreadsheets/d/1RTvPgw29yTXi9GAAc8kSQAJ-3sQU7MqOMwZgbAEoG4E/edit#gid=0). Please [write to us](mkhan57@worldbank.org) with suggestions for addiitons to this spreadsheet.
"""