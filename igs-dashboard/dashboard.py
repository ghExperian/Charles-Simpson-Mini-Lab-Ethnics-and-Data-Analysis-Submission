import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import nh3

st.title("IGS Dashboard: California Census Tracts")
st.markdown("Visualize social and economic indicators for low- and high-income neighborhoods.")

@st.cache_data
def login_to_api(username, password, api_url="http://localhost:8000/token"):
    try:
        response = requests.post(api_url, data={"username": username, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.RequestException as e:
        st.error(f"Login failed: {str(e)}")
        return None

@st.cache_data
def fetch_api_data(token, api_url="http://localhost:8000/tracts/"):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        for item in data:
            item["census_tract"] = nh3.clean(item["census_tract"])
        return pd.DataFrame(data)
    except requests.RequestException as e:
        st.error(f"API error: {str(e)}")
        return None

# Login
st.sidebar.header("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
if st.sidebar.button("Login"):
    token = login_to_api(username, password)
    if token:
        st.session_state.token = token
        st.success("Login successful!")
    else:
        st.stop()

# Fetch data
if "token" not in st.session_state:
    st.warning("Please log in to access data.")
    st.stop()
df = fetch_api_data(st.session_state.token)
if df is None:
    st.stop()

# Data structure: List of unique census tracts
tract_list = sorted(list(df["census_tract"]))
st.write(f"Available Census Tracts: {tract_list}")

# Filters
st.sidebar.header("Filters")
selected_tract = st.sidebar.selectbox("Select Census Tract", ["All"] + tract_list)
min_inclusion = st.sidebar.slider("Minimum Inclusion Score", 0, 100, 0)
filtered_df = df[df["inclusion_score"] >= min_inclusion]
if selected_tract != "All":
    filtered_df = filtered_df[filtered_df["census_tract"] == selected_tract]

# Layout
col1, col2 = st.columns(2)
with col1:
    st.subheader("Census Tract Data")
    st.dataframe(filtered_df)
with col2:
    st.subheader("Inclusion vs. Growth")
    fig = px.scatter(filtered_df, x="inclusion_score", y="growth_score", color="census_tract")
    st.plotly_chart(fig)