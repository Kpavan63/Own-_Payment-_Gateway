from flask import Flask, request, jsonify, send_file, Response
from flask_mysqldb import MySQL
from flask_cors import CORS
import qrcode
import io
import requests
import time
import threading

app = Flask(__name__)
CORS(app)  # Enable CORS

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'veg-order'

mysql = MySQL(app)

TELEGRAM_BOT_TOKEN = '7433779583:AAG_oeR7L8FB3cgNV1byYYUKgz3z1-8iDcw'
TELEGRAM_CHAT_ID = '5137930710'  # Replace with your Telegram chat ID

order_status_updates = {}  # Change this to a dictionary

def send_telegram_message(message, order_id):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'reply_markup': {
            'inline_keyboard': [[
                {'text': 'Received', 'callback_data': f'received_{order_id}'},
                {'text': 'Not Received', 'callback_data': f'not_received_{order_id}'}
            ]]
        }
    }
    requests.post(url, json=payload)

@app.route('/process-order', methods=['POST'])
def process_order():
    try:
        data = request.json
        items = data['items']
        total = data['total']
        status = data['status']
        
        cursor = mysql.connection.cursor()
        # Insert the order
        query = 'INSERT INTO orders (total, status) VALUES (%s, %s)'
        cursor.execute(query, (total, status))
        order_id = cursor.lastrowid
        
        # Insert each item
        for item in items:
            item_query = 'INSERT INTO order_items (order_id, name, price, weight, unit, quantity) VALUES (%s, %s, %s, %s, %s, %s)'
            cursor.execute(item_query, (order_id, item['name'], item['price'], item['weight'], item['unit'], item['quantity']))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'success': True, 'orderId': order_id})
    except Exception as e:
        app.logger.error(f"Error processing order: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/submit-delivery-details', methods=['POST'])
def submit_delivery_details():
    try:
        data = request.json
        pincode = data.get('pincode')
        
        # List of predefined valid pincodes
        valid_pincodes = ['523105', '523292']
        
        if pincode in valid_pincodes:
            cursor = mysql.connection.cursor()
            delivery_query = '''
                INSERT INTO delivery_details (order_id, name, phone, email, address1, address2, village, road_name, pincode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(delivery_query, (
                data['orderId'], data['name'], data['phone'], data['email'],
                data['address1'], data['address2'], data['village'],
                data['roadName'], data['pincode']
            ))
            mysql.connection.commit()
            cursor.close()
            
            # Fetch total amount and order details for the Telegram message
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT total FROM orders WHERE id = %s', (data['orderId'],))
            order_result = cursor.fetchone()
            cursor.close()
            
            if order_result:
                total_amount = order_result[0]
                message = f"New Order Received!\nOrder ID: {data['orderId']}\nTotal Amount: {total_amount}\n\nDelivery Details:\nName: {data['name']}\nPhone: {data['phone']}\nEmail: {data['email']}\nAddress 1: {data['address1']}\nAddress 2: {data['address2']}\nVillage: {data['village']}\nRoad Name: {data['roadName']}\nPincode: {data['pincode']}"
                send_telegram_message(message, data['orderId'])
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid pincode. Please enter a valid pincode.'}), 400
    except Exception as e:
        app.logger.error(f"Error submitting delivery details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate-qrcode', methods=['GET'])
def generate_qrcode():
    order_id = request.args.get('orderId')
    if not order_id:
        return jsonify({'success': False, 'error': 'Order ID is required'}), 400

    # Fetch total amount for the given order_id from database
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT total FROM orders WHERE id = %s', (order_id,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        total_amount = result[0]
        qr_data = f'upi://pay?pa=9848885326@paytm&pn=YourName&mc=0000&tid={order_id}&tt=123456&am={total_amount}&cu=INR&url='
        qr = qrcode.make(qr_data)
        
        # Save QR code to a bytes buffer
        buffer = io.BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)

        return send_file(buffer, mimetype='image/png')
    else:
        return jsonify({'success': False, 'error': 'Order not found'}), 404

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    app.logger.info(f"Received data: {data}")

    if 'callback_query' in data:
        callback_query = data['callback_query']
        callback_data = callback_query.get('data')
        callback_query_id = callback_query.get('id')
        app.logger.info(f"Callback data: {callback_data}")
        app.logger.info(f"Callback query ID: {callback_query_id}")
        order_id = callback_data.split('_')[1]

        if callback_data.startswith('received'):
            cursor = mysql.connection.cursor()
            cursor.execute('UPDATE orders SET status = %s WHERE id = %s', ('success', order_id))
            mysql.connection.commit()
            cursor.close()
            response = requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery', json={
                'callback_query_id': callback_query_id,
                'text': 'Order received and confirmed!'
            })
            app.logger.info(f"Telegram API response: {response.text}")
            order_status_updates[order_id] = 'success'
        elif callback_data.startswith('not_received'):
            cursor = mysql.connection.cursor()
            cursor.execute('UPDATE orders SET status = %s WHERE id = %s', ('not received', order_id))
            mysql.connection.commit()
            cursor.close()
            response = requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery', json={
                'callback_query_id': callback_query_id,
                'text': 'Order not received and cancelled!'
            })
            app.logger.info(f"Telegram API response: {response.text}")
            order_status_updates[order_id] = 'not received'

    return jsonify({'success': True})

@app.route('/order-status-updates/<order_id>', methods=['GET'])
def order_status_updates_stream(order_id):
    def generate():
        while True:
            status = order_status_updates.get(order_id)
            if status:
                yield f"data: {status}\n\n"
                del order_status_updates[order_id]  # Clear the status after sending
            time.sleep(1)  # Check every second

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(port=3100, debug=True)
