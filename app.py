import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import pycountry

# Load dataset
df = pd.read_csv("data/new_jobsfr_global.csv")

# ======= Colour-blind-safe palettes ======= #
CATEGORICAL = px.colors.qualitative.Safe
SEQUENTIAL = px.colors.sequential.Viridis
BLUES = px.colors.sequential.Blues

# ======= Accessibility Helper (Alt-Text) ======= #
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

# ======= Convert Country → ISO-3 Codes ======= #
def to_iso3(country):
    try:
        return pycountry.countries.lookup(country).alpha_3
    except:
        return None

# ======= KPI Card ======= #
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

# ======= DASH APP ======= #
app = Dash(__name__)
app.title = "AI Job Market Dashboard"

app.layout = html.Div(
    style={"background": "#0D1117", "padding": "25px", "fontFamily": "Arial"},
    children=[

        html.H1("🔍 AI Job Market Insights Dashboard",
                style={"color": "white", "textAlign": "center"}),

        html.Br(),

        # ========== KPIs ========== #
        html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
            kpi("Median Salary", f"${df['salary_usd'].median():,.0f}"),
            kpi("Total Jobs", f"{len(df):,}"),
            kpi("Avg Experience", f"{df['years_experience'].mean():.1f} yrs"),
            kpi("Avg Benefits", f"{df['benefits_score'].mean():.1f}/10"),
        ]),

        html.Br(),

        # ========== FILTERS ========== #
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

        # ========== CHART BLOCKS ========== #

        html.Div([
            dcc.Graph(id="salary_dist"),
            desc("Shows how salaries are distributed across roles. "
                 "Violin shows distribution; boxplot summarises spread; points show individual postings.")
        ]),

        html.Div([
            dcc.Graph(id="exp_salary"),
            desc("How salary changes across experience levels. Senior roles consistently offer higher pay.")
        ]),

        html.Div([
            dcc.Graph(id="company_salary"),
            desc("Average salary by company size. Larger organisations generally pay more due to higher budgets.")
        ]),

        html.Div([
            dcc.Graph(id="education_salary"),
            desc("Average salary by education level. Higher education levels tend to correlate with higher salaries.")
        ]),

        html.Div([
            dcc.Graph(id="industry_salary"),
            desc("Treemap showing which industries have the highest salary levels and job counts.")
        ]),

        html.Div([
            dcc.Graph(id="location_map"),
            desc("World map showing AI job counts and average salary per country.")
        ]),
    ]
)

# ======= CALLBACK ======= #
@app.callback(
    [
        Output("salary_dist", "figure"),
        Output("exp_salary", "figure"),
        Output("company_salary", "figure"),
        Output("education_salary", "figure"),   # NEW
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

    # ===== Salary Distribution ===== #
    fig1 = px.violin(
        df2, y="salary_usd", box=True, points="all",
        color_discrete_sequence=["#58A6FF"],
        title="💰 Salary Distribution (USD)"
    )
    fig1.update_yaxes(title="Salary (USD)")
    fig1.update_layout(margin=dict(b=80))

    # ===== Salary by Experience Level ===== #
    fig2 = px.box(
        df2, x="experience_level", y="salary_usd",
        color="experience_level", color_discrete_sequence=CATEGORICAL,
        title="📈 Salary by Experience Level"
    )
    fig2.update_yaxes(title="Salary (USD)")
    fig2.update_xaxes(title="Experience Level")
    fig2.update_layout(margin=dict(b=80))

    # ===== Company Size Salaries ===== #
    comp_avg = df2.groupby("company_size")["salary_usd"].mean().reset_index()

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=comp_avg["salary_usd"], y=comp_avg["company_size"],
        mode="markers+lines",
        marker=dict(size=14, color="#58A6FF"),
        line=dict(color="#58A6FF", width=3)
    ))
    fig3.update_layout(
        title="🏢 Average Salary by Company Size",
        xaxis_title="Salary (USD)",
        yaxis_title="Company Size",
        margin=dict(b=80)
    )

    # ===== Education Salary Plot ===== #
    if "education_required" in df2.columns:
        edu_avg = df2.groupby("education_required")["salary_usd"].mean().reset_index()

        fig_edu = px.bar(
            edu_avg,
            x="education_required",
            y="salary_usd",
            color="salary_usd",
            color_continuous_scale=BLUES,
            title="🎓 Average Salary by Education Level"
        )
        fig_edu.update_xaxes(title="Education Level")
        fig_edu.update_yaxes(title="Salary (USD)")
        fig_edu.update_layout(margin=dict(b=80))
    else:
        fig_edu = go.Figure()
        fig_edu.update_layout(
            title="🎓 Education Level Data Missing",
            margin=dict(b=80)
        )

    # ===== Industry Salary Treemap ===== #
    fig4 = px.treemap(
        df2, path=["industry"], values="salary_usd",
        color="salary_usd", color_continuous_scale=BLUES,
        title="🏭 Salary by Industry"
    )
    fig4.update_layout(margin=dict(b=80))


    # ===== Location Map (Job Count + Avg Salary) ===== #
    country_stats = df2.groupby("company_location").agg(
        count=("company_location", "size"),
        avg_salary=("salary_usd", "mean")
    ).reset_index()

    country_stats["iso_alpha"] = country_stats["company_location"].apply(to_iso3)
    country_stats = country_stats.dropna(subset=["iso_alpha"])

    fig6 = px.choropleth(
        country_stats,
        locations="iso_alpha",
        color="count",
        hover_name="company_location",
        hover_data={
            "count": True,
            "avg_salary": ":,.0f",
            "iso_alpha": False
        },
        color_continuous_scale=BLUES,
        title="🌍 Global AI Jobs by Country (Job Count & Average Salary)"
    )
    fig6.update_layout(margin=dict(b=80))

    return fig1, fig2, fig3, fig_edu, fig4,fig6

# ======= RUN SERVER ======= #
if __name__ == "__main__":
    app.run(debug=True)
