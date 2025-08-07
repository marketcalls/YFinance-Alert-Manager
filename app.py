from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import yfinance as yf
import threading
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_alerts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database Models
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(10), nullable=False)  # above, below, equal
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_triggered = db.Column(db.DateTime, nullable=True)
    client_id = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'condition': self.condition,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }

class TriggerLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(10), nullable=False)
    alert_price = db.Column(db.Float, nullable=False)
    trigger_price = db.Column(db.Float, nullable=False)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'symbol': self.symbol,
            'condition': self.condition,
            'alert_price': self.alert_price,
            'trigger_price': self.trigger_price,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }

# Global variables to store active subscriptions and websocket connections
active_subscriptions = {}  # client_id -> set of symbols
websocket_connections = {}  # symbol -> websocket
stock_prices = {}  # symbol -> latest price data

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    # Initialize empty subscription set for this client
    active_subscriptions[request.sid] = set()
    
    # Send all existing alerts to the client
    alerts = Alert.query.all()
    emit('alerts_list', [alert.to_dict() for alert in alerts])
    
    # Send recent trigger logs
    recent_logs = TriggerLog.query.order_by(TriggerLog.triggered_at.desc()).limit(50).all()
    emit('trigger_logs', [log.to_dict() for log in recent_logs])
    
    # Send all persisted subscriptions and auto-restore them
    subscriptions = Subscription.query.order_by(Subscription.last_accessed.desc()).all()
    if subscriptions:
        subscription_symbols = [sub.symbol for sub in subscriptions]
        emit('restore_subscriptions', subscription_symbols)
        
        # Auto-resubscribe to all persisted symbols
        for sub in subscriptions:
            symbol = sub.symbol
            sub.last_accessed = datetime.utcnow()
            active_subscriptions[request.sid].add(symbol)
            
            # Create websocket connection if it doesn't exist
            if symbol not in websocket_connections:
                def create_message_handler(symbol_name):
                    def message_handler(message):
                        # Store latest price
                        stock_prices[symbol_name] = message
                        
                        # Broadcast to all subscribed clients
                        for cid, symbols in active_subscriptions.items():
                            if symbol_name in symbols:
                                socketio.emit('stock_update', {
                                    'symbol': symbol_name,
                                    'data': message
                                }, room=cid)
                        
                        # Check alerts
                        current_price = float(message.get('price', 0))
                        check_alerts(symbol_name, current_price)
                    return message_handler
                
                try:
                    ws = yf.WebSocket()
                    ws.subscribe([symbol])
                    websocket_connections[symbol] = ws
                    
                    # Start listening in a separate thread
                    thread = threading.Thread(target=ws.listen, args=(create_message_handler(symbol),), daemon=True)
                    thread.start()
                except Exception as e:
                    print(f"Error creating websocket for {symbol}: {e}")
        
        db.session.commit()

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    client_id = request.sid
    
    # Get symbols this client was subscribed to
    if client_id in active_subscriptions:
        symbols = active_subscriptions[client_id]
        del active_subscriptions[client_id]
        
        # Check if any other clients are subscribed to these symbols
        for symbol in symbols:
            still_subscribed = any(
                symbol in subs for cid, subs in active_subscriptions.items()
            )
            
            # If no one else is subscribed, close the websocket
            if not still_subscribed and symbol in websocket_connections:
                try:
                    websocket_connections[symbol].close()
                    del websocket_connections[symbol]
                    del stock_prices[symbol]
                except:
                    pass

@socketio.on('subscribe')
def handle_subscribe(data):
    symbol = data['symbol'].upper()
    client_id = request.sid
    
    with app.app_context():
        # Add to this client's subscriptions
        if client_id not in active_subscriptions:
            active_subscriptions[client_id] = set()
        
        active_subscriptions[client_id].add(symbol)
        
        # Persist subscription in database
        subscription = Subscription.query.filter_by(symbol=symbol).first()
        if not subscription:
            subscription = Subscription(symbol=symbol)
            db.session.add(subscription)
        else:
            subscription.last_accessed = datetime.utcnow()
        db.session.commit()
        
        # If websocket for this symbol doesn't exist, create it
        if symbol not in websocket_connections:
            def create_message_handler(symbol_name):
                def message_handler(message):
                    # Store latest price
                    stock_prices[symbol_name] = message
                    
                    # Broadcast to all subscribed clients
                    for cid, symbols in active_subscriptions.items():
                        if symbol_name in symbols:
                            socketio.emit('stock_update', {
                                'symbol': symbol_name,
                                'data': message
                            }, room=cid)
                    
                    # Check alerts
                    current_price = float(message.get('price', 0))
                    check_alerts(symbol_name, current_price)
                return message_handler
            
            # Create new websocket connection
            try:
                ws = yf.WebSocket()
                ws.subscribe([symbol])
                websocket_connections[symbol] = ws
                
                # Start listening in a separate thread
                thread = threading.Thread(target=ws.listen, args=(create_message_handler(symbol),), daemon=True)
                thread.start()
                
                emit('subscription_success', {'symbol': symbol})
            except Exception as e:
                emit('subscription_error', {'error': str(e)})
        else:
            emit('subscription_success', {'symbol': symbol})
            # Send latest price if available
            if symbol in stock_prices:
                emit('stock_update', {'symbol': symbol, 'data': stock_prices[symbol]})

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    symbol = data['symbol'].upper()
    client_id = request.sid
    
    with app.app_context():
        if client_id in active_subscriptions and symbol in active_subscriptions[client_id]:
            active_subscriptions[client_id].discard(symbol)
            
            # Remove from database (permanent unsubscribe)
            subscription = Subscription.query.filter_by(symbol=symbol).first()
            if subscription:
                db.session.delete(subscription)
                db.session.commit()
            
            # Check if any other clients are subscribed
            still_subscribed = any(
                symbol in subs for cid, subs in active_subscriptions.items()
            )
            
            if not still_subscribed and symbol in websocket_connections:
                try:
                    websocket_connections[symbol].close()
                    del websocket_connections[symbol]
                    del stock_prices[symbol]
                except:
                    pass
            
            emit('unsubscribe_success', {'symbol': symbol})

@socketio.on('get_subscriptions')
def handle_get_subscriptions():
    client_id = request.sid
    symbols = list(active_subscriptions.get(client_id, set()))
    emit('subscriptions_list', symbols)

@socketio.on('create_alert')
def handle_create_alert(data):
    symbol = data['symbol'].upper()
    price = float(data['price'])
    condition = data['condition']
    
    alert = Alert(
        symbol=symbol,
        price=price,
        condition=condition,
        client_id=request.sid
    )
    db.session.add(alert)
    db.session.commit()
    
    # Broadcast to all clients
    socketio.emit('alert_created', alert.to_dict())

@socketio.on('update_alert')
def handle_update_alert(data):
    alert_id = data['id']
    alert = Alert.query.get(alert_id)
    
    if alert:
        alert.price = float(data['price'])
        alert.condition = data['condition']
        alert.active = data.get('active', True)
        db.session.commit()
        
        # Broadcast to all clients
        socketio.emit('alert_updated', alert.to_dict())

@socketio.on('delete_alert')
def handle_delete_alert(data):
    alert_id = data['id']
    alert = Alert.query.get(alert_id)
    
    if alert:
        db.session.delete(alert)
        db.session.commit()
        
        # Broadcast to all clients
        socketio.emit('alert_deleted', {'id': alert_id})

@socketio.on('toggle_alert')
def handle_toggle_alert(data):
    alert_id = data['id']
    alert = Alert.query.get(alert_id)
    
    if alert:
        alert.active = not alert.active
        db.session.commit()
        
        # Broadcast to all clients
        socketio.emit('alert_updated', alert.to_dict())

def check_alerts(symbol, current_price):
    """Check if any alerts should be triggered for the given symbol and price"""
    with app.app_context():
        alerts = Alert.query.filter_by(symbol=symbol, active=True).all()
        
        for alert in alerts:
            triggered = False
            
            if alert.condition == 'above' and current_price > alert.price:
                triggered = True
            elif alert.condition == 'below' and current_price < alert.price:
                triggered = True
            elif alert.condition == 'equal' and abs(current_price - alert.price) < 0.01:
                triggered = True
            
            if triggered:
                # Check if alert was recently triggered (within last 60 seconds)
                if alert.last_triggered:
                    time_diff = (datetime.utcnow() - alert.last_triggered).total_seconds()
                    if time_diff < 60:
                        continue
                
                # Update last triggered time and pause the alert
                alert.last_triggered = datetime.utcnow()
                alert.active = False  # Auto-pause after triggering
                
                # Create trigger log
                log = TriggerLog(
                    alert_id=alert.id,
                    symbol=symbol,
                    condition=alert.condition,
                    alert_price=alert.price,
                    trigger_price=current_price
                )
                db.session.add(log)
                db.session.commit()
                
                # Broadcast alert triggered event
                socketio.emit('alert_triggered', {
                    'id': alert.id,
                    'symbol': symbol,
                    'condition': alert.condition,
                    'alert_price': alert.price,
                    'current_price': current_price,
                    'log': log.to_dict()
                })
                
                # Broadcast alert update to reflect paused state
                socketio.emit('alert_updated', alert.to_dict())

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)