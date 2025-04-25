import streamlit as st
import plotly.graph_objects as go
from database import get_user_score

def show_performance_chart(email):
    """Show user performance using a donut chart"""
    score = get_user_score(email)
    
    # Create a donut chart showing score vs. remaining
    max_score = 5  # Based on 5 questions
    
    # Ensure score is within range
    score = min(max(score, 0), max_score)
    remaining = max_score - score
    
    # Round the score for display
    score_rounded = round(score, 1)
    
    # Create the donut chart
    fig = go.Figure(data=[go.Pie(
        labels=['Score', 'Remaining'],
        values=[score, remaining],
        hole=0.6,  # Makes it a donut chart
        marker_colors=['#4CAF50', '#EEEEEE']  # Green for score, light gray for remaining
    )])
    
    # Add annotation in the center
    fig.update_layout(
        annotations=[dict(
            text=f"{score_rounded}/{max_score}",
            x=0.5, y=0.5,
            font_size=24,
            showarrow=False
        )],
        title="Your Average Score",
        showlegend=True
    )
    
    st.plotly_chart(fig)