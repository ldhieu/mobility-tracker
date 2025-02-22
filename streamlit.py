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
from hdx.data.dataset import Dataset
from hdx.utilities.easy_logging import setup_logging
from hdx.api.configuration import Configuration
try:
    Configuration.create(hdx_site="prod", hdx_read_only=True, user_agent="WBG")
except:
    pass

# ----------READING FACEBOOK DATA--------------------
@st.experimental_memo
def read_pacific_typhoons():
    r = requests.get(
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFJfCoAhf_no2vxzaTLMgqAqcx9XpNmX5HQOY2sX5BsNdopYsSZUoAV7lc5mCfnWTpmc5IN_4QNXBW/pub?output=csv"
    )
    pac = r.content
    pac = pd.read_csv(
        BytesIO(pac),
        index_col=0,
        parse_dates=["start_date", "end_date"],
        low_memory=False,
    )
    return pac


@st.experimental_memo
def download_from_hdx():
    """
    Function to download latest movement range maps from HDX.
    """
    names = Dataset.get_resources(Dataset.read_from_hdx("movement-range-maps"))[
        1:3
    ]  # ['download_url']
    urls = [i["download_url"] for i in names]
    return urls


@st.experimental_memo
def government_response_reader():
    url1 = "https://github.com/OxCGRT/covid-policy-tracker/raw/master/data/OxCGRT_withnotes_2020.csv"
    url2 = "https://github.com/OxCGRT/covid-policy-tracker/raw/master/data/OxCGRT_withnotes_2021.csv"
    s1 = requests.get(url1).content
    s2 = requests.get(url2).content
    c1 = pd.read_csv(io.StringIO(s1.decode("utf-8")), low_memory=False)
    c2 = pd.read_csv(io.StringIO(s2.decode("utf-8")), low_memory=False)
    c = pd.concat([c1, c2], ignore_index=True)
    #c = pd.read_csv(io.StringIO(s.decode("utf-8")), low_memory=False)
    c = c[
        [
            "CountryName",
            "CountryCode",
            "Date",
            "StringencyIndex",
            "C1_Notes",
            "C2_Notes",
            "C3_Notes",
            "C4_Notes",
            "C5_Notes",
            "C6_Notes",
            "C7_Notes",
            "C8_Notes",
        ]
    ]
    c.columns = [
        "CountryName",
        "country",
        "ds",
        "Policy Stringency",
        "School closures",
        "Workplace closures",
        "Cancellations of public events",
        "Restrictions on gatherings",
        "Public transport closures",
        "Stay-at-home requirements",
        "Internal movement restrictions",
        "International travel controls",
    ]
    char = 300
    c["ds"] = pd.to_datetime(c["ds"], format="%Y%m%d")
    c["Stringency Metric"] = "Oxford Stringency Index"
    c["School closures"] = (
        c["School closures"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    c["Workplace closures"] = (
        c["Workplace closures"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    c["Cancellations of public events"] = (
        c["Cancellations of public events"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    c["Restrictions on gatherings"] = (
        c["Restrictions on gatherings"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    c["Public transport closures"] = (
        c["Public transport closures"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    c["Stay-at-home requirements"] = (
        c["Stay-at-home requirements"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    c["Internal movement restrictions"] = (
        c["Internal movement restrictions"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    c["International travel controls"] = (
        c["International travel controls"]
        .fillna("No new restrictions")
        .apply(lambda x: x[:char].split(". ")[0])
    )
    return c


@st.experimental_memo
def facebook_data_reader():
    url20 = download_from_hdx()[1]
    url21 = download_from_hdx()[0]
    print(url20)
    print(url21)
    y20 = urlopen(url20)
    y21 = urlopen(url21)
    zipfile20 = ZipFile(BytesIO(y20.read()))
    zipfile21 = ZipFile(BytesIO(y21.read()))
    file20 = [i for i in zipfile20.namelist() if "movement" in i][0]
    file21 = [i for i in zipfile21.namelist() if "movement" in i][0]
    df20 = pd.read_csv(zipfile20.open(file20), sep="\t", low_memory=False)
    df21 = pd.read_csv(zipfile21.open(file21), sep="\t", low_memory=False)
    df = pd.concat([df20, df21], ignore_index=True)
    df = df[df["country"].isin(["VNM", "TLS", "PHL"])]
    df["ds"] = pd.to_datetime(df["ds"])
    df["Change in Mobility"] = (
        df["all_day_bing_tiles_visited_relative_change"] * 100
    ).round(2)
    df["Staying Put"] = (df["all_day_ratio_single_tile_users"] * 100).round(2)
    return df


fb = facebook_data_reader()
pac = read_pacific_typhoons().reset_index()
pac["_y"] = 0
pac["y"] = 100

# ----------INTRODUCTION-----------------------------
# col1, col2 = st.beta_columns(2)
st.header(
    "Can big data be used to monitor human mobility disruptions in near-real time?"
)
"""
### 
2020 highlighted that climate-related and public health crises can result in widespread disruptions to human movement. With emerging sources of big data comes the promise of informing response, recovery, and ultimate resilience to these risks in near-real-time. Using location data derived from Facebook's [_Movement Range Maps_](https://dataforgood.fb.com/tools/movement-range-maps/), we provide a comparative cross-border visualization of human movement in the face of such challenges in selected Pacific countries.
"""
# st.markdown('')
st.subheader("Let's begin.")
"\n\nYou can change what is visualized in the plot below by using the form in the **sidebar on the left.** **Scroll** to zoom in and out of the plot."
html = " <a href='https://bdo-vietnam.com'> <img src='https://raw.githubusercontent.com/ldhieu/mobility-tracker/main/logo-observatory.png' width=300> </a>"

st.sidebar.markdown(html, unsafe_allow_html=True)

country = st.sidebar.radio(
    "Start by selecting a country from the following Pacific countries.",
    ("Vietnam", "the Philippines", "Timor Leste"),
    help="At the moment, only a few Pacific countries are visualized on this site. Please [write to us](mailto:mkhan57@worldbank.org) if you would like us to add other countries supported by Facebook onto the site.",
)
metric = st.sidebar.radio(
    "What metric are you interested in monitoring?",
    options=("Mobility change", "Staying put/sheltering in place"),
    help="The **Change in Movement** metric looks at how much people are moving around and compares it to a baseline period that predates most social distancing measures. The **Stay Put** metric looks at the fraction of the population that appears to stay within a small area surrounding their home for an entire day.",
)


if country == "Vietnam":
    nat_column = "country"
    prov_column = "VARNAME_1"
    city_column = "VARNAME_2"
elif country == "Timor Leste":
    nat_column = "country_x"
    prov_column = "polygon_name"
    city_column = "polygon_name"
else:
    nat_column = "country"
    prov_column = "NAME_1"
    city_column = "NAME_2"

# ----------COUNTRY & DEFAULT DICTIONARIES----------
c_dict = {"Vietnam": "VNM", "the Philippines": "PHL", "Timor Leste": "TLS"}
default_provinces = {
    "Vietnam": ["Ha Noi", "Thua Thien Hue", "Da Nang"],
    "the Philippines": ["Metropolitan Manila", "Albay"],
    "Timor Leste": "Dili Barat",
}
default_cities = {
    "Vietnam": ["Ha Giang", "Hue"],
    "the Philippines": ["Quezon City", "Tuguegarao City", "Barili"],
    "Timor Leste": "Dili Barat",
}
metric_dict = {
    "Mobility change": "Change in Mobility",
    "Staying put/sheltering in place": "Staying Put",
}
metric_ylabel = {
    "Mobility change": " Change in Mobility (from baseline) (%)",
    "Staying put/sheltering in place": "Facebook users staying put (%)",
}
metric_ylabel_full = {
    "Mobility change": "Change in Mobility",
    "Staying put/sheltering in place": "Facebook users staying put (%)",
}
analysis_label = {
    "Provincial level": "Provinces",
    "City/municipality level": "Cities/municipalities",
    "Custom": "Affected",
}
analysis_level = {
    "National level": nat_column,
    "Provincial level": prov_column,
    "City/municipality level": city_column,
    "Custom": None,
}
typhoon_dict = {
    "Vietnam": pd.DataFrame(
        {
            "Date": [
                "2020-10-05",
                "2020-10-09",
                "2020-10-11",
                "2020-10-13",
                "2020-10-24",
                "2020-10-27",
                "2020-11-5",
                "2020-11-9",
                "2020-11-14",
            ],
            "Event": [
                "Tropical Depression",
                "Tropical Storm Linfa",
                "Tropical Storm Nangka",
                "Tropical Depression Ofel",
                "Typhoon Saudel",
                "Typhoon Molave",
                "Typhoon Goni",
                "Tropical Storm Etau",
                "Typhoon Vamco",
            ],
        }
    ),
    "the Philippines": pd.DataFrame(
        {
            "Date": [
                "2020-5-8",
                "2020-6-10",
                "2020-7-11",
                "2020-7-30",
                "2020-7-31",
                "2020-8-6",
                "2020-8-9",
                "2020-8-9",
                "2020-8-16",
                "2020-8-20",
                "2020-8-27",
                "2020-8-30",
                "2020-9-10",
                "2020-9-15",
                "2020-9-19",
                "2020-9-25",
                "2020-10-4",
                "2020-10-6",
                "2020-10-11",
                "2020-10-13",
                "2020-10-18",
                "2020-10-19",
                "2020-10-22",
                "2020-10-26",
                "2020-10-30",
                "2020-11-6",
                "2020-11-8",
                "2020-12-18",
            ],
            "Event": [
                "Typhoon Vonggong (Ango)",
                "Tropical Storm Nuri (Butchoy)",
                "Tropical Depression Carina",
                "Typhoon Hagupit (Dindo)",
                "Tropical Storm Sinlaki",
                "Tropical Storm Jangmi (Enteng)",
                "Tropical Depression 06W",
                "Severe Tropical Storm Mekkhala (Ferdie)",
                "Severe Tropical Storm Higos (Helen)",
                "Typhoon Bavi (Igme)",
                "Typhoon Maysak (Julian)",
                "Typhoon Haishen (Kristine)",
                "Tropical Depression 12W",
                "Tropical Storm Noul (Leon)",
                "Severe Tropical Storm Dolphin (Marce)",
                "Severe Tropical Storm Kujira",
                "Typhoon Chan-hom",
                "Tropical Storm Linfa",
                "Tropical Storm Nangka (Nika)",
                "Tropical Depression Ofel",
                "Typhoon Saudel (Pepito)",
                "Tropical Depression 20W",
                "Typhoon Molave (Quinta)",
                "Typhoon Goni (Rolly)",
                "Severe Tropical Storm Atsani (Siony)",
                "Tropical Storm Etau (Tonyo)",
                "Typhoon Vamco (Ulysses)",
                "Tropical Storm Krovanh (Vicky)",
            ],
        }
    ),
    "Timor Leste": pd.DataFrame({"Date": ["2020-3-13"], "Event": ["Dili Flooding"]}),
}
# ----------FILTERING DATA-----------------------------
@st.experimental_memo
def facebook_data_filter(df, country):
    df = df[df["country"] == c_dict[country]]
    if country != "Timor Leste":
        adm1 = gpd.read_file(
            f"boundaries/{c_dict[country]}/gadm36_{c_dict[country]}_1.shp"
        )
        adm2 = gpd.read_file(
            f"boundaries/{c_dict[country]}/gadm36_{c_dict[country]}_2.shp"
        )
        df = pd.merge(
            df,
            adm2[["GID_1", "GID_2", "VARNAME_2", "NAME_1", "NAME_2"]],
            left_on="polygon_id",
            right_on="GID_2",
        ).merge(adm1[["GID_1", "VARNAME_1"]], on="GID_1")
    # else:
    # adm1 = gpd.read_file(f'boundaries/TLS/tls_admbnda_adm1_who_ocha_20200911.shp')
    # adm2 = gpd.read_file(f'boundaries/TLS/tls_admbnda_adm2_who_ocha_20200911.shp')
    return df


df = facebook_data_filter(fb, country)


def time_widget():
    time_range = st.slider(
        "Select the date range you would like to visualize.",
        data["ds"].min().to_pydatetime(),
        data["ds"].max().to_pydatetime(),
        (data["ds"].min().to_pydatetime(), data["ds"].max().to_pydatetime()),
        format="MM/DD/YY",
    )
    return time_range


# ----------DEFINING A FUNCTION FOR PLOTTING TOOLTIP-----------------------------
def plotting(
    data,
    metric,
    column=None,
    color=None,
    date_df=None,
    viz=None,
    country=None,
    pac=None,
):
    date_df = typhoon_dict[country]
    if metric == "Staying put/sheltering in place":
        domain = [0, 100]
    else:
        domain = [-100, 100]
    date_df["y"] = 100
    base = (
        alt.Chart(data)
        .encode(
            x=alt.X(
                "ds",
                axis=alt.Axis(title="Date"),
            )
        )
        .properties(width=800, height=300)
    )
    pr = base.mark_line(interpolate="basis", strokeWidth=2).encode(
        y=alt.Y(
            metric_dict[metric],
            axis=alt.Axis(title=metric_ylabel[metric]),
            scale=alt.Scale(domain=domain),
        ),
        color=color,
        tooltip=[metric_dict[metric]],
    )
    circle = base.mark_circle(opacity=0.5, size=20).encode(
        alt.Y("Policy Stringency", axis=alt.Axis(title="COVID-19 Policy Stringency")),
        tooltip=[
            "Policy Stringency:N",
            "School closures",
            "Workplace closures",
            "Cancellations of public events",
            "Restrictions on gatherings",
            "Public transport closures",
            "Stay-at-home requirements",
            "Internal movement restrictions",
            "International travel controls",
        ],
        color=alt.Color(
            "Stringency Metric",
            scale=alt.Scale(scheme="Pastel2"),
            legend=alt.Legend(orient="bottom"),
        ),
    )
    try:
        pac["Disaster Event"] = "Pacific Typhoon"
        rules = (
            alt.Chart(pac.reset_index())
            .mark_rect(
                opacity=0.3,
            )
            .encode(
                tooltip=["Province", "Event"],
                x="start_date",
                x2="end_date",
                y2="y",
                y="_y",
                color=alt.Color(
                    "Disaster Event",
                    legend=alt.Legend(orient="bottom"),
                    scale=alt.Scale(scheme="reds"),
                ),
            )
        )
    except:
        pass
    if set(viz) == set(["COVID-19 Restrictions"]):
        chart = (
            alt.layer(circle, pr)
            .interactive(bind_y=False)
            .resolve_scale(y="independent", color="independent")
            .configure_axis(grid=False)
            .configure_view(strokeOpacity=0)
        )
    if set(viz) == set(["Pacific Typhoons"]):
        chart = (
            alt.layer(pr, rules)
            .interactive(bind_y=False)
            .resolve_scale(color="independent")
            .configure_axis(grid=False)
        )  # .configure_view(strokeOpacity=0)
    if set(viz) == set(["COVID-19 Restrictions", "Pacific Typhoons"]):
        chart = (
            alt.layer(circle, rules)
            .interactive(bind_y=False)
            .resolve_scale(color="independent")
        )  # .configure_axis(grid=False)#.configure_view(strokeOpacity=0)
        chart = (
            alt.layer(chart, pr)
            .resolve_scale(color="independent", y="independent")
            .configure_axis(grid=False)
        )  # .configure_view(strokeOpacity=0)
    return chart


g = government_response_reader()
# ----------SELECTION OF LEVEL OF ANALYSIS----------------------
st.header(f"Analysis of mobility changes in {country}.")
viz = st.multiselect(
    "Select the type of disruption to human mobility you would like to visualize.",
    options=["COVID-19 Restrictions", "Pacific Typhoons"],
    default=["COVID-19 Restrictions", "Pacific Typhoons"],
)

# ----------ALL BUT TIMOR LESTE----------------------
if country != "Timor Leste":
    # viz = st.multiselect('Select the type of disruption to human mobility you would like to visualize.',options=['COVID-19 Restrictions','Pacific Typhoons'],default=['COVID-19 Restrictions','Pacific Typhoons'])
    analysis = st.sidebar.radio(
        "At what level would you like to conduct your analysis?",
        options=(
            "National level",
            "Provincial level",
            "City/municipality level",
            "Custom",
        ),
    )
    analysis_level_default = {
        "Provincial level": default_provinces,
        "City/municipality level": default_cities,
        "Custom": None,
    }
    analysis_flooding_default = {
        "Vietnam": ["Thua Thien Hue", "Quang Binh", "Quang Ngai"],
        "the Philippines": ["Albay", "Catanduanes", "Metropolitan Manila"],
    }

    if analysis != "Custom":
        column = analysis_level[analysis]
        if analysis == "National level":
            area = [c_dict[country]]
        elif analysis == "Provincial level":
            flood_provinces = st.sidebar.radio(
                "Filter options below to only include provinces that were affected by 2020 Pacific floods?",
                options=("Yes", "No"),
                index=1,
            )
            if flood_provinces == "Yes":
                area = (
                    pac[pac["Country"] == country]["Province"]
                    .sort_values()
                    .unique()
                    .reshape(1, -1)[0]
                )
                area = st.sidebar.multiselect(
                    f"This dropdown only contains {analysis_label[analysis].lower()} that were affected by Pacific typhoons. Select as many of these as you would like to visualize and/or compare.",
                    options=tuple(area),
                    default=analysis_flooding_default[country],
                    help="Names of administrative units are taken from the [Database of Global Administrative Areas (GADM)](https://gadm.org/download_country_v3.html). Note that some cities, e.g. Hanoi, Metropolitan Manila, and Dili, show up in the provinces list because they are centrally-administered units.",
                )
            else:
                area = st.sidebar.multiselect(
                    f"Select as many {analysis_label[analysis].lower()} as you would like to visualize and/or compare.",
                    options=tuple(
                        (df[column].sort_values().unique()).reshape(1, -1)[0]
                    ),
                    default=analysis_level_default[analysis][country],
                    help="Names of administrative units are taken from the [Database of Global Administrative Areas (GADM)](https://gadm.org/download_country_v3.html). Note that some cities, e.g. Hanoi, Metropolitan Manila, and Dili, show up in the provinces list because they are centrally-administered units.",
                )
        else:
            area = st.sidebar.multiselect(
                f"Select as many {analysis_label[analysis].lower()} as you would like to visualize and/or compare.",
                options=tuple((df[column].sort_values().unique()).reshape(1, -1)[0]),
                default=analysis_level_default[analysis][country],
                help="Names of administrative units are taken from the [Database of Global Administrative Areas (GADM)](https://gadm.org/download_country_v3.html). Note that some cities, e.g. Hanoi, Metropolitan Manila, and Dili, show up in the provinces list because they are centrally-administered units.",
            )
        data = df[df[column].isin(area)]
        pac = pac[
            pac["Province"].isin(data[analysis_level["Provincial level"]].unique())
        ]
        data = data.groupby([column, "ds"]).mean().reset_index()
        cols = [i for i in data.columns if "country" not in i]
        data = pd.merge(data[cols], g[g["country"] == c_dict[country]], on="ds")
        color = alt.Color(
            column,
            legend=alt.Legend(title=metric_ylabel_full[metric], orient="bottom"),
            scale=alt.Scale(scheme="magma"),
        )
        plot_slot = st.empty()


    else:
        ## -----------COMPARISON GROUP 1--------------------
        default_prov1 = {
            "Vietnam": ["Da Nang"],
            "the Philippines": "Metropolitan Manila",
            "Timor Leste": "Dili Barat",
        }
        default_cities1 = {
            "Vietnam": ["Ha Giang"],
            "the Philippines": ["Quezon City"],
            "Timor Leste": "Dili Barat",
        }
        st.sidebar.subheader(f"Comparison Group 1.")
        prov1 = st.sidebar.multiselect(
            f"Select provinces/centrally-controlled municipalities to include in comparison group 1.",
            options=tuple(
                (df[analysis_level["Provincial level"]].sort_values().unique()).reshape(
                    1, -1
                )[0]
            ),
            default=default_prov1[country],
        )
        cities_in = st.sidebar.multiselect(
            f"Select cities/muncipalities to include in comparison group 1.",
            options=tuple(
                (
                    df[analysis_level["City/municipality level"]].sort_values().unique()
                ).reshape(1, -1)[0]
            ),
            default=default_cities1[country],
        )
        df1 = df[
            (df[analysis_level["Provincial level"]].isin(prov1))
            | (df[analysis_level["City/municipality level"]].isin(cities_in))
        ]

        ## -----------COMPARISON GROUP 2--------------------
        default_prov2 = {
            "Vietnam": ["Ha Noi", "Ho Chi Minh"],
            "the Philippines": ["Albay", "Catanduanes"],
            "Timor Leste": "Dili Barat",
        }
        default_cities2 = {
            "Vietnam": ["Quang Binh"],
            "the Philippines": ["Tuguegarao City"],
            "Timor Leste": "Dili Barat",
        }
        st.sidebar.subheader(f"Comparison Group 2.")
        prov2_default = ["Ha Noi", "Ho Chi Minh"]
        prov2 = st.sidebar.multiselect(
            f"Select provinces/centrally-controlled municipalities to include in comparison group 2.",
            options=tuple(
                (df[analysis_level["Provincial level"]].sort_values().unique()).reshape(
                    1, -1
                )[0]
            ),
            default=default_prov2[country],
        )
        cities_ex = st.sidebar.multiselect(
            f"Select cities/muncipalities to include in comparison group 2.",
            options=tuple(
                (
                    df[analysis_level["City/municipality level"]].sort_values().unique()
                ).reshape(1, -1)[0]
            ),
            default=default_cities2[country],
        )
        df2 = df[
            ~(
                (df[analysis_level["Provincial level"]].isin(prov2))
                | (df[analysis_level["City/municipality level"]].isin(cities_ex))
            )
        ]
        in_1 = pac["Province"].isin(prov1)
        in_2 = pac["Province"].isin(prov2)
        pac = pac[in_1 | in_2]
        # chg
        df1 = (
            df1.set_index("ds")
            .resample("1D")
            .mean()
            .reset_index()
            .set_index("ds")
            .resample("7D")
            .mean()
            .reset_index()
        )
        df1["status"] = "Group 1"

        df2 = df2.set_index("ds").resample("1D").mean().reset_index()
        df2["status"] = "Group 2"
        data = pd.concat([df1, df2])
        data = pd.merge(data, g[g["country"] == c_dict[country]], on="ds")
        base = alt.Chart(data).encode(x="ds")
        line = base.mark_line(color="red").encode(y="PolicyValue:Q")
        color = alt.Color(
            "status",
            legend=alt.Legend(title="Comparison groups", orient="bottom"),
            scale=alt.Scale(scheme="magma"),
        )
        plot_slot = st.empty()
## -----------TIMOR LESTE--------------------
else:
    # viz = ['COVID-19 Restrictions']
    st.write(f"For {country}, data is only available for Dili Timur and Dili Barat.")
    analysis = st.sidebar.multiselect(
        "Select your area of interest",
        options=["Dili Barat", "Dili Timur"],
        default=["Dili Barat", "Dili Timur"],
    )
    data = (
        df[df["polygon_name"].isin(analysis)]
        .groupby(["polygon_name", "ds"])
        .mean()
        .reset_index()
    )
    data = pd.merge(data, g[g["country"] == c_dict[country]], on="ds")
    pac = pac[pac["Province"].isin(analysis)]
    color = alt.Color("polygon_name", legend=alt.Legend(title="Area"))
    plot_slot = st.empty()
    # st.write(plotting(data,metric,color=color,country=country,viz=viz,pac=pac))
plot_slot.write(plotting(data, metric, color=color, country=country, viz=viz, pac=pac))
# ----------DOWNLOADING DATA----------------------


def get_table_download_link_csv(df):
    csv = df.to_csv(index=False).encode()
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="facebook_export.csv" target="_blank">here.</a>'
    return href


st.subheader("Export data")
st.markdown(
    f"Download the data visualized in the plot above by clicking {get_table_download_link_csv(data)}",
    unsafe_allow_html=True,
)

str = """
### Data Sources
- Raw data for Facebook's Movement Range maps can be found [on the Humanitarian Data Exchange](https://data.humdata.org/dataset/movement-range-maps).
- Province and city/municipality names used are taken from the [Database of Global Administrative Areas (GADM)](https://gadm.org/download_country_v3.html).
- COVID-19 Policy Restrictions data can be found in the [Oxford Coronavirus Government Response Tracker (OXCGRT)](https://www.bsg.ox.ac.uk/research/research-projects/covid-19-government-response-tracker)
- A spreadsheet containing all the weather events used in this app can be found [here](https://docs.google.com/spreadsheets/d/1RTvPgw29yTXi9GAAc8kSQAJ-3sQU7MqOMwZgbAEoG4E/edit#gid=0). Please [write to us](mailto:mkhan57@worldbank.org) with suggestions for additions to this spreadsheet.

### Other resources
- [[Blog]](https://towardsdatascience.com/small-districts-big-data-who-does-geo-referenced-mobility-data-represent-78212ca004f6) Who Does Smartphone Location Data Represent?
- [[Blog]](https://towardsdatascience.com/the-digital-tailwinds-of-pandemics-and-typhoons-cross-border-insights-from-facebook-mobility-data-763c493b5ecc) Can Human Mobility Disruptions in Cities Be Seen in Near-Real-Time?
- [[Blog]](https://mahamfkhan.medium.com/how-do-people-move-during-a-disaster-fad910e5de45) Quantifying disruptions to human activity in near-real-time: A tutorial
"""
st.markdown(str)
