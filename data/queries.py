import streamlit as st
import pandas as pd
import geopandas as gpd
from config.database import DatabaseConfig
from config.settings import CACHE_CONFIG, COLORS, HEALTH_THRESHOLDS
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
        
    
    @st.cache_data(ttl=CACHE_CONFIG["health_indicators_ttl"])
    def get_national_averages(_self) -> dict:
        """Get national averages for all key health indicators"""
        try:
            query = f'''
            SELECT 
                -- Health System Indicators
                AVG("Health_worker_density__index_") as national_health_worker_density,
                AVG("Medical_practitioners_per_100_0") as national_doctors_per_100k,
                AVG("Professional_nurses_per_100_000") as national_nurses_per_100k,
                AVG("Pharmacists_per_100_000_populat") as national_pharmacists_per_100k,
            
                -- Communicable Diseases
                AVG("TB_DS_treatment_success_rate") as national_tb_success_rate,
                AVG("TB_MDR_treatment_success_rate") as national_tb_mdr_success_rate,
                AVG("Adult_living_with_HIV_viral_loa") as national_hiv_viral_suppression,
                AVG("Antiretroviral_effective_covera") as national_art_coverage,
            
                -- Non-Communicable Diseases  
                AVG("Diabetes_prevalence") as national_diabetes_prevalence,
                AVG("Diabetes_treatment_coverage") as national_diabetes_treatment,
                AVG("Cervical_cancer_screening_cov_1") as national_cervical_screening,
                AVG("Percentage_of_adults_overweight") as national_overweight_rate,
            
                -- Social Determinants
                AVG("Percentage_no_money_for_food") as national_food_insecurity,
                AVG("Unemployment_rate") as national_unemployment_rate,
                AVG("Percentage_limited_Hospital") as national_limited_hospital_access,
                AVG("Percentage_limited_clinic") as national_limited_clinic_access,
            
                -- Health System Infrastructure
                AVG("Hospital_beds_per_10_000_target") as national_beds_per_10k,
                AVG("Percentage_Ideal_clinics") as national_ideal_clinics,
                AVG("PHC_utilisation_rate") as national_phc_utilization,
            
                -- Population and Facilities
                SUM("Total_population") as national_total_population,
                SUM("Number_of_health_facilities") as national_total_facilities,
                SUM("Total_living_with_HIV") as national_total_hiv_cases,
            
                -- Additional Indicators
                AVG("Immunisation_under_1_year_cov_1") as national_immunization_coverage,
                AVG("Live_birth_in_facility_1") as national_facility_births,
                AVG("Tobacco_non_smoking_prevalence") as national_tobacco_non_smoking
            
            FROM {_self.config.table_name}
            WHERE "Total_population" IS NOT NULL 
            AND "Total_population" > 0
            '''
        
            result = pd.read_sql(query, _self.engine)
        
            if result.empty:
                st.warning("⚠️ Could not calculate national averages")
                return {}
        
            national_averages = result.iloc[0].to_dict()
        
            cleaned_averages = {}
            for key, value in national_averages.items():
                if pd.notna(value):
                    cleaned_averages[key] = float(value)
                else:
                    cleaned_averages[key] = None
        
            return cleaned_averages
        
        except Exception as e:
            st.error(f"❌ Error calculating national averages: {str(e)}")
            return {}
        

    
    def calculate_performance_vs_national(_self, local_value, national_avg, indicator_name: str) -> dict:
        """
        Calculate performance comparison using HEALTH_THRESHOLDS from settings
        
        Args:
            local_value: Local area indicator value
            national_avg: National average for the same indicator
            indicator_name: Name of the indicator to determine thresholds
        
        Returns:
            dict: Performance analysis with status based on actual thresholds
        """
        
        if pd.isna(local_value) or pd.isna(national_avg) or national_avg == 0:
            return {
                "status": "insufficient_data",
                "percentage_diff": None,
                "interpretation": "Insufficient data for comparison",
                "color": COLORS["insufficient_data"],
                "emoji": "⚪",
                "direction": "unknown"
            }
        
        percentage_diff = ((float(local_value) - float(national_avg)) / float(national_avg)) * 100
        
        threshold_mapping = {
            "health_worker_density": "health_worker_density",
            "tb_success_rate": "tb_treatment_success", 
            "tb_ds_treatment_success_rate": "tb_treatment_success",
            "hiv_viral_suppression": "hiv_viral_suppression",
            "adult_living_with_hiv_viral_loa": "hiv_viral_suppression",
            "immunization_coverage": "immunization_coverage",
            "immunisation_under_1_year_cov": "immunization_coverage"
        }
        
        threshold_key = None
        indicator_lower = indicator_name.lower()
        
        for key_pattern, threshold_name in threshold_mapping.items():
            if key_pattern in indicator_lower:
                threshold_key = threshold_name
                break
        
        if threshold_key and threshold_key in HEALTH_THRESHOLDS:
            thresholds = HEALTH_THRESHOLDS[threshold_key]
            local_val = float(local_value)
            
            if local_val >= thresholds["excellent"]:
                status = "excellent"
                emoji = "🟢"
            elif local_val >= thresholds["good"]:
                status = "good" 
                emoji = "🟢"
            elif local_val >= thresholds["moderate"]:
                status = "moderate"
                emoji = "🟡"
            elif local_val >= thresholds["poor"]:
                status = "needs_attention"
                emoji = "🟠"
            else:
                status = "poor"
                emoji = "🔴"
            
            interpretation = f"{local_val:.1f} ({status.replace('_', ' ')}) | {abs(percentage_diff):.1f}% {'above' if percentage_diff > 0 else 'below'} national avg"
            
        else:
            # Fallback to percentage-based comparison for indicators without specific thresholds
            if percentage_diff >= 15:
                status, emoji = "excellent", "🟢"
            elif percentage_diff >= 5:
                status, emoji = "good", "🟢"
            elif percentage_diff >= -5:
                status, emoji = "moderate", "🟡"
            elif percentage_diff >= -15:
                status, emoji = "needs_attention", "🟠"
            else:
                status, emoji = "poor", "🔴"
            
            interpretation = f"{abs(percentage_diff):.1f}% {'above' if percentage_diff > 0 else 'below'} national average"
        
        return {
            "status": status,
            "percentage_diff": round(percentage_diff, 1),
            "interpretation": interpretation,
            "color": COLORS["geographic_performance"][status],
            "emoji": emoji,
            "threshold_used": threshold_key is not None,
            "local_value": local_value,
            "national_value": national_avg
        }