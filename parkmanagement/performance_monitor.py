# parkmanagement/performance_monitor.py

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from functools import wraps
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Detailliertes Performance-Monitoring für wissenschaftliche Auswertung
    """
    
    def __init__(self):
        self.metrics = []
        self.current_session = None
        
    def start_session(self, session_name: str, context: Dict[str, Any] = None):
        """Startet eine neue Monitoring-Session"""
        self.current_session = {
            "session_name": session_name,
            "start_time": time.time(),
            "start_datetime": datetime.now().isoformat(),
            "context": context or {},
            "operations": [],
            "total_duration": None
        }
        logger.info(f"🔍 Performance Session gestartet: {session_name}")
        
    def end_session(self):
        """Beendet die aktuelle Session und speichert Ergebnisse"""
        if self.current_session:
            self.current_session["total_duration"] = time.time() - self.current_session["start_time"]
            self.current_session["end_datetime"] = datetime.now().isoformat()
            
            self.metrics.append(self.current_session.copy())
            
            logger.info(f"✅ Session '{self.current_session['session_name']}' beendet: "
                       f"{self.current_session['total_duration']:.2f}s")
            
            # Reset für nächste Session
            self.current_session = None
    
    @contextmanager
    def measure_operation(self, operation_name: str, details: Dict[str, Any] = None):
        """Context Manager für einzelne Operationen"""
        start_time = time.time()
        operation_data = {
            "operation": operation_name,
            "start_time": start_time,
            "details": details or {},
            "duration": None,
            "success": True,
            "error": None
        }
        
        try:
            logger.info(f"⏱️  Starte: {operation_name}")
            yield operation_data
            
        except Exception as e:
            operation_data["success"] = False
            operation_data["error"] = str(e)
            logger.error(f"❌ Fehler bei {operation_name}: {e}")
            raise
            
        finally:
            operation_data["duration"] = time.time() - start_time
            
            if self.current_session:
                self.current_session["operations"].append(operation_data)
            
            status = "✅" if operation_data["success"] else "❌"
            logger.info(f"{status} {operation_name}: {operation_data['duration']:.2f}s")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der letzten Session zurück"""
        if not self.metrics:
            return {"error": "Keine Monitoring-Daten verfügbar"}
        
        last_session = self.metrics[-1]
        operations = last_session["operations"]
        
        # Operationen nach Typ gruppieren
        operation_types = {}
        for op in operations:
            op_type = op["operation"]
            if op_type not in operation_types:
                operation_types[op_type] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "min_time": float('inf'),
                    "max_time": 0,
                    "success_rate": 0
                }
            
            stats = operation_types[op_type]
            stats["count"] += 1
            stats["total_time"] += op["duration"]
            stats["min_time"] = min(stats["min_time"], op["duration"])
            stats["max_time"] = max(stats["max_time"], op["duration"])
            
            if op["success"]:
                stats["success_rate"] += 1
        
        # Durchschnitte berechnen
        for stats in operation_types.values():
            if stats["count"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["count"]
                stats["success_rate"] = (stats["success_rate"] / stats["count"]) * 100
        
        return {
            "session_info": {
                "name": last_session["session_name"],
                "total_duration": last_session["total_duration"],
                "total_operations": len(operations),
                "context": last_session["context"]
            },
            "operation_breakdown": operation_types,
            "bottlenecks": self._identify_bottlenecks(operation_types),
            "recommendations": self._generate_recommendations(operation_types, last_session["total_duration"])
        }
    
    def _identify_bottlenecks(self, operation_types: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Identifiziert die größten Performance-Bottlenecks"""
        bottlenecks = []
        
        for op_name, stats in operation_types.items():
            percentage_of_total = (stats["total_time"] / sum(s["total_time"] for s in operation_types.values())) * 100
            
            if percentage_of_total > 15:  # Mehr als 15% der Gesamtzeit
                bottlenecks.append({
                    "operation": op_name,
                    "percentage_of_total": round(percentage_of_total, 1),
                    "total_time": round(stats["total_time"], 2),
                    "avg_time": round(stats["avg_time"], 2),
                    "count": stats["count"],
                    "severity": "critical" if percentage_of_total > 40 else "high" if percentage_of_total > 25 else "medium"
                })
        
        return sorted(bottlenecks, key=lambda x: x["percentage_of_total"], reverse=True)
    
    def _generate_recommendations(self, operation_types: Dict[str, Dict], total_time: float) -> List[str]:
        """Generiert Optimierungsempfehlungen basierend auf den Metriken"""
        recommendations = []
        
        # API-Call Analyse
        api_operations = [op for op in operation_types.keys() if "api" in op.lower() or "google" in op.lower()]
        if len(api_operations) > 3:
            recommendations.append("Parallelisierung der API-Calls implementieren - potenzielle Zeitersparnis: 60-80%")
        
        # Langsame Einzeloperationen
        slow_operations = [op for op, stats in operation_types.items() if stats["avg_time"] > 5]
        if slow_operations:
            recommendations.append(f"Kritische Operationen optimieren: {', '.join(slow_operations)}")
        
        # Caching-Potenzial
        repeated_operations = [op for op, stats in operation_types.items() if stats["count"] > 1]
        if repeated_operations:
            recommendations.append("Caching für wiederholte Operationen implementieren")
        
        # Gesamtzeit-Bewertung
        if total_time > 20:
            recommendations.append("Dringende Architektur-Optimierung erforderlich - Ziel: <5 Sekunden")
        elif total_time > 10:
            recommendations.append("Performance-Optimierung empfohlen - Ziel: <3 Sekunden")
        
        return recommendations
    
    def export_for_research(self) -> Dict[str, Any]:
        """Exportiert alle Daten für wissenschaftliche Auswertung"""
        return {
            "monitoring_metadata": {
                "total_sessions": len(self.metrics),
                "export_timestamp": datetime.now().isoformat(),
                "purpose": "Masterarbeit Performance-Analyse"
            },
            "all_sessions": self.metrics,
            "aggregated_statistics": self._calculate_aggregated_stats()
        }
    
    def _calculate_aggregated_stats(self) -> Dict[str, Any]:
        """Berechnet aggregierte Statistiken über alle Sessions"""
        if not self.metrics:
            return {}
        
        all_operations = []
        for session in self.metrics:
            all_operations.extend(session["operations"])
        
        return {
            "total_operations": len(all_operations),
            "avg_session_duration": sum(s["total_duration"] for s in self.metrics) / len(self.metrics),
            "operation_frequency": self._get_operation_frequency(all_operations),
            "success_rates": self._get_success_rates(all_operations)
        }
    
    def _get_operation_frequency(self, operations: List[Dict]) -> Dict[str, int]:
        """Häufigkeit der verschiedenen Operationen"""
        frequency = {}
        for op in operations:
            op_name = op["operation"]
            frequency[op_name] = frequency.get(op_name, 0) + 1
        return frequency
    
    def _get_success_rates(self, operations: List[Dict]) -> Dict[str, float]:
        """Erfolgsraten der verschiedenen Operationen"""
        success_rates = {}
        operation_counts = {}
        
        for op in operations:
            op_name = op["operation"]
            operation_counts[op_name] = operation_counts.get(op_name, 0) + 1
            
            if op["success"]:
                success_rates[op_name] = success_rates.get(op_name, 0) + 1
        
        # In Prozent umrechnen
        for op_name in success_rates:
            success_rates[op_name] = (success_rates[op_name] / operation_counts[op_name]) * 100
        
        return success_rates


# Singleton Instance für globale Nutzung
performance_monitor = PerformanceMonitor()


# Decorator für automatisches Monitoring von Funktionen
def monitor_performance(operation_name: str = None):
    """Decorator für automatisches Performance-Monitoring"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with performance_monitor.measure_operation(op_name, {"args_count": len(args), "kwargs_keys": list(kwargs.keys())}):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Hilfsfunktionen für einfache Nutzung
def start_route_monitoring(start_adresse: str, parkplatz_count: int):
    """Startet Monitoring für Routenberechnung"""
    performance_monitor.start_session(
        "route_calculation",
        {
            "start_address": start_adresse,
            "parking_options": parkplatz_count,
            "user_agent": "MatchRoute-Research"
        }
    )

def end_route_monitoring():
    """Beendet Monitoring und gibt Summary zurück"""
    performance_monitor.end_session()
    return performance_monitor.get_session_summary()

def get_research_export():
    """Holt alle Monitoring-Daten für Forschung"""
    return performance_monitor.export_for_research()