from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy.exc import IntegrityError
df = pd.read_csv(r'temp_questions.csv')

app = Flask(__name__, template_folder=r'templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'
db = SQLAlchemy(app)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(80), nullable=False)
    number = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    isbn = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint('section', 'number', name='_section_number_uc'),)
    
# with app.app_context():
#     db.create_all()
#     for index,row in df.iterrows():
#         question = Question(page=row['page'], section=row['section'], number=row['qnumb'], content=row['question'])
#         db.session.add(question)
#         db.session.commit()


# with app.app_context():
#     db.drop_all()
    
with app.app_context():
   db.create_all()  
   for index, row in df.iterrows():
       # Check if entry already exists
       existing_question = Question.query.filter_by(section=row['section'], number=row['qnumb']).first()
       if not existing_question:
           question = Question(page=row['page'], section=row['section'], number=row['qnumb'], content=row['question'],isbn=row['isbn'])
           db.session.add(question)
           try:
               db.session.commit()
           except IntegrityError:
               db.session.rollback()
               print(f"Duplicate entry found for section {row['section']} and question number {row['qnumb']}. Skipping...")       

from flask import render_template

@app.route('/')
def index():
    questions = Question.query.all()
    return render_template('index.html', questions=questions)

if __name__ == "__main__":
    app.run(debug=True,use_reloader=False)