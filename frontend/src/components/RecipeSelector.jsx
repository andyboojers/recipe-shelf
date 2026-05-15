import React from 'react';

function RecipeSelector({ drafts, onSelect, onCancel }) {
  return (
    <div className="glass-card" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Multiple Recipes Detected</h2>
          <p style={{ color: 'var(--text-muted)' }}>Gemini found {drafts.length} distinct recipes on this page. Which one would you like to edit and save?</p>
        </div>
        <button onClick={onCancel} style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: 'var(--text-main)' }}>
          Cancel
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {drafts.map((draft) => (
          <div 
            key={draft.id} 
            className="glass-card" 
            onClick={() => onSelect(draft)}
            style={{ 
              cursor: 'pointer',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              background: 'rgba(255,255,255,0.02)'
            }}
          >
            {draft.image_path ? (
              <img 
                src={`/api/files/${draft.image_path}`} 
                alt={draft.title} 
                style={{ width: '100%', height: '160px', objectFit: 'cover', borderRadius: '8px' }} 
              />
            ) : (
              <div style={{ height: '160px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                No cropped image
              </div>
            )}
            <div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>{draft.title || 'Untitled Recipe'}</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                {draft.ingredients?.length || 0} ingredients
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RecipeSelector;
