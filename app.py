import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import pycountry

df = pd.read_csv("data/new_jobsfr_global.csv")
#color blind 
CATEGORICAL = px.colors.qualitative.Safe
SEQUENTIAL = px.colors.sequential.Viridis
BLUES = px.colors.sequential.Blues

def desc(text):
    return html.Div(
        text,
        style={
            "color": "#D0D0D0",
            "fontSize": "14px",
            "marginTop": "10px",
            "marginBottom": "40px",
            "paddingBottom": "10px"
        },
        **{"aria-label": text}
    )
#convert country to iso 3 code
def to_iso3(country):
    try:
        return pycountry.countries.lookup(country).alpha_3
    except:
        return None

def kpi(label, value):
    return html.Div(
        style={
            "background": "#161B22",
            "padding": "18px",
            "borderRadius": "10px",
            "color": "white",
            "width": "23%",
            "boxShadow": "0 4px 10px rgba(0,0,0,0.3)",
            "textAlign": "center"
        },
        children=[
            html.H4(label, style={"marginBottom": "8px"}),
            html.H2(value, style={"color": "#58A6FF"})
        ]
    )

app = Dash(__name__)
app.title = "AI Job Market Dashboard"

app.layout = html.Div(
    style={"background": "#0D1117", "padding": "25px", "fontFamily": "Arial"},
    children=[

        html.H1("AI Job Market Insights Dashboard",
                style={"color": "white", "textAlign": "center"}),

        html.Br(),

        html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
            kpi("Median Salary", f"${df['salary_usd'].median():,.0f}"),
            kpi("Total Jobs in database", f"{len(df):,}"),
            kpi("Avg Experience", f"{df['years_experience'].mean():.1f} yrs"),
            kpi("Avg Benefits", f"{df['benefits_score'].mean():.1f}/10"),
        ]),

        html.Br(),

        html.H3("Filters", style={"color": "white"}),
        html.Div(style={"display": "flex", "gap": "20px"}, children=[
            html.Div([
                html.Label("Experience Level", style={"color": "white"}),
                dcc.Dropdown(
                    [{"label": i, "value": i} for i in df["experience_level"].unique()],
                    id="filter_exp", placeholder="All",
                    style={"color": "#000"}
                )
            ], style={"width": "33%"}),

            html.Div([
                html.Label("Job Title", style={"color": "white"}),
                dcc.Dropdown(
                    [{"label": i, "value": i} for i in df["job_title"].unique()],
                    id="filter_title", placeholder="All",
                    style={"color": "#000"}
                )
            ], style={"width": "33%"}),

            html.Div([
                html.Label("Company Location", style={"color": "white"}),
                dcc.Dropdown(
                    [{"label": i, "value": i} for i in df["company_location"].unique()],
                    id="filter_country", placeholder="All",
                    style={"color": "#000"}
                )
            ], style={"width": "33%"}),
        ]),

        html.Br(),


        html.Div([
            dcc.Graph(id="salary_dist"),
            desc("Shows how salaries are distributed across roles. "
                 "The violin shows spread; the boxplot shows median & quartiles. Salary in USD.")
        ]),

        html.Div([
            dcc.Graph(id="exp_salary"),
            desc("Salary differences across experience levels. Higher experience generally means higher salary.")
        ]),

        html.Div([
            dcc.Graph(id="company_salary"),
            desc("Average salary by company size: small, medium, large.")
        ]),

        html.Div([
            dcc.Graph(id="education_salary"),
            desc("Average salary by education level (Bachelor, Master, PhD). Shows how education relates to salary.")
        ]),

        html.Div([
            dcc.Graph(id="industry_salary"),
            desc("Treemap showing average salary across industries. Large blocks = more listings.")
        ]),

        html.Div([
            dcc.Graph(id="location_map"),
            desc("World map showing average AI salary by country (USD). Uses ISO-3 codes for reliability.")
        ]),
    ]
)

@app.callback(
    [
        Output("salary_dist", "figure"),
        Output("exp_salary", "figure"),
        Output("company_salary", "figure"),
        Output("education_salary", "figure"),
        Output("industry_salary", "figure"),
        Output("location_map", "figure"),
    ],
    [
        Input("filter_exp", "value"),
        Input("filter_title", "value"),
        Input("filter_country", "value"),
    ]
)
def update_graphs(exp, title, country):
    df2 = df.copy()

    if exp:
        df2 = df2[df2["experience_level"] == exp]
    if title:
        df2 = df2[df2["job_title"] == title]
    if country:
        df2 = df2[df2["company_location"] == country]
#salary distribution
    fig1 = px.violin(
        df2, y="salary_usd", box=True, points="all",
        color_discrete_sequence=["#58A6FF"],
        title="Salary Distribution (USD)"
    )
    fig1.update_yaxes(title="Salary (USD)")
    fig1.update_layout(margin=dict(b=80))
#salary by experience level
    fig2 = px.box(
        df2, x="experience_level", y="salary_usd",
        color="experience_level", color_discrete_sequence=CATEGORICAL,
        title="Salary by Experience Level"
    )
    fig2.update_yaxes(title="Salary (USD)")
    fig2.update_xaxes(title="Experience Level")
    fig2.update_layout(margin=dict(b=80))

    #salary by company size
    comp_avg = df2.groupby("company_size")["salary_usd"].mean().reset_index()

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=comp_avg["salary_usd"], y=comp_avg["company_size"],
        mode="markers+lines",
        marker=dict(size=14, color="#58A6FF"),
        line=dict(color="#58A6FF", width=3)
    ))
    fig3.update_layout(
        title=" Average Salary by Company Size",
        xaxis_title="Salary (USD)",
        yaxis_title="Company Size",
        margin=dict(b=80)
    )

    #salary by education level
    if "education_required" in df2.columns:
        edu_avg = df2.groupby("education_required")["salary_usd"].mean().reset_index()

        fig_edu = px.bar(
            edu_avg,
            x="education_required",
            y="salary_usd",
            color="salary_usd",
            color_continuous_scale=BLUES,
            title=" Average Salary by Education Level"
        )
        fig_edu.update_xaxes(title="Education Level")
        fig_edu.update_yaxes(title="Salary (USD)")
        fig_edu.update_layout(margin=dict(b=80))
    else:
        fig_edu = go.Figure()
        fig_edu.update_layout(
            title=" Education Level Data Missing",
            margin=dict(b=80)
        )

    #salary by industry
    fig4 = px.treemap(
        df2, path=["industry"], values="salary_usd",
        color="salary_usd", color_continuous_scale=BLUES,
        title=" Salary by Industry"
    )
    fig4.update_layout(margin=dict(b=80))

    #salary by location
    country_stats = df2.groupby("company_location").agg(
        avg_salary=("salary_usd", "mean")
    ).reset_index()

    country_stats["iso_alpha"] = country_stats["company_location"].apply(to_iso3)
    country_stats = country_stats.dropna(subset=["iso_alpha"])

    fig6 = px.choropleth(
        country_stats,
        locations="iso_alpha",
        color="avg_salary",
        hover_name="company_location",
        hover_data={
            "avg_salary": ":,.0f",
            "iso_alpha": False
        },
        color_continuous_scale=BLUES,
        title=" Average AI Salary by Country (USD)"
    )
    fig6.update_coloraxes(colorbar_title="Avg Salary (USD)")
    fig6.update_layout(margin=dict(b=80))

    return fig1, fig2, fig3, fig_edu, fig4, fig6

if __name__ == "__main__":
    app.run(debug=True)
