from typing import Any, Dict, List, Optional, Tuple

from pymongo.collection import Collection
from sqlalchemy import text

from app import mysql_db, mongo_db, neo4j_db, NEO4JDB


# MongoDB, Neo4j

def get_publication_details_mongo_db(publication_id: int) -> Optional[Dict[str, Any]]:
    collection: Collection = mongo_db["publications"]
    publication = collection.find_one({"id": int(publication_id)}, {"_id": 0, "keywords": 0})
    return add_author_affiliations_to_publication(publication, publication_id)


def get_publication_details_neo4j_db(publication_id: int) -> Optional[Dict[str, Any]]:
    records, _, _ = neo4j_db.execute_query(
        """
        MATCH (pub:PUBLICATION)
        WHERE pub.id = "p" + toString($publication_id)
        RETURN pub
        """,
        publication_id = int(publication_id),
        database_ = NEO4JDB,
    )

    if not records:
        return None

    publication = dict(records[0]["pub"])
    return add_author_affiliations_to_publication(publication, publication_id)


# MySQL

def query_mysql(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    with mysql_db.connect() as db_conn:
        query_result = db_conn.execute(text(query), params or {})
        return [dict(row._mapping) for row in query_result]


def get_universities_db() -> List[Dict[str, Any]]:
    return query_mysql(
        """
        SELECT id, name
        FROM university
        ORDER BY name
        """
    )


def get_faculty_db() -> List[Dict[str, Any]]:
    return query_mysql(
        # TRIM removes leading spaces in faculty name
        """
        SELECT f.id, f.name, u.id AS university_id, u.name AS university_name
        FROM faculty AS f
        LEFT JOIN university AS u ON f.university_id = u.id
        ORDER BY TRIM(f.name)
        """
    )


def get_faculty_affiliation_db(faculty_id: int) -> Optional[Dict[str, Any]]:
    rows = query_mysql(
        """
        SELECT f.id, f.name, u.id AS university_id, u.name AS university_name
        FROM faculty AS f
        LEFT JOIN university AS u ON f.university_id = u.id
        WHERE f.id = :faculty_id
        """,
        {"faculty_id": faculty_id},
    )
    return rows[0] if rows else None


def add_university_db(name: str) -> None:
    with mysql_db.begin() as db_conn:
        db_conn.execute(text("CALL add_university(:name)"), {"name": name})


def merge_universities_db(source_university_id: int, target_university_id: int) -> None:
    with mysql_db.begin() as db_conn:
        db_conn.execute(
            text("CALL merge_universities(:source_id, :target_id)"),
            {"source_id": source_university_id, "target_id": target_university_id},
        )


def change_faculty_affiliation_db(faculty_id: int, university_id: int) -> None:
    with mysql_db.begin() as db_conn:
        db_conn.execute(
            text(
                """
                UPDATE faculty
                SET university_id = :university_id
                WHERE id = :faculty_id
                """
            ),
            {"faculty_id": faculty_id, "university_id": university_id},
        )


def get_inter_university_faculty_db(left_university_id: int, right_university_id: int
                                    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    left_faculty = query_mysql(
        # TRIM removes leading spaces in faculty name
        """
        SELECT DISTINCT f1.id, f1.name
        FROM faculty AS f1, faculty AS f2, faculty_publication AS fp1, faculty_publication AS fp2
        WHERE f1.id = fp1.faculty_id
        AND f1.university_id = :left_university_id
        AND f2.id = fp2.faculty_id
        AND f2.university_id = :right_university_id
        -- AND f1.id <> f2.id
        AND fp1.publication_id = fp2.publication_id
        ORDER BY TRIM(f1.name)
        """,
        {
            "left_university_id": left_university_id,
            "right_university_id": right_university_id,
        },
    )

    right_faculty = query_mysql(
        """
        SELECT DISTINCT f2.id, f2.name
        FROM faculty AS f1, faculty AS f2, faculty_publication AS fp1, faculty_publication AS fp2
        WHERE f1.id = fp1.faculty_id
        AND f1.university_id = :left_university_id
        AND f2.id = fp2.faculty_id
        AND f2.university_id = :right_university_id
        --  AND f1.id <> f2.id
        AND fp1.publication_id = fp2.publication_id
        ORDER BY TRIM(f2.name)
        """,
        {
            "left_university_id": left_university_id,
            "right_university_id": right_university_id,
        },
    )

    return left_faculty, right_faculty


def get_publications_of_faculty_other_university_db(faculty_id: int, other_university_id: int
                                                    ) -> List[Dict[str, Any]]:
    return query_mysql(
        """
        SELECT DISTINCT p.id, p.title, p.year
        FROM publication AS p, faculty AS f_other, faculty_publication AS fp_selected, faculty_publication AS fp_other
        WHERE p.id = fp_selected.publication_id
        AND p.id = fp_other.publication_id
        AND f_other.id = fp_other.faculty_id
        AND f_other.university_id = :other_university_id
        -- AND f_other.id <> :faculty_id
        AND fp_selected.faculty_id = :faculty_id
        ORDER BY p.title
        """,
        {"faculty_id": faculty_id, "other_university_id": other_university_id},
    )


# SQL stored procedures, prepared statement, transaction

def add_university_procedure() -> None:
    create_sql = """
    CREATE PROCEDURE add_university(IN added_university_name VARCHAR(255))
    BEGIN
        SET @uni_id = (
            SELECT MAX(id) + 1
            FROM university
        );

        SET @uni_name = added_university_name;

        SET @prep_sql = '
            INSERT INTO university (id, name)
            SELECT ?, ?
            WHERE NOT EXISTS (
                SELECT *
                FROM university
                WHERE name = ?
            )
        ';

        PREPARE prep_stmt FROM @prep_sql;
        EXECUTE prep_stmt USING @uni_id, @uni_name, @uni_name;
        DEALLOCATE PREPARE prep_stmt;
    END
    """

    with mysql_db.begin() as db_conn:
        db_conn.execute(text("DROP PROCEDURE IF EXISTS add_university"))
        db_conn.exec_driver_sql(create_sql)


def merge_university_procedure() -> None:
    create_sql = """
    CREATE PROCEDURE merge_universities(
        IN source_id INT,
        IN target_id INT
    )
    BEGIN
        DECLARE EXIT HANDLER FOR SQLEXCEPTION
        BEGIN
            ROLLBACK;
            RESIGNAL;
        END;

        START TRANSACTION;

        IF source_id = target_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Source and target universities must be different';
        END IF;

        IF NOT EXISTS (
            SELECT *
            FROM university
            WHERE id = source_id
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Source university does not exist';
        END IF;

        IF NOT EXISTS (
            SELECT *
            FROM university
            WHERE id = target_id
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Target university does not exist';
        END IF;

        UPDATE faculty
        SET university_id = target_id
        WHERE university_id = source_id;

        DELETE FROM university
        WHERE id = source_id;

        COMMIT;
    END
    """

    with mysql_db.begin() as db_conn:
        db_conn.execute(text("DROP PROCEDURE IF EXISTS merge_universities"))
        db_conn.exec_driver_sql(create_sql)


def get_publication_authors_affiliations_db(publication_id: int) -> List[Dict[str, Any]]:
    return query_mysql(
        """
        SELECT DISTINCT
            TRIM(f.name) AS author_name,
            u.name AS affiliation
        FROM faculty AS f, faculty_publication AS fp, university AS u
        WHERE f.id = fp.faculty_id
        AND u.id = f.university_id
        AND fp.publication_id = :publication_id
        ORDER BY TRIM(f.name)
        """,
        {"publication_id": publication_id},
    )


def add_author_affiliations_to_publication(publication: Optional[Dict[str, Any]], publication_id: int) -> Optional[Dict[str, Any]]:
    if not publication:
        return None

    enriched_publication = dict(publication)
    enriched_publication["author_affiliations"] = get_publication_authors_affiliations_db(publication_id)
    return enriched_publication
