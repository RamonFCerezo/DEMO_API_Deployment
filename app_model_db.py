from flask import Flask, request, jsonify
import os
import pickle
from sklearn.model_selection import cross_val_score
import pandas as pd
import sqlite3


os.chdir(os.path.dirname(__file__))

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route("/", methods=['GET'])
def hello():
    return "Bienvenido a mi API del modelo advertising"

# 1. Endpoint que devuelva la predicción de los nuevos datos enviados mediante argumentos en la llamada
@app.route('/v1/predict', methods=['GET'])
def predict():
    model = pickle.load(open('advertising_model','rb'))

    tv = request.args.get('tv', None)
    radio = request.args.get('radio', None)
    newspaper = request.args.get('newspaper', None)

    if tv is None or radio is None or newspaper is None:
        return "Missing args, the input values are needed to predict"
    else:
        prediction = model.predict([[tv,radio,newspaper]])
        return "The prediction of sales investing that amount of money in TV, radio and newspaper is: " + str(round(prediction[0],2)) + 'k €'


# 2. Un endpoint para almacenar nuevos registros en la base de datos que deberá estar previamente creada.

@app.route('/v1/ingest_data', methods=['POST', 'GET'])
def new_data():
    request.method = 'POST'
    if request.method == 'POST' and 'tv' in request.args and 'radio' in request.args and 'newspaper' in request.args and 'sales' in request.args:
        connection = sqlite3.connect('vent.db')
        crsr = connection.cursor()
        radio = float(request.args['radio'])
        tv = float(request.args['tv'])
        newspaper = float(request.args['newspaper'])
        sales = float(request.args['sales'])
        query = '''INSERT INTO VENTAS (TV, radio, newspaper, sales)
                   VALUES (?,?,?,?)'''
        response = '''SELECT * FROM VENTAS ORDER BY id DESC LIMIT 5'''
        result = crsr.execute(query, (tv, radio, newspaper, sales)).fetchall()
        result2 = crsr.execute(response).fetchall()
        connection.commit()
        connection.close()
        return jsonify(result2)
    else:
        return "Nothing new added to the database" + request.method

# 3. Posibilidad de reentrenar de nuevo el modelo con los posibles nuevos registros que se recojan.

@app.route('/v2/retrain', methods=['POST', 'GET'])

def retrain():
    if request.method == 'POST':
        model = pickle.load(open('advertising_model','rb'))
        connection = sqlite3.connect("vent.db")
        crsr = connection.cursor()
        query = '''SELECT * FROM VENTAS'''
        crsr.execute(query)
        ans = crsr.fetchall()
        names = [description[0] for description in crsr.description]
        X = pd.DataFrame(ans,columns=names)
        X_train = X[['TV', 'radio', 'newspaper']]
        y_train = X['sales']
        model.fit(X_train, y_train)
        with open("advertising_model", "wb") as f:
            pickle.dump(model, f)
        connection.close()
        return "<b>Model updated with new data<b>"

# app.run()