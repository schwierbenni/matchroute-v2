import React from 'react';

const LoadingSpinner = ({ message = "Lädt...", size = "default" }) => {
  const sizeClasses = {
    small: "w-4 h-4",
    default: "w-8 h-8",
    large: "w-12 h-12"
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
      <div className="flex flex-col items-center justify-center space-y-4">
        {/* Animated Route Calculation */}
        <div className="relative">
          {/* Car Animation */}
          <div className="relative w-32 h-16 mb-4">
            {/* Road */}
            <div className="absolute bottom-0 w-full h-2 bg-gray-300 rounded-full"></div>
            <div className="absolute bottom-0 w-full h-1 bg-gray-400 rounded-full"></div>
            
            {/* Dashed center line */}
            <div className="absolute bottom-0.5 w-full h-0.5 bg-white rounded-full opacity-60">
              <div className="flex space-x-2 h-full animate-pulse">
                <div className="w-4 h-full bg-gray-500 rounded-full"></div>
                <div className="w-4 h-full bg-gray-500 rounded-full"></div>
                <div className="w-4 h-full bg-gray-500 rounded-full"></div>
                <div className="w-4 h-full bg-gray-500 rounded-full"></div>
              </div>
            </div>
            
            {/* Moving Car */}
            <div className="absolute bottom-2 animate-bounce">
              <div className="text-2xl animate-pulse">🚗</div>
            </div>
            
            {/* Destination */}
            <div className="absolute bottom-2 right-0 text-2xl">🏟️</div>
          </div>
          
          {/* Main Spinner */}
          <div className="relative">
            <div className={`${sizeClasses[size]} border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto`}></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2 h-2 bg-indigo-600 rounded-full animate-ping"></div>
            </div>
          </div>
        </div>

        {/* Loading Steps */}
        <div className="w-full max-w-sm">
          <div className="flex justify-between text-xs text-gray-500 mb-2">
            <span>Start</span>
            <span>Berechnung</span>
            <span>Fertig</span>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-indigo-600 to-purple-600 h-2 rounded-full transition-all duration-1000 animate-pulse"
              style={{
                width: message.includes("Fertig") ? "100%" : 
                       message.includes("Kartendaten") ? "80%" : 
                       message.includes("berechnet") ? "60%" : "30%"
              }}
            ></div>
          </div>
        </div>

        {/* Message */}
        <div className="text-center space-y-2">
          <p className="text-lg font-medium text-gray-800 animate-pulse">
            {message}
          </p>
          
          <div className="flex items-center justify-center space-x-1 text-indigo-600">
            <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: "0ms"}}></div>
            <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: "150ms"}}></div>
            <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{animationDelay: "300ms"}}></div>
          </div>
        </div>

        {/* Fun Facts during loading */}
        <div className="text-center mt-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
          <p className="text-sm text-indigo-700 font-medium mb-2">💡 Wussten Sie schon?</p>
          <p className="text-xs text-indigo-600">
            Wir analysieren Verkehrsdaten, Parkplatzkapazitäten und ÖPNV-Verbindungen, 
            um Ihnen die beste Route zu berechnen.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;