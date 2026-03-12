import plotly.graph_objects as go

def create_radar_chart(scores):
    """Creates a radar chart from audit scores."""
    categories = list(scores.keys())
    values = list(scores.values())
    values.append(values[0])
    categories.append(categories[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(99, 110, 250, 0.15)',
        line=dict(color='#636EFA', width=2),
        marker=dict(size=8, color='#636EFA'),
        name='Your Stack'
    ))

    # Benchmark overlay
    benchmark_values = [7] * len(categories)
    fig.add_trace(go.Scatterpolar(
        r=benchmark_values,
        theta=categories,
        fill='none',
        line=dict(color='#00CC96', width=2, dash='dash'),
        marker=dict(size=0),
        name='Industry Benchmark (7/10)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10, color="#888"),
                gridcolor="#E0E0E0"
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#333")
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        margin=dict(l=80, r=80, t=40, b=80),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig

def create_score_gauge(score, title):
    """Creates a single gauge chart for a score."""
    if score >= 7:
        color = "#00CC96"
        bar_color = "rgba(0,204,150,0.3)"
    elif score >= 5:
        color = "#FFA15A"
        bar_color = "rgba(255,161,90,0.3)"
    else:
        color = "#EF553B"
        bar_color = "rgba(239,85,59,0.3)"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="/10", font=dict(size=28, color="#333")),
        gauge=dict(
            axis=dict(range=[0, 10], tickwidth=1, tickcolor="#ccc", dtick=2),
            bar=dict(color=color, thickness=0.7),
            bgcolor=bar_color,
            borderwidth=0,
            steps=[
                dict(range=[0, 4], color="rgba(239,85,59,0.08)"),
                dict(range=[4, 7], color="rgba(255,161,90,0.08)"),
                dict(range=[7, 10], color="rgba(0,204,150,0.08)")
            ],
        ),
        title=dict(text=title, font=dict(size=14, color="#555"))
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=30, r=30, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig

def create_bar_comparison(data_points, benchmarks):
    """Creates a horizontal bar chart comparing metrics to benchmarks."""
    labels = list(data_points.keys())
    values = list(data_points.values())
    bench = [benchmarks.get(k, {}).get("average", 0) for k in labels]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation='h',
        name='Your Data',
        marker_color='#636EFA',
        text=[f"{v}" for v in values],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        y=labels,
        x=bench,
        orientation='h',
        name='Benchmark',
        marker_color='rgba(0,204,150,0.5)',
        text=[f"{b}" for b in bench],
        textposition='outside'
    ))

    fig.update_layout(
        barmode='group',
        height=300,
        margin=dict(l=10, r=40, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#F0F0F0"),
        yaxis=dict(autorange="reversed")
    )

    return fig
