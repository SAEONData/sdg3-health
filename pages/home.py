import streamlit as st
from components.geographic_filter import GeographicFilter
from components.map_visualization import MapVisualization
from config.database import DatabaseConfig
from config.settings import PAGES_CONFIG, MAP_LAYERS
import pandas as pd

def render():
    """Render the complete Home - SDG 3 Overview page"""
    
    st.title("🏠 SDG 3: Ensure Good Health and Promote Well-being for All")
    st.markdown("### South Africa Health Dashboard Overview")
    
    geo_filter = GeographicFilter()
    map_viz = MapVisualization()
    
    selection = geo_filter.render_sidebar_filter()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Geographic Overview")
        
        display_current_selection(selection)
        
        selected_layer = map_viz.render_layer_toggles()
        
        with st.spinner("🗺️ Loading map..."):
            map_obj = map_viz.render_map(selection, selected_layer)
            
            from streamlit_folium import st_folium
            
            try: 
                map_data = st_folium(
                    map_obj, 
                    width=700, 
                    height=500,
                    returned_data=["last_clicked"],
                    key="main_map"
                )
            except TypeError as e:
                map_data=st_folium(
                    map_obj, 
                    width=700, 
                    height=500,
                    key="main_map"
                )
                       
    with col2:
        st.subheader("📊 Summary Stats")
        
        render_summary_panel(selection)
        
        st.markdown("---")
        st.markdown("### Quick Navigation")
        render_navigation_buttons()


def display_current_selection(selection: dict):
    """Display current geographic selection with appropriate styling"""
    
    if selection["level"] == "national":
        st.success("**Current View**: All South Africa")
        st.markdown("*Select a province from the sidebar to drill down*")
        
    elif selection["level"] == "province":
        st.success(f"**Current View**: {selection['province_name']} Province")
        st.markdown("*Select a district to drill down further*")
        
    elif selection["level"] == "district": 
        st.success(f"**Current View**: {selection['district_name']} District")
        st.markdown(f"**Province**: {selection['province_name']}")
        st.markdown("*Select a municipality for detailed view*")
        
    elif selection["level"] == "municipality":
        st.success(f"**Current View**: {selection['municipality_name']}")
        st.markdown(f"**District**: {selection['district_name']}")
        st.markdown(f"**Province**: {selection['province_name']}")


def render_summary_panel(selection: dict):
    """Render summary statistics panel for selected geographic area"""
    
    summary_data = get_summary_statistics(selection)
    
    if summary_data is not None and not summary_data.empty:
        
        st.markdown("#### 🎯 Key Health Indicators")
        
        # Create metrics in a grid
        col1, col2 = st.columns(2)
        
        with col1:
            # Health Worker Density
            health_worker_density = summary_data.get('avg_health_worker_density', 0)
            if pd.notna(health_worker_density):
                st.metric(
                    label="🏥 Health Worker Density",
                    value=f"{health_worker_density:.1f}",
                    help="Per 10,000 population"
                )
            
            # TB Treatment Success Rate
            tb_success = summary_data.get('avg_tb_success_rate', 0)
            if pd.notna(tb_success):
                st.metric(
                    label="🫁 TB Treatment Success",
                    value=f"{tb_success:.1f}%",
                    help="DS-TB treatment success rate"
                )
        
        with col2:
            # HIV Cases
            hiv_cases = summary_data.get('total_hiv_cases', 0)
            if pd.notna(hiv_cases):
                st.metric(
                    label="🦠 People Living with HIV",
                    value=f"{int(hiv_cases):,}",
                    help="Total HIV cases"
                )
            
            # Health Facilities
            facilities = summary_data.get('total_facilities', 0)
            if pd.notna(facilities):
                st.metric(
                    label="🏗️ Health Facilities",
                    value=f"{int(facilities):,}",
                    help="Total health facilities"
                )
        
        # Population information
        st.markdown("#### 👥 Population Information")
        population = summary_data.get('total_population', 0)
        if pd.notna(population):
            st.metric(
                label="Total Population",
                value=f"{int(population):,}",
                help="Total population in selected area"
            )
        
        st.markdown("---") 
        selected_layer = st.session_state.get('map_layer_selector', 'Health_worker_density__index_')
        
        if selected_layer in MAP_LAYERS:
            layer_info = MAP_LAYERS[selected_layer]
            
            st.markdown(f"**Current Layer**: {layer_info['display_name']}")
            st.markdown(f"**Measuring**: {layer_info['description']} ({layer_info['unit']})")
        
    else:
        st.warning("📊 No data available for current selection")
        st.markdown("*Try selecting a different geographic area*")



def get_summary_statistics(selection: dict) -> pd.DataFrame:
    """Get summary statistics for selected geographic area"""
    
    config = DatabaseConfig()
    
    try:
        where_conditions = []
        params = {}
        
        if selection["province_code"]:
            where_conditions.append('"PROVINCE" = %(province_code)s')
            params["province_code"] = selection["province_code"]
        
        if selection["district_code"]:
            where_conditions.append('"DISTRICT" = %(district_code)s')
            params["district_code"] = selection["district_code"]
        
        if selection["municipality_code"]:
            where_conditions.append('"CAT_B" = %(municipality_code)s')
            params["municipality_code"] = selection["municipality_code"]
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f'''
        SELECT 
            SUM("Total_population") as total_population,
            AVG("Health_worker_density__index_") as avg_health_worker_density,
            SUM("Total_living_with_HIV") as total_hiv_cases,
            AVG("TB_DS_treatment_success_rate") as avg_tb_success_rate,
            SUM("Number_of_health_facilities") as total_facilities,
            COUNT(*) as total_areas
        FROM {config.table_name}
        {where_clause}
        '''
        
        result = pd.read_sql(query, config.get_engine(), params=params)
        return result.iloc[0] if not result.empty else None
        
    except Exception as e:
        st.error(f"Error loading summary statistics: {str(e)}")
        return None


def render_navigation_buttons():
    """Render quick navigation buttons to other dashboard pages"""
    
    st.markdown("**Explore Specific Health Areas:**")
    
    if st.button("🦠 HIV & TB Analysis", use_container_width=True, help="Detailed communicable disease analysis"):
        st.info("🚧 HIV & TB Analysis page coming soon...")
        
    if st.button("💔 Non-Communicable Diseases", use_container_width=True, help="Diabetes, cancer, cardiovascular diseases"):
        st.info("🚧 Non-Communicable Diseases page coming soon...")
        
    if st.button("🏛️ Social Determinants", use_container_width=True, help="Social factors affecting health"):
        st.info("🚧 Social Determinants page coming soon...")
        
    if st.button("🏥 Health System Capacity", use_container_width=True, help="Healthcare workforce and infrastructure"):
        st.info("🚧 Health System Capacity page coming soon...")
    
    st.markdown("---")
    st.markdown("**📋 About This Dashboard**")
    st.markdown("""
    This dashboard tracks South Africa's progress towards **SDG 3: Ensure Good Health and Promote Well-being for All**.
    
    **Key Features:**
    - 🗺️ Interactive geographic filtering
    - 📈 Performance benchmarking
    - 🎯 SDG target tracking
    """)


def navigate_to_page(page_name: str):
    """Navigate to a specific page (for future implementation)"""
    st.session_state.page_navigation = page_name
    st.rerun()