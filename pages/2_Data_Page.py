# Lab 3: API data page
# TODO: Rename this file to fit your page. Keep the number at the front, since it sets the
#       page's order in the sidebar (for example, 2_Pokedex.py).
#
# This page shows data from your API, processed with your own Python code. No AI on this page.
# It should have:
#   - at least 2 meaningful user inputs (for example st.selectbox, st.text_input, st.slider)
#   - at least 2 dynamic visuals that change based on the user's input: charts, displays of
#     images, or other visualizations (see the example website for examples!)



import requests
import streamlit as st
import pandas as pd



st.set_page_config(
    page_title="Global Trade Insights",
    page_icon="🌍",
    layout="wide"
)



EXPORT_INDICATOR = "TX.VAL.MRCH.CD.WT"
IMPORT_INDICATOR = "TM.VAL.MRCH.CD.WT"

BASE_URL = "https://api.worldbank.org/v2"

START_YEAR = 1960
END_YEAR = 2025



@st.cache_data(ttl=86400)
def get_countries():

    url = f"{BASE_URL}/country"

    params = {
        "format": "json",
        "per_page": 300
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()

    countries = []

    if len(data) > 1 and data[1] is not None:

        for country in data[1]:

            if country["region"]["id"] != "NA":

                countries.append({
                    "name": country["name"],
                    "code": country["id"]
                })

    countries.sort(key=lambda x: x["name"])

    return countries



@st.cache_data(ttl=86400)
def get_indicator_data(country_code, indicator, start_year, end_year):

    url = (
        f"{BASE_URL}/country/{country_code}/indicator/"
        f"{indicator}"
    )

    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 1000
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    result = response.json()

    observations = []

    if len(result) > 1 and result[1] is not None:

        for item in result[1]:

            observations.append({
                "Year": int(item["date"]),
                "Value": item["value"]
            })

    return pd.DataFrame(observations)



@st.cache_data(ttl=86400)
def get_trade_data(country_code, start_year, end_year):

    exports = get_indicator_data(
        country_code,
        EXPORT_INDICATOR,
        start_year,
        end_year
    )

    imports = get_indicator_data(
        country_code,
        IMPORT_INDICATOR,
        start_year,
        end_year
    )

    exports = exports.rename(columns={"Value": "Exports"})
    imports = imports.rename(columns={"Value": "Imports"})

    trade_data = pd.merge(
        exports,
        imports,
        on="Year",
        how="outer"
    )

    trade_data = trade_data.sort_values("Year")

    return trade_data



try:

    countries = get_countries()

    country_names = [
        country["name"] for country in countries
    ]

    country_codes = {
        country["name"]: country["code"]
        for country in countries
    }

except requests.exceptions.RequestException as error:

    st.error(f"Could not retrieve the country list: {error}")
    st.stop()



st.title("🌍 Global Trade Insights")

st.write(
    "Explore international merchandise trade data "
    "through country comparisons and historical analysis."
)

st.caption(
    "Data source: World Bank Indicators API | "
    "Values are in current US dollars."
)


# FEATURE 1: COUNTRY COMPARISON

st.header("1. Country Comparison")

st.write(
    "Compare merchandise imports and exports "
    "between two countries in a selected year."
)

col1, col2, col3 = st.columns(3)

with col1:

    country_1 = st.selectbox(
        "First Country",
        country_names,
        index=country_names.index("United States")
        if "United States" in country_names else 0
    )

with col2:

    available_countries = [
        country for country in country_names
        if country != country_1
    ]

    country_2 = st.selectbox(
        "Second Country",
        available_countries
    )

with col3:

    comparison_year = st.selectbox(
        "Select Year",
        list(range(END_YEAR, START_YEAR - 1, -1))
    )


if st.button("Compare Countries"):

    try:

        data_1 = get_trade_data(
            country_codes[country_1],
            comparison_year,
            comparison_year
        )

        data_2 = get_trade_data(
            country_codes[country_2],
            comparison_year,
            comparison_year
        )

        if not data_1.empty and not data_2.empty:

            comparison_data = pd.DataFrame([
                {
                    "Country": country_1,
                    "Exports": data_1.iloc[0]["Exports"],
                    "Imports": data_1.iloc[0]["Imports"]
                },
                {
                    "Country": country_2,
                    "Exports": data_2.iloc[0]["Exports"],
                    "Imports": data_2.iloc[0]["Imports"]
                }
            ])

            comparison_data = comparison_data.dropna(
                subset=["Exports", "Imports"],
                how="all"
            )

            if not comparison_data.empty:

                st.subheader(
                    f"Trade Comparison – {comparison_year}"
                )

                st.bar_chart(
                    comparison_data.set_index("Country")
                )

                st.dataframe(
                    comparison_data,
                    use_container_width=True
                )

            else:

                st.warning(
                    "No trade data is available for these countries."
                )

        else:

            st.warning(
                "No data was found for the selected year."
            )

    except requests.exceptions.RequestException as error:

        st.error(f"API request failed: {error}")


st.divider()


# FEATURE 2: TRADE BALANCE ANALYSIS

st.header("2. Trade Balance Analysis")

st.write(
    "Examine whether a country has a trade surplus "
    "or a trade deficit in a selected year."
)

balance_country = st.selectbox(
    "Select a Country",
    country_names,
    key="balance_country"
)

balance_year = st.selectbox(
    "Select Year for Trade Balance",
    list(range(END_YEAR, START_YEAR - 1, -1)),
    key="balance_year"
)


if st.button("Analyze Trade Balance"):

    try:

        balance_data = get_trade_data(
            country_codes[balance_country],
            balance_year,
            balance_year
        )

        if not balance_data.empty:

            exports = balance_data.iloc[0]["Exports"]
            imports = balance_data.iloc[0]["Imports"]

            if pd.notna(exports) and pd.notna(imports):

                trade_balance = exports - imports

                st.subheader(
                    f"{balance_country} – {balance_year}"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Merchandise Exports",
                        f"${exports:,.0f}"
                    )

                with col2:

                    st.metric(
                        "Merchandise Imports",
                        f"${imports:,.0f}"
                    )

                with col3:

                    st.metric(
                        "Trade Balance",
                        f"${trade_balance:,.0f}"
                    )

                if trade_balance > 0:

                    st.success(
                        "Trade Surplus: Exports are greater than imports."
                    )

                elif trade_balance < 0:

                    st.warning(
                        "Trade Deficit: Imports are greater than exports."
                    )

                else:

                    st.info(
                        "Balanced Trade: Exports equal imports."
                    )

                balance_chart = pd.DataFrame({
                    "Category": ["Exports", "Imports"],
                    "Value": [exports, imports]
                })

                st.bar_chart(
                    balance_chart.set_index("Category")
                )

            else:

                st.warning(
                    "One or both observations are missing. "
                    "Trade balance cannot be calculated."
                )

        else:

            st.warning(
                "No trade data is available for this selection."
            )

    except requests.exceptions.RequestException as error:

        st.error(f"API request failed: {error}")


st.divider()


# FEATURE 3: HISTORICAL TRADE TRENDS

st.header("3. Historical Trade Trends")

st.write(
    "Explore how merchandise imports and exports "
    "have changed over a selected historical period."
)

historical_country = st.selectbox(
    "Select a Country for Historical Analysis",
    country_names,
    key="historical_country"
)

year_range = st.slider(
    "Select Historical Period",
    min_value=START_YEAR,
    max_value=END_YEAR,
    value=(2000, END_YEAR)
)


if st.button("Show Historical Trends"):

    try:

        historical_data = get_trade_data(
            country_codes[historical_country],
            year_range[0],
            year_range[1]
        )

        if not historical_data.empty:

            historical_data["Trade Balance"] = (
                historical_data["Exports"]
                - historical_data["Imports"]
            )

            st.subheader(
                f"Historical Trade Trends – {historical_country}"
            )

            st.line_chart(
                historical_data.set_index("Year")[
                    ["Exports", "Imports"]
                ]
            )

            st.subheader("Annual Trade Balance")

            st.bar_chart(
                historical_data.set_index("Year")[
                    ["Trade Balance"]
                ]
            )

            st.dataframe(
                historical_data,
                use_container_width=True
            )

        else:

            st.warning(
                "No historical data is available for this selection."
            )

    except requests.exceptions.RequestException as error:

        st.error(f"API request failed: {error}")

