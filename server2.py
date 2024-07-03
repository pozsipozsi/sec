from flask import Flask, request, render_template
from flask_httpauth import HTTPBasicAuth
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.io as pio
import ftfy

app = Flask(__name__)
auth = HTTPBasicAuth()
# Adatbázis kapcsolat adatok
live_db_config = {
    "host": "localhost",
    "user": "ageus",
    "password": "Pfronten0915#1",
    "database": "stube_07_01",
    "port": 3306
}

dev_db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "stube_07_01",
    "port": 3306
}

# Kiválasztott adatbázis kapcsolat
use_live_db = False  # True: LIVE adatbázis, False: DEV adatbázis
selected_db_config = live_db_config if use_live_db else dev_db_config


# Felhasználók és jelszavak
users = {
    "admin": "Pfronten0915",
    "user": "password"
}

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

# Funkció az ékezetes karakterek javítására
def fix_encoding(text):
    return ftfy.fix_text(text)

def get_products():
    conn = mysql.connector.connect(**selected_db_config)

    cursor = conn.cursor()
    query = "SELECT id, name FROM products WHERE status = 1"
    cursor.execute(query)
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    #print(products)
    # Az adatok javítása
    corrected_data = [(id, fix_encoding(text)) for id, text in products]
    # Javított adatok kiírása
    #for item in corrected_data:
        #print(item)
    #return products
    return corrected_data

def get_products_with_categorie_id(id):
    conn = mysql.connector.connect(**selected_db_config)

    cursor = conn.cursor()
    query = f"SELECT id FROM products WHERE status = 1 AND category_id = {id}"
    cursor.execute(query)
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    #print(products)
    # Az adatok javítása
    #corrected_data = [(id, fix_encoding(text)) for id, text in products]
    formatted_data = [str(item[0]) for item in products]
    # Javított adatok kiírása
    #for item in corrected_data:
        #print(item)
    #return products
    return formatted_data

def get_categories():
    conn = mysql.connector.connect(**selected_db_config)

    cursor = conn.cursor()
    query = "SELECT id, name FROM products_category"
    cursor.execute(query)
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    #print(products)
    # Az adatok javítása
    corrected_data = [(id, fix_encoding(text)) for id, text in categories]
    # Javított adatok kiírása
    for item in corrected_data:
        print(item)
    #return products
    return corrected_data

def get_users(id):
    conn = mysql.connector.connect(**selected_db_config)

    cursor = conn.cursor()
    query = f"SELECT id, name FROM users WHERE status = 1 AND id = {id}"
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    #print(products)
    # Az adatok javítása
    corrected_data = [(id, fix_encoding(text)) for id, text in users]
    # Javított adatok kiírása
    for item in corrected_data:
        print(item)
    #return products
    return corrected_data

def get_data(filters):
    conn = mysql.connector.connect(**selected_db_config)

    cursor = conn.cursor()

    query = "SELECT * FROM order_items WHERE 1=1"
    for key, value in filters.items():
        if value:
            if key in ['date_from', 'date_to']:
                continue
            if key in ['date', 'start_date', 'end_date', 'modify_date']:
                query += f" AND {key} = '{value}'"
            else:
                query += f" AND {key} = {value}"
    
    if filters.get('date_from') and filters.get('date_to'):
        date_from = filters['date_from']
        date_to = filters['date_to'] + " 23:59:59.999999"
        query += f" AND date BETWEEN '{date_from}' AND '{date_to}'"

    cursor.execute(query)
    results = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(results, columns=columns)

    cursor.close()
    conn.close()

    df['date'] = pd.to_datetime(df['date'])

    return df

def get_gratuity_sum(date_from, date_to, state):
    conn = mysql.connector.connect(**selected_db_config)

    cursor = conn.cursor()
    query = ("SELECT SUM(price_sum_gratuity) FROM orders "
             "WHERE date_last BETWEEN %s AND %s AND state = %s")
    cursor.execute(query, (date_from, date_to, state))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result[0] if result[0] is not None else 0

def grup_gratuity_sum(date_from, date_to, state):
    conn = mysql.connector.connect(**selected_db_config)
    cursor = conn.cursor()
    query = ("""
        SELECT * FROM orders WHERE date_last BETWEEN %s AND %s AND state = %s
    """)
    cursor.execute(query, (date_from, date_to, state))
    result = cursor.fetchall()
    print(result)
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result, columns=columns)
    cursor.close()
    conn.close()
    print(df)

    return df

