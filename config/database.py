import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Database connection configuration for local PostgreSQL"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB')
        self.username = os.getenv('POSTGRES_USER')
        self.password = os.getenv('POSTGRES_PASSWORD')
        self.schema = os.getenv('POSTGRES_SCHEMA')
        self.table = os.getenv('POSTGRES_TABLE')
        
        self._validate_config()
    
    def _validate_config(self):
        """Validate that required environment variables are set"""
        required_vars = ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            st.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            st.error("Please check your .env file contains: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
            st.stop()
    
    @st.cache_resource
    def get_engine(_self):
        """Get SQLAlchemy engine with connection pooling"""
        try:
            connection_string = (
                f"postgresql+psycopg2://{_self.username}:{_self.password}@"
                f"{_self.host}:{_self.port}/{_self.database}"
            )
   
            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                echo=False, 
                pool_pre_ping=True
            )
            
            return engine
            
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
            st.error("Error: Please check your .env file and ensure PostgreSQL is running")
            st.stop()
    
    @property
    def table_name(self):
        """Get fully qualified table name"""
        return f'"{self.schema}"."{self.table}"'
    
    def test_connection(self):
        """Test database connection and table access"""
        try:
            engine = self.get_engine()
            
            test_query = f"""
            SELECT COUNT(*) as row_count 
            FROM {self.table_name} 
            LIMIT 1
            """
            
            import pandas as pd
            result = pd.read_sql(test_query, engine)
            
            st.info(f"📊 Estimated rows in table: {result['row_count'].iloc[0]:,}")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Table access failed: {str(e)}")
            st.error(f"Please ensure table {self.table_name} exists and is accessible")
            return False