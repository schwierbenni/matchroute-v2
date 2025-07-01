import React from 'react';
import { 
  Clock, 
  MapPin, 
  Car, 
  Navigation, 
  Users, 
  ExternalLink,
  Star,
  Target,
  Route,
  Zap,
  Database,
  AlertCircle,
  CheckCircle2,
  Calendar
} from 'lucide-react';

const formatMinutes = (min) => {
  if (!min) return "—";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h > 0 ? `${h}h ${m}min` : `${m}min`;
};

const formatKm = (km) => {
  return km ? `${parseFloat(km).toFixed(1)} km` : "—";
};

const getMethodIcon = (method) => {
  switch (method) {
    case 'walking': return Users;
    case 'transit': return Car;
    case 'driving': return Car;
    default: return Navigation;
  }
};

const getMethodLabel = (method) => {
  switch (method) {
    case 'walking': return 'zu Fuß';
    case 'transit': return 'ÖPNV';
    case 'driving': return 'Auto';
    default: return method;
  }
};

const getTrafficColor = (rating) => {
  if (rating >= 5) return 'text-green-700 bg-green-100 border-green-300';
  if (rating >= 4) return 'text-blue-700 bg-blue-100 border-blue-300';
  if (rating >= 3) return 'text-yellow-700 bg-yellow-100 border-yellow-300';
  if (rating >= 2) return 'text-orange-700 bg-orange-100 border-orange-300';
  return 'text-red-700 bg-red-100 border-red-300';
};

const getTrafficLabel = (rating) => {
  const labels = {
    5: 'Excellent',
    4: 'Good', 
    3: 'Fair',
    2: 'Poor',
    1: 'Critical'
  };
  return labels[rating] || 'Unknown';
};

const getAvailabilityIcon = (score) => {
  if (score >= 4) return CheckCircle2;
  if (score >= 3) return Clock;
  return AlertCircle;
};

const getAvailabilityColor = (score) => {
  if (score >= 4) return 'text-green-600';
  if (score >= 3) return 'text-yellow-600';
  return 'text-red-600';
};

const handleGoogleMapsClick = (navigationLinks) => {
  if (!navigationLinks) {
    alert('Navigation Links nicht verfügbar');
    return;
  }

  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  let linkToOpen = navigationLinks.web_link;
  
  if (isMobile && navigationLinks.mobile_link) {
    linkToOpen = navigationLinks.mobile_link;
  }
  
  window.open(linkToOpen, '_blank', 'noopener,noreferrer');
};

const handleWalkingNavigationClick = (walkingNavigation) => {
  if (!walkingNavigation) {
    alert('Fußweg-Navigation nicht verfügbar');
    return;
  }
  
  window.open(walkingNavigation.web_link, '_blank', 'noopener,noreferrer');
};