def grup_gratuity_sum_11(date_from, date_to, state):
    conn = mysql.connector.connect(**selected_db_config)
    cursor = conn.cursor()
    query = ("""
        SELECT * FROM orders WHERE date_last BETWEEN %s AND %s AND state = %s
    """)
    cursor.execute(query, (date_from, date_to, state))
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result, columns=columns)
    cursor.close()
    conn.close()

    # Summing the price_sum_gratuity column for the total
    total = df['price_sum_gratuity'].sum()

    # Grouping by users_id and summing the price_sum_gratuity for each user
    user_grouped_sum = df.groupby('users_id')['price_sum_gratuity'].sum().reset_index()

    # Renaming columns for clarity
    user_grouped_sum.columns = ['user_id', 'total_gratuity_sum']

    # Replacing user_id with user names
    user_grouped_sum['user_name'] = user_grouped_sum['user_id'].apply(get_users)
    user_grouped_sum = user_grouped_sum[['user_name', 'total_gratuity_sum']]

    # Converting DataFrame to list of dictionaries
    user_grouped_sum_list = user_grouped_sum.to_dict('records')

    result = {
        "total": total,
        "user_grouped_sum": user_grouped_sum_list
    }

    return result

def grup_gratuity_sum_12_14(date_from, date_to):
    conn = mysql.connector.connect(**selected_db_config)
    cursor = conn.cursor()
    query = ("""
        SELECT * FROM orders WHERE date_last BETWEEN %s AND %s AND (state = 12 OR state = 14)
    """)
    cursor.execute(query, (date_from, date_to))
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result, columns=columns)
    cursor.close()
    conn.close()

    # Summing the price_sum_gratuity column for the total
    total = df['price_sum_gratuity'].sum()

    # Grouping by users_id and summing the price_sum_gratuity for each user
    user_grouped_sum = df.groupby('courier_id')['price_sum_gratuity'].sum().reset_index()

    # Renaming columns for clarity
    user_grouped_sum.columns = ['courier_id', 'total_gratuity_sum']

    # Replacing courier_id with user names 
    user_grouped_sum['courier_name'] = user_grouped_sum['courier_id'].apply(get_users)
    user_grouped_sum = user_grouped_sum[['courier_name', 'total_gratuity_sum']]

    # Converting DataFrame to list of dictionaries
    user_grouped_sum_list = user_grouped_sum.to_dict('records')


    result = {
        "total": total,
        "user_grouped_sum": user_grouped_sum_list
    }

    return result

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():
    products = get_products()
    categories = get_categories()
    product_results = []

    if request.method == 'POST':
        categories_id = request.form.getlist('categories_id')
        product_id = request.form.get('products_id')
        print(categories_id)
        if categories_id:
            selected_products = get_products_with_categorie_id(categories_id[0])
            #selected_products = request.form.getlist('products_id')
        else:
            selected_products = product_id
        print(selected_products)
        #['1331', '1332', '1337', '1340']
        #[(1331,), (1332,), (1333,), (1334,)]
        
        filters = {
            'status': request.form.get('status'),
            'quantity': request.form.get('quantity'),
            'date': request.form.get('date'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'price': request.form.get('price'),
            'discount_price': request.form.get('discount_price'),
            'prepare_state': request.form.get('prepare_state'),
            'paid_num': request.form.get('paid_num'),
            'modify_date': request.form.get('modify_date'),
            'quantity_new': request.form.get('quantity_new'),
            'half': request.form.get('half'),
            'food_order_num': request.form.get('food_order_num'),
            'print_on_cooklist': request.form.get('print_on_cooklist'),
            'restaurant_id': request.form.get('restaurant_id'),
            'auto_cooklist_print': request.form.get('auto_cooklist_print'),
            'waste_user_id': request.form.get('waste_user_id'),
            'waste_comment': request.form.get('waste_comment'),
            'date_from': request.form.get('date_from'),
            'date_to': request.form.get('date_to')
        }

        for product_id in selected_products:
            product_name = next((p[1] for p in products if str(p[0]) == product_id), "")
            filters['products_id'] = product_id

            df = get_data(filters)

            df['quantity'] = df['quantity'].astype(int)
            total_quantity = df['quantity'].sum()
            
            # Biztosítjuk, hogy a 'date' oszlop datetime formátumban legyen
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            aggregated_df = df.groupby('date')[['quantity']].sum().reset_index()

            # Dinamikusan beállítjuk a chart magasságát
            bar_height = 40  # Az oszlopok magassága pixelben
            chart_height = max(800, bar_height * len(aggregated_df))

            # Horizontális chart
            fig = px.bar(aggregated_df, x='quantity', y='date', orientation='h', title=f'{product_name} eladásai napi bontásban')
            fig.update_layout(
                xaxis_title='Eladott mennyiség',
                yaxis_title='Dátum',
                height=chart_height  # Beállítjuk a dinamikus magasságot
            )

            # Dátumok mm-dd formátumra állítása
            aggregated_df['date_str'] = pd.to_datetime(aggregated_df['date']).dt.strftime('%m-%d')
            fig.update_yaxes(
                tickmode='array',
                tickvals=aggregated_df['date'],
                ticktext=aggregated_df['date_str']
            )

            fig.update_traces(texttemplate='%{x}', textposition='outside')  # Az értékek megjelenítése az oszlopok végén

            graph_html = pio.to_html(fig, full_html=False)

            # Vertikális chart
            fig2 = px.bar(aggregated_df, x='date', y='quantity', orientation='v', title=f'{product_name} eladásai napi bontásban')
            fig2.update_layout(
                xaxis_title='Dátum',
                yaxis_title='Eladott mennyiség',
                height=chart_height  # Beállítjuk a dinamikus magasságot
            )

            # Dátumok mm-dd formátumra állítása
            fig2.update_xaxes(
                tickmode='array',
                tickvals=aggregated_df['date'],
                ticktext=aggregated_df['date_str']
            )

            fig2.update_traces(texttemplate='%{y}', textposition='outside')  # Az értékek megjelenítése az oszlopok végén

            graph_html_2 = pio.to_html(fig2, full_html=False)

            product_results.append({
                'name': product_name,
                'total_quantity': total_quantity,
                'graph_html_h': graph_html,
                'graph_html_v': graph_html_2
            })

        return render_template('index.html', products=products, categories=categories, product_results=product_results)

    return render_template('index.html', products=products, categories=categories)

@app.route('/gratuity_sum', methods=['GET', 'POST'])
@auth.login_required
def gratuity_sum():
    gratuity_total = 0
    if request.method == 'POST':
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to') + " 23:59:59.999999"
        time_now = pd.Timestamp.now()
        if pd.Timestamp(date_to) > time_now:
            date_to = str(time_now)
        #state = request.form.get('state')
        state = '11'
        gratuity_11 = get_gratuity_sum(date_from, date_to, state)
        gratuity_12 = get_gratuity_sum(date_from, date_to, '12')
        gratuity_14 = get_gratuity_sum(date_from, date_to, '14')
        gratuity_12_14_sum = gratuity_12 + gratuity_14
        gratuity_12_14_11_sum = gratuity_11 + gratuity_12 + gratuity_14
        gratuity_total = get_gratuity_sum(date_from, date_to, state)
        list = grup_gratuity_sum_11(date_from, date_to, state)
        list2 = grup_gratuity_sum_12_14(date_from, date_to)
        #users = get_users(4021)
    elif request.method == 'GET':
        #date_from = '2024-06-27'
        date_from = pd.Timestamp.now().strftime('%Y-%m-%d')
        #date_to = '2024-06-27 23:59:59.999999'
        date_to = pd.Timestamp.now()
        state = '11'
        gratuity_11 = get_gratuity_sum(date_from, date_to, state)
        gratuity_12 = get_gratuity_sum(date_from, date_to, '12')
        gratuity_14 = get_gratuity_sum(date_from, date_to, '14')
        gratuity_12_14_sum = gratuity_12 + gratuity_14
        gratuity_12_14_11_sum = gratuity_11 + gratuity_12 + gratuity_14
        
        list = grup_gratuity_sum_11(date_from, date_to, state)
        list2 = grup_gratuity_sum_12_14(date_from, date_to)
        #users = get_users(4021)
        
    return render_template(
        'gratuity_sum.html', 
        gratuity_11=gratuity_11, 
        gratuity_12=gratuity_12, 
        gratuity_14=gratuity_14, 
        gratuity_12_14_sum=gratuity_12_14_sum, 
        gratuity_12_14_11_sum=gratuity_12_14_11_sum, 
        gratuity_total=gratuity_total, 
        list_11=list, 
        list_12_14=list2,
        date_from=date_from,
        date_to=date_to, 
        #users=users
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
