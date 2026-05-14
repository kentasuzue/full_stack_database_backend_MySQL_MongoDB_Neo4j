from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app import server
from db import *


# REST API error

def api_error(error_message: str, status_code: int = 400):
    return jsonify({"error": error_message}), status_code


def sqlalchemy_error(sqlalchemy_err: SQLAlchemyError) -> str:
    return str(sqlalchemy_err.orig) if hasattr(sqlalchemy_err, "orig") else str(sqlalchemy_err)


# REST API MySQL

@server.get("/api/universities")
def api_get_universities():

    try:
        return jsonify(get_universities_db()), 200

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


@server.post("/api/universities")
def api_add_university():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return api_error("University name is required.", 400)

    try:
        add_university_db(name)
        return jsonify({"message": "University added.", "name": name}), 201

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


@server.post("/api/universities/merge")
def api_merge_universities():
    data = request.get_json(silent=True) or {}
    source_id = data.get("source_id")
    target_id = data.get("target_id")

    if not source_id or not target_id:
        return api_error("source_id and target_id are required.", 400)

    if int(source_id) == int(target_id):
        return api_error("A university cannot be merged into itself.", 400)

    try:
        merge_universities_db(int(source_id), int(target_id))
        return jsonify(
            {
                "message": "Universities merged.",
                "source_id": int(source_id),
                "target_id": int(target_id),
            }
        ), 200

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


@server.get("/api/faculty")
def api_get_faculty():

    try:
        return jsonify(get_faculty_db()), 200

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


@server.get("/api/faculty/<int:faculty_id>/affiliation")
def api_get_faculty_affiliation(faculty_id: int):

    try:
        row = get_faculty_affiliation_db(faculty_id)
        if not row:
            return api_error("Faculty member not found.", 404)
        return jsonify(row), 200

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


@server.patch("/api/faculty/<int:faculty_id>/affiliation")
def api_change_faculty_affiliation(faculty_id: int):
    data = request.get_json(silent=True) or {}
    university_id = data.get("university_id")

    if not university_id:
        return api_error("university_id is required.", 400)

    try:
        current = get_faculty_affiliation_db(faculty_id)
        if not current:
            return api_error("Faculty member not found.", 404)

        if current["university_id"] == int(university_id):
            return api_error(
                "Faculty is already affiliated with the selected university.",
                400,
            )

        change_faculty_affiliation_db(faculty_id, int(university_id))
        updated = get_faculty_affiliation_db(faculty_id)

        return jsonify(
            {
                "message": "Faculty affiliation updated.",
                "faculty": updated,
            }
        ), 200

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


@server.get("/api/coauthors")
def api_get_coauthors():
    left_id = request.args.get("left_university_id", type=int)
    right_id = request.args.get("right_university_id", type=int)

    if not left_id or not right_id:
        return api_error("left_university_id and right_university_id are required.", 400)

    try:
        left_faculty, right_faculty = get_inter_university_faculty_db(left_id, right_id)
        return jsonify(
            {
                "left_faculty": left_faculty,
                "right_faculty": right_faculty,
            }
        ), 200

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


@server.get("/api/faculty/<int:faculty_id>/publications")
def api_get_faculty_publications(faculty_id: int):
    other_university_id = request.args.get("other_university_id", type=int)

    if not other_university_id:
        return api_error("other_university_id is required.", 400)

    try:
        rows = get_publications_of_faculty_other_university_db(
            faculty_id,
            other_university_id,
        )
        return jsonify(rows), 200

    except SQLAlchemyError as sqlalchemy_err:
        return api_error(sqlalchemy_error(sqlalchemy_err), 500)


# REST API MongoDB, Neo4j

@server.get("/api/mongo/publications/<int:publication_id>")
def api_get_publication_mongo(publication_id: int):

    try:
        publication = get_publication_details_mongo_db(publication_id)
        if not publication:
            return api_error("Publication not in MongoDB.", 404)
        return jsonify(publication), 200

    except Exception as sqlalchemy_err:
        return api_error(f"MongoDB access failed: {sqlalchemy_err}", 500)


@server.get("/api/neo4j/publications/<int:publication_id>")
def api_get_publication_neo4j(publication_id: int):

    try:
        publication = get_publication_details_neo4j_db(publication_id)
        if not publication:
            return api_error("Publication not  in Neo4j.", 404)
        return jsonify(publication), 200

    except Exception as sqlalchemy_err:
        return api_error(f"Neo4j access failed: {sqlalchemy_err}", 500)

