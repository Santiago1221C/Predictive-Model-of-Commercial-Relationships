import React from 'react';

const Logo: React.FC = () => {
  return (
    <div className="flex items-center space-x-3">
      {/* Icono gráfico */}
      <div className="relative">
        {/* Línea curva base */}
        <svg width="40" height="20" viewBox="0 0 40 20" className="text-teal-700">
          <path
            d="M 5 15 Q 20 5 35 15"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
          />
        </svg>
        
        {/* Hojas en arco */}
        <div className="absolute top-0 left-0 w-full h-full">
          <svg width="40" height="20" viewBox="0 0 40 20" className="text-green-400">
            {/* Hoja central */}
            <ellipse cx="20" cy="8" rx="3" ry="6" fill="currentColor" transform="rotate(-10 20 8)" />
            {/* Hoja izquierda */}
            <ellipse cx="12" cy="10" rx="2.5" ry="5" fill="currentColor" transform="rotate(-25 12 10)" />
            {/* Hoja derecha */}
            <ellipse cx="28" cy="10" rx="2.5" ry="5" fill="currentColor" transform="rotate(25 28 10)" />
            {/* Hojas exteriores */}
            <ellipse cx="8" cy="12" rx="2" ry="4" fill="currentColor" transform="rotate(-40 8 12)" />
            <ellipse cx="32" cy="12" rx="2" ry="4" fill="currentColor" transform="rotate(40 32 12)" />
          </svg>
        </div>
      </div>
      
      {/* Texto */}
      <div className="flex flex-col">
        <span className="text-xs font-bold text-teal-700 tracking-wider">GRUPO</span>
        <div className="flex items-center">
          <span className="text-xl font-bold text-teal-700">Bios</span>
          {/* Hoja en el punto de la i */}
          <div className="relative">
            <div className="w-2 h-2 bg-green-400 rounded-full ml-1"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Logo;
