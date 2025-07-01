import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { 
  MapPin, 
  Clock, 
  Car, 
  User, 
  Calendar,
  TrendingUp,
  Navigation,
  Repeat
} from "lucide-react";
import axiosClient from "../api/axiosClient";

const DashboardPage = () => {
  const [profil, setProfil] = useState(null);
  const [recentRoutes, setRecentRoutes] = useState([]);
  const [stats, setStats] = useState({
    totalRoutes: 0,
    avgDuration: 0,
    favoriteParking: null
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        // Profil laden
        const profilRes = await axiosClient.get("api/profil/");
        setProfil(profilRes.data);

        // Routen-Statistiken laden
        try {
          const routesRes = await axiosClient.get("api/routen/");
          const routes = routesRes.data || [];
          setRecentRoutes(routes.slice(0, 5)); // Letzte 5 Routen
          
          // Echte Statistiken berechnen
          if (routes.length > 0) {
            const totalMinutes = routes.reduce((sum, r) => sum + (r.dauer_minuten || 0), 0);
            const avgDur = totalMinutes / routes.length;
            
            // Häufigsten Parkplatz finden
            const parkingCounts = {};
            routes.forEach(route => {
              if (route.parkplatz?.name) {
                parkingCounts[route.parkplatz.name] = (parkingCounts[route.parkplatz.name] || 0) + 1;
              }
            });
            
            const mostUsedParking = Object.keys(parkingCounts).length > 0 
              ? Object.keys(parkingCounts).reduce((a, b) => parkingCounts[a] > parkingCounts[b] ? a : b)
              : null;
            
            setStats({
              totalRoutes: routes.length,
              avgDuration: Math.round(avgDur),
              favoriteParking: mostUsedParking
            });
          }
        } catch (routeError) {
          console.log("Routen konnten nicht geladen werden:", routeError);
          // Leere Werte setzen statt Fehler
          setStats({ totalRoutes: 0, avgDuration: 0, favoriteParking: null });
          setRecentRoutes([]);
        }
        
      } catch (err) {
        console.error("Fehler beim Laden der Dashboard-Daten:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatDuration = (minutes) => {
    if (!minutes) return "—";
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m}min` : `${m}min`;
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Guten Morgen";
    if (hour < 18) return "Guten Tag";
    return "Guten Abend";
  };

  const repeatRoute = (route) => {
    // Navigation zur Routenplanung mit vorausgefüllter Adresse
    const params = new URLSearchParams({ address: route.start_adresse });
    window.location.href = `/routenplanung?${params.toString()}`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="text-lg font-medium text-gray-700">Dashboard wird geladen...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!profil) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
          <div className="text-center">
            <User className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-800 mb-2">Profil nicht verfügbar</h2>
            <p className="text-gray-600">Bitte überprüfen Sie Ihre Anmeldung.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        
        {/* Welcome Header */}
        <div className="mb-8">
          <div className="bg-white/70 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
                  {getGreeting()}, {profil.username}!
                </h1>
                <p className="text-xl text-gray-600">
                  Willkommen in Ihrem MatchRoute Dashboard
                </p>
              </div>
              <div className="hidden md:block">
                <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-3xl font-bold shadow-lg">
                  {profil.username.charAt(0).toUpperCase()}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Real Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          
          {/* Total Routes */}
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6 hover:shadow-xl transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Geplante Routen</p>
                <p className="text-3xl font-bold text-indigo-600">{stats.totalRoutes}</p>
              </div>
              <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                <MapPin className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
          </div>

          {/* Average Duration */}
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6 hover:shadow-xl transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Ø Anreisezeit</p>
                <p className="text-3xl font-bold text-green-600">{formatDuration(stats.avgDuration)}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <Clock className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          {/* Favorite Parking */}
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6 hover:shadow-xl transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Lieblings-Parkplatz</p>
                <p className="text-lg font-bold text-purple-600 truncate" title={stats.favoriteParking}>
                  {stats.favoriteParking || "Noch keine Daten"}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <Car className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column - Team Info & Recent Routes */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Team & Stadium Card */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden">
              <div className="relative">
                {profil.stadion?.bild_url && (
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={profil.stadion.bild_url}
                      alt={profil.stadion.name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                    <div className="absolute bottom-4 left-6 text-white">
                      <h3 className="text-2xl font-bold">{profil.stadion.name}</h3>
                      <p className="text-sm opacity-90 flex items-center">
                        <MapPin className="w-4 h-4 mr-1" />
                        {profil.stadion.adresse}
                      </p>
                    </div>
                  </div>
                )}
                
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                        <User className="w-5 h-5 mr-2" />
                        Ihr Verein
                      </h4>
                      {profil.lieblingsverein ? (
                        <div className="space-y-2">
                          <div className="flex items-center space-x-3">
                            <span className="font-bold text-lg text-indigo-600">
                              {profil.lieblingsverein.name}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            <p><span className="font-medium">Liga:</span> {profil.lieblingsverein.liga}</p>
                            <p><span className="font-medium">Stadt:</span> {profil.lieblingsverein.stadt}</p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-gray-500 italic">Kein Lieblingsverein hinterlegt</p>
                      )}
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
                        <TrendingUp className="w-5 h-5 mr-2" />
                        Ihre Statistiken
                      </h4>
                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Routen geplant:</span>
                            <span className="font-semibold">{stats.totalRoutes}</span>
                          </div>
                          {stats.avgDuration > 0 && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Ø Dauer:</span>
                              <span className="font-semibold">{formatDuration(stats.avgDuration)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Routes */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                <Clock className="w-6 h-6 mr-2" />
                Letzte Routen
              </h3>
              
              {recentRoutes.length > 0 ? (
                <div className="space-y-4">
                  {recentRoutes.map((route) => (
                    <div key={route.id} className="bg-white rounded-xl p-4 border border-gray-200 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <MapPin className="w-4 h-4 text-gray-500" />
                            <span className="font-medium text-gray-800">{route.start_adresse}</span>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span className="flex items-center">
                              <Car className="w-4 h-4 mr-1" />
                              {route.parkplatz?.name || "Parkplatz"}
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              {formatDuration(route.dauer_minuten)}
                            </span>
                            <span className="flex items-center">
                              <Calendar className="w-4 h-4 mr-1" />
                              {new Date(route.erstelldatum).toLocaleDateString('de-DE')}
                            </span>
                          </div>
                        </div>
                        <button 
                          onClick={() => repeatRoute(route)}
                          className="ml-4 bg-indigo-100 text-indigo-600 px-3 py-2 rounded-lg text-sm font-medium hover:bg-indigo-200 transition-colors flex items-center space-x-1"
                        >
                          <Repeat className="w-4 h-4" />
                          <span>Wiederholen</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">Noch keine Routen geplant</p>
                  <Link
                    to="/routenplanung"
                    className="inline-flex items-center space-x-2 bg-indigo-600 text-white px-6 py-2 rounded-xl font-medium hover:bg-indigo-700 transition-colors"
                  >
                    <Navigation className="w-4 h-4" />
                    <span>Erste Route planen</span>
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Quick Actions */}
          <div className="space-y-6">
            
            {/* Quick Actions */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                <Navigation className="w-5 h-5 mr-2" />
                Schnellaktionen
              </h3>
              
              <div className="space-y-3">
                <Link
                  to="/routenplanung"
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 rounded-xl font-medium hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 flex items-center justify-center space-x-2 shadow-lg"
                >
                  <MapPin className="w-5 h-5" />
                  <span>Neue Route planen</span>
                </Link>
              </div>
            </div>

            {/* Profile Completion (nur wenn unvollständig) */}
            {(!profil.lieblingsverein || !profil.stadion) && (
              <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6">
                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Profil vervollständigen
                </h3>
                
                <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-200">
                  <p className="text-sm text-yellow-800 mb-3">
                    Vervollständigen Sie Ihr Profil für personalisierte Routenempfehlungen.
                  </p>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span>Lieblingsverein:</span>
                      <span className={profil.lieblingsverein ? "text-green-600" : "text-red-600"}>
                        {profil.lieblingsverein ? "✓" : "✗"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Stadion-Info:</span>
                      <span className={profil.stadion ? "text-green-600" : "text-red-600"}>
                        {profil.stadion ? "✓" : "✗"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;