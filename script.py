from app import app, db, Topic

if __name__ != '__main__':
    exit()

def delete_row(keyword=""):
    with app.app_context(): # Butuh konteks aplikasi untuk akses database
        query = db.select(Topic)
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(Topic.title.ilike(search_term))
            # delete the rows
            row = db.session.execute(query).first()[0]
            db.session.delete(row)
        else:         
            rows = db.session.execute(query)
            for row in rows:
                row = row[0]
                db.session.delete(row)
    
        db.session.commit()
        print("Done")

delete_row()
