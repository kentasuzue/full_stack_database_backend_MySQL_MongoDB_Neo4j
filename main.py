from app import app
from ui import layout

import db
import api
import callbacks


# initialize stored procedures
db.add_university_procedure()
db.merge_university_procedure()

app.layout = layout

if __name__ == "__main__":
    app.run(debug=True)