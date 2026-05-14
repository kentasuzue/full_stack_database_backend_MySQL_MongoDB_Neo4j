import json
from urllib.parse import quote_plus
# import mysql.connector
from sqlalchemy import create_engine
from pymongo import MongoClient
from neo4j import GraphDatabase

import subprocess

import os
import shutil

def config_db(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)

    mysql_config = config["mysql"]
    password = quote_plus(mysql_config["password"])
    mysql_db = create_engine(
        f"mysql+pymysql://{mysql_config['user']}"
        f":{password}"
        f"@{mysql_config['host']}"
        f":{mysql_config['port']}"
        f"/{mysql_config['database']}"
    )

    mongo_config = config["mongo"]
    uri = f"mongodb://{mongo_config['host']}:{mongo_config['port']}/"
    client = MongoClient(uri)
    mongo_db = client[mongo_config['database']]

    neo4j_config = config["neo4j"]

    uri = f"neo4j://{neo4j_config['host']}"
    auth = (f"{neo4j_config['user']}", f"{neo4j_config['password']}")
    NEO4JDB = neo4j_config['database']
    neo4j_db = GraphDatabase.driver(uri, auth=auth)

    return mysql_db, mongo_db, neo4j_db, NEO4JDB


def backup_mysql(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)

    mysql_config = config["mysql"]

    # password = quote_plus(mysql_config["password"])

    cmd = [
        f"mysqldump",
        "--add-drop-table",
        "--set-gtid-purged=OFF",
        f"-u{mysql_config['user']}",
        f"-p{mysql_config["password"]}",
        f"-h{mysql_config['host']}",
        f"-P {mysql_config['port']}",
        f"{mysql_config['database']}"
    ]

    with open(f"{mysql_config['database']}_backup.sql", "w", encoding="utf-8") as f:
        backup_result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)

    if backup_result.returncode == 0:
        print("MySQL backup successful")
    else:
        print("MySQL backup failed")
        print(backup_result.stderr)


def restore_mysql(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)

    mysql_config = config["mysql"]

    cmd = [
        "mysql",
        f"-u{mysql_config['user']}",
        f"-p{mysql_config['password']}",
        f"-h{mysql_config['host']}",
        f"-P {mysql_config['port']}",
        mysql_config["database"]
    ]

    backup_file = f"{mysql_config['database']}_backup.sql"

    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            restore_result = subprocess.run(
                cmd,
                stdin=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        print("MySQL restore successful")

    except subprocess.CalledProcessError as e:
        print("MySQL restore failed")
        print(e.stderr)


def restore_mysql_safe(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    mysql_config = config["mysql"]
    database = mysql_config["database"]
    temp_database = f"{database}_temp_restore"
    backup_file = f"{database}_backup.sql"

    try:
        # 1. Drop temp DB if it already exists, then create a fresh temp DB
        prepare_temp_cmd = [
            "mysql",
            f"-u{mysql_config['user']}",
            f"-p{mysql_config['password']}",
            f"-h{mysql_config['host']}",
            f"-P {mysql_config['port']}",
            "-e",
            (
                f"DROP DATABASE IF EXISTS `{database}`; "
                f"CREATE DATABASE `{database}`;"
            ),
        ]
        subprocess.run(
            prepare_temp_cmd,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        # 2. Restore backup into temp DB
        restore_temp_cmd = [
            "mysql",
            f"-u{mysql_config['user']}",
            f"-p{mysql_config['password']}",
            f"-h{mysql_config['host']}",
            f"-P {mysql_config['port']}",
            temp_database,
        ]
        with open(backup_file, "r", encoding="utf-8") as backup_f:
            subprocess.run(
                restore_temp_cmd,
                stdin=backup_f,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

        # 3. Replace original DB only after temp restore succeeded
        swap_cmd = [
            "mysql",
            f"-u{mysql_config['user']}",
            f"-p{mysql_config['password']}",
            f"-h{mysql_config['host']}",
            f"-P {mysql_config['port']}",
            "-e",
            (
                f"DROP DATABASE IF EXISTS `{database}`; "
                f"CREATE DATABASE `{database}`;"
            ),
        ]
        subprocess.run(
            swap_cmd,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        # 4. Restore same backup again into the fresh real DB
        restore_real_cmd = [
            "mysql",
            f"-u{mysql_config['user']}",
            f"-p{mysql_config['password']}",
            f"-h{mysql_config['host']}",
            f"-P {mysql_config['port']}",
            database,
        ]
        with open(backup_file, "r", encoding="utf-8") as backup_f:
            subprocess.run(
                restore_real_cmd,
                stdin=backup_f,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

        # 5. Clean up temp DB
        cleanup_cmd = [
            "mysql",
            f"-u{mysql_config['user']}",
            f"-p{mysql_config['password']}",
            f"-h{mysql_config['host']}",
            f"-P {mysql_config['port']}",
            "-e",
            f"DROP DATABASE IF EXISTS `{temp_database}`;",
        ]
        subprocess.run(
            cleanup_cmd,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        print("MySQL safe restore successful")

    except subprocess.CalledProcessError as e:
        print("MySQL safe restore failed")
        print(e.stderr)




def backup_mongodb(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)

    mongo_config = config["mongo"]
    uri = f"mongodb://{mongo_config['host']}:{mongo_config['port']}/"

    cmd = [
        "mongodump",
        f"--uri={uri}",
        f"--db={mongo_config['database']}",
        "--out=mongo_backup/"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("MongoDB backup successful")
    else:
        print("MongoDB backup failed.")
        print(result.stderr)


def restore_mongodb(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)

    mongo_config = config["mongo"]
    uri = f"mongodb://{mongo_config['host']}:{mongo_config['port']}/"

    cmd = [
        "mongorestore",
        f"--uri={uri}",
        f"--db={mongo_config['database']}",
        "--drop",
        f"mongo_backup/{mongo_config['database']}"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("MongoDB restore successful")
    else:
        print("MongoDB restore failed.")
        print(result.stderr)


def backup_neo4j_msg():
    src_db_path = r"C:\Users\kenta\.Neo4jDesktop2\Data\dbmss\dbms-b52580e7-9528-448a-9807-0ebb26a98d59\data\databases\academicworld"
    backup_root = os.path.abspath("neo4j_backup")
    dst_db_path = os.path.join(backup_root, "academicworld")

    try:
        if not os.path.exists(src_db_path):
            print("Source database folder does not exist:")
            print(src_db_path)
            return

        os.makedirs(backup_root, exist_ok=True)

        if os.path.exists(dst_db_path):
            shutil.rmtree(dst_db_path)

        print("Copying database files...")
        shutil.copytree(src_db_path, dst_db_path)

        print("Backup successful")
        print("Saved to:", dst_db_path)

    except Exception as e:
        print("Backup failed")
        print(e)


def restore_neo4j_msg():
    dbms_path = r"C:\Users\kenta\.Neo4jDesktop2\Data\dbmss\dbms-b52580e7-9528-448a-9807-0ebb26a98d59"
    target_db_path = os.path.join(dbms_path, "data", "databases", "academicworld")

    backup_root = os.path.abspath("neo4j_backup")
    backup_db_path = os.path.join(backup_root, "academicworld")

    try:
        if not os.path.exists(backup_db_path):
            print("Backup database folder does not exist:")
            print(backup_db_path)
            return

        # ⚠️ MUST stop Neo4j Desktop DBMS before this
        print("Make sure Neo4j DBMS is STOPPED in Neo4j Desktop before restoring!")

        # Remove existing database
        if os.path.exists(target_db_path):
            print("Removing existing database...")
            shutil.rmtree(target_db_path)

        # Restore from backup
        print("Restoring database files...")
        shutil.copytree(backup_db_path, target_db_path)

        print("Restore successful")
        print("Restored to:", target_db_path)

    except Exception as e:
        print("Restore failed")
        print(e)


if __name__ == "__main__":
    # backup_mysql("config.json")
    # restore_mysql_safe("config.json")
    restore_mysql("config.json")
    # backup_mongodb("config.json")
    # restore_mongodb("config.json")
    # backup_neo4j_msg()
    # restore_neo4j_msg()