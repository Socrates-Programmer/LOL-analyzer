from flask import Blueprint, render_template

bp = Blueprint('match_analyzer', __name__, static_folder='static')


@bp.route('/')
def home():

    return render_template('pages/home.html')

@bp.route('/Analyzer')
def match_analyzer():

    return render_template('pages/analyzer.html', equipo1_prob=55, equipo2_prob=45)