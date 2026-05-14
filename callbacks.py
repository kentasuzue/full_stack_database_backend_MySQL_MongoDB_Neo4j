from typing import Optional

from dash import Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

from app import app
from ui import notice, pub_details_table
from client import json_request, get_faculty_options, get_university_options, get_publication_options


# Dropdown visibility

@app.callback(
    Output("add-university-controls", "style"),
    Output("merge-university-controls", "style"),
    Input("university-action", "value"),
)
def show_university_action_controls(action: str):

    hidden = {"display": "none"} # hide unselected controls
    visible = {"display": "block", "marginTop": "10px"}

    return (
        visible if action == "add" else hidden,
        visible if action == "merge" else hidden,
    )


@app.callback(
    Output("faculty-dropdown-1", "options"),
    Output("university-dropdown-1", "options"),
    Output("university-dropdown-2", "options"),
    Output("university-dropdown-3", "options"),
    Output("university-dropdown-4", "options"),
    Output("university-dropdown-5", "options"),
    Input("refresh-token", "data"),
)
def load_primary_dropdowns(_: int):

    try:
        faculty_rows = json_request("GET", "/faculty")
        university_rows = json_request("GET", "/universities")

    except Exception:
        return [], [], [], [], [], []

    faculty_options = get_faculty_options(faculty_rows)
    university_options = get_university_options(university_rows)

    return (
        faculty_options,
        university_options,
        university_options,
        university_options,
        university_options,
        university_options,
    )


# Button enablement

@app.callback(
    Output("confirm-add-1", "disabled"),
    Input("new-university-name", "value"),
    prevent_initial_call=True,
)
def enable_add_button(name: Optional[str]):

    return not bool(name and name.strip())


@app.callback(
    Output("confirm-merge-1", "disabled"),
    Input("university-dropdown-1", "value"),
    Input("university-dropdown-2", "value"),
    prevent_initial_call=True,
)
def enable_merge_button(source_id: Optional[int], target_id: Optional[int]):

    return not (source_id and target_id and source_id != target_id)


# Callbacks for university and faculty affiliation management

@app.callback(
    Output("university-action-status", "children"),
    Output("refresh-token", "data"),
    Input("confirm-add-1", "n_clicks"),
    Input("confirm-merge-1", "n_clicks"),
    State("new-university-name", "value"),
    State("university-dropdown-1", "value"),
    State("university-dropdown-2", "value"),
    State("refresh-token", "data"),
    prevent_initial_call=True,
)
def handle_university_action(add_clicks, merge_clicks, new_name, source_id, target_id, token):
    triggered = callback_context.triggered_id

    try:
        if triggered == "confirm-add-1":
            clean_name = (new_name or "").strip()
            if not clean_name:
                return notice("Enter a university name before adding.", "caution"), token

            json_request("POST", "/universities", json={"name": clean_name})

            return notice(f"Added university: {clean_name}", "success"), token + 1

        if triggered == "confirm-merge-1":
            if source_id == target_id:
                return notice("A university cannot be merged into itself.", "caution"), token

            json_request(
                "POST",
                "/universities/merge",
                json={"source_id": source_id, "target_id": target_id},
            )

            return notice("Merged the 'University to Delete' into the 'University to Merge Into'.", "success"), token + 1

    except Exception as exc:

        return notice(f"Database operation failed: {exc}", "error"), token

    raise PreventUpdate


@app.callback(
    Output("faculty-current-affiliation", "children"),
    Input("faculty-dropdown-1", "value"),
    Input("refresh-token", "data"),
)
def show_current_affiliation(faculty_id: Optional[int], _token):

    if not faculty_id:
        return notice("Select a faculty member to show their current affiliation.", "info")

    try:
        row = json_request("GET", f"/faculty/{faculty_id}/affiliation")

    except Exception as exc:
        return notice(str(exc), "caution")

    university_name = row.get("university_name") or "None"

    return notice(f"{row['name']} is affiliated with {university_name}.", "info")


@app.callback(
    Output("change-status", "children"),
    Output("refresh-token", "data", allow_duplicate=True),
    Input("confirm-change-1", "n_clicks"),
    State("faculty-dropdown-1", "value"),
    State("university-dropdown-3", "value"),
    State("refresh-token", "data"),
    prevent_initial_call=True,
)
def handle_affiliation_change(n_clicks: int, faculty_id: Optional[int], new_university_id: Optional[int], token: int):

    if not n_clicks:
        raise PreventUpdate

    if not faculty_id or not new_university_id:
        return notice("Select both a faculty member and a new university affiliation.", "caution"), token

    try:
        json_request(
            "PATCH",
            f"/faculty/{faculty_id}/affiliation",
            json={"university_id": new_university_id},
        )

        return notice("Faculty affiliation updated.", "success"), token + 1

    except Exception as exc:

        return notice(f"Affiliation update failed: {exc}", "error"), token


