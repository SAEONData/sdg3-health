"""
Application settings and constants for SDG3 Health Dashboard
Centralizes all configuration in one place for easy maintenance
"""

# Main application configuration
APP_CONFIG = {
    "page_title": "SDG 3 Health Dashboard - South Africa",
    "page_icon": "🏥",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Visual design constants from technical specification
COLORS = {
    "primary": "#0066CC",             
    "good_performance": "#28A745",     # Green - Good performance
    "moderate_performance": "#FFC107",  # Yellow - Moderate performance  
    "needs_attention": "#DC3545",      # Red - Needs attention
    "insufficient_data": "#6C757D",    # Gray - Insufficient/No data
    
    "geographic_performance": {
        "excellent": "#28A745",
        "good": "#20C997", 
        "moderate": "#FFC107",
        "poor": "#FD7E14",
        "critical": "#DC3545"
    }
}


PAGES_CONFIG = {
    "home": {
        "title": "🏠 Home - SDG 3 Overview",
        "description": "National SDG 3 progress dashboard",
        "icon": "🏠"
    },
    "communicable": {
        "title": "🦠 Communicable Diseases", 
        "description": "HIV/TB analysis and treatment outcomes",
        "icon": "🦠"
    },
    "non_communicable": {
        "title": "💔 Non-Communicable Diseases",
        "description": "Diabetes, cancer, cardiovascular diseases", 
        "icon": "💔"
    },
    "social_determinants": {
        "title": "🏛️ Social Determinants & Risk Factors",
        "description": "Social factors affecting health outcomes",
        "icon": "🏛️"
    },
    "health_system": {
        "title": "🏥 Health System Capacity",
        "description": "Healthcare workforce and infrastructure",
        "icon": "🏥"
    }
}


INDICATORS = {
    "geographic_performance": "🟢🟡🔴⚪", 
    "trend_indicators": "📈📊📉☁️",   
    "performance_icons": {
        "improving": "📈",
        "stable": "📊", 
        "declining": "📉",
        "unknown": "☁️"
    }
}


GEOGRAPHIC_LEVELS = {
    "national": {
        "display_name": "National",
        "description": "All"
    },
    "province": {
        "code_col": "PROVINCE", 
        "name_col": "Province_name",
        "display_name": "Province",
        "icon": "🏔️",
        "description": "Provincial level"
    },
    "district": {
        "code_col": "DISTRICT", 
        "name_col": "DISTRICT_N",
        "display_name": "District", 
        "icon": "🏛️",
        "description": "District level"
    },
    "municipality": {
        "code_col": "CAT_B", 
        "name_col": "MUNICNAME_1",
        "display_name": "Municipality",
        "icon": "🏘️", 
        "description": "Municipality level"
    }
}


PAGES_CONFIG = {
    "home": {
        "title": "🏠 Home - SDG Overview",
        "description": "National SDG 3 dashboard",
        "icon": "🏠"
    },
    "communicable": {
        "title": "🦠 Communicable Diseases", 
        "description": "HIV/TB analysis and treatment outcomes",
        "icon": "🦠"
    },
    "non_communicable": {
        "title": "💔 Non-Communicable Diseases",
        "description": "Diabetes, cancer, cardiovascular diseases", 
        "icon": "💔"
    },
    "social_determinants": {
        "title": "🏛️ Social Determinants & Risk Factors",
        "description": "Social factors affecting health outcomes",
        "icon": "🏛️"
    },
    "health_system": {
        "title": "🏥 Health System Capacity",
        "description": "Healthcare workforce and infrastructure",
        "icon": "🏥"
    }
}

# Caching configuration
CACHE_CONFIG = {
    "geographic_data_ttl": 3600 * 24,  
    "health_indicators_ttl": 3600 * 24, 
    "spatial_data_ttl": 3600 * 6,     
    "summary_stats_ttl": 3600,         
}


HEALTH_THRESHOLDS = {
    "health_worker_density": {
        "excellent": 25.0,    
        "good": 15.0,
        "moderate": 10.0,
        "poor": 5.0
    },
    "tb_treatment_success": {
        "excellent": 85.0,    # percentage
        "good": 75.0, 
        "moderate": 65.0,
        "poor": 50.0
    },
    "hiv_viral_suppression": {
        "excellent": 90.0,    # percentage
        "good": 80.0,
        "moderate": 70.0, 
        "poor": 60.0
    },
    "immunization_coverage": {
        "excellent": 95.0,    # percentage
        "good": 85.0,
        "moderate": 75.0,
        "poor": 65.0
    }
}



MAP_CONFIG = {
    "default_zoom": 6,
    "min_zoom": 5,
    "max_zoom": 12,
    "center_lat": -28.5, 
    "center_lon": 24.5,
    "neighboring_radius_km": 50,
    "map_height": 500,   
    "map_width": 700,  
}



LAYOUT_CONFIG = {
    "sidebar_width": 300,
    "main_content_columns": [2, 1],      # Map column vs Summary column ratio
    "summary_panel_height": 500,
    "chart_height": 400,
    "metrics_columns": 2,                # Number of columns for metrics display
}


# SDG 3 specific indicators and targets
SDG3_TARGETS = {
    "maternal_mortality": {
        "target_value": 70,  # per 100,000 live births by 2030
        "current_value": None,  
        "unit": "per 100,000 live births"
    },
    "under5_mortality": {
        "target_value": 25,  # per 1,000 live births by 2030
        "current_value": None,
        "unit": "per 1,000 live births"
    },
    "health_worker_density": {
        "target_value": 44.5,  # per 10,000 population by 2030
        "current_value": None,
        "unit": "per 10,000 population"
    }
}

MAP_LAYERS = {
    "Health_worker_density__index_": {
        "display_name": "🏥 Health Worker Density",
        "description": "Health workers per 10,000 population",
        "color_scheme": "YlOrRd",
        "unit": "per 10,000"
    },
    "Total_living_with_HIV": {
        "display_name": "🦠 HIV Cases",
        "description": "Total people living with HIV",
        "color_scheme": "Reds",
        "unit": "cases"
    },
    "TB_DS_treatment_success_rate": {
        "display_name": "🫁 TB Treatment Success",
        "description": "DS-TB treatment success rate",
        "color_scheme": "Greens",
        "unit": "%"
    },
    "Number_of_health_facilities": {
        "display_name": "🏗️ Health Facilities",
        "description": "Number of health facilities",
        "color_scheme": "Blues",
        "unit": "facilities"
    },
    "Total_population": {
        "display_name": "👥 Population Density",
        "description": "Total population",
        "color_scheme": "Purples",
        "unit": "people"
    }
}

