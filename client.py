from typing import Any, Dict, List

import requests

from app import API_BASE_URL

# client helpers

def json_request(http_method: str, endpoint_path: str, **kwargs) -> Any:
    response = requests.request(http_method, f"{API_BASE_URL}{endpoint_path}", timeout=5, **kwargs)

    if response.status_code >= 400:
        try:
            message = response.json().get("error", response.text)
        except Exception:
            message = response.text
        raise RuntimeError(message)

    if not response.text:
        return None

    return response.json()


def get_faculty_options(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"label": row["name"], "value": row["id"]} for row in rows]


def get_university_options(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"label": row["name"], "value": row["id"]} for row in rows]


def get_publication_options(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pub_options = []
    for row in rows:
        year = row.get("year") or "n.d."
        pub_options.append({"label": f"{row['title']} ({year})", "value": row["id"]})
    return pub_options