@app.callback(
    Output("change-status", "children", allow_duplicate=True),
    Input("faculty-dropdown-1", "value"),
    Input("university-dropdown-3", "value"),
    prevent_initial_call=True,
)
def clear_affiliation_status_on_change(faculty_id, university_id):

    return ""


# Callbacks for coauthors

@app.callback(
    Output("faculty-dropdown-2", "options"),
    Output("faculty-dropdown-3", "options"),
    Output("inter-university-status", "children"),
    Input("university-dropdown-4", "value"),
    Input("university-dropdown-5", "value"),
    Input("refresh-token", "data"),
)
def load_inter_university_faculty(left_university_id: Optional[int], right_university_id: Optional[int], _token):

    if not left_university_id or not right_university_id:
        return [], [], notice(
            "Choose two universities to load co-authors affiliated with left and right universities.",
            "info",
        )

    try:
        data = json_request(
            "GET",
            "/coauthors",
            params={
                "left_university_id": left_university_id,
                "right_university_id": right_university_id,
            },
        )

    except Exception as exc:

        return [], [], notice(str(exc), "caution")

    left_options = get_faculty_options(data.get("left_faculty", []))
    right_options = get_faculty_options(data.get("right_faculty", []))

    if not left_options or not right_options:

        return left_options, right_options, notice(
            "No inter-university co-author faculty found for this university pair.","caution",
        )

    return left_options, right_options, notice("Matching faculty loaded.", "success")


@app.callback(
    Output("faculty-selection-warning", "children"),
    Input("faculty-dropdown-2", "value"),
    Input("faculty-dropdown-3", "value"),
)
def validate_faculty_selection(left_faculty_id, right_faculty_id):

    if left_faculty_id and right_faculty_id and left_faculty_id == right_faculty_id:
        return notice("Warning: Left-selected faculty should be different from right-selected faculty.", "caution")

    return ""


@app.callback(
    Output("faculty-status-left", "children"),
    Output("faculty-status-right", "children"),
    Input("faculty-dropdown-2", "value"),
    Input("faculty-dropdown-3", "value"),
)
def show_faculty_guidance(left_faculty_id, right_faculty_id):
    left_msg = ""
    right_msg = ""

    if not left_faculty_id:
        left_msg = notice("Select left-side faculty to view matching publications in Step 3.", "info")

    if not right_faculty_id:
        right_msg = notice("Select right-side faculty to view matching publications in Step 3.", "info")

    return left_msg, right_msg


@app.callback(
    Output("publication-dropdown-1", "options"),
    Output("publication-dropdown-2", "options"),
    Input("faculty-dropdown-2", "value"),
    Input("faculty-dropdown-3", "value"),
    State("university-dropdown-4", "value"),
    State("university-dropdown-5", "value"),
)
def load_publications(left_faculty_id, right_faculty_id, left_university_id, right_university_id):

    left_publications = []
    right_publications = []

    try:
        if left_faculty_id and right_university_id:
            left_publications = json_request(
                "GET",
                f"/faculty/{left_faculty_id}/publications",
                params={"other_university_id": right_university_id},
            )

        if right_faculty_id and left_university_id:
            right_publications = json_request(
                "GET",
                f"/faculty/{right_faculty_id}/publications",
                params={"other_university_id": left_university_id},
            )

    except Exception:

        return [], []

    return get_publication_options(left_publications), get_publication_options(right_publications)


@app.callback(
    Output("publication-status-left", "children"),
    Output("publication-status-right", "children"),
    Input("publication-dropdown-1", "value"),
    Input("publication-dropdown-2", "value"),
)
def show_publication_guidance(left_pub_id, right_pub_id):

    left_msg = ""
    right_msg = ""

    if not left_pub_id:
        left_msg = notice("Select a left-side publication to view left details.", "info")

    if not right_pub_id:
        right_msg = notice("Select a right-side publication to view right details.", "info")

    return left_msg, right_msg


@app.callback(
    Output("publication-details-left", "children"),
    Input("publication-dropdown-1", "value"),
)
def show_left_publication_details(publication_id: Optional[int]):

    if not publication_id:
        return notice("Select a left-side publication in Step 3).", "info")

    try:
        return pub_details_table(json_request("GET", f"/neo4j/publications/{publication_id}"))

    except Exception as exc:

        return notice(str(exc), "error")


@app.callback(
    Output("publication-details-right", "children"),
    Input("publication-dropdown-2", "value"),
)
def show_right_publication_details(publication_id: Optional[int]):

    if not publication_id:
        return notice("Select a right-side publication in Step 3).", "info")

    try:
        return pub_details_table(json_request("GET", f"/mongo/publications/{publication_id}"))

    except Exception as exc:

        return notice(str(exc), "error")
