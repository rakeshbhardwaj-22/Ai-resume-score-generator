import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Tuple

def create_gauge_chart(score: float, title: str = "ATS Match Score") -> go.Figure:
    """
    Create a beautiful interactive gauge chart for the ATS score.
    """
    # Define color based on score range
    if score >= 80:
        bar_color = "#00CC96"  # Premium Emerald
    elif score >= 60:
        bar_color = "#636EFA"  # Premium Royal Blue
    elif score >= 40:
        bar_color = "#FECB52"  # Amber Yellow
    else:
        bar_color = "#EF553B"  # Soft Crimson

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title, 'font': {'size': 20, 'color': '#7F8C8D'}, 'align': 'center'},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#BDC3C7"},
            'bar': {'color': bar_color, 'thickness': 0.8},
            'bgcolor': "#F4F6F7",
            'borderwidth': 1,
            'bordercolor': "#BDC3C7",
            'steps': [
                {'range': [0, 40], 'color': '#FCE4D6'},
                {'range': [40, 60], 'color': '#FFF2CC'},
                {'range': [60, 80], 'color': '#E2EFDA'},
                {'range': [80, 100], 'color': '#C6E0B4'}
            ]
        }
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=50, b=30),
        height=300
    )
    return fig

def create_radar_chart(breakdown: Dict[str, float]) -> go.Figure:
    """
    Create a radar chart showing the performance breakdown across ATS dimensions.
    """
    categories = [
        'Semantic Similarity', 
        'Skills Alignment', 
        'Experience Suitability', 
        'Education Suitability'
    ]
    
    # Map from database fields to user-friendly titles
    mapping = {
        'semantic_similarity': 'Semantic Similarity',
        'skills_alignment': 'Skills Alignment',
        'experience_suitability': 'Experience Suitability',
        'education_suitability': 'Education Suitability'
    }

    values = [breakdown.get(k, 0.0) for k in mapping.keys()]
    
    # Radar chart requires closing the loop by repeating the first element
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(99, 110, 250, 0.3)',
        line=dict(color='#636EFA', width=2),
        name='Candidate Profile'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
                gridcolor="#E5E7E9"
            ),
            angularaxis=dict(
                gridcolor="#E5E7E9"
            )
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=50, t=40, b=40),
        height=320
    )
    return fig

def create_skill_donut_chart(found_count: int, missing_count: int) -> go.Figure:
    """
    Create a donut chart representing matched vs missing skills.
    """
    labels = ['Matched Skills', 'Missing Skills']
    values = [found_count, missing_count]
    colors = ['#2ECC71', '#E74C3C']  # Green, Red

    # Handle case where both counts are zero to prevent division by zero error in UI
    if found_count == 0 and missing_count == 0:
        values = [1, 0]
        labels = ['No Skills Defined', '']
        colors = ['#BDC3C7', 'rgba(0,0,0,0)']

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5,
        marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2))
    )])
    
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=30, b=50),
        height=280
    )
    return fig

def create_leaderboard_chart(leaderboard_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a horizontal bar chart comparing candidate match percentages.
    """
    if not leaderboard_data:
        # Return blank figure with notice
        fig = go.Figure()
        fig.update_layout(
            title="No Candidates Found",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    # Convert to DataFrame
    df = pd.DataFrame(leaderboard_data)
    
    # Sort descending for the leaderboard display
    # Keep only the top 10 candidates
    df = df.sort_values(by="match_percentage", ascending=True).tail(10)

    fig = go.Figure(go.Bar(
        x=df["match_percentage"],
        y=df["candidate_name"],
        orientation='h',
        marker=dict(
            color=df["match_percentage"],
            colorscale='Blues',
            line=dict(color='rgba(50, 171, 96, 1.0)', width=1)
        ),
        text=df["match_percentage"].apply(lambda x: f"{x:.1f}%"),
        textposition='inside',
        insidetextanchor='end'
    ))

    fig.update_layout(
        title={
            'text': "Top Candidates (Match %)",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 16}
        },
        xaxis=dict(
            title="Match Percentage (%)", 
            range=[0, 105],
            gridcolor="#E5E7E9"
        ),
        yaxis=dict(title="Candidate Name"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=100, r=20, t=50, b=40),
        height=min(400, len(leaderboard_data) * 45 + 100)
    )
    return fig

def create_keyword_bar_chart(keyword_weights: List[Tuple[str, float]]) -> go.Figure:
    """
    Create a horizontal bar chart displaying job description keywords and their TF-IDF relevance weights.
    """
    if not keyword_weights:
        fig = go.Figure()
        return fig

    # Reverse order so highest weight is at the top of the chart
    keyword_weights = keyword_weights[::-1]
    
    keywords, weights = zip(*keyword_weights)

    fig = go.Figure(go.Bar(
        x=weights,
        y=keywords,
        orientation='h',
        marker=dict(
            color='#8E44AD',  # Professional Purple
            line=dict(color='rgba(142, 68, 173, 1.0)', width=1)
        )
    ))

    fig.update_layout(
        title={
            'text': "Top Job Description Keywords Importance",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 16}
        },
        xaxis=dict(title="Importance Weight", gridcolor="#E5E7E9"),
        yaxis=dict(title="Keyword"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=100, r=20, t=50, b=40),
        height=320
    )
    return fig
