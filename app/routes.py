from flask import Blueprint, render_template, request, redirect, flash, current_app
import os

bp = Blueprint('match_analyzer', __name__, static_folder='static')


@bp.route('/')
def home():

    return render_template('pages/home.html')

@bp.route('/Analyzer')
def match_analyzer():
    db = current_app.db
    invocadores_raw = list(db.invocadores.find())
    
    # Convertir _id a string para evitar problemas en plantilla
    invocadores = []
    for i in invocadores_raw:
        i['_id'] = str(i['_id'])
        invocadores.append(i)
    
    print("Jugadores desde DB:", invocadores)
    return render_template('pages/analyzer.html',
                        invocadores=invocadores,
                        equipo1_prob=55,
                        equipo2_prob=45)




@bp.route('/summoner', methods=["GET", "POST"])
def summoner():
    if request.method == "POST":
        summoner_name = request.form.get("summonerName")
        tagline = request.form.get("tagline")
        password = request.form.get("password")

        if password != os.getenv("PASS"):
            flash("❌ Contraseña incorrecta", "danger")
            return redirect("/summoner")

        db = current_app.db
        invocadores = db.invocadores

        invocadores.insert_one({
            "summoner_name": summoner_name,
            "tagline": tagline
        })

        flash(f"✅ {summoner_name}#{tagline} guardado correctamente", "success")
        return redirect("/summoner")

    return render_template('pages/summoner.html')

@bp.route('/summoner/list')
def summoner_list():
    db = current_app.db
    invocadores = db.invocadores.find()

    return render_template('pages/all_summoners.html', invocadores=invocadores)