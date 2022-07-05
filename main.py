
import datetime
import random

from flask import Flask, render_template, request, redirect,flash
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token


app = Flask(__name__)
app.secret_key = "Yetunde"
datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()


@app.route('/')
def root():
    _data = {}
    _data = fetch_ev()
    return render_template('index.html', data= _data)

@app.route('/add_ev', methods=['POST'])
def addEv():
    id_token = request.cookies.get("token")
    
    if id_token:
        try:
            if not check_if_ev_exist(request.form.get('manufacturer').lower(),request.form.get('evname').lower(),int(request.form.get('year'))):
             
                createEv(request.form.get('manufacturer').lower(), request.form.get('evname').lower(), request.form.get('batterysize'), request.form.get('powerrating'),
            request.form.get('year'), request.form.get('wltprange'), request.form.get('cost'))
            else:
             
                flash("EV with same manufacturer, vehicle name and year exist in datastore")
        except ValueError as exc:
             error_message = str(exc)
    return redirect('/')

def check_if_ev_exist(m,n,y):
    query = datastore_client.query(kind='EV')   
    query.add_filter('manufacturer', '=', m)
    query.add_filter('evname', '=', n)
    query.add_filter('year', '=', y)
    check_ev = query.fetch()
    if list(check_ev): return True
    else: return False

@app.route('/listing')
def listing():    
    return render_template('listing.html' ,data= fetch_ev())

@app.route('/update', methods=['POST'])
def update():  
    _data=retrieveUpdate(request.form)
    reviewdata = retrieveComment_byId(request.form.get(id))
    return render_template('details.html', data=_data ,commentdata = reviewdata['comments'], average_rating = reviewdata['avg'])

@app.route('/filter', methods=['POST'])
def filter():
 
    result = []    
    list_of_ids = []
    set_of_ids = set()
    manufacturer=request.form.get('manufacturer').lower()
    evname=request.form.get('evname').lower()
    batterymin=request.form.get('batterymin')
    batterymax=request.form.get('batterymax')
    powermin=request.form.get('powermin')
    powermax=request.form.get('powermax')
    wltpmin=request.form.get('wltpmin')
    wltpmax=request.form.get('wltpmax')
    costmin=request.form.get('costmin')
    costmax=request.form.get('costmax')
    yearmin=request.form.get('yearmin')
    yearmax=request.form.get('yearmax')

    # get data id from store
    if manufacturer:
        list_of_ids.append(get_searched_ev_ids('manufacturer',manufacturer))

    if evname:
        list_of_ids.append(get_searched_ev_ids('evname', evname))

    if batterymin:

        list_of_ids.append(get_searched_ev_ids_by_range('batterysize', float(batterymin), float(batterymax)))

    if costmin:

        list_of_ids.append(get_searched_ev_ids_by_range('cost', float(costmin), float(costmax)))

    if yearmin:

        list_of_ids.append(get_searched_ev_ids_by_range('year', int(yearmin), int(yearmax)))

    if powermin:

        list_of_ids.append(get_searched_ev_ids_by_range('powerrating', float(powermin), float(powermax)))

    if wltpmin:

        list_of_ids.append(get_searched_ev_ids_by_range('wltprange', float(wltpmin), float(wltpmax)))


    # join all the id data with interception
    x = 0
    for lst in list_of_ids:
        if x == 0:
            set_of_ids = lst
        else:
            set_of_ids = set_of_ids.intersection(lst)
        x = x + 1

    # loop through the id data and get details. Save the result in a list and send it to the view   
    for id in set_of_ids:
        result.append(retrieveEv_byId(id))
  
    if (manufacturer == "" and evname == "" and batterymin == "" and batterymax == "" and costmin == "" 
    and costmax == ""and yearmin == "" and yearmax == "" and powermin == "" and powermax == "" and wltpmin == ""and wltpmax == ""):
       
        result=fetch_ev()
    
 
    return render_template('listing.html' ,data= result)

@app.route('/search', methods=['POST'])
def search():
    result = None
    search=request.form.get('search').lower()
    
    # get data id from store
    if search:       
        query = datastore_client.query(kind='EV')
        query.add_filter('manufacturer', '=', search)
        _data = query.fetch()
        result = _data
        
        if not result:
            query = datastore_client.query(kind='EV')
            query.add_filter('evname', '=', search)
            result = query.fetch()
    
    else:
        result = fetch_ev()
    
    return render_template('listing.html' ,data = result)


def get_searched_ev_ids(col, searchword):
    data = set()
    query = datastore_client.query(kind='EV')
    query.add_filter(col, '=', searchword)
    results = query.fetch()
    for result in results:
        data.add(result['evid'])
    return data

def get_searched_ev_ids_by_range(col,min, max):
    data = set()
    query = datastore_client.query(kind='EV')
    query.add_filter(col, '>=', min)
    query.add_filter(col, '<=', max)
    results = query.fetch()
    for result in results:
        data.add(result['evid'])
    return data

def retrieveUpdate(data):
        entity_key = datastore_client.key('EV', int(data['id']))
        entity = datastore.Entity(key = entity_key)
        if not check_if_ev_exist(data['manufacturer'].lower(),data['evname'].lower(),int(data['year'])):
            entity.update({
            'evid':data['id'],
            'manufacturer': data['manufacturer'].lower(),
            'evname': data['evname'].lower(),
            'batterysize': float(data['batterysize']),
            'powerrating': float(data['powerrating']),
            'year': int(data['year']),
            'wltprange': float(data['wltprange']),
            'cost':  float(data['cost']),
            'date': datetime.datetime.now()
            })   
            datastore_client.put(entity)
        else:
                
            flash("EV with same manufacturer, vehicle name and year exist in datastore")

        return retrieveEv_byId(data['id'])

