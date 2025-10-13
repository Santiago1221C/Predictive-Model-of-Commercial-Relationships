import React from 'react';

const Logo = () => {
  return (
    <div className="flex items-center space-x-3">
      <img 
        src="/grupo_bios.png" 
        alt="Grupo Bios" 
        className="w-10 h-10 object-contain"
      />
      <div>
        <span className="text-2xl font-bold text-[#00657F]">Grupo</span>
        <span className="text-2xl font-bold text-[#AACF00]"> Bios</span>
      </div>
    </div>
  );
};

export default Logo;
