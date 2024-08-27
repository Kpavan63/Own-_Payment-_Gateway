from flask import Flask, jsonify, render_template_string, request
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'veg-order'

mysql = MySQL(app)

# HTML template as a multi-line string
admin_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Anton+SC&display=swap" rel="stylesheet">
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding-top: 20px;
            padding-bottom: 20px;
        }
        .container {
            max-width: 1200px;
        }
        h1 {
            text-align: center;
            font-family: "Anton SC", sans-serif;
            font-weight: 400;
            font-style: normal;
        }
        .table-container {
            margin-top: 20px;
        }
        .totals {
            margin-bottom: 20px;
            text-align: center;
        }
        .totals h3{
            background-color:black;
            color:white;
            padding:7px 50px;
        }
        #totalAmount{
            color:green;
            font-weight:bold;
        }
        @media (max-width: 768px) {
            .table-responsive {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Admin Panel</h1>

        <div class="totals">
            <h3>Total Amount: <span id="totalAmount">0</span></h3>
            <h3>Total Orders: <span id="totalOrders">0</span></h3>
        </div>

        <div class="input-group mb-3">
            <input type="text" class="form-control" placeholder="Search by Order ID" id="searchOrder">
            <div class="input-group-append">
                <button class="btn btn-primary" type="button" onclick="searchOrders()">Search</button>
            </div>
        </div>
        <div class="form-group">
            <label for="filterStatus">Filter by Shipping Status:</label>
            <select class="form-control" id="filterStatus" onchange="filterOrders()">
                <option value="">All</option>
                <option value="Pending">Pending</option>
                <option value="Shipped">Shipped</option>
                <option value="Delivered">Delivered</option>
            </select>
        </div>

        <div class="table-container table-responsive">
            <h2>Orders</h2>
            <table class="table table-bordered" id="ordersTable">
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>Total</th>
                        <th>Shipping Status</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Orders will be populated here -->
                </tbody>
            </table>
        </div>

        <div class="table-container table-responsive" id="orderDetailsContainer" style="display: none;">
            <h2>Order Items</h2>
            <table class="table table-bordered" id="orderItemsTable">
                <thead>
                    <tr>
                        <th>Item ID</th>
                        <th>Order ID</th>
                        <th>Name</th>
                        <th>Price</th>
                        <th>Weight</th>
                        <th>Unit</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Order items will be populated here -->
                </tbody>
            </table>

            <h2>Delivery Details</h2>
            <table class="table table-bordered" id="deliveryDetailsTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Email</th>
                        <th>Address 1</th>
                        <th>Address 2</th>
                        <th>Village</th>
                        <th>Road Name</th>
                        <th>Pincode</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Delivery details will be populated here -->
                </tbody>
            </table>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    <script>
        $(document).ready(function() {
            function updateTotals() {
                $.get('/admin/orders/summary', function(summary) {
                    $('#totalAmount').text(summary.total_amount);
                    $('#totalOrders').text(summary.total_orders);
                });
            }

            // Initial update of totals
            updateTotals();

            // Fetch and display orders
            $.get('/admin/orders', function(orders) {
                var ordersTableBody = $('#ordersTable tbody');
                ordersTableBody.empty();
                orders.forEach(function(order) {
                    ordersTableBody.append(
                        `<tr>
                            <td>${order[0]}</td>
                            <td>${order[1]}</td>
                            <td>
                                <select class="form-control" onchange="updateShippingStatus(${order[0]}, this.value)">
                                    <option value="Pending" ${order[2] === 'Pending' ? 'selected' : ''}>Pending</option>
                                    <option value="Shipped" ${order[2] === 'Shipped' ? 'selected' : ''}>Shipped</option>
                                    <option value="Delivered" ${order[2] === 'Delivered' ? 'selected' : ''}>Delivered</option>
                                </select>
                            </td>
                            <td>${order[3]}</td>
                            <td><button class="btn btn-info" onclick="showOrderDetails(${order[0]})">View Details</button></td>
                        </tr>`
                    );
                });
            });

            window.showOrderDetails = function(orderId) {
                // Fetch and display order items
                $.get(`/admin/order-items/${orderId}`, function(orderItems) {
                    var orderItemsTableBody = $('#orderItemsTable tbody');
                    orderItemsTableBody.empty();
                    orderItems.forEach(function(item) {
                        orderItemsTableBody.append(
                            `<tr>
                                <td>${item[0]}</td>
                                <td>${item[1]}</td>
                                <td>${item[2]}</td>
                                <td>${item[3]}</td>
                                <td>${item[4]}</td>
                                <td>${item[5]}</td>
                                <td>${item[6]}</td>
                            </tr>`
                        );
                    });
                });

                // Fetch and display delivery details
                $.get(`/admin/delivery-details/${orderId}`, function(deliveryDetails) {
                    var deliveryDetailsTableBody = $('#deliveryDetailsTable tbody');
                    deliveryDetailsTableBody.empty();
                    if (deliveryDetails) {
                        deliveryDetailsTableBody.append(
                            `<tr>
                                <td>${deliveryDetails.order_id}</td>
                                <td>${deliveryDetails.name}</td>
                                <td>${deliveryDetails.phone}</td>
                                <td>${deliveryDetails.email}</td>
                                <td>${deliveryDetails.address1}</td>
                                <td>${deliveryDetails.address2}</td>
                                <td>${deliveryDetails.village}</td>
                                <td>${deliveryDetails.road_name}</td>
                                <td>${deliveryDetails.pincode}</td>
                            </tr>`
                        );
                    }
                });

                $('#orderDetailsContainer').show();
            };

            window.searchOrders = function() {
                var searchValue = $('#searchOrder').val().toLowerCase();
                var ordersTableBody = $('#ordersTable tbody tr');
                ordersTableBody.each(function() {
                    var orderId = $(this).find('td:first').text().toLowerCase();
                    if (orderId.includes(searchValue)) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            };

            window.filterOrders = function() {
                var filterValue = $('#filterStatus').val();
                var ordersTableBody = $('#ordersTable tbody tr');
                ordersTableBody.each(function() {
                    var status = $(this).find('td:nth-child(3) select').val();
                    if (filterValue === "" || status === filterValue) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            };

            window.updateShippingStatus = function(orderId, status) {
                $.ajax({
                    url: `/admin/update-shipping-status/${orderId}`,
                    method: 'POST',
                    data: { status: status },
                    success: function(response) {
                        alert(response.message);
                        updateTotals();
                    }
                });
            };
        });
    </script>
</body>
</html>
"""
@app.route('/admin')
def admin_panel():
    return render_template_string(admin_html)


@app.route('/admin/orders/summary', methods=['GET'])
def get_summary():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT SUM(total) AS total_amount, COUNT(*) AS total_orders FROM orders')
    summary = cursor.fetchone()
    cursor.close()
    return jsonify({'total_amount': summary[0], 'total_orders': summary[1]})

@app.route('/admin/orders', methods=['GET'])
def get_orders():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, total, shipping_status, status FROM orders')
    orders = cursor.fetchall()
    cursor.close()
    return jsonify(orders)

@app.route('/admin/order-items/<int:order_id>', methods=['GET'])
def get_order_items(order_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, order_id, name, price, weight, unit, quantity FROM order_items WHERE order_id = %s', (order_id,))
    order_items = cursor.fetchall()
    cursor.close()
    return jsonify(order_items)

@app.route('/admin/delivery-details/<int:order_id>', methods=['GET'])
def get_delivery_details(order_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT order_id, name, phone, email, address1, address2, village, road_name, pincode FROM delivery_details WHERE order_id = %s', (order_id,))
    delivery_details = cursor.fetchone()
    cursor.close()
    if delivery_details:
        delivery_details_dict = {
            'order_id': delivery_details[0],
            'name': delivery_details[1],
            'phone': delivery_details[2],
            'email': delivery_details[3],
            'address1': delivery_details[4],
            'address2': delivery_details[5],
            'village': delivery_details[6],
            'road_name': delivery_details[7],
            'pincode': delivery_details[8]
        }
        return jsonify(delivery_details_dict)
    else:
        return jsonify({}), 404

@app.route('/admin/update-shipping-status/<int:order_id>', methods=['POST'])
def update_shipping_status(order_id):
    new_status = request.form['status']
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE orders SET shipping_status = %s WHERE id = %s', (new_status, order_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Shipping status updated successfully!'})

if __name__ == '__main__':
    app.run(port=3200, debug=True)
