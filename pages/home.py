import streamlit as st
from components.geographic_filter import GeographicFilter
from components.map_visualization import MapVisualization
from data.queries import GeographicQueries
from config.database import DatabaseConfig
from config.settings import PAGES_CONFIG, MAP_LAYERS
import pandas as pd

def render():
    """Render the complete Home - SDG 3 Overview page"""
    
    st.title("South Africa Health Dashboard")
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
    """Render summary statistics panel with performance calculations and national context"""
    
    # Initialize queries
    geo_queries = GeographicQueries()
    
    summary_data = get_summary_statistics(selection)
    
    if summary_data is not None and not summary_data.empty:
        
        st.markdown("#### 🎯 Key Health Indicators")
        
        with st.spinner("📊 Loading national averages..."):
            national_averages = geo_queries.get_national_averages()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Health Worker Density with performance
            health_worker_density = summary_data.get('avg_health_worker_density', 0)
            if pd.notna(health_worker_density) and national_averages:
                national_hwd = national_averages.get("national_health_worker_density")
                performance = geo_queries.calculate_performance_vs_national(
                    health_worker_density,
                    national_hwd,
                    "health_worker_density"
                )
                
                st.metric(
                    label=f"{performance['emoji']} Health Worker Density",
                    value=f"{health_worker_density:.1f}",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {health_worker_density:.1f} | National avg: {national_hwd:.1f} | Per 10,000 population"
                )
            
            # TB Treatment Success with performance
            tb_success = summary_data.get('avg_tb_success_rate', 0)
            if pd.notna(tb_success) and national_averages:
                national_tb = national_averages.get("national_tb_success_rate")
                performance = geo_queries.calculate_performance_vs_national(
                    tb_success,
                    national_tb,
                    "tb_ds_treatment_success_rate"
                )
                
                st.metric(
                    label=f"{performance['emoji']} TB Treatment Success",
                    value=f"{tb_success:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {tb_success:.1f}% | National avg: {national_tb:.1f}% | DS-TB treatment success"
                )
        
        with col2:
            hiv_cases = summary_data.get('total_hiv_cases', 0)
            if pd.notna(hiv_cases):

                if hiv_cases >= 1_000_000:
                    display_value = f"{hiv_cases/1_000_000:.1f}M"
                elif hiv_cases >= 1_000:
                    display_value = f"{hiv_cases/1_000:.1f}K"
                else:
                    display_value = f"{int(hiv_cases):,}"
                
                national_total_hiv = national_averages.get("national_total_hiv_cases") if national_averages else None
                if national_total_hiv and national_total_hiv > 0:
                    proportion = (hiv_cases / national_total_hiv) * 100
                    help_text = f"Local: {display_value} | {proportion:.1f}% of national total ({national_total_hiv/1_000_000:.1f}M)"
                else:
                    help_text = f"Total HIV cases in selected area: {display_value}"
                
                st.metric(
                    label="🦠 People Living with HIV",
                    value=display_value,
                    help=help_text
                )
            
            facilities = summary_data.get('total_facilities', 0)
            if pd.notna(facilities):
                
                national_facilities = national_averages.get("national_total_facilities") if national_averages else None
                if national_facilities and national_facilities > 0:
                    proportion = (facilities / national_facilities) * 100
                    help_text = f"Local: {int(facilities):,} | {proportion:.1f}% of national total ({int(national_facilities):,})"
                else:
                    help_text = f"Total health facilities: {int(facilities):,}"
                
                st.metric(
                    label="🏗️ Health Facilities",
                    value=f"{int(facilities):,}",
                    help=help_text
                )
        
        st.markdown("#### 👥 Population Information")
        population = summary_data.get('total_population', 0)
        if pd.notna(population):
            if population >= 1_000_000:
                display_pop = f"{population/1_000_000:.1f}M"
            elif population >= 1_000:
                display_pop = f"{population/1_000:.1f}K"
            else:
                display_pop = f"{int(population):,}"
            
            national_pop = national_averages.get("national_total_population") if national_averages else None
            if national_pop and national_pop > 0:
                proportion = (population / national_pop) * 100
                help_text = f"Local: {display_pop} | {proportion:.1f}% of national population ({national_pop/1_000_000:.1f}M)"
            else:
                help_text = f"Total population in selected area: {display_pop}"
            
            st.metric(
                label="Total Population",
                value=display_pop,
                help=help_text
            )
        
        if national_averages:
            st.markdown("#### 📈 Performance vs National Average")
            
            with st.expander("📊 View National Average Values", expanded=False):
                st.markdown("**National Averages for Comparison:**")
                
                ref_col1, ref_col2 = st.columns(2)
                
                with ref_col1:
                    if national_averages.get("national_health_worker_density"):
                        st.markdown(f"🏥 **Health Worker Density**: {national_averages['national_health_worker_density']:.1f}")
                    if national_averages.get("national_tb_success_rate"):
                        st.markdown(f"🫁 **TB Treatment Success**: {national_averages['national_tb_success_rate']:.1f}%")
                
                with ref_col2:
                    if national_averages.get("national_total_hiv_cases"):
                        hiv_nat = national_averages['national_total_hiv_cases']
                        st.markdown(f"🦠 **Total HIV Cases**: {hiv_nat/1_000_000:.1f}M")
                    if national_averages.get("national_total_facilities"):
                        st.markdown(f"🏗️ **Health Facilities**: {int(national_averages['national_total_facilities']):,}")
            
            performance_ind = []
            
            if pd.notna(health_worker_density):
                perf = geo_queries.calculate_performance_vs_national(
                    health_worker_density,
                    national_averages.get("national_health_worker_density"),
                    "health_worker_density"
                )

                performance_ind.append({
                    "name": "Health Worker Density",
                    "performance": perf,
                    "local": health_worker_density,
                    "national": national_averages.get("national_health_worker_density")
                })
            
            if pd.notna(tb_success):
                perf = geo_queries.calculate_performance_vs_national(
                    tb_success,
                    national_averages.get("national_tb_success_rate"),
                    "tb_ds_treatment_success_rate"
                )
                performance_ind.append({
                    "name": "TB Treatment Success",
                    "performance": perf,
                    "local": tb_success,
                    "national": national_averages.get("national_tb_success_rate")
                })
            
            for indicator in performance_ind:
                perf = indicator["performance"]
                local_val = indicator["local"]
                national_val = indicator["national"]
                
                if national_val:
                    st.markdown(f"{perf['emoji']} **{indicator['name']}**: {local_val:.1f} vs {national_val:.1f} (national) — {perf['interpretation']}")
                else:
                    st.markdown(f"{perf['emoji']} **{indicator['name']}**: {perf['interpretation']}")
            
            if not performance_ind:
                st.markdown("*Performance indicators will appear when data is available*")
        
        else:
            st.warning("⚠️ National averages not available for comparison")
        
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
            AVG("Adult_living_with_HIV_viral_loa") as avg_hiv_viral_suppression,
            AVG("Diabetes_prevalence") as avg_diabetes_prevalence,
            AVG("Immunisation_under_1_year_cov_1") as avg_immunization_coverage,
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
    This dashboard tracks South Africa's progress towards **South Africa Health Goals as per the SDG 3**.

    **Key Features:**
    - 🎯 SDG target tracking
    - 🗺️ Interactive geographic filtering
    - 📈 Performance benchmarking
    """)


def navigate_to_page(page_name: str):
    """Navigate to a specific page (for future implementation)"""
    st.session_state.page_navigation = page_name
    st.rerun()