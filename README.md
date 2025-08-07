# YFinance Alert Manager

A comprehensive real-time stock price monitoring and alert system built with Flask, WebSockets, and yfinance. Monitor multiple stocks simultaneously, set intelligent price alerts, and receive instant notifications with automatic alert management.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![WebSocket](https://img.shields.io/badge/WebSocket-Enabled-orange)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue)

## Features

### 📈 Real-time Stock Monitoring
- Monitor multiple stocks simultaneously
- Live price updates via WebSocket connections
- Real-time volume and percentage change tracking
- Support for stocks, ETFs, and cryptocurrencies (e.g., AAPL, SPY, BTC-USD)

### 🔔 Intelligent Alert System
- **Color-coded alerts with visual indicators:**
  - 🟢 Green: Price above threshold (↑)
  - 🔴 Red: Price below threshold (↓)
  - 🔵 Blue: Price equal to target (=)
- **Smart alert management:**
  - Automatic pause after trigger to prevent spam
  - Manual pause/resume functionality
  - Edit alerts without recreation
  - Bulk alert operations
- **Persistent storage:** SQLite database with full history
- **Audio notifications:** Instant sound alerts on trigger
- **Anti-spam protection:** 60-second cooldown between triggers

### 💻 Modern User Interface
- **Clean, responsive design** with DaisyUI components
- **Dark/Light theme toggle** for user preference
- **Optimized three-column layout:**
  - **Left:** Stock subscriptions and alert management
  - **Center:** Live price displays for all monitored stocks
  - **Right:** Active alerts monitoring + triggered alerts history
- **Real-time updates** without page refresh
- **Intuitive controls** with contextual buttons and status indicators

### 💾 Advanced Data Management
- **SQLite database** with full ACID compliance
- **Persistent alert storage** survives server restarts
- **Complete audit trail** with trigger history and timestamps
- **SQLAlchemy ORM** for reliable database operations
- **Automatic schema creation** on first run
- **Data integrity** with foreign key constraints

## Key Features Overview

### 🎯 Smart Alert Workflow
1. **Create alerts** with customizable price thresholds
2. **Monitor actively** in real-time with visual indicators
3. **Auto-pause on trigger** to prevent notification spam
4. **Resume manually** when ready to monitor again
5. **Complete history** of all triggered alerts with timestamps

### 🖥️ User Interface Layout
- **Left Column**: Stock subscription management and alert creation/editing
- **Center Column**: Live price monitoring for all subscribed stocks
- **Right Column Top**: Active alerts with quick pause functionality
- **Right Column Bottom**: Triggered alerts history and logs

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/marketcalls/yfinance-alert-manager.git
cd yfinance-alert-manager
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. **Add stocks to monitor:**
   - Enter a stock symbol (e.g., AAPL, GOOGL, BTC-USD)
   - Click "Add" to start monitoring

4. **Set price alerts:**
   - Select a subscribed stock from the dropdown
   - Enter your target price
   - Choose condition (Above/Below/Equal)
   - Click "Save Alert"

5. **Monitor and manage alerts:**
   - **View active alerts**: Monitor currently active alerts in the right column
   - **Auto-pause on trigger**: Alerts automatically pause after triggering to prevent spam
   - **Quick pause**: Use the pause button (⏸) in the active alerts section
   - **Edit**: Modify price or condition without losing history
   - **Resume**: Reactivate paused alerts when ready
   - **Delete**: Remove alert permanently
   - **View history**: See all triggered alerts with timestamps

## Project Structure

```
yfinance-alert-manager/
│
├── app.py                 # Main Flask application with SQLAlchemy models
├── requirements.txt       # Python dependencies  
├── LICENSE               # MIT License
├── README.md            # Project documentation
├── .gitignore           # Git ignore patterns
│
├── templates/
│   └── index.html       # Single-page application with full UI
│
├── static/              # Static assets (auto-generated if needed)
│
└── stock_alerts.db      # SQLite database (auto-created on first run)
```

## Database Schema

The application uses two main tables:

### Alert Table
- Stores all price alert configurations
- Tracks active/paused status and trigger history
- Links alerts to client sessions

### TriggerLog Table  
- Maintains complete audit trail of triggered alerts
- Records exact trigger prices and timestamps
- Provides historical analysis capabilities

## Technical Details

### Backend Technologies
- **Flask**: Web framework
- **Flask-SocketIO**: WebSocket support for real-time updates
- **Flask-SQLAlchemy**: Database ORM
- **yfinance**: Yahoo Finance data streaming
- **SQLite**: Lightweight database for alert storage

### Frontend Technologies
- **DaisyUI**: Tailwind CSS component library
- **Socket.IO Client**: Real-time communication
- **Vanilla JavaScript**: No framework dependencies

### Database Schema

#### Alert Table
- `id`: Primary key
- `symbol`: Stock symbol
- `price`: Alert trigger price
- `condition`: above/below/equal
- `active`: Boolean status
- `created_at`: Timestamp
- `last_triggered`: Last trigger time

#### TriggerLog Table
- `id`: Primary key
- `alert_id`: Foreign key to Alert
- `symbol`: Stock symbol
- `condition`: Trigger condition
- `alert_price`: Original alert price
- `trigger_price`: Actual trigger price
- `triggered_at`: Timestamp

## API Endpoints

### WebSocket Events

#### Client → Server
- `subscribe`: Subscribe to a stock symbol
- `unsubscribe`: Unsubscribe from a stock
- `create_alert`: Create a new price alert
- `update_alert`: Modify existing alert
- `delete_alert`: Remove an alert
- `toggle_alert`: Pause/resume an alert

#### Server → Client
- `stock_update`: Real-time price updates
- `alert_triggered`: Alert notification
- `alerts_list`: List of all alerts
- `trigger_logs`: Alert trigger history

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Known Issues

- **WebSocket connections** may timeout after extended periods of inactivity
- **International stock symbols** may have limited support depending on yfinance data availability
- **Audio notifications** require browser permissions (auto-granted on most modern browsers)
- **Auto-pause feature** prevents continuous alerts but requires manual reactivation
- **Browser refresh** may temporarily disconnect WebSocket (reconnects automatically)

## Future Enhancements

- [ ] **Email/SMS notifications** for triggered alerts
- [ ] **Technical indicators** (RSI, MACD, Moving Averages)
- [ ] **Price charts** with historical data visualization
- [ ] **Alert analytics** with performance metrics
- [ ] **Export functionality** (CSV/JSON) for alerts and trigger history
- [ ] **Multi-user support** with authentication and user-specific alerts
- [ ] **Mobile app** with push notifications
- [ ] **Docker containerization** for easy deployment
- [ ] **API endpoints** for programmatic alert management
- [ ] **Webhook support** for third-party integrations
- [ ] **Advanced alert conditions** (percentage change, volume-based)
- [ ] **Portfolio tracking** with total value monitoring

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**MarketCalls**
- GitHub: [@marketcalls](https://github.com/marketcalls/)

## Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for providing free stock data
- [DaisyUI](https://daisyui.com/) for the beautiful UI components
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) for WebSocket support

## Support

If you encounter any issues or have questions, please:
1. Check the [Issues](https://github.com/marketcalls/yfinance-alert-manager/issues) page
2. Create a new issue with detailed information
3. Or reach out via GitHub

---

**Disclaimer**: This tool is for educational purposes only. Always do your own research before making investment decisions. The authors are not responsible for any financial losses incurred through the use of this software.