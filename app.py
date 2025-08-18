import streamlit as st
from pages import home, communicable_diseases
from config.settings import APP_CONFIG
from config.database import DatabaseConfig

st.set_page_config(
    page_title=APP_CONFIG["page_title"],
    page_icon=APP_CONFIG["page_icon"], 
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["initial_sidebar_state"]
)

def initialize_database():
    """Initialize and test database connection"""
    if 'db_initialized' not in st.session_state:
        with st.spinner("🔄 Loading..."):
            config = DatabaseConfig()
            
            if config.test_connection():
                st.session_state.db_initialized = True
                st.session_state.db_config = config
            else:
                st.stop()

def main():
    """Main application entry point with page navigation"""  
    
    initialize_database()
    
    st.sidebar.markdown("## South African Health Dashboard")
    
    page = st.sidebar.selectbox(
        "Select Page:",
        options=["Home - Health Overview", "Communicable Diseases"],
        help="Navigate between different health analysis areas"
    )

    if page == "Home - Health Overview":
        home.render()
    elif page == "Communicable Diseases":
        communicable_diseases.render()

if __name__ == "__main__":
    main()