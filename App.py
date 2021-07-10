from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
import numpy as np
import json

setup = False
app = Flask(__name__)   
app.secret_key = "flash message"
app.config['MYSQL_HOST'] = '*******'
app.config['MYSQL_USER'] = '******'
app.config['MYSQL_PASSWORD'] = '****'
app.config['MYSQL_DB'] = '********'
mysql = MySQL(app)

# ====================================================
def get_valFromDB(dbVarStr, dbName="train_schedule",condi=None):
    cur = mysql.connection.cursor()
    sql ="SELECT "+dbVarStr+" FROM "+dbName
    if condi is not None:
        sql = "SELECT "+dbVarStr+" FROM "+dbName+" WHERE "+condi
    cur.execute(sql)
    data = cur.fetchall()
    if len(data)==1:
        lst = [np.squeeze(data).tolist()]
    else:
        lst = list(set(np.squeeze(data)))
        
    cur.close()
    return lst

# ====================================================

@app.route('/')
def Index():
    # --------
    # 1. load Booking list
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM booking")
    data01 = cur.fetchall()
    # 2. load train schedule
    cur.execute("SELECT * FROM train_schedule")
    data02 = cur.fetchall()
    cur.close()
    return render_template('index.html', booking = data01, train_shedule = data02 )

# ----------------------------------------------
# Insert
# ----------------------------------------------

@app.route('/insert',methods = ['POST'])
def insert():
    if request.method == "POST":
        flash("Data Insert Successfully")
        
        name = request.form['name']
        date = request.form['date']
        trainid = request.form['trainid']
        start = request.form['startStat']
        end = request.form['endStat']
        amount = request.form['amount']
        total = request.form['total']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM booking" )
        data = cur.fetchone()
        maxIdx = data[0] +1
        mysql.connection.commit()
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO booking (booking.index, Name , Date , TrainID ,StatStart , StatEnd ,amount, Fare ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",(maxIdx, name,date,trainid,start,end,amount, total))
        mysql.connection.commit()
        
        return redirect(url_for('Index'))

# ----------------------------------------------
# Update
# ----------------------------------------------

@app.route('/update',methods = ['POST','GET'])      
def update():
    if request.method == "POST":
        data = request.form.to_dict()
        orderID = data['id']
        name = data['name']
        date = data['date']
        trainid = data['trainid']
        start = data['startStat']
        end = data['endStat']
        amount = data['amount']
        #fare = data['total']
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE booking SET Name=%s, Date=%s, TrainID=%s, StatStart=%s, StatEnd=%s, amount=%s WHERE booking.index=%s ",(name,date,trainid,start,end,amount,orderID))
        flash("Data Update Successfully")
        mysql.connection.commit()
        return redirect(url_for('Index'))
    
# ----------------------------------------------
# Delete
# ----------------------------------------------
@app.route('/delete/<string:id>',methods = ['POST','GET'])
def delete(id):
    flash("Data Delete Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM booking WHERE booking.index =%s", (id,))
    mysql.connection.commit()
    return redirect(url_for('Index'))

# ----------------------------------------------
# Query options
# ----------------------------------------------
@app.route('/updateDrop/dateSele')
def update_seleDate():
    # 0. info from user 
    sele_date = request.args.get('date', type=str)
    
    # ===================================
    # 1. DB Query 
    sqlCondi = "Date = '"+sele_date+"'"
    stStat = get_valFromDB("Origin", "train_schedule", sqlCondi)
    # -----------------------------------
    # 2. Options HTML 
    startStat_html='<option value=" "></option>'  
    for entry in stStat:
        startStat_html += '<option value="{}">{}</option>'.format(entry, entry)
    # ====================================    
    return jsonify(start_opt = startStat_html)


@app.route('/updateDrop/startSele')
def update_seleStartStat():
    # 0. info from user 
    sele_date = request.args.get('date', type=str)
    sele_start = request.args.get('sele_start', type=str)
    # ===================================
    # 1. DB Query
    sqlCondi = "Date = '"+sele_date+"' AND Origin = '"+sele_start+"'"
    stEnd = get_valFromDB("Destination", "train_schedule", sqlCondi)
    # -----------------------------------
    # 2. Options HTML 
    endStat_html = '<option value=" "></option>'
    for entry in stEnd:
        endStat_html += '<option value="{}">{}</option>'.format(entry, entry)
    # ==================================== 
    return jsonify(end_opt = endStat_html) #, train_selected = trainId_html, amountAllow = amount_html) #

@app.route('/updateDrop/endSele')
def update_seleEndStat():
    # 0. info from user 
    sele_date = request.args.get('date', type=str)
    sele_start = request.args.get('sele_start', type=str)
    sele_end = request.args.get('sele_end', type=str)
    # ===================================
    # 1. DB Query
    sqlCondi = "Date = '"+sele_date+"' AND Origin = '"+sele_start+"' AND Destination = '"+sele_end+"'"
    TrainIDs = get_valFromDB("TrainID", "train_schedule", sqlCondi)
    # -----------------------------------
    # 2. Options HTML
    train_html = '<option value=" "></option>' 
    for entry in TrainIDs:
        train_html += '<option value="{}">{}</option>'.format(entry, entry)  
    # =====================================
    return jsonify(train_opt = train_html) # , amountAllow= amount_html) #

@app.route('/updateDrop/trainSele')
def update_seleTrainId():
    # ====== update amount and price
    # 0. Infos from user 
    sele_date = request.args.get('date', type=str)
    sele_start = request.args.get('sele_start', type=str)
    sele_end = request.args.get('sele_end', type=str)
    sele_trainid = request.args.get('trainid', type=str)
    sele_amount = request.args.get('amount', type=str)
    sele_amount = int(sele_amount) if sele_amount is not None else 1
    # ====== 2. Query DB for seats ============
    sqlCondi_01 = "Date = '"+sele_date+"' AND Origin = '"+sele_start+"' AND Destination = '"+sele_end+"' AND TrainID='"+sele_trainid+"'"
    seats_lf = get_valFromDB("Seats", "train_schedule", sqlCondi_01)[0]
    
    sqlCondi_02 = "Date = '"+sele_date+"' AND TrainID ='"+sele_trainid+"' AND StatStart = '"+sele_start+"' AND StatEnd ='"+sele_end+"'"
    cur = mysql.connection.cursor()
    cur.execute("SELECT SUM(Amount) FROM BOOKING WHERE "+sqlCondi_02)
    
    booking_data = cur.fetchone()[0]
    booking_data = booking_data if booking_data is not None else 0
    mysql.connection.commit()
    
    max_amount = 0
    ava_amount =0
    if  seats_lf is not None:
        max_amount = max(seats_lf-booking_data, 0)
        ava_amount = min(int(sele_amount), max_amount)
    print(seats_lf, ava_amount, booking_data, sele_amount)
    # ===== 3. Compute for Price ==========
    all_stations = ['台北','台中','台南','左營']
    farePerStat = 50
    distance = abs(all_stations.index(sele_start) - all_stations.index(sele_end))
    price = max(distance*ava_amount*farePerStat, 0 )
    # =====================================
    return jsonify(amount_limit ="{}".format(max_amount), price_show="{}".format(price))

@app.route('/updateDrop/amountSele')
def update_seleAmount():
    # select
    sele_date = request.args.get('date', type=str)
    sele_trainid = request.args.get('trainid', type=str)
    sele_start = request.args.get('sele_start', type=str)
    sele_end = request.args.get('sele_end', type=str)
    sele_amount = request.args.get('amount', type=str)
    sele_amount = int(sele_amount) if sele_amount is not None else 1
    #===================================================
    sqlCondi_01 = "Date = '"+sele_date+"' AND Origin = '"+sele_start+"' AND Destination = '"+sele_end+"' AND TrainID='"+sele_trainid+"'"
    seats_lf = get_valFromDB("Seats", "train_schedule", sqlCondi_01)[0]

    sqlCondi_02 = "Date = '"+sele_date+"' AND TrainID ='"+sele_trainid+"' AND StatStart = '"+sele_start+"' AND StatEnd ='"+sele_end+"'"
    cur = mysql.connection.cursor()
    cur.execute("SELECT SUM(Amount) FROM BOOKING WHERE "+sqlCondi_02)

    booking_data = cur.fetchone()[0]
    booking_data = booking_data if booking_data is not None else 0
    mysql.connection.commit()

    max_amount = 0
    ava_amount =0
    if  seats_lf is not None:
        max_amount = max(seats_lf-booking_data, 0)
        ava_amount = min(int(sele_amount), max_amount)
    
    #===================================================
    all_stations = ['台北','台中','台南','左營']
    farePerStat = 50
    distance = abs(all_stations.index(sele_start) - all_stations.index(sele_end))
    price = max(distance*ava_amount*farePerStat, 0 )
    
    return jsonify(price_show="{}".format(price))

if __name__ == '__main__':
    app.run(debug=True)
