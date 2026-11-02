import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from dashboard.utils import data_loader as dl


QUICK_LOCATIONS = {
    # INDORE
    "SVVV University, Indore": (22.81796, 75.84781),
    "Vijay Nagar, Indore": (22.7533, 75.8937),
    "Rajwada, Indore": (22.7177, 75.8655),
    "Indore Airport": (22.7218, 75.8011),
    "IIT Indore": (22.5204, 75.9207),
    "Palasia, Indore": (22.7244, 75.8839),
    "Bhawarkua, Indore": (22.6958, 75.8687),
    "Rau, Indore": (22.6380, 75.8060),
    "Mhow, Indore": (22.5579, 75.7580),
    "Pithampur": (22.6133, 75.6860),
    "Mangliya, Indore": (22.7940, 75.9250),
    "Super Corridor, Indore": (22.7460, 75.8300),

    # BHOPAL
    "Bhopal - New Market": (23.2599, 77.4126),
    "MP Nagar, Bhopal": (23.2330, 77.4340),
    "Arera Colony, Bhopal": (23.2110, 77.4330),
    "Kolar Road, Bhopal": (23.1710, 77.4110),
    "Bairagarh, Bhopal": (23.2840, 77.3430),
    "BHEL, Bhopal": (23.2040, 77.4600),
    "Habibganj, Bhopal": (23.2230, 77.4370),
    "Bhojpur, Raisen": (23.1030, 77.5870),
    "Sanchi, Raisen": (23.4860, 77.7390),

    # UJJAIN DIVISION
    "Ujjain - Mahakal": (23.1765, 75.7885),
    "Dewas City": (22.9676, 76.0534),
    "Nagda": (23.4550, 75.4170),
    "Ratlam": (23.3315, 75.0367),
    "Mandsaur": (24.0717, 75.0699),
    "Neemuch": (24.4764, 74.8624),
    "Shajapur": (23.4260, 76.2730),
    "Agar Malwa": (23.7110, 76.0150),

    # SAGAR DIVISION
    "Sagar City": (23.8388, 78.7378),
    "Makronia, Sagar": (23.9072, 78.7251),
    "Damoh": (23.8381, 79.4422),
    "Chhatarpur": (24.9167, 79.5833),
    "Tikamgarh": (24.7430, 78.8300),
    "Panna": (24.7180, 80.1850),
    "Niwari": (25.0060, 78.7350),

    # BHOPAL DIVISION
    "Sehore": (23.2030, 77.0840),
    "Vidisha": (23.5251, 77.8081),
    "Raisen": (23.3315, 77.7810),
    "Rajgarh": (24.0020, 76.7280),
    "Narmadapuram": (22.7510, 77.7270),
    "Itarsi": (22.6148, 77.7628),
    "Betul": (21.9000, 77.9000),

    # GWALIOR-CHAMBAL DIVISION
    "Gwalior": (26.2183, 78.1828),
    "Morena": (26.4980, 77.9950),
    "Bhind": (26.5640, 78.7870),
    "Shivpuri": (25.4230, 77.6620),
    "Datia": (25.6650, 78.4610),
    "Sheopur": (25.6720, 76.6960),

    # JABALPUR DIVISION
    "Jabalpur": (23.1815, 79.9864),
    "Katni": (23.8340, 80.3940),
    "Narsinghpur": (22.9470, 79.1940),
    "Seoni": (22.0860, 79.5430),
    "Chhindwara": (22.0570, 78.9380),
    "Balaghat": (21.8120, 80.1830),
    "Mandla": (22.5980, 80.3710),

    # REWA AND SHAHDOL DIVISION
    "Rewa": (24.5362, 81.3037),
    "Satna": (24.6005, 80.8322),
    "Sidhi": (24.4160, 81.8790),
    "Singrauli": (24.1990, 82.6750),
    "Shahdol": (23.3010, 81.3560),
    "Umaria": (23.5240, 80.8370),
    "Anuppur": (23.1030, 81.6900),

    # NIMAR AND OTHER REGIONS
    "Khandwa": (21.8240, 76.3500),
    "Burhanpur": (21.3100, 76.2300),
    "Khargone": (21.8230, 75.6100),
    "Barwani": (22.0320, 74.9000),
    "Dhar": (22.6010, 75.3020),
    "Jhabua": (22.7670, 74.5900),
    "Alirajpur": (22.3100, 74.3600),
    "Maheshwar": (22.1770, 75.5870),
    "Omkareshwar": (22.2450, 76.1520),
    "Mandu": (22.3330, 75.3970),
}


@st.cache_data(ttl=86400, show_spinner=False)
def geocode_place(place):
    geolocator = Nominatim(
        user_agent="MP_Groundwater_Intelligence_Academic_Project"
    )
    try:
        result = geolocator.geocode(
            f"{place}, Madhya Pradesh, India",
            timeout=12,
            country_codes="in"
        )
        if result:
            return {
                "latitude": result.latitude,
                "longitude": result.longitude,
                "address": result.address
            }
    except (GeocoderTimedOut, GeocoderServiceError):
        return None
    return None


