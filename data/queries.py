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

            
    def get_national_averages(_self) -> dict:
        """Get national averages for all key health indicators"""
        try:
            query = f'''
            SELECT 

                -- Population and Facilities
                SUM("Total_population") as national_total_population,
                SUM("Number_of_health_facilities") as national_total_facilities,
                SUM("Total_living_with_HIV") as national_total_hiv_cases,
                ROUND((SUM("Total_living_with_HIV")::DECIMAL / SUM("Total_population")) * 100000, 1) as national_hiv_prevalence,

                -- Health System Indicators
                AVG("Health_worker_density__index_") as national_health_worker_density,
                AVG("Medical_practitioners_per_100_0") as national_doctors_per_100k,
                AVG("Professional_nurses_per_100_000") as national_nurses_per_100k,
                AVG("Pharmacists_per_100_000_populat") as national_pharmacists_per_100k,
            
                -- Communicable Diseases
                AVG("TB_DS_treatment_success_rate") as national_tb_success_rate,
                AVG("TB_MDR_treatment_success_rate") as national_tb_mdr_success_rate,

                AVG("TB_DS_treatment_success_rate")  as national_tb_ds_success_rate,

                CASE 
                    WHEN SUM("Total_living_with_HIV") > 0 THEN 
                        ROUND((SUM("Adult_living_with_HIV_viral_loa")::DECIMAL / SUM("Total_living_with_HIV")) * 100, 1)
                    ELSE NULL 
                END as national_hiv_viral_suppression,
                
                CASE 
                    WHEN SUM("Total_population") > 0 THEN 
                        ROUND((SUM("HIV_test_15_years_and_older__ex")::DECIMAL / SUM("Total_population")) * 100, 1)
                    ELSE NULL 
                END as national_hiv_testing_coverage,

                -- TB Drug Resistance Rate
                CASE 
                    WHEN (SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort")) > 0 THEN 
                        SUM("TB_Rifampicin_resistance_confir")::DECIMAL / 
                            (SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort")) * 100
                    ELSE NULL 
                END as national_tb_drug_resistance_rate,


                CASE 
                    WHEN (SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort")) > 0 THEN 
                        ROUND(
                            ((SUM("All_DS_TB_patients_in_cohort")::DECIMAL + SUM("All_MDR_TB_patients_in_cohort")::DECIMAL - 
                            SUM("TB_DS_client_lost_to_follow_up_")::DECIMAL - SUM("TB_MDR_client_loss_to_follow_up")::DECIMAL) / 
                            (SUM("All_DS_TB_patients_in_cohort")::DECIMAL + SUM("All_MDR_TB_patients_in_cohort")::DECIMAL)) * 100.0, 
                            1
                        )
                    ELSE NULL 
                END as national_tb_treatment_completion_rate,

                -- TB Total Cases
                SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort") as national_total_tb_cases,

                ROUND(AVG("Antiretroviral_effective_covera")::DECIMAL, 1) as national_art_coverage,

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
                st.warning("Could not calculate national averages")
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
            "viral_suppression": "hiv_viral_suppression",           
            "art_coverage": "art_coverage",                         
            "hiv_prevalence": "hiv_prevalence",                    
            "testing_coverage": "hiv_testing_coverage", 
            "ds_tb_success": "tb_treatment_success",
            "mdr_tb_success": "tb_treatment_success",           
            "drug_resistance": "tb_drug_resistance",           
            "treatment_completion": "tb_treatment_completion", 
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
            
            
            direction = thresholds.get("direction", "higher_better")
            
            if direction == "lower_better":
                if local_val <= thresholds["excellent"]:
                    status, emoji = "excellent", "🟢"
                elif local_val <= thresholds["good"]:
                    status, emoji = "good", "🟢"
                elif local_val <= thresholds["moderate"]:
                    status, emoji = "moderate", "🟡"
                elif local_val <= thresholds["poor"]:
                    status, emoji = "poor", "🟠"  
                else:
                    status, emoji = "critical", "🔴"
            else:
                if local_val >= thresholds["excellent"]:
                    status, emoji = "excellent", "🟢"
                elif local_val >= thresholds["good"]:
                    status, emoji = "good", "🟢"
                elif local_val >= thresholds["moderate"]:
                    status, emoji = "moderate", "🟡"
                elif local_val >= thresholds["poor"]:
                    status, emoji = "poor", "🟠" 
                else:
                    status, emoji = "critical", "🔴" 

            interpretation = f"{local_val:.1f} ({status.replace('_', ' ')}) | {abs(percentage_diff):.1f}% {'above' if percentage_diff > 0 else 'below'} national avg"

        else:
            if percentage_diff >= 15:
                status, emoji = "excellent", "🟢"
            elif percentage_diff >= 5:
                status, emoji = "good", "🟢"
            elif percentage_diff >= -5:
                status, emoji = "moderate", "🟡"
            elif percentage_diff >= -15:
                status, emoji = "poor", "🟠"
            else:
                status, emoji = "critical", "🔴"

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
    


    def get_hiv_indicators(_self, geographic_selection: dict) -> dict:
        """
        Get HIV indicators for selected geography with national comparisons
        Args:
            geographic_selection: Geographic selection dict from GeographicFilter
        
        Returns:
            dict: Complete HIV indicators with performance analysis
        """
        try:
            where_conditions = []
            params = {}
            
            if geographic_selection.get("province_code"):
                where_conditions.append('"PROVINCE" = %(province_code)s')
                params["province_code"] = geographic_selection["province_code"]
            
            if geographic_selection.get("district_code"):
                where_conditions.append('"DISTRICT" = %(district_code)s')
                params["district_code"] = geographic_selection["district_code"]
            
            if geographic_selection.get("municipality_code"):
                where_conditions.append('"CAT_B" = %(municipality_code)s')
                params["municipality_code"] = geographic_selection["municipality_code"]
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f'''
                SELECT 
                    SUM("Total_living_with_HIV") as total_hiv_cases,
                    SUM("Total_population") as total_population,
                    
                    CASE 
                        WHEN SUM("Total_living_with_HIV") > 0 THEN 
                            ROUND((SUM("Adult_living_with_HIV_viral_loa")::DECIMAL / SUM("Total_living_with_HIV")) * 100, 1)
                        ELSE NULL 
                    END as avg_viral_load_suppression,
                    
                    ROUND(AVG("Antiretroviral_effective_covera")::DECIMAL, 1) as avg_art_coverage,
                    
                    CASE 
                        WHEN SUM("Total_population") > 0 THEN 
                            ROUND((SUM("HIV_test_15_years_and_older__ex")::DECIMAL / SUM("Total_population")) * 100, 1)
                        ELSE NULL 
                    END as avg_testing_coverage,
                    
                    ROUND((SUM("Total_living_with_HIV")::DECIMAL / SUM("Total_population")) * 100000, 1) as hiv_prevalence_rate
                    
                FROM {_self.config.table_name}
                {where_clause}
                '''
            
            local_result = pd.read_sql(query, _self.engine, params=params)
            national_averages = _self.get_national_averages()

            if not local_result.empty and pd.notna(local_result.iloc[0]['total_population']) and local_result.iloc[0]['total_population'] > 0:
                row = local_result.iloc[0]
                
                local_indicators = {
                    'hiv_prevalence': row['hiv_prevalence_rate'] if pd.notna(row['hiv_prevalence_rate']) else None,
                    'art_coverage': row['avg_art_coverage'] if pd.notna(row['avg_art_coverage']) else None,
                    'viral_suppression': row['avg_viral_load_suppression'] if pd.notna(row['avg_viral_load_suppression']) else None,
                    'testing_coverage': row['avg_testing_coverage'] if pd.notna(row['avg_testing_coverage']) else None
                }
                population = row['total_population']
                total_hiv_cases = row['total_hiv_cases'] if pd.notna(row['total_hiv_cases']) else None
            else:
                local_indicators = {
                    'hiv_prevalence': None,
                    'art_coverage': None,
                    'viral_suppression': None,
                    'testing_coverage': None
                }
                population = None
                total_hiv_cases = None
            
            performance_indicators = {}
            
            national_key_mapping = {
                'art_coverage': 'national_art_coverage',
                'viral_suppression': 'national_hiv_viral_suppression',
                'hiv_prevalence': 'national_hiv_prevalence',
                'testing_coverage': 'national_hiv_testing_coverage'
            }
            
            for indicator, local_value in local_indicators.items():
                national_key = national_key_mapping.get(indicator)
                national_value = national_averages.get(national_key) if national_key and national_averages else None

                performance_indicators[indicator] = _self.calculate_performance_vs_national(
                    local_value, national_value, indicator
                )


            return {
                'local_data': {
                    'hiv_prevalence': local_indicators['hiv_prevalence'],
                    'art_coverage': local_indicators['art_coverage'],
                    'viral_suppression': local_indicators['viral_suppression'],
                    'testing_coverage': local_indicators['testing_coverage'],
                    'total_hiv_cases': total_hiv_cases,
                    'population': population
                },
                'national_averages': {
                    'hiv_prevalence': national_averages.get('national_hiv_prevalence') if national_averages else None,
                    'art_coverage': national_averages.get('national_art_coverage') if national_averages else None,
                    'viral_suppression': national_averages.get('national_hiv_viral_suppression') if national_averages else None,
                    'testing_coverage': national_averages.get('national_hiv_testing_coverage') if national_averages else None,
                    'total_hiv_cases': national_averages.get('national_total_hiv_cases') if national_averages else None
                },
                'performance_indicators': performance_indicators,
                'geography_info': {
                    'level': geographic_selection.get('level', 'national'),
                    'name': geographic_selection.get(f"{geographic_selection.get('level', 'national')}_name", "South Africa"),
                    'population': population
                }
            }
            
        except Exception as e:
            st.error(f"❌ Error calculating HIV indicators: {str(e)}")
            return {
                'local_data': {
                    'hiv_prevalence': None,
                    'art_coverage': None,
                    'viral_suppression': None,
                    'testing_coverage': None,
                    'total_hiv_cases': None,
                    'population': None
                },
                'national_averages': {},
                'performance_indicators': {},
                'geography_info': {
                    'level': geographic_selection.get('level', 'national'),
                    'name': geographic_selection.get(f"{geographic_selection.get('level', 'national')}_name", "South Africa"),
                    'population': None
                }
            }
        
    
    def get_tb_indicators(_self, geographic_selection: dict) -> dict:
        """
        Get TB indicators for selected geography with national comparisons
        Returns complete TB context including local data, national averages, and performance indicators
        
        Args:
            geographic_selection: Geographic selection dict from GeographicFilter
        
        Returns:
            dict: Complete TB indicators with performance analysis
        """
        try:
            where_conditions = []
            params = {}
            
            if geographic_selection.get("province_code"):
                where_conditions.append('"PROVINCE" = %(province_code)s')
                params["province_code"] = geographic_selection["province_code"]
            
            if geographic_selection.get("district_code"):
                where_conditions.append('"DISTRICT" = %(district_code)s')
                params["district_code"] = geographic_selection["district_code"]
            
            if geographic_selection.get("municipality_code"):
                where_conditions.append('"CAT_B" = %(municipality_code)s')
                params["municipality_code"] = geographic_selection["municipality_code"]
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f'''
            SELECT 
            ROUND(AVG("TB_DS_treatment_success_rate")::DECIMAL, 1) as ds_tb_success_rate,
            ROUND(AVG("TB_MDR_treatment_success_rate")::DECIMAL, 1) as mdr_tb_success_rate,
            ROUND(AVG("TB_XDR_treatment_success_rate")::DECIMAL, 1) as xdr_tb_success_rate,
            
            CASE 
                WHEN (SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort")) > 0 THEN 
                    ROUND((SUM("TB_Rifampicin_resistance_confir")::DECIMAL / 
                        (SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort"))::DECIMAL) * 100, 1)
                ELSE NULL 
            END as drug_resistance_rate,
            
            CASE 
                WHEN (SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort")) > 0 THEN 
                    ROUND(
                        ((SUM("All_DS_TB_patients_in_cohort")::DECIMAL + SUM("All_MDR_TB_patients_in_cohort")::DECIMAL - 
                        SUM("TB_DS_client_lost_to_follow_up_")::DECIMAL - SUM("TB_MDR_client_loss_to_follow_up")::DECIMAL) / 
                        (SUM("All_DS_TB_patients_in_cohort")::DECIMAL + SUM("All_MDR_TB_patients_in_cohort")::DECIMAL)) * 100.0, 
                        1
                    )
                ELSE NULL 
            END as treatment_completion_rate,
            
            SUM("All_DS_TB_patients_in_cohort") + SUM("All_MDR_TB_patients_in_cohort") as total_tb_cases,
            SUM("Total_population") as total_population
            
        FROM {_self.config.table_name}
        {where_clause}
            '''
            
            local_result = pd.read_sql(query, _self.engine, params=params)
            national_averages = _self.get_national_averages()
            
            if not local_result.empty and pd.notna(local_result.iloc[0]['total_population']) and local_result.iloc[0]['total_population'] > 0:
                row = local_result.iloc[0]
                
                local_indicators = {
                    'ds_tb_success': row['ds_tb_success_rate'] if pd.notna(row['ds_tb_success_rate']) else None,
                    'mdr_tb_success': row['mdr_tb_success_rate'] if pd.notna(row['mdr_tb_success_rate']) else None,
                    'drug_resistance': row['drug_resistance_rate'] if pd.notna(row['drug_resistance_rate']) else None,
                    'treatment_completion': row['treatment_completion_rate'] if pd.notna(row['treatment_completion_rate']) else None
                }
                population = row['total_population']
                total_tb_cases = row['total_tb_cases'] if pd.notna(row['total_tb_cases']) else None
            else:
                local_indicators = {
                    'ds_tb_success': None,
                    'mdr_tb_success': None,
                    'drug_resistance': None,
                    'treatment_completion': None
                }
                population = None
                total_tb_cases = None
            
            performance_indicators = {}
            
            national_key_mapping = {
                'ds_tb_success': 'national_tb_ds_success_rate',
                'mdr_tb_success': 'national_tb_mdr_success_rate',
                'drug_resistance': 'national_tb_drug_resistance_rate',
                'treatment_completion': 'national_tb_treatment_completion_rate'
            }
            
            for indicator, local_value in local_indicators.items():
                national_key = national_key_mapping.get(indicator)
                national_value = national_averages.get(national_key) if national_key and national_averages else None
                
                performance_indicators[indicator] = _self.calculate_performance_vs_national(
                    local_value, national_value, indicator
                )
            
            return {
                'local_data': {
                    'ds_tb_success': local_indicators['ds_tb_success'],
                    'mdr_tb_success': local_indicators['mdr_tb_success'],
                    'drug_resistance': local_indicators['drug_resistance'],
                    'treatment_completion': local_indicators['treatment_completion'],
                    'total_tb_cases': total_tb_cases,
                    'population': population
                },
                'national_averages': {
                    'ds_tb_success': national_averages.get('national_tb_ds_success_rate') if national_averages else None,
                    'mdr_tb_success': national_averages.get('national_tb_mdr_success_rate') if national_averages else None,
                    'drug_resistance': national_averages.get('national_tb_drug_resistance_rate') if national_averages else None,
                    'treatment_completion': national_averages.get('national_tb_treatment_completion_rate') if national_averages else None,
                    'total_tb_cases': national_averages.get('national_total_tb_cases') if national_averages else None
                },
                'performance_indicators': performance_indicators,
                'geography_info': {
                    'level': geographic_selection.get('level', 'national'),
                    'name': geographic_selection.get(f"{geographic_selection.get('level', 'national')}_name", "South Africa"),
                    'population': population
                }
            }
            
        except Exception as e:
            st.error(f"❌ Error loading TB indicators: {str(e)}")
            return {
                'local_data': {
                    'ds_tb_success': None,
                    'mdr_tb_success': None,
                    'drug_resistance': None,
                    'treatment_completion': None,
                    'total_tb_cases': None,
                    'population': None
                },
                'national_averages': {},
                'performance_indicators': {},
                'geography_info': {
                    'level': geographic_selection.get('level', 'national'),
                    'name': geographic_selection.get(f"{geographic_selection.get('level', 'national')}_name", "South Africa"),
                    'population': None
                }
            }