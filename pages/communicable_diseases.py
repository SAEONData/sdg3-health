import streamlit as st
import pandas as pd
from components.geographic_filter import GeographicFilter
from data.queries import GeographicQueries
from config.settings import PAGES_CONFIG, COLORS


def render():
    """Render the complete Communicable Diseases page - Phase 1: HIV Analysis"""
    
    st.title("HIV/AIDS & Tuberculosis Analysis")
    
    geo_filter = GeographicFilter()
    selection = geo_filter.render_sidebar_filter()
    
    st.subheader("HIV Analysis")
    render_hiv_panel(selection)
    
    st.markdown("---")
    
    st.subheader(" TB Analysis")
    render_tb_panel(selection)
    
    st.markdown("---")
    
    st.subheader("🔄 Co-infection Analysis")
    st.info("🚧 **Phase 3**: Co-infection Analysis coming soon...")
    with st.expander("📋 Planned Co-infection Features", expanded=False):
        st.markdown("**Will include:**")
        st.markdown("- HIV-TB Overlap Areas")
        st.markdown("- Joint Treatment Outcomes")
        st.markdown("- Risk Factor Correlation")
        st.markdown("- Geographic Hotspot Analysis")    


def render_hiv_panel(selection: dict):
    """Render HIV analysis panel with full width layout"""
    
    geo_queries = GeographicQueries()

    with st.spinner("Loading HIV indicators..."):
        hiv_data = geo_queries.get_hiv_indicators(selection)
    
    if hiv_data and hiv_data['local_data'] and any(v is not None for v in hiv_data['local_data'].values()):
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("👥 Population Context")
        
            total_hiv_cases = hiv_data['local_data']['total_hiv_cases']
            if pd.notna(total_hiv_cases) and total_hiv_cases > 0:
                if total_hiv_cases >= 1_000_000:
                    display_hiv = f"{total_hiv_cases/1_000_000:.1f}M"
                elif total_hiv_cases >= 1_000:
                    display_hiv = f"{total_hiv_cases/1_000:.1f}K"
                else:
                    display_hiv = f"{int(total_hiv_cases):,}"
                
                national_total_hiv = hiv_data['national_averages'].get('total_hiv_cases')
                if national_total_hiv and national_total_hiv > 0:
                    proportion = (total_hiv_cases / national_total_hiv) * 100
                    help_text = f"Local: {display_hiv} | {proportion:.1f}% of national total ({national_total_hiv/1_000_000:.1f}M)"
                else:
                    help_text = f"Total HIV cases in selected area: {display_hiv}"
                
                st.metric(
                    label="Total HIV Cases recorded",
                    value=display_hiv,
                    help=help_text
                )
        
        with col2:
            hiv_prevalence = hiv_data['local_data']['hiv_prevalence']

            if pd.notna(hiv_prevalence):
                performance = hiv_data['performance_indicators']['hiv_prevalence']
                national_hiv_prev = hiv_data['national_averages'].get('hiv_prevalence')
                
                st.metric(
                    label=f"{performance['emoji']} HIV Prevalence",
                    value=f"{hiv_prevalence:.1f} per 100K",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {hiv_prevalence:.1f} | National avg: {national_hiv_prev:.1f} | Per 100,000 population"
                )
            else:
                st.metric(
                    label="🦠 HIV Prevalence",
                    value="No data",
                    help="HIV prevalence data not available for this area"
                )
            
            viral_suppression = hiv_data['local_data']['viral_suppression']
            
            if pd.notna(viral_suppression):
                performance = hiv_data['performance_indicators']['viral_suppression']
                national_viral = hiv_data['national_averages'].get('viral_suppression')
                
                st.metric(
                    label=f"{performance['emoji']} Viral Suppression",
                    value=f"{viral_suppression:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {viral_suppression:.1f}% | National avg: {national_viral:.1f}% | HIV viral load suppression"
                )
            else:
                st.metric(
                    label="Viral Suppression", 
                    value="No data",
                    help="Viral suppression data not available for this area"
                )

        with col3:
            art_coverage = hiv_data['local_data']['art_coverage']
            if pd.notna(art_coverage):
                performance = hiv_data['performance_indicators']['art_coverage']
                national_art = hiv_data['national_averages'].get('art_coverage')
                
                st.metric(
                    label=f"{performance['emoji']} ART Coverage",
                    value=f"{art_coverage:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {art_coverage:.1f}% | National avg: {national_art:.1f}% | Antiretroviral treatment coverage"
                )
            else:
                st.metric(
                    label="💊 ART Coverage",
                    value="No data", 
                    help="ART coverage data not available for this area"
                )
            
            testing_coverage = hiv_data['local_data']['testing_coverage']

            if pd.notna(testing_coverage):
                performance = hiv_data['performance_indicators']['testing_coverage']
                national_testing = hiv_data['national_averages'].get('testing_coverage')
                
                st.metric(
                    label=f"{performance['emoji']} Testing Coverage",
                    value=f"{testing_coverage:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {testing_coverage:.1f}% | National avg: {national_testing:.1f}% | HIV testing coverage (15+ years)"
                )
            else:
                st.metric(
                    label="🧪 Testing Coverage",
                    value="No data",
                    help="Testing coverage data not available for this area"
                )
        
        st.markdown("#### HIV Performance vs National Average")
        
        with st.expander("📊 View National HIV Averages", expanded=False):
            st.markdown("**National HIV Averages for Comparison:**")
            
            ref_col1, ref_col2 = st.columns(2)
            
            with ref_col1:
                nat_prev = hiv_data['national_averages'].get('hiv_prevalence')
                if nat_prev:
                    st.markdown(f"🦠 **HIV Prevalence**: {nat_prev:.1f} per 100K")
                nat_viral = hiv_data['national_averages'].get('viral_suppression')
                if nat_viral:
                    st.markdown(f"🎯 **Viral Suppression**: {nat_viral:.1f}%")
            
            with ref_col2:
                nat_art = hiv_data['national_averages'].get('art_coverage')
                if nat_art:
                    st.markdown(f"💊 **ART Coverage**: {nat_art:.1f}%")
                nat_testing = hiv_data['national_averages'].get('testing_coverage')
                if nat_testing:
                    st.markdown(f"🧪 **Testing Coverage**: {nat_testing:.1f}%")
        
        performance_indicators = []
        
        hiv_indicators = [
            ('HIV Prevalence', 'hiv_prevalence'),
            ('ART Coverage', 'art_coverage'),
            ('Viral Suppression', 'viral_suppression'),
            ('Testing Coverage', 'testing_coverage')
        ]
        
        for name, key in hiv_indicators:
            local_val = hiv_data['local_data'].get(key)
            national_val = hiv_data['national_averages'].get(key)
            perf = hiv_data['performance_indicators'].get(key)
            
            if pd.notna(local_val) and perf:
                performance_indicators.append({
                    "name": name,
                    "performance": perf,
                    "local": local_val,
                    "national": national_val
                })
        
        for indicator in performance_indicators:
            perf = indicator["performance"]
            local_val = indicator["local"]
            national_val = indicator["national"]
            
            if national_val:
                if 'prevalence' in indicator["name"].lower():
                    st.markdown(f"{perf['emoji']} **{indicator['name']}**: {local_val:.1f} per 100K vs {national_val:.1f} (national) — {perf['interpretation']}")
                else:
                    st.markdown(f"{perf['emoji']} **{indicator['name']}**: {local_val:.1f}% vs {national_val:.1f}% (national) — {perf['interpretation']}")
            else:
                st.markdown(f"{perf['emoji']} **{indicator['name']}**: {perf['interpretation']}")
        
        if not performance_indicators:
            st.markdown("*Performance indicators will appear when data is available*")
        
        
    else:
        st.warning("No HIV data available for current selection")
        st.markdown("*Try selecting a different geographic area*")
        
        st.markdown("**HIV indicators we track:**")
        st.markdown("- 🦠 HIV Prevalence (per 100,000 population)")
        st.markdown("- 💊 ART Coverage (%)")
        st.markdown("- 🎯 Viral Suppression (%)")
        st.markdown("- 🧪 Testing Coverage (%)")


def render_tb_panel(selection: dict):
    """Render TB analysis panel with 5 metrics in single row"""
    
    geo_queries = GeographicQueries()
    
    with st.spinner("Loading TB indicators..."):
        tb_data = geo_queries.get_tb_indicators(selection)
    
    if tb_data and tb_data['local_data'] and any(v is not None for v in tb_data['local_data'].values()):
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_tb_cases = tb_data['local_data']['total_tb_cases']
            if pd.notna(total_tb_cases) and total_tb_cases > 0:
                if total_tb_cases >= 1_000_000:
                    display_tb = f"{total_tb_cases/1_000_000:.1f}M"
                elif total_tb_cases >= 1_000:
                    display_tb = f"{total_tb_cases/1_000:.1f}K"
                else:
                    display_tb = f"{int(total_tb_cases):,}"
                
                national_total_tb = tb_data['national_averages'].get('total_tb_cases')
                if national_total_tb and national_total_tb > 0:
                    proportion = (total_tb_cases / national_total_tb) * 100
                    help_text = f"Local: {display_tb} | {proportion:.1f}% of national total ({national_total_tb/1_000:.1f}K)"
                else:
                    help_text = f"Total TB cases in selected area: {display_tb}"
                
                st.metric(
                    label="Total TB Cases",
                    value=display_tb,
                    help=help_text
                )
            else:
                st.metric(
                    label="Total TB Cases",
                    value="No data",
                    help="TB case data not available for this area"
                )
        
        with col2:
            ds_tb_success = tb_data['local_data']['ds_tb_success']
            if pd.notna(ds_tb_success):
                performance = tb_data['performance_indicators']['ds_tb_success']
                national_ds_tb = tb_data['national_averages'].get('ds_tb_success')
                
                st.metric(
                    label=f"{performance['emoji']} DS-TB Success",
                    value=f"{ds_tb_success:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {ds_tb_success:.1f}% | National avg: {national_ds_tb:.1f}% | Drug-sensitive TB treatment success"
                )
            else:
                st.metric(
                    label="DS-TB Success",
                    value="No data",
                    help="DS-TB treatment success data not available"
                )
            
        with col3:
            mdr_tb_success = tb_data['local_data']['mdr_tb_success']
            if pd.notna(mdr_tb_success):
                performance = tb_data['performance_indicators']['mdr_tb_success']
                national_mdr_tb = tb_data['national_averages'].get('mdr_tb_success')
                
                st.metric(
                    label=f"{performance['emoji']} MDR-TB Success",
                    value=f"{mdr_tb_success:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {mdr_tb_success:.1f}% | National avg: {national_mdr_tb:.1f}% | Multi-drug resistant TB treatment success"
                )
            else:
                st.metric(
                    label="MDR-TB Success",
                    value="No data", 
                    help="MDR-TB treatment success data not available"
                )

        with col4:
            drug_resistance = tb_data['local_data']['drug_resistance']
            if pd.notna(drug_resistance):
                performance = tb_data['performance_indicators']['drug_resistance']
                national_resistance = tb_data['national_averages'].get('drug_resistance')
                
                st.metric(
                    label=f"{performance['emoji']} Drug Resistance",
                    value=f"{drug_resistance:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {drug_resistance:.1f}% | National avg: {national_resistance:.1f}% | Rifampicin resistance rate"
                )
            else:
                st.metric(
                    label="💊 Drug Resistance", 
                    value="No data",
                    help="Drug resistance data not available"
                )
            
        with col5:
            treatment_completion = tb_data['local_data']['treatment_completion']
            if pd.notna(treatment_completion):
                performance = tb_data['performance_indicators']['treatment_completion']
                national_completion = tb_data['national_averages'].get('treatment_completion')
                
                st.metric(
                    label=f"{performance['emoji']} Treatment Completion",
                    value=f"{treatment_completion:.1f}%",
                    delta=f"{performance['percentage_diff']:+.1f}% vs national" if performance['percentage_diff'] else None,
                    help=f"Local: {treatment_completion:.1f}% | National avg: {national_completion:.1f}% | TB treatment completion rate"
                )
            else:
                st.metric(
                    label="Treatment Completion",
                    value="No data",
                    help="Treatment completion data not available"
                )
        
        st.markdown("#### TB Performance vs National Average")
        
        with st.expander("View National TB Averages", expanded=False):
            st.markdown("**National TB Averages for Comparison:**")
            
            ref_col1, ref_col2 = st.columns(2)
            
            with ref_col1:
                nat_ds_tb = tb_data['national_averages'].get('ds_tb_success')
                if nat_ds_tb:
                    st.markdown(f" **DS-TB Success**: {nat_ds_tb:.1f}%")
                nat_resistance = tb_data['national_averages'].get('drug_resistance')
                if nat_resistance:
                    st.markdown(f" **Drug Resistance**: {nat_resistance:.1f}%")
            
            with ref_col2:
                nat_mdr_tb = tb_data['national_averages'].get('mdr_tb_success')
                if nat_mdr_tb:
                    st.markdown(f" **MDR-TB Success**: {nat_mdr_tb:.1f}%")
                nat_completion = tb_data['national_averages'].get('treatment_completion')
                if nat_completion:
                    st.markdown(f" **Treatment Completion**: {nat_completion:.1f}%")
        
        performance_indicators = []
        
        tb_indicators = [
            ('DS-TB Success Rate', 'ds_tb_success'),
            ('MDR-TB Success Rate', 'mdr_tb_success'),
            ('Drug Resistance Rate', 'drug_resistance'),
            ('Treatment Completion', 'treatment_completion')
        ]
        
        for name, key in tb_indicators:
            local_val = tb_data['local_data'].get(key)
            national_val = tb_data['national_averages'].get(key)
            perf = tb_data['performance_indicators'].get(key)
            
            if pd.notna(local_val) and perf:
                performance_indicators.append({
                    "name": name,
                    "performance": perf,
                    "local": local_val,
                    "national": national_val
                })
        
        for indicator in performance_indicators:
            perf = indicator["performance"]
            local_val = indicator["local"]
            national_val = indicator["national"]
            
            if national_val:
                st.markdown(f"{perf['emoji']} **{indicator['name']}**: {local_val:.1f}% vs {national_val:.1f}% (national) — {perf['interpretation']}")
            else:
                st.markdown(f"{perf['emoji']} **{indicator['name']}**: {perf['interpretation']}")
        
        if not performance_indicators:
            st.markdown("*Performance indicators will appear when data is available*")
        
    else:
        st.warning("No TB data available for current selection")
        st.markdown("*Try selecting a different geographic area*")
        
        st.markdown("**TB indicators we track:**")
        st.markdown("-  Total TB Cases")
        st.markdown("-  DS-TB Treatment Success Rate (%)")
        st.markdown("-  MDR-TB Treatment Success Rate (%)")
        st.markdown("-  Drug Resistance Rate (%)")
        st.markdown("- Treatment Completion Rate (%)")