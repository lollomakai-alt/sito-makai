import React, { useEffect, useState } from 'react';

export default function MenuSection() {
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch dei dati dal backend Python su Vercel
    fetch('/api/menu')
      .then((res) => res.json())
      .then((data) => {
        // Assumiamo che la risposta sia { menu: [...] } come definito nel backend
        setMenuItems(data.menu);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Errore menu:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="text-center text-amber-600 py-10">Caricamento tesori in corso...</div>;
  }

  return (
    // Griglia responsive: 1 colonna su mobile, 2 su tablet, 3 su desktop
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
      {menuItems.map((item) => (
        <div key={item.id} className="bg-stone-900 rounded-2xl overflow-hidden border border-amber-900/30 shadow-lg group transition hover:border-amber-500/50 flex flex-col">
          
          {/* CONTENITORE IMMAGINE (Alta visibilità) */}
          <div className="aspect-[4/3] w-full overflow-hidden bg-stone-800">
            <img 
              src={item.image} // L'URL arriva dal backend
              alt={item.name}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              loading="lazy" // Caricamento pigro per le performance
            />
          </div>

          {/* CONTENITORE TESTO */}
          <div className="p-6 flex-1 flex flex-col">
            <div className="flex justify-between items-start mb-3">
              <h4 className="text-xl font-bold text-white group-hover:text-amber-300 transition">{item.name}</h4>
              <span className="bg-amber-950 text-amber-200 text-xs font-mono px-3 py-1 rounded-full border border-amber-700/50">
                {item.category}
              </span>
            </div>
            
            <p className="text-stone-300 text-sm mb-5 flex-1">{item.description}</p>
            
            <div className="flex justify-between items-center mt-auto pt-4 border-t border-amber-900/30">
              <span className="text-2xl font-extrabold text-amber-400">€ {item.price.toFixed(2)}</span>
              <button className="bg-stone-800 text-amber-100 text-xs px-4 py-2 rounded-lg font-semibold hover:bg-amber-600 hover:text-stone-950 transition">
                Aggiungi al Vassoio
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}