@app.route('/add')
def add():
    return render_template('add.html')


@app.route('/compare')
def compare():
    return render_template('compare.html', data = fetch_ev())


@app.route('/compare_view', methods = ['POST'])
def compare_view():
    ids = request.form.getlist('evid')
    data = []
    # _temp_rating = []
    _data_temp = []

    maxCost = 0
    minCost = 0
    maxPower = 0
    minPower = 0
    minYear=0
    maxYear=0
    minBattery=0
    maxBattery=0
    minWltp=0
    maxWltp=0
    minAvg=0
    maxAvg=0

    
    if len(ids) < 2:
        flash("Comparison requires at least two EVs")
        return render_template('compare.html', data = fetch_ev())

    for id in ids:
        review_avg = retrieveComment_byId(id)['avg']
        _raw_data = retrieveEv_byId(id)
        _raw_data['avg'] = review_avg
        _data_temp.append(_raw_data)

    rev_query = datastore_client.query(kind = 'Evcomments')
    review_query = rev_query.add_filter('evid', '=', id)
    rev = review_query.fetch()
    
    # get max and min values
    for item in _data_temp:
        cost = float(item.get('cost'))
        if cost > maxCost:
            maxCost = cost
        if cost < minCost or minCost == 0:
            minCost = cost

        power = float(item.get('powerrating'))
        if power > maxPower:
            maxPower = power
        if power < minPower or minPower == 0:
            minPower = power

        battery = float(item.get('batterysize'))
        if battery > maxBattery:
            maxBattery = battery
        if battery < minBattery or minBattery == 0:
            minBattery = battery

        year = int(item.get('year'))
        if year > maxYear:
            maxYear = year
        if year < minYear or minYear == 0:
            minYear = year
        
        wltp = float(item.get('wltprange'))
        if wltp > maxWltp:
            maxWltp = wltp
        if wltp < minWltp or minWltp == 0:
            minWltp = wltp
        
        rating = float(item.get('avg'))
        if rating > maxAvg:
            maxAvg = rating
        if rating < minAvg or minAvg == 0:
            minAvg = rating

    for item in _data_temp:
        _temp_item = item
      
        color = ""
        cost = float(item.get('cost'))
        if cost == maxCost:
            color = "min"
        elif cost == minCost:
            color = "max"
        _temp_item['costColor'] = color

        color = ""
        power = float(item.get('powerrating'))
        if power == maxPower:
            color = "max"
        elif power == minPower:
            color = "min"
        _temp_item['powerColor'] = color


        color = ""
        battery = float(item.get('batterysize'))
        if battery == maxBattery:
            color = "max"
        elif battery == minBattery:
            color = "min"
        _temp_item['batteryColor'] = color

        color = ""
        year = int(item.get('year'))
        if year == maxYear:
            color = "max"
        elif year == minYear:
            color = "min"
        _temp_item['yearColor'] = color

        color = ""
        wltp = float(item.get('wltprange'))
        if wltp == maxWltp:
            color = "max"
        elif wltp == minWltp:
            color = "min"
        _temp_item['wltpColor'] = color

        color = ""
        rating = float(item.get('avg'))
        if rating == maxAvg:
            color = "max"
        elif rating == minAvg:
            color = "min"
        _temp_item['avgColor'] = color
        _temp_item['avg'] = rating


        data.append(_temp_item)

    return render_template('compare_view.html', data = data)

@app.route('/delete/<id>')
def delete(id):
    deleteEv(id)
    return redirect('/')

@app.route('/detail/<id>')
def detail(id):
    
    _data=retrieveEv_byId(id)
    review = retrieveComment_byId(id)
    return render_template('details.html', data=_data, commentdata = review['comments'], average_rating = review['avg'])

@app.route('/comment', methods=['POST'])
def comment():
    data = request.form
    id = random.getrandbits(63)
    entity_key = datastore_client.key('EVcomments', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({     
        'evreview': data.get('evreview'),
        'evrating': data.get('evrating'),
        'evid': data.get('evid'),
        'date': datetime.datetime.now()
    })
    datastore_client.put(entity)
    review = retrieveComment_byId(data.get('evid'))
    return render_template('details.html', data= retrieveEv_byId(data.get('evid')), 
    commentdata = review['comments'], average_rating=review['avg'])


def createEv(manufacturer, evname, batterysize, powerrating, year, wltprange, cost):
 # 63 bit random number that will serve as the key for the entity.
    id = random.getrandbits(63)
    entity_key = datastore_client.key('EV', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({     
        'evid': id,
        'manufacturer': manufacturer,
        'evname': evname,
        'batterysize': float(batterysize),
        'powerrating': float(powerrating),
        'year': int(year),
        'wltprange': float(wltprange),
        'cost':  float(cost),
        'date': datetime.datetime.now()
    })
    datastore_client.put(entity)
    return id

def deleteEv(id):
    entity_key = datastore_client.key('EV', int(id))
    datastore_client.delete(entity_key)
  

def fetch_ev():
    query = datastore_client.query(kind='EV')
    query.order = ['-date']
    data = query.fetch()
    return data

def  retrieveEv_byId(id):
    query_key = datastore_client.key('EV',int(id))
    data = datastore_client.get(query_key)
    return data

def  retrieveComment_byId(id):
    comments = []
    data = None
    result = None
    
    query = datastore_client.query(kind='EVcomments')
    query.add_filter('evid', '=', id)
    result = query.fetch()
    sum = 0
    count = 0
    avg = 0

    for x in result:
        
        comments.append(x)
        sum = sum + float(x['evrating'])
        count = count + 1
    if sum > 0 :
        avg = sum/count
        
    data = {'comments':comments, 'avg':"{:.2f}".format(avg)}
    return data




if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
