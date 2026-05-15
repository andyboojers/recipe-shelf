import React, { useState } from 'react';

function ImageSelector({ candidateImages, onSelect, onSkip }) {
  const [saving, setSaving] = useState(false);

  const handleSelect = async (base64Image) => {
    setSaving(true);
    try {
      await onSelect(base64Image);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="glass-card" style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
      <h2 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Select an Image</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        We found these photos on the page. Which one belongs to your selected recipe?
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {candidateImages.map((imgStr, idx) => (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '12px' }}>
            <img 
              src={`data:image/jpeg;base64,${imgStr}`} 
              alt={`Candidate ${idx}`} 
              style={{ width: '100%', borderRadius: '8px', objectFit: 'contain', aspectRatio: '1' }} 
            />
            <button 
              onClick={() => handleSelect(imgStr)} 
              disabled={saving}
              style={{ width: '100%' }}
            >
              Select
            </button>
          </div>
        ))}
      </div>

      <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '1.5rem' }}>
        <button 
          onClick={onSkip} 
          disabled={saving}
          style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: 'var(--text-main)' }}
        >
          Skip / No Image
        </button>
      </div>
    </div>
  );
}

export default ImageSelector;