def calculate_distances(lat, lon, df):
    earth_radius = 6371.0

    lat1 = np.radians(lat)
    lon1 = np.radians(lon)
    lat2 = np.radians(df["latitude"].to_numpy(dtype=float))
    lon2 = np.radians(df["longitude"].to_numpy(dtype=float))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )

    df = df.copy()
    df["distance_km"] = (
        2 * earth_radius * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    )
    return df.sort_values("distance_km")


def render():
    st.markdown(
        '<div class="page-title">Location-Based Groundwater Search</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        "Search a location in Madhya Pradesh and explore nearby CGWB groundwater stations.",
        unsafe_allow_html=True
    )

    latest = dl.load_latest_readings()
    quarterly = dl.load_quarterly_summary()

    if latest is None or latest.empty:
        st.error("Latest station readings are unavailable.")
        return

    required = {"latitude", "longitude", "station", "wl_raw"}
    if not required.issubset(latest.columns):
        st.error(f"Station data is missing required columns: {required - set(latest.columns)}")
        return

    stations = latest.copy()
    stations["latitude"] = pd.to_numeric(stations["latitude"], errors="coerce")
    stations["longitude"] = pd.to_numeric(stations["longitude"], errors="coerce")
    stations["wl_raw"] = pd.to_numeric(stations["wl_raw"], errors="coerce")

    stations = stations.dropna(subset=["latitude", "longitude"])
    stations = stations[
        stations["latitude"].between(21, 27)
        & stations["longitude"].between(74, 83)
    ].copy()

    if stations.empty:
        st.error("No valid Madhya Pradesh station coordinates found.")
        return

    st.sidebar.markdown("## 🔍 Search Location")

    quick_choice = st.sidebar.selectbox(
        "Quick select a location",
        ["-- Select location --"] + list(QUICK_LOCATIONS.keys())
    )

    if quick_choice != "-- Select location --":
        qlat, qlon = QUICK_LOCATIONS[quick_choice]
        st.session_state["groundwater_location"] = {
            "latitude": qlat,
            "longitude": qlon,
            "address": quick_choice
        }

    search_query = st.sidebar.text_input(
        "Or enter any city / town / area",
        placeholder="Example: Indore, Dewas, Sehore"
    )

    if st.sidebar.button("🔎 Search location", type="primary"):
        if not search_query.strip():
            st.sidebar.warning("Enter a location first.")
        else:
            with st.spinner("Finding location..."):
                result = geocode_place(search_query.strip())

            if result:
                st.session_state["groundwater_location"] = result
                st.sidebar.success("Location found.")
            else:
                st.sidebar.error("Location not found. Try a more specific name.")

    if "groundwater_location" not in st.session_state:
        st.info("Search for a city or select a quick location to begin.")
        st.caption("Example: SVVV University, Indore")
        return

    location = st.session_state["groundwater_location"]
    lat = float(location["latitude"])
    lon = float(location["longitude"])

    st.subheader("📍 Selected Location")

    c1, c2, c3 = st.columns(3)
    c1.metric("Latitude", f"{lat:.6f}")
    c2.metric("Longitude", f"{lon:.6f}")
    c3.metric("Available CGWB stations", f"{len(stations):,}")

    st.caption(location.get("address", "Selected map location"))

    nearby = calculate_distances(lat, lon, stations)
    nearest = nearby.iloc[0]

    st.markdown("---")
    st.subheader("🗺️ Nearby CGWB Monitoring Stations")

    map_obj = folium.Map(
        location=[lat, lon],
        zoom_start=10,
        tiles="OpenStreetMap"
    )

    folium.Marker(
        [lat, lon],
        tooltip="Selected search location",
        popup="Your selected location",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(map_obj)

    for _, row in nearby.head(100).iterrows():
        level = row.get("wl_raw")
        popup_text = (
            f"Station: {row['station']}<br>"
            f"District: {row.get('district', 'Unavailable')}<br>"
            f"Groundwater reading: {level}<br>"
            f"Distance: {row['distance_km']:.2f} km"
        )

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color="blue",
            fill=True,
            fill_opacity=0.75,
            tooltip=str(row["station"]),
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(map_obj)

    map_result = st_folium(
        map_obj,
        width=None,
        height=500,
        key="location_groundwater_map"
    )

    if map_result and map_result.get("last_clicked"):
        clicked = map_result["last_clicked"]
        new_location = {
            "latitude": float(clicked["lat"]),
            "longitude": float(clicked["lng"]),
            "address": "Location selected by clicking the map"
        }

        old = st.session_state["groundwater_location"]
        if (
            abs(old["latitude"] - new_location["latitude"]) > 0.00001
            or abs(old["longitude"] - new_location["longitude"]) > 0.00001
        ):
            st.session_state["groundwater_location"] = new_location
            st.rerun()

    st.caption(
        f"Showing the 100 nearest stations. "
        f"Nearest station distance: {nearest['distance_km']:.2f} km."
    )

    st.subheader("📊 Nearest Station Details")

    c1, c2, c3 = st.columns(3)
    c1.metric("Station", str(nearest["station"]))
    c2.metric("District", str(nearest.get("district", "Unavailable")))
    c3.metric(
        "Distance",
        f"{nearest['distance_km']:.2f} km"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Latest groundwater reading",
        f"{nearest['wl_raw']:.3f} m" if pd.notna(nearest["wl_raw"]) else "Unavailable"
    )
    c2.metric("Station latitude", f"{nearest['latitude']:.6f}")
    c3.metric("Station longitude", f"{nearest['longitude']:.6f}")

    st.caption(
        "The groundwater reading belongs to the monitoring station, "
        "not directly to the searched location."
    )

    st.subheader("Nearby Station List")
    display_cols = [
        c for c in [
            "station", "district", "distance_km",
            "latitude", "longitude", "wl_raw", "datetime"
        ] if c in nearby.columns
    ]

    st.dataframe(
        nearby[display_cols].head(20).round(4),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.subheader("📅 Quarterly Groundwater History")

    if quarterly is None or quarterly.empty:
        st.warning("Quarterly summary is unavailable.")
        return

    station_options = nearby.head(20)["station"].astype(str).tolist()

    selected_station = st.selectbox(
        "Choose a nearby station for quarterly analysis",
        station_options,
        index=0
    )

    history = quarterly[
        quarterly["station"].astype(str) == selected_station
    ].copy()

    if history.empty:
        st.warning("No quarterly observations found for this station.")
        return

    # Normalize representative_month safely: the loader may provide
    # numeric month values (3, 6, 9, 12) or month names.
    month_lookup = {
        "3": "March", "3.0": "March", "mar": "March", "march": "March",
        "6": "June", "6.0": "June", "jun": "June", "june": "June",
        "9": "September", "9.0": "September", "sep": "September",
        "sept": "September", "september": "September",
        "12": "December", "12.0": "December", "dec": "December",
        "december": "December",
    }
    month_order = ["March", "June", "September", "December"]

    history["month_name"] = (
        history["representative_month"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(month_lookup)
    )
    history["year"] = pd.to_numeric(history["year"], errors="coerce")
    history["wl_mean"] = pd.to_numeric(history["wl_mean"], errors="coerce")

    history = history.dropna(
        subset=["year", "month_name", "wl_mean"]
    ).copy()
    history["year"] = history["year"].astype(int)

    if history.empty:
        st.warning(
            "This station has no valid March, June, September or December "
            "groundwater observations in the quarterly summary."
        )
        return

    # Create the pivot before using it in st.dataframe.
    pivot = (
        history.pivot_table(
            index="year",
            columns="month_name",
            values="wl_mean",
            aggfunc="mean",
        )
        .reindex(columns=month_order)
        .sort_index()
    )
    pivot.columns.name = None

    st.markdown(f"**Quarterly readings for {selected_station}**")
    st.dataframe(
        pivot.style.format("{:.3f}", na_rep="Unavailable"),
        use_container_width=True,
    )

    chart_data = history.copy()

    if not chart_data.empty:
        import plotly.express as px

        # Explicit blue/teal palette prevents Plotly's default pink colors.
        month_colors = {
            "March": "#2563EB",
            "June": "#0F766E",
            "September": "#0891B2",
            "December": "#475569",
        }

        chart = px.line(
            chart_data,
            x="year",
            y="wl_mean",
            color="month_name",
            markers=True,
            category_orders={"month_name": month_order},
            color_discrete_map=month_colors,
            title="Groundwater Level Across Representative Months",
            labels={
                "year": "Year",
                "wl_mean": "Average groundwater level (m)",
                "month_name": "Representative month",
            },
            template="plotly_white",
        )
        chart.update_traces(line=dict(width=2.5), marker=dict(size=8))
        chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1E293B"),
            title_font=dict(color="#0F172A"),
            legend_title_text="Representative month",
            height=430,
            hovermode="x unified",
        )
        st.plotly_chart(chart, use_container_width=True)

    st.download_button(
        "Download quarterly station history",
        data=history.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_station}_quarterly_history.csv",
        mime="text/csv",
    )

    st.info(
        "Quarterly values are averages of available readings in March, June, "
        "September and December. Missing months are shown as unavailable. "
        "The nearest station is a proxy for the selected location, not a "
        "direct measurement at that location."
    )

    st.warning(
        "Groundwater level alone cannot determine drinking-water quality, "
        "well yield, drilling depth or well-construction suitability. "
        "Those assessments require verified field, geological and laboratory data."
    )
