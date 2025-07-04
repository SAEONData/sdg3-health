import streamlit as st
import pandas as pd
import geopandas as gpd
from config.database import DatabaseConfig
from config.settings import CACHE_CONFIG
import logging

class GeographicQueries:
    """Geographic-related database queries with error handling"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = self.config.get_engine()
    
    @st.cache_data(ttl=CACHE_CONFIG['geographic_data_ttl'])
    def get_provinces(_self) -> pd.DataFrame:
        """Get all provinces for dropdown"""
        try:
            query = f'''
            SELECT DISTINCT "PROVINCE", "Province_name" 
            FROM {_self.config.table_name}
            WHERE "Province_name" IS NOT NULL 
              AND "PROVINCE" IS NOT NULL
            ORDER BY "Province_name"
            '''
            
            df = pd.read_sql(query, _self.engine)
            
            if df.empty:
                st.warning("No province data found in database")
                return pd.DataFrame(columns=["PROVINCE", "Province_name"])
        
            return df
            
        except Exception as e:
            st.error(f"❌ Error loading provinces: {str(e)}")
            return pd.DataFrame(columns=["PROVINCE", "Province_name"])
    
    @st.cache_data(ttl=CACHE_CONFIG['health_indicators_ttl'])
    def get_districts(_self, province_code: str) -> pd.DataFrame:
        """Get districts for selected province"""
        try:
            query = f'''
            SELECT DISTINCT "DISTRICT", "DISTRICT_N" 
            FROM {_self.config.table_name}
            WHERE "PROVINCE" = %(province_code)s 
              AND "DISTRICT_N" IS NOT NULL
              AND "DISTRICT" IS NOT NULL
            ORDER BY "DISTRICT_N"
            '''
            
            df = pd.read_sql(query, _self.engine, params={"province_code": province_code})
            
            if df.empty:
                return pd.DataFrame(columns=["DISTRICT", "DISTRICT_N"])
            
            return df
            
        except Exception as e:
            st.error(f"❌ Error loading districts: {str(e)}")
            return pd.DataFrame(columns=["DISTRICT", "DISTRICT_N"])
    
    @st.cache_data(ttl=CACHE_CONFIG['health_indicators_ttl'])
    def get_municipalities(_self, district_code: str) -> pd.DataFrame:
        """Get municipalities for selected district"""
        try:
            query = f'''
            SELECT DISTINCT "CAT_B", "MUNICNAME_1" 
            FROM {_self.config.table_name}
            WHERE "DISTRICT" = %(district_code)s 
              AND "MUNICNAME_1" IS NOT NULL
              AND "CAT_B" IS NOT NULL
            ORDER BY "MUNICNAME_1"
            '''
            df = pd.read_sql(query, _self.engine, params={"district_code": district_code})

            if df.empty:
                return pd.DataFrame(columns=["CAT_B", "MUNICNAME_1"])
            return df
            
        except Exception as e:
            st.error(f"❌ Error loading municipalities: {str(e)}")
            return pd.DataFrame(columns=["CAT_B", "MUNICNAME_1"])
        
 
    @st.cache_data(ttl=CACHE_CONFIG["spatial_data_ttl"])
    def get_province_boundaries(_self) -> gpd.GeoDataFrame:
        """Get province boundaries with health indicators"""
        
        query = f'''
        SELECT 
            "PROVINCE",
            "Province_name",
            AVG("Health_worker_density__index_") as "Health_worker_density__index_",
            SUM("Total_living_with_HIV") as "Total_living_with_HIV",
            AVG("TB_DS_treatment_success_rate") as "TB_DS_treatment_success_rate",
            COUNT("Number_of_health_facilities") as "Number_of_health_facilities",
            SUM("Total_population") as "Total_population",
            ST_Union("geometry") as "geometry"
        FROM {_self.config.table_name}
        WHERE "geometry" IS NOT NULL
        GROUP BY "PROVINCE", "Province_name"
        ORDER BY "Province_name"
        '''
        
        try:
            return gpd.read_postgis(query, _self.engine, geom_col='geometry')
        except Exception as e:
            st.error(f"Error loading province boundaries: {str(e)}")
            return gpd.GeoDataFrame()


    @st.cache_data(ttl=CACHE_CONFIG["spatial_data_ttl"])
    def get_district_boundaries(_self, province_code: str) -> gpd.GeoDataFrame:
        """Get district boundaries for selected province"""
        
        query = f'''
        SELECT 
            "DISTRICT",
            "DISTRICT_N",
            "PROVINCE",
            "Province_name",
            AVG("Health_worker_density__index_") as "Health_worker_density__index_",
            SUM("Total_living_with_HIV") as "Total_living_with_HIV",
            AVG("TB_DS_treatment_success_rate") as "TB_DS_treatment_success_rate",
            COUNT("Number_of_health_facilities") as "Number_of_health_facilities",
            SUM("Total_population") as "Total_population",
            ST_Union("geometry") as "geometry"
        FROM {_self.config.table_name}
        WHERE "PROVINCE" = %(province_code)s
          AND "geometry" IS NOT NULL
        GROUP BY "DISTRICT", "DISTRICT_N", "PROVINCE", "Province_name"
        ORDER BY "DISTRICT_N"
        '''
        
        try:
            return gpd.read_postgis(query, _self.engine, geom_col='geometry', params={"province_code": province_code})
        except Exception as e:
            st.error(f"Error loading district boundaries: {str(e)}")
            return gpd.GeoDataFrame()
    
    
    @st.cache_data(ttl=CACHE_CONFIG["spatial_data_ttl"])
    def get_municipality_boundaries(_self, district_code: str) -> gpd.GeoDataFrame:
        """Get municipality boundaries for selected district"""
        
        query = f'''
        SELECT 
            "CAT_B",
            "MUNICNAME_1",
            "DISTRICT",
            "DISTRICT_N",
            "Health_worker_density__index_",
            "Total_living_with_HIV",
            "TB_DS_treatment_success_rate",
            "Number_of_health_facilities",
            "Total_population",
            "geometry"
        FROM {_self.config.table_name}
        WHERE "DISTRICT" = %(district_code)s
          AND "geometry" IS NOT NULL
        ORDER BY "MUNICNAME_1"
        '''
        
        try:
            return gpd.read_postgis(query, _self.engine, geom_col='geometry', params={"district_code": district_code})
        except Exception as e:
            st.error(f"Error loading municipality boundaries: {str(e)}")
            return gpd.GeoDataFrame()