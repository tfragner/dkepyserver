from app import app, db
from app.models import User, Sparql, Parameter


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Sparql': Sparql, 'Parameter': Parameter}
