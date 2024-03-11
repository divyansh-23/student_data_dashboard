import plotly.express as px
import pandas as pd
import numpy as np
import dash
from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate

# Path to your data file
file_path = 'data/data_sim_updated.csv'  # Adjust this to the path of your dataset file

# Load the dataset into a Pandas DataFrame
df = pd.read_csv(file_path)

# Handle Missing Values
df.dropna(inplace=True)

# Convert Grades to a Numerical Scale


def grade_to_number(grade):
    grade_mapping = {
        'A+': 4.33, 'A': 4.00, 'A-': 3.67,
        'B+': 3.33, 'B': 3.00, 'B-': 2.67,
        'C+': 2.33, 'C': 2.00, 'C-': 1.67,
        'D+': 1.33, 'D': 1.00, 'D-': 0.67,
        'F': 0.00, 'W': -0.3  # Withdrawn grades can be considered as missing data
    }
    return grade_mapping.get(grade, np.nan)


# Apply the conversion function to the grade column
df['grade_numeric'] = df['Grade'].apply(grade_to_number)

# Drop rows where conversion resulted in NaN
df.dropna(subset=['grade_numeric'], inplace=True)

# Ensure data consistency
df['Gender'] = df['Gender'].str.lower()
df['Race/Ethnicity'] = df['Race/Ethnicity'].str.lower()  # Corrected column name
df['Course'] = df['Course'].str.upper()

# Initialize Dash app
app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1('Student Performance Dashboard', style={'textAlign': 'center'}),

    # Container for dropdowns
    html.Div([
        # Overview Dropdown
        html.Div([
            html.Label('Overview'),
            dcc.Dropdown(
                id='primary-category-dropdown',
                options=[
                    {'label': 'Course', 'value': 'Course'},
                    {'label': 'COVID Impact', 'value': 'COVID Impact'},
                    {'label': 'First Generation', 'value': 'First Generation'},
                    {'label': 'Gender', 'value': 'Gender'},
                    # Corrected option label
                    {'label': 'Race/Ethnicity', 'value': 'Race/Ethnicity'},
                    {'label': 'Semester', 'value': 'Semester'},
                ],
                value='Course',  # Default or initial value
                clearable=False
            ),
        ], style={'width': '48%', 'display': 'inline-block'}),

        # Drill-down Dropdown
        html.Div([
            html.Label('Drill-down'),
            dcc.Dropdown(
                id='secondary-category-dropdown',
                clearable=True  # Ensure this dropdown is clearable
            ),
        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'}),
    ]),

    dcc.Graph(id='grade-distribution-graph'),
])


@app.callback(
    Output('secondary-category-dropdown', 'options'),
    [Input('primary-category-dropdown', 'value')]
)
def set_secondary_options(selected_primary):
    all_options = [col for col in df.columns if col not in [
        'Grade', 'grade_numeric', selected_primary]]
    return [{'label': col, 'value': col} for col in all_options]


@app.callback(
    Output('grade-distribution-graph', 'figure'),
    [Input('primary-category-dropdown', 'value'),
     Input('secondary-category-dropdown', 'value')]
)
def update_graph(primary_selection, secondary_selection):
    if not primary_selection:
        raise PreventUpdate

    # Determine which columns to use for coloring and faceting based on selections
    color_col = primary_selection if primary_selection in df.columns else None
    facet_row = secondary_selection if secondary_selection and secondary_selection in df.columns and secondary_selection != primary_selection else None

    # Filtering the DataFrame for selected categories (if needed)
    # This step might include filtering or adjusting df based on the selections
    filtered_df = df  # Assuming no additional filtering is required

    # Group and calculate percentages for the selected categories
    if facet_row:
        # If there's a secondary selection, include it in grouping
        group_fields = [color_col, facet_row, 'Grade']
    else:
        # Otherwise, just use the primary selection and Grade
        group_fields = [color_col, 'Grade']

    counts = filtered_df.groupby(
        group_fields).size().reset_index(name='counts')
    total_counts = counts.groupby(group_fields[:-1])['counts'].transform('sum')
    counts['percentage'] = (counts['counts'] / total_counts) * 100

    # Add a text column for hover information, showing counts
    counts['Count'] = counts['counts'].astype(str)

    # Determine dynamic height
    if secondary_selection and primary_selection != secondary_selection:
        unique_values = filtered_df[secondary_selection].nunique()
        height_per_subplot = 300  # Set minimum height per subplot
        # Ensure a minimum total height
        total_height = max(unique_values * height_per_subplot, 900)
    else:
        total_height = 600

    # Generate the figure based on the primary and (optionally) secondary selections
    fig = px.bar(counts, y='Grade', x='percentage', color=color_col,
                 facet_row=facet_row,  # Use facet_row if secondary selection is made
                 orientation='h',
                 barmode='group',  # Display bars side by side
                 title=f'Distribution by {primary_selection}' + \
                 (f' and {secondary_selection}' if facet_row else ''),
                 labels={'percentage': 'Percentage of Total'},
                 category_orders={"Grade": [
                     "W", "F", "D-", "D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+"]},
                 # Include percentage, exclude default count display
                 hover_data={'percentage': True, 'counts': False},
                 text='Count')  # Use hover_text for hover information

    fig.update_layout(plot_bgcolor='white',
                      paper_bgcolor='white', height=total_height)
    fig.update_xaxes(matches=None, showticklabels=True)
    return fig

# After initializing your Dash app
if __name__ == '__main__':
    app.run_server(debug=True)