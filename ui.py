import json
from typing import Any, Dict, Optional

from dash import dash_table, dcc, html

# UI

def notice(message: str, kind: str = "info") -> html.Div:
    colors = {
        "caution": "gold",
        "error": "salmon",
        "info": "skyblue",
        "success": "lightgreen",
    }
    return html.Div(
        message,
        style={
            "backgroundColor": colors.get(kind, colors["info"]),
            "borderRadius": "10px",
            "marginTop": "10px",
            "padding": "12px",
        },
    )


def box(children: Any) -> html.Div:
    return html.Div(
        children,
        style={
            "border": "1px solid #ddd",
            "borderRadius": "20px",
            "boxShadow": "0 3px 10px rgba(0,0,0,0.20)",
            "marginBottom": "30px",
            "padding": "30px",
        },
    )


def adjacent_columns(left_col: Any, right_col: Any) -> html.Div:
    return html.Div(
        [
            html.Div(
                left_col,
                style = {
                    "display": "inline-block",  # side-by-side dropdowns
                    "marginRight": "1%",
                    "verticalAlign": "top",
                    "width": "49%",
                },
            ),
            html.Div(
                right_col,
                style = {
                    "display": "inline-block",  # side-by-side dropdowns
                    "marginLeft": "1%",
                    "verticalAlign": "top",
                    "width": "49%",
                },
            ),
        ]
    )


def dropdown_panel(label: str, dropdown_id: str, helper_text: str, status_id: Optional[str] = None) -> Any:
    children = [
        html.Label(label),
        dcc.Dropdown(id = dropdown_id),
        html.Small(helper_text),
    ]

    if status_id:
        children.append(html.Div(id = status_id, style = {"marginTop": "15px"}))

    return children


def university_pair_selector() -> Any:
    return adjacent_columns(
        [html.Label("Left University"), dcc.Dropdown(id = "university-dropdown-4")],
        [html.Label("Right University"), dcc.Dropdown(id = "university-dropdown-5")],
    )


def coauthor_faculty_selector() -> Any:
    return adjacent_columns(
        dropdown_panel(
            "Faculty affiliated with left-selected university",
            "faculty-dropdown-2",
            "Shown faculty has left-selected university affiliation and has a co-author with right-selected university affiliation.",
            "faculty-status-left",
        ),
        dropdown_panel(
            "Faculty affiliated with right-selected university",
            "faculty-dropdown-3",
            "Shown faculty has right-selected university affiliation and has a co-author with left-selected university affiliation.",
            "faculty-status-right",
        ),
    )


def coauthored_publication_selector() -> Any:
    return adjacent_columns(
        dropdown_panel(
            "Publication for left-selected faculty",
            "publication-dropdown-1",
            "Shown publications have the left-selected author and a co-author affiliated with the right-selected university.",
            "publication-status-left",
        ),
        dropdown_panel(
            "Publication for right-selected faculty",
            "publication-dropdown-2",
            "Shown publications have the right-selected author and a co-author affiliated with the left-selected university.",
            "publication-status-right",
        ),
    )


def author_affiliations_table(rows: Optional[Any]) -> Any:
    if not rows:
        return notice("No author affiliation rows found for this publication.", "caution")

    table_rows = []
    for row in rows:
        table_rows.append(
            {
                "Author": row.get("author_name", ""),
                "Affiliation": row.get("affiliation") or "None",
            }
        )

    return dash_table.DataTable(
        columns=[
            {"name": "Author", "id": "Author"},
            {"name": "Affiliation", "id": "Affiliation"},
        ],
        data=table_rows,
        page_size=10,
        style_table={"overflowX": "auto", "marginTop": "10px"},
        style_cell={
            "fontFamily": "inherit",
            "fontSize": "16px",
            "height": "auto",
            "padding": "10px",
            "textAlign": "left",
            "whiteSpace": "normal",
        },
        style_header={"fontWeight": "bold"},
    )


def pub_details_table(details: Optional[Dict[str, Any]]) -> Any:
    if not details:
        return notice("No details found for this publication.", "caution")

    field_order = [
        ("id", "ID"),
        ("title", "Title"),
        ("authors", "Authors"),
        ("year", "Year"),
        ("venue", "Venue"),
        ("numCitations", "Citations"),
        ("citations", "Citations"),
    ]

    rows = []
    for key, label in field_order:
        if key not in details:
            continue

        value = details[key]

        if isinstance(value, list):
            value = ", ".join(map(str, value))

        elif isinstance(value, dict):
            value = html.Pre(
                json.dumps(value, default = str, indent = 3),
                style = {"whiteSpace": "pre-wrap"},
            )

        rows.append(html.Tr([html.Th(label), html.Td(value)]))

    author_rows = details.get("author_affiliations")

    return html.Div(
        [
            html.Table(rows, style = {"width": "100%"}),
            html.H5("Authors and affiliations", style = {"marginTop": "20px"}),
            author_affiliations_table(author_rows),
        ]
    )

# Layout

layout = html.Div(
    [
        dcc.Store(id = "refresh-token", data = 0),
        html.H1("AcademicWorld Dashboard"),
        html.P(
            "Manage university records, faculty affiliations, and inter-university co-authored publications.",
            style = {
                "fontSize": "24px",
                "marginBottom": "20px",
            },
        ),

        box([
            html.H3("University Management: Merge or Add a University"),
            dcc.RadioItems(
                id = "university-action",
                options = [
                    {"label": "Add University", "value": "add"},
                    {"label": "Merge University", "value": "merge"},
                ],
                value = "add",
            ),
            html.Div(
                id = "university-action-controls",
                children = [
                    html.Div(
                        id = "add-university-controls",
                        children = [
                            html.Label("New university name"),
                            dcc.Input(
                                id = "new-university-name",
                                placeholder = "Enter university name",
                                type = "text",
                                style = {"width": "50%"},
                            ),
                            html.Button(
                                "Confirm Add",
                                id = "confirm-add-1",
                                disabled = True,
                                n_clicks = 0,
                                style = {"marginLeft": "20px"},
                            ),
                        ],
                    ),
                    html.Div(
                        id = "merge-university-controls",
                        children = adjacent_columns(
                            [
                                html.Label("University to Delete"),
                                dcc.Dropdown(id = "university-dropdown-1"),
                            ],
                            [
                                html.Label("University to Merge Into"),
                                dcc.Dropdown(id = "university-dropdown-2"),
                                html.Button(
                                    "Confirm Merge",
                                    id = "confirm-merge-1",
                                    disabled = True,
                                    n_clicks = 0,
                                    style = {"marginTop": "15px"},
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            html.Div(id = "university-action-status"),
        ]),

        box([
            html.H3("Faculty University Affiliation Management: Change University Affiliation of Faculty"),
            adjacent_columns(
                [
                    html.Label("Faculty"),
                    dcc.Dropdown(id = "faculty-dropdown-1"),
                    html.Div(id = "faculty-current-affiliation",
                             style = {"marginTop": "15px"}),
                ],
                [
                    html.Label("New University Affiliation"),
                    dcc.Dropdown(id = "university-dropdown-3"),
                    html.Button(
                        "Confirm Change",
                        id = "confirm-change-1",
                        n_clicks = 0,
                        style = {"marginTop": "15px"},
                    ),
                ],
            ),
            html.Div(id = "change-status"),
        ]),

        html.H2("Find Publications Co-Authored by Faculty at Selected Universities"),

        box([
            html.H3("Step 1) Choose Two University Affiliations of Faculty"),
            university_pair_selector(),
            html.Div(id = "inter-university-status"),
        ]),

        box([
            html.H3("Step 2) Choose Faculty Affiliated with Each Chosen University"),
            coauthor_faculty_selector(),
            html.Div(id = "faculty-selection-warning"),
        ]),

        box([
            html.H3("Step 3) Choose Publication Co-authored by Selected Faculty"),
            coauthored_publication_selector(),
        ]),

        box([
            html.H3("Step 4) Show Details of Selected Publication"),
            adjacent_columns(
                [html.H5("Details of Left-Selected Publication — Neo4j"), html.Div(id = "publication-details-left")],
                [html.H5("Details of Right-Selected Publication — MongoDB"), html.Div(id = "publication-details-right")],
            ),
        ]),
    ],
    style = {"marginTop": "0",
             "marginBottom": "0",
             "marginLeft": "auto",
             "marginRight": "auto",
             "maxWidth": "1200px",
             "padding": "32px"},
)