const ParkplatzCard = ({ vorschlag, index, isActive, onClick }) => {
  const isRecommended = index === 0;
  const MethodIcon = getMethodIcon(vorschlag.beste_methode);
  const liveData = vorschlag.live_parking_data;
  const hasLiveData = vorschlag.has_live_data;
  
  const handleClick = () => {
    onClick(vorschlag);
    
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('focusParkplatz', {
        detail: {
          lat: vorschlag.parkplatz.latitude,
          lng: vorschlag.parkplatz.longitude,
          name: vorschlag.parkplatz.name
        }
      }));
    }, 100);
  };
  
  return (
    <div
      onClick={handleClick}
      className={`
        cursor-pointer p-5 rounded-2xl border-2 transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl
        ${isActive 
          ? 'border-indigo-500 bg-indigo-50 shadow-xl ring-2 ring-indigo-200' 
          : isRecommended 
            ? 'border-green-400 bg-green-50 hover:border-green-500 hover:shadow-lg' 
            : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
        }
      `}
    >
      {/* Header mit Live-Daten Status */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h4 className="text-xl font-bold text-gray-800 flex items-center">
              <MapPin className="w-5 h-5 mr-2 text-gray-600" />
              {vorschlag.parkplatz.name}
            </h4>
            
            <div className="flex gap-2">
              {isRecommended && (
                <span className="bg-gradient-to-r from-green-600 to-emerald-600 text-white text-xs px-3 py-1 rounded-full font-medium shadow-sm flex items-center">
                  <Star className="w-3 h-3 mr-1" />
                  Empfehlung
                </span>
              )}
              {isActive && (
                <span className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs px-3 py-1 rounded-full font-medium shadow-sm flex items-center">
                  <Target className="w-3 h-3 mr-1" />
                  Ausgewählt
                </span>
              )}
              {hasLiveData && (
                <span className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white text-xs px-3 py-1 rounded-full font-medium shadow-sm flex items-center">
                  <Database className="w-3 h-3 mr-1" />
                  Live-Daten
                </span>
              )}
            </div>
          </div>
          
          {/* Gesamtzeit prominent mit Verkehrsbewertung */}
          <div className="flex items-center gap-4 mb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-600" />
              <span className="text-3xl font-bold text-indigo-600">
                {formatMinutes(vorschlag.gesamtzeit)}
              </span>
              <span className="text-sm text-gray-500 font-medium">Gesamt</span>
            </div>
            
            {vorschlag.verkehr_bewertung && (
              <div className={`px-3 py-1 rounded-full border text-sm font-medium flex items-center ${getTrafficColor(vorschlag.verkehr_bewertung)}`}>
                <Zap className="w-4 h-4 mr-1" />
                {getTrafficLabel(vorschlag.verkehr_bewertung)} ({vorschlag.verkehr_bewertung}/5)
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 🎯 LIVE-PARKPLATZ-DATEN SEKTION */}
      {hasLiveData && liveData && (
        <div className="mb-4 bg-blue-50 rounded-xl p-4 border border-blue-200">
          <div className="flex items-center justify-between mb-3">
            <h5 className="font-semibold text-gray-800 flex items-center">
              <Database className="w-4 h-4 mr-2 text-blue-600" />
              Live-Verfügbarkeit
            </h5>
            <div className={`text-xs px-2 py-1 rounded-full font-medium ${liveData.freshness?.css_class || 'bg-gray-100 text-gray-600'}`}>
              {liveData.freshness?.status || 'Unbekannt'}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="flex items-center justify-between">
                <span className="text-gray-500 text-sm flex items-center">
                  <Car className="w-3 h-3 mr-1" />
                  Frei:
                </span>
                <span className="font-bold text-lg text-blue-600">{liveData.frei || 0}</span>
              </div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="flex items-center justify-between">
                <span className="text-gray-500 text-sm">Gesamt:</span>
                <span className="font-bold text-lg text-gray-700">{liveData.capacity || 0}</span>
              </div>
            </div>
          </div>
          
          {/* Belegungsanzeige */}
          <div className="mb-3">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Belegung:</span>
              <span className="font-medium">{liveData.occupancy?.occupancy_rate || 0}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-500 ${
                  (liveData.occupancy?.occupancy_rate || 0) <= 30 ? 'bg-green-500' :
                  (liveData.occupancy?.occupancy_rate || 0) <= 60 ? 'bg-blue-500' :
                  (liveData.occupancy?.occupancy_rate || 0) <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${liveData.occupancy?.occupancy_rate || 0}%` }}
              ></div>
            </div>
          </div>
          
          {/* Verfügbarkeits-Status */}
          <div className={`text-sm px-3 py-2 rounded-lg border flex items-center ${liveData.occupancy?.css_class || 'bg-gray-100 text-gray-600'}`}>
            {React.createElement(getAvailabilityIcon(liveData.occupancy?.availability_score || 0), { 
              className: `w-4 h-4 mr-2 ${getAvailabilityColor(liveData.occupancy?.availability_score || 0)}` 
            })}
            <span className="font-medium">{liveData.occupancy?.occupancy_text || 'Status unbekannt'}</span>
          </div>
        </div>
      )}

      {/* Routenaufschlüsselung */}
      <div className="space-y-4">
        
        {/* Phase 1: Auto-Fahrt zum Parkplatz */}
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">1</div>
              <div>
                <span className="font-semibold text-gray-800 flex items-center">
                  <Car className="w-4 h-4 mr-2" />
                  Fahrt zum Parkplatz
                </span>
                <p className="text-xs text-gray-600">Mit aktueller Verkehrslage</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-blue-600 flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {formatMinutes(vorschlag.dauer_traffic || vorschlag.dauer_auto)}
              </div>
              <div className="text-xs text-gray-500 flex items-center">
                <Route className="w-3 h-3 mr-1" />
                {formatKm(vorschlag.distanz_km)}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3 text-sm mb-3">
            <div className="bg-white rounded-lg p-2 border border-blue-100">
              <span className="text-gray-500 block flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                Normal:
              </span>
              <span className="font-medium text-gray-800">{formatMinutes(vorschlag.dauer_auto)}</span>
            </div>
            <div className="bg-white rounded-lg p-2 border border-blue-100">
              <span className="text-gray-500 block flex items-center">
                <Zap className="w-3 h-3 mr-1" />
                Live-Verkehr:
              </span>
              <span className="font-medium text-blue-600">{formatMinutes(vorschlag.dauer_traffic || vorschlag.dauer_auto)}</span>
            </div>
          </div>
          
          {/* Google Maps Navigation Button */}
          {vorschlag.navigation_links && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleGoogleMapsClick(vorschlag.navigation_links);
              }}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 shadow-sm"
            >
              <Navigation className="w-4 h-4" />
              <span>In Google Maps öffnen</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
          
          {/* Verkehrsverzögerung Warnung */}
          {vorschlag.dauer_traffic && vorschlag.dauer_traffic > vorschlag.dauer_auto && (
            <div className="mt-2 text-xs text-orange-700 bg-orange-50 px-3 py-2 rounded-lg border border-orange-200 flex items-center">
              <Zap className="w-3 h-3 mr-1 text-orange-600" />
              <span className="font-medium">Verkehrsverzögerung:</span>
              <span className="ml-1">+{vorschlag.dauer_traffic - vorschlag.dauer_auto} min durch aktuellen Verkehr</span>
            </div>
          )}
        </div>

        {/* Phase 2: Weiterreise zum Stadion */}
        <div className="bg-green-50 rounded-xl p-4 border border-green-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-white font-bold text-sm">2</div>
              <div>
                <span className="font-semibold text-gray-800 flex items-center">
                  <MethodIcon className="w-4 h-4 mr-2" />
                  Weiterreise zum Stadion
                </span>
                <p className="text-xs text-gray-600">
                  Empfohlen: {getMethodLabel(vorschlag.beste_methode)}
                </p>
              </div>
            </div>
            <div className="text-lg font-bold text-green-600 flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              {formatMinutes(
                vorschlag.beste_methode === 'transit' 
                  ? vorschlag.dauer_transit 
                  : vorschlag.dauer_walking
              )}
            </div>
          </div>
          
          {/* Vergleich der Optionen */}
          <div className="grid grid-cols-2 gap-3 text-sm mb-3">
            {vorschlag.dauer_walking && (
              <div className={`rounded-lg p-2 border ${vorschlag.beste_methode === 'walking' ? 'bg-green-100 border-green-300' : 'bg-white border-green-100'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700 flex items-center">
                    <Users className="w-3 h-3 mr-1" />
                    zu Fuß
                  </span>
                  <span className={vorschlag.beste_methode === 'walking' ? 'font-bold text-green-700' : 'font-medium text-gray-600'}>
                    {formatMinutes(vorschlag.dauer_walking)}
                  </span>
                </div>
              </div>
            )}
            {vorschlag.dauer_transit && (
              <div className={`rounded-lg p-2 border ${vorschlag.beste_methode === 'transit' ? 'bg-green-100 border-green-300' : 'bg-white border-green-100'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700 flex items-center">
                    <Car className="w-3 h-3 mr-1" />
                    ÖPNV
                  </span>
                  <span className={vorschlag.beste_methode === 'transit' ? 'font-bold text-green-700' : 'font-medium text-gray-600'}>
                    {formatMinutes(vorschlag.dauer_transit)}
                  </span>
                </div>
              </div>
            )}
          </div>
          
          {/* Navigation für Fußweg */}
          {vorschlag.beste_methode === 'walking' && vorschlag.walking_navigation && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleWalkingNavigationClick(vorschlag.walking_navigation);
              }}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 shadow-sm"
            >
              <Users className="w-4 h-4" />
              <span>Fußweg in Google Maps</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Gesamtberechnung */}
        <div className="border-t border-gray-200 pt-4">
          <div className="bg-gray-50 rounded-xl p-3 border border-gray-200">
            <div className="flex justify-between items-center text-sm mb-2">
              <span className="text-gray-600 font-medium flex items-center">
                <Route className="w-4 h-4 mr-1" />
                Gesamtberechnung:
              </span>
              <div className="flex items-center gap-2 text-gray-800 font-medium">
                <span>{formatMinutes(vorschlag.dauer_traffic || vorschlag.dauer_auto)}</span>
                <span className="text-gray-400">+</span>
                <span>{formatMinutes(
                  vorschlag.beste_methode === 'transit' 
                    ? vorschlag.dauer_transit 
                    : vorschlag.dauer_walking
                )}</span>
                <span className="text-gray-400">=</span>
                <span className="text-indigo-600 font-bold text-lg flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {formatMinutes(vorschlag.gesamtzeit)}
                </span>
              </div>
            </div>
          </div>
          
          {/* Verkehrskommentar */}
          {vorschlag.verkehr_kommentar && (
            <div className="mt-3 text-sm text-gray-700 bg-blue-50 p-3 rounded-xl border border-blue-100">
              <div className="flex items-start gap-2">
                <Zap className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <span className="italic">{vorschlag.verkehr_kommentar}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Click Indicator mit Live-Data Info */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Target className="w-3 h-3" />
            <span>Klicken für Kartenansicht</span>
            {hasLiveData && (
              <span className="ml-2 text-blue-600 font-medium flex items-center">
                <Database className="w-3 h-3 mr-1" />
                Live-Daten verfügbar
              </span>
            )}
          </span>
          <div className="flex items-center gap-2">
            <span className="bg-gray-100 px-2 py-1 rounded text-xs font-medium">#{index + 1}</span>
            {hasLiveData && liveData?.last_update && (
              <span className="text-xs text-gray-400 flex items-center">
                <Calendar className="w-3 h-3 mr-1" />
                {new Date(liveData.last_update).toLocaleTimeString('de-DE', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </span>
            )}
            <ExternalLink className="w-3 h-3 transform transition-transform group-hover:translate-x-1" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParkplatzCard;