import pandas as pd
import plotly.express as px
import pycountry
import pycountry_convert as pc

def iso3_to_continent(alpha3):
    try:
        country = pycountry.countries.get(alpha_3=alpha3)
        if not country:
            return "Other"
        iso2 = country.alpha_2
        cont_code = pc.country_alpha2_to_continent_code(iso2)
        return {
            "AF": "Africa",
            "AS": "Asia",
            "EU": "Europe",
            "NA": "North America",
            "OC": "Oceania",
            "SA": "South America",
            "AN": "Antarctica"
        }.get(cont_code, "Other")
    except:
        return "Other"


# Load & merge data
df_ind = pd.read_csv("unicef_indicator_2.csv")
df_meta = pd.read_csv("unicef_metadata.csv")
df = pd.merge(df_ind, df_meta, on=["alpha_3_code","time_period"], how="left")

# Add continent information
df["continent"] = df["alpha_3_code"].apply(iso3_to_continent)
print("Continents found:", sorted(df["continent"].unique()))


# 1) Time‐Series HTML
ts = df.groupby("time_period", as_index=False).agg({
    "obs_value":"mean",
    "Life expectancy at birth, total (years)":"mean"
}).rename(columns={
    "obs_value":"Coverage",
    "Life expectancy at birth, total (years)":"LifeExpectancy"
})
fig1 = px.line(ts, x="time_period", y=["Coverage","LifeExpectancy"],
               labels={"time_period":"Year","value":"Coverage","variable":"Indicator"},
               title="A Journey of Progress: Vaccination Coverage and Life Expectancy over time")
fig1.update_layout(legend_title_text="")
fig1.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=[
                dict(count=5, label="5 Y", step="year", stepmode="backward"),
                dict(count=10, label="10 Y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]
        ),
        rangeslider=dict(visible=True),
        title="Year"
    )
)

fig1.write_html("time_series.html", include_plotlyjs="cdn")
print("✓ time_series.html generated")

#2 ─── Interactive Map with Continent Dropdown & Year Slider ───
years = sorted(df["time_period"].unique())
continents = ["All"] + sorted(df["continent"].dropna().unique())

# 1) Display the **latest** year by default
init_year = years[-1]      # was years[0]
df0 = df[df.time_period == init_year]

fig = px.choropleth(
    df0,
    locations="alpha_3_code",
    color="obs_value",
    color_continuous_scale="Viridis",
    labels={"obs_value":"Coverage (%)"},
    title=f"RCV1 Coverage in All Continents ({init_year})"
)

# … build your continent dropdown exactly as before …
# ─── Add Continent Dropdown ───
# Build a list of continents (you already created df["continent"])
continents = ["All"] + sorted(df["continent"].dropna().unique())

# Create one button per continent
buttons = []
for cont in continents:
    if cont == "All":
        dff = df[df.time_period == init_year]
        label = "All Continents"
    else:
        dff = df[(df.time_period == init_year) & (df.continent == cont)]
        label = cont
    buttons.append(dict(
        method="update",
        label=label,
        args=[
            {"locations": [dff["alpha_3_code"]], "z": [dff["obs_value"]]},
            {"title": f"RCV1 Coverage in {label} ({init_year})"}
        ]
    ))

# Inject the dropdown into the layout
fig.update_layout(
    updatemenus=[dict(
        buttons=buttons,
        direction="down",
        x=0.0,
        y=1.1,
        showactive=True
    )]
)
# ───────────────────────────────


# 2) Build the year‐slider steps
steps = []
for year in years:
    dff = df[df.time_period == year]
    steps.append(dict(
        method="update",
        label=str(year),
        args=[
            {"locations": [dff["alpha_3_code"]], "z": [dff["obs_value"]]},
            {"title":f"Global Vaccination Coverage ({year})"}
        ]
    ))

#3 ─── Scatter: GDP vs. Vaccination Coverage with Full 1980–2023 Slider ───
import plotly.express as px

# 1) Define the full slider range
years = list(range(1980, 2024))   # 1980 through 2023

# 2) Build the animated scatter
fig3 = px.scatter(
    df,
    x="GDP per capita (constant 2015 US$)",
    y="obs_value",
    animation_frame="time_period",
    animation_group="alpha_3_code",
    color="continent",
    hover_name="alpha_3_code",
    labels={
        "obs_value": "Coverage (%)",
        "GDP per capita (constant 2015 US$)": "GDP per Capita (2015 US$)"
    },
    title="GDP per Capita vs. Vaccination Coverage (1980–2023)",
    category_orders={"time_period": years}
)

# 3) Tidy up layout
fig3.update_layout(
    legend_title_text="Continent"
)

# 4) Default the slider handle to the last year (2023)
if fig3.layout.sliders:
    fig3.layout.sliders[0].active = len(years) - 1

# 5) Write out the updated HTML
fig3.write_html("scatter.html", include_plotlyjs="cdn")
print("✓ scatter.html (1980–2023 slider) generated")




# 4) Bar Chart HTML (Top 10 Growth Rates)
# Compute growth rate per country between first and last year
df_sorted = df.sort_values(["alpha_3_code", "time_period"])
summary = (
    df_sorted
      .groupby("alpha_3_code", as_index=False)
      .agg(
          first_obs=("obs_value", "first"),
          last_obs=("obs_value", "last")
      )
)
summary["GrowthRate"] = (summary["last_obs"] / summary["first_obs"] - 1) * 100

top10 = summary.nlargest(10, "GrowthRate")

fig4 = px.bar(
    top10,
    x="alpha_3_code",
    y="GrowthRate",
    labels={"alpha_3_code":"Country","GrowthRate":"% Growth"},
    title="Top 10 Countries by Vaccination Coverage Growth"
)
fig4.write_html("bar.html", include_plotlyjs="cdn")
print("✓ bar.html generated")
