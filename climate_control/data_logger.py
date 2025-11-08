"""
Data Logging Module

Provides SQLite-based logging of sensor readings, control decisions, and actuator states.
Includes CSV export functionality and database management.
"""

import sqlite3
import time
import logging
import csv
import os
from datetime import datetime
from typing import Optional, List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLogger:
    """
    Handles data logging to SQLite database with CSV export capability.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the data logger.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        logging_config = self.config.get('logging', {})
        
        self.db_path = logging_config.get('database_path', 'climate_data.db')
        self.csv_export_dir = logging_config.get('csv_export_dir', 'exports')
        self.max_db_size_mb = logging_config.get('max_db_size_mb', 100)
        
        self.conn = None
        self.cursor = None
        
        self._initialize_database()
        self._create_export_directory()
    
    def _initialize_database(self):
        """Initialize SQLite database and create tables."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # Create sensor readings table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    temp_rate REAL,
                    humidity_rate REAL
                )
            ''')
            
            # Create control decisions table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS control_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    mode TEXT NOT NULL,
                    pump_state INTEGER NOT NULL,
                    chiller_state INTEGER NOT NULL,
                    dehumidifier_state INTEGER NOT NULL,
                    reason TEXT,
                    priority INTEGER
                )
            ''')
            
            # Create actuator state table (for detailed tracking)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS actuator_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    actuator_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    runtime REAL,
                    cycle_count INTEGER
                )
            ''')
            
            # Create system events table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT
                )
            ''')
            
            # Create indexes for faster queries
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
                ON sensor_readings(timestamp)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_control_timestamp 
                ON control_decisions(timestamp)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON system_events(timestamp)
            ''')
            
            self.conn.commit()
            
            logger.info(f"Database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_export_directory(self):
        """Create directory for CSV exports if it doesn't exist."""
        if not os.path.exists(self.csv_export_dir):
            os.makedirs(self.csv_export_dir)
            logger.info(f"Created export directory: {self.csv_export_dir}")
    
    def log_sensor_reading(self, temperature: float, humidity: float, 
                          temp_rate: Optional[float] = None,
                          humidity_rate: Optional[float] = None):
        """
        Log a sensor reading.
        
        Args:
            temperature: Temperature in Celsius
            humidity: Humidity in %
            temp_rate: Rate of temperature change (°C/min)
            humidity_rate: Rate of humidity change (%/min)
        """
        try:
            timestamp = time.time()
            
            self.cursor.execute('''
                INSERT INTO sensor_readings 
                (timestamp, temperature, humidity, temp_rate, humidity_rate)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, temperature, humidity, temp_rate, humidity_rate))
            
            self.conn.commit()
            
            logger.debug(f"Logged sensor reading: {temperature:.2f}°C, {humidity:.1f}%")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to log sensor reading: {e}")
    
    def log_control_decision(self, mode: str, pump: bool, chiller: bool, 
                           dehumidifier: bool, reason: str = "", priority: int = 0):
        """
        Log a control decision.
        
        Args:
            mode: Operating mode name
            pump: Pump state
            chiller: Chiller state
            dehumidifier: Dehumidifier state
            reason: Reason for the decision
            priority: Decision priority (0-10)
        """
        try:
            timestamp = time.time()
            
            self.cursor.execute('''
                INSERT INTO control_decisions 
                (timestamp, mode, pump_state, chiller_state, dehumidifier_state, reason, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, mode, int(pump), int(chiller), int(dehumidifier), reason, priority))
            
            self.conn.commit()
            
            logger.debug(f"Logged control decision: {mode}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to log control decision: {e}")
    
    def log_actuator_state(self, actuator_name: str, state: str, 
                          runtime: float = 0.0, cycle_count: int = 0):
        """
        Log actuator state information.
        
        Args:
            actuator_name: Name of the actuator
            state: Current state (ON/OFF/FAULT)
            runtime: Current runtime in seconds
            cycle_count: Total number of cycles
        """
        try:
            timestamp = time.time()
            
            self.cursor.execute('''
                INSERT INTO actuator_states 
                (timestamp, actuator_name, state, runtime, cycle_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, actuator_name, state, runtime, cycle_count))
            
            self.conn.commit()
            
            logger.debug(f"Logged actuator state: {actuator_name} = {state}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to log actuator state: {e}")
    
    def log_event(self, event_type: str, message: str, severity: str = "INFO"):
        """
        Log a system event.
        
        Args:
            event_type: Type of event (e.g., 'startup', 'error', 'warning')
            message: Event message
            severity: Severity level (INFO/WARNING/ERROR/CRITICAL)
        """
        try:
            timestamp = time.time()
            
            self.cursor.execute('''
                INSERT INTO system_events 
                (timestamp, event_type, severity, message)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, event_type, severity, message))
            
            self.conn.commit()
            
            logger.debug(f"Logged event: {event_type} - {message}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to log event: {e}")
    
    def get_recent_readings(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """
        Get recent sensor readings.
        
        Args:
            hours: Number of hours of history to retrieve
            limit: Maximum number of readings to return
            
        Returns:
            List of reading dictionaries
        """
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            self.cursor.execute('''
                SELECT timestamp, temperature, humidity, temp_rate, humidity_rate
                FROM sensor_readings
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (cutoff_time, limit))
            
            rows = self.cursor.fetchall()
            
            readings = []
            for row in rows:
                readings.append({
                    'timestamp': row[0],
                    'datetime': datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'),
                    'temperature': row[1],
                    'humidity': row[2],
                    'temp_rate': row[3],
                    'humidity_rate': row[4]
                })
            
            return readings
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent readings: {e}")
            return []
    
    def get_recent_decisions(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        Get recent control decisions.
        
        Args:
            hours: Number of hours of history to retrieve
            limit: Maximum number of decisions to return
            
        Returns:
            List of decision dictionaries
        """
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            self.cursor.execute('''
                SELECT timestamp, mode, pump_state, chiller_state, 
                       dehumidifier_state, reason, priority
                FROM control_decisions
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (cutoff_time, limit))
            
            rows = self.cursor.fetchall()
            
            decisions = []
            for row in rows:
                decisions.append({
                    'timestamp': row[0],
                    'datetime': datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'),
                    'mode': row[1],
                    'pump': bool(row[2]),
                    'chiller': bool(row[3]),
                    'dehumidifier': bool(row[4]),
                    'reason': row[5],
                    'priority': row[6]
                })
            
            return decisions
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent decisions: {e}")
            return []
    
    def get_system_events(self, hours: int = 24, severity: str = None) -> List[Dict]:
        """
        Get system events.
        
        Args:
            hours: Number of hours of history to retrieve
            severity: Filter by severity level (optional)
            
        Returns:
            List of event dictionaries
        """
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            if severity:
                self.cursor.execute('''
                    SELECT timestamp, event_type, severity, message
                    FROM system_events
                    WHERE timestamp > ? AND severity = ?
                    ORDER BY timestamp DESC
                ''', (cutoff_time, severity))
            else:
                self.cursor.execute('''
                    SELECT timestamp, event_type, severity, message
                    FROM system_events
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                ''', (cutoff_time,))
            
            rows = self.cursor.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    'timestamp': row[0],
                    'datetime': datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': row[1],
                    'severity': row[2],
                    'message': row[3]
                })
            
            return events
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get system events: {e}")
            return []
    
    def export_to_csv(self, filename: str = None, hours: int = 24) -> str:
        """
        Export data to CSV file.
        
        Args:
            filename: Output filename (auto-generated if None)
            hours: Number of hours of history to export
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"climate_data_{timestamp}.csv"
        
        filepath = os.path.join(self.csv_export_dir, filename)
        
        try:
            # Get data
            readings = self.get_recent_readings(hours=hours, limit=100000)
            decisions = self.get_recent_decisions(hours=hours, limit=100000)
            
            # Create decision lookup by timestamp (rounded to second)
            decision_map = {}
            for decision in decisions:
                ts_key = int(decision['timestamp'])
                decision_map[ts_key] = decision
            
            # Write combined data
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = [
                    'datetime', 'timestamp', 
                    'temperature', 'humidity', 
                    'temp_rate', 'humidity_rate',
                    'mode', 'pump', 'chiller', 'dehumidifier',
                    'decision_reason'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for reading in reversed(readings):  # Oldest to newest
                    ts_key = int(reading['timestamp'])
                    decision = decision_map.get(ts_key, {})
                    
                    row = {
                        'datetime': reading['datetime'],
                        'timestamp': reading['timestamp'],
                        'temperature': reading['temperature'],
                        'humidity': reading['humidity'],
                        'temp_rate': reading.get('temp_rate', ''),
                        'humidity_rate': reading.get('humidity_rate', ''),
                        'mode': decision.get('mode', ''),
                        'pump': decision.get('pump', ''),
                        'chiller': decision.get('chiller', ''),
                        'dehumidifier': decision.get('dehumidifier', ''),
                        'decision_reason': decision.get('reason', '')
                    }
                    
                    writer.writerow(row)
            
            logger.info(f"Exported {len(readings)} readings to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise
    
    def check_database_size(self) -> float:
        """
        Check database size in MB.
        
        Returns:
            Database size in megabytes
        """
        try:
            size_bytes = os.path.getsize(self.db_path)
            size_mb = size_bytes / (1024 * 1024)
            return size_mb
        except:
            return 0.0
    
    def cleanup_old_data(self, days: int = 30):
        """
        Remove data older than specified days.
        
        Args:
            days: Number of days of data to keep
        """
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            # Delete old sensor readings
            self.cursor.execute('''
                DELETE FROM sensor_readings WHERE timestamp < ?
            ''', (cutoff_time,))
            
            # Delete old control decisions
            self.cursor.execute('''
                DELETE FROM control_decisions WHERE timestamp < ?
            ''', (cutoff_time,))
            
            # Delete old actuator states
            self.cursor.execute('''
                DELETE FROM actuator_states WHERE timestamp < ?
            ''', (cutoff_time,))
            
            # Keep system events longer (2x retention)
            event_cutoff = time.time() - (days * 2 * 24 * 3600)
            self.cursor.execute('''
                DELETE FROM system_events WHERE timestamp < ?
            ''', (event_cutoff,))
            
            self.conn.commit()
            
            # Vacuum to reclaim space
            self.cursor.execute('VACUUM')
            
            logger.info(f"Cleaned up data older than {days} days")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_statistics(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {}
            
            # Count records in each table
            self.cursor.execute('SELECT COUNT(*) FROM sensor_readings')
            stats['sensor_readings'] = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM control_decisions')
            stats['control_decisions'] = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM actuator_states')
            stats['actuator_states'] = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM system_events')
            stats['system_events'] = self.cursor.fetchone()[0]
            
            # Get time range
            self.cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM sensor_readings')
            min_ts, max_ts = self.cursor.fetchone()
            
            if min_ts and max_ts:
                stats['data_start'] = datetime.fromtimestamp(min_ts).strftime('%Y-%m-%d %H:%M:%S')
                stats['data_end'] = datetime.fromtimestamp(max_ts).strftime('%Y-%m-%d %H:%M:%S')
                stats['data_span_hours'] = (max_ts - min_ts) / 3600
            
            stats['database_size_mb'] = self.check_database_size()
            
            return stats
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Example usage and testing
if __name__ == "__main__":
    print("Data Logger Test")
    print("-" * 40)
    
    # Create logger
    logger_obj = DataLogger()
    
    # Log some test data
    print("Logging test data...")
    for i in range(10):
        temp = 5.0 + i * 0.1
        humidity = 90.0 - i * 0.2
        
        logger_obj.log_sensor_reading(temp, humidity, temp_rate=0.5, humidity_rate=-0.1)
        logger_obj.log_control_decision("idle", False, False, False, "Testing", 0)
        
        time.sleep(0.1)
    
    logger_obj.log_event("test", "Test event", "INFO")
    
    # Get statistics
    print("\nDatabase Statistics:")
    stats = logger_obj.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Export to CSV
    print("\nExporting to CSV...")
    csv_path = logger_obj.export_to_csv()
    print(f"Exported to: {csv_path}")
    
    # Get recent readings
    print("\nRecent readings:")
    readings = logger_obj.get_recent_readings(hours=1, limit=5)
    for reading in readings[:3]:
        print(f"  {reading['datetime']}: {reading['temperature']:.1f}°C, {reading['humidity']:.1f}%")
    
    logger_obj.close()

