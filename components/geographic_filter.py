import streamlit as st
import pandas as pd
from data.queries import GeographicQueries
from config.settings import GEOGRAPHIC_LEVELS, COLORS
from typing import Dict, Optional

class GeographicFilter:
    """Geographic cascade filter component - Main focus for testing"""
    
    def __init__(self):
        self.queries = GeographicQueries()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize geographic selection in session state"""
        if 'selected_province' not in st.session_state:
            st.session_state.selected_province = None
        if 'selected_district' not in st.session_state:
            st.session_state.selected_district = None  
        if 'selected_municipality' not in st.session_state:
            st.session_state.selected_municipality = None
    
    def render_sidebar_filter(self) -> Dict[str, Optional[str]]:
        """Render the geographic filter in sidebar with detailed feedback"""
        
        st.sidebar.markdown("### Filter")
        
        selection = {
            "province_code": None,
            "province_name": None,
            "district_code": None, 
            "district_name": None,
            "municipality_code": None,
            "municipality_name": None,
            "level": "national"
        }
        
        # === PROVINCE SELECTION ===
        st.sidebar.markdown("#### Province")
        
        provinces_df = self.queries.get_provinces()
        
        if not provinces_df.empty:
            province_options = ["All South Africa"] + provinces_df["Province_name"].tolist()
            
            selected_province_name = st.sidebar.selectbox(
                "Select Province:",
                options=province_options,
                key="province_selector",
                help="Select a province to drill down to district level"
            )
            
            # === DISTRICT SELECTION ===
            if selected_province_name != "All South Africa":
                # Get province code
                province_row = provinces_df[provinces_df["Province_name"] == selected_province_name]
                
                if not province_row.empty:
                    province_code = province_row["PROVINCE"].iloc[0]
                    
                    selection.update({
                        "province_code": province_code,
                        "province_name": selected_province_name,
                        "level": "province"
                    })
                    
                    st.sidebar.markdown("#### District")
                    
                    districts_df = self.queries.get_districts(province_code)
                    
                    if not districts_df.empty:
                        district_options = ["🏛️ All Districts"] + districts_df["DISTRICT_N"].tolist()
                        
                        selected_district_name = st.sidebar.selectbox(
                            "Select District:",
                            options=district_options,
                            key="district_selector",
                            help="Select a district to drill down to municipality level"
                        )
                        
                        # === MUNICIPALITY SELECTION ===
                        if selected_district_name != "🏛️ All Districts":
                            district_row = districts_df[districts_df["DISTRICT_N"] == selected_district_name]
                            
                            if not district_row.empty:
                                district_code = district_row["DISTRICT"].iloc[0]
                                
                                selection.update({
                                    "district_code": district_code,
                                    "district_name": selected_district_name,
                                    "level": "district"
                                })
                                
                                st.sidebar.markdown("#### Municipality")
                                
                                municipalities_df = self.queries.get_municipalities(district_code)
                            
                                if not municipalities_df.empty:
                                    municipality_options = ["🏘️ All Municipalities"] + municipalities_df["MUNICNAME_1"].tolist()
                                    
                                    selected_municipality_name = st.sidebar.selectbox(
                                        "Select Municipality:",
                                        options=municipality_options,
                                        key="municipality_selector",
                                        help="Select specific municipality for detailed view"
                                    )
                                    
                                    if selected_municipality_name != "🏘️ All Municipalities":
                                        municipality_row = municipalities_df[
                                            municipalities_df["MUNICNAME_1"] == selected_municipality_name
                                        ]
                                        
                                        if not municipality_row.empty:
                                            municipality_code = municipality_row["CAT_B"].iloc[0]
                                            
                                            selection.update({
                                                "municipality_code": municipality_code,
                                                "municipality_name": selected_municipality_name,
                                                "level": "municipality"
                                            })
        
        # === SELECTION SUMMARY ===
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📋 Current Selection")
        
        if selection["level"] == "national":
            st.sidebar.info("**Viewing**: All South Africa")
        elif selection["level"] == "province":
            st.sidebar.info(f"🏔️ **Province**: {selection['province_name']}")
        elif selection["level"] == "district":
            st.sidebar.info(f"🏛️ **District**: {selection['district_name']}\n📍 **Province**: {selection['province_name']}")
        elif selection["level"] == "municipality":
            st.sidebar.info(f"🏘️ **Municipality**: {selection['municipality_name']}\n🏛️ **District**: {selection['district_name']}\n📍 **Province**: {selection['province_name']}")
        
        if st.sidebar.button("Reset ", help="Reset to national view"):
            for key in ["province_selector", "district_selector", "municipality_selector"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.session_state.geographic_selection = selection
        return selection