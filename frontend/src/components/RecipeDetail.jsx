import React, { useState } from 'react';

function RecipeDetail({ recipe, onBack }) {
  if (!recipe) return null;

  const [activeTab, setActiveTab] = useState(
    recipe.image_drive_id ? 'relevant' : 'original'
  );

  const hasCropped = !!recipe.image_drive_id;
  const hasOriginal = recipe.original_drive_ids && recipe.original_drive_ids.length > 0;

  return (
    <div className="glass-card" style={{ maxWidth: '1200px', margin: '0 auto', animation: 'fadeIn 0.5s ease-out' }}>
      {/* Header / Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1rem' }}>
        <button 
          onClick={onBack}
          style={{ 
            background: 'transparent', 
            border: '1px solid var(--glass-border)', 
            color: 'var(--text-main)', 
            boxShadow: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.2rem',
            borderRadius: '2rem',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
          className="hover-scale"
        >
          ← Back to Library
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={() => {
              if (window.confirm("Are you sure you want to delete this recipe? This action cannot be undone.")) {
                fetch(`/api/recipes/${recipe.id}`, { method: 'DELETE' })
                  .then(res => {
                    if (res.ok) {
                      onBack();
                    } else {
                      alert("Failed to delete recipe");
                    }
                  })
                  .catch(err => alert("Error deleting recipe: " + err.message));
              }
            }}
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#ef4444',
              padding: '0.6rem 1.2rem',
              borderRadius: '2rem',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              fontWeight: '600',
              boxShadow: 'none'
            }}
            className="hover-scale"
          >
            Delete Recipe
          </button>
          <h2 style={{ margin: 0, color: 'var(--primary)', fontWeight: '700' }}>Recipe Viewer</h2>
        </div>
      </div>

      {/* Main Layout: Side-by-Side original scan and parsed text */}
      <div className="two-column-layout recipe-detail">
        {/* Left Side: Recipe Images (Relevant Cropped vs. Original) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {hasCropped && hasOriginal ? (
            <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.25)', padding: '0.3rem', borderRadius: '2rem', border: '1px solid var(--glass-border)' }}>
              <button
                type="button"
                onClick={() => setActiveTab('relevant')}
                style={{
                  flex: 1,
                  background: activeTab === 'relevant' ? 'var(--primary)' : 'transparent',
                  border: 'none',
                  color: activeTab === 'relevant' ? '#fff' : 'var(--text-muted)',
                  padding: '0.5rem 1rem',
                  borderRadius: '2rem',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                  transition: 'all 0.3s ease',
                  boxShadow: 'none'
                }}
              >
                Relevant Photo
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('original')}
                style={{
                  flex: 1,
                  background: activeTab === 'original' ? 'var(--primary)' : 'transparent',
                  border: 'none',
                  color: activeTab === 'original' ? '#fff' : 'var(--text-muted)',
                  padding: '0.5rem 1rem',
                  borderRadius: '2rem',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                  transition: 'all 0.3s ease',
                  boxShadow: 'none'
                }}
              >
                Original Scan{recipe.original_drive_ids.length > 1 ? 's' : ''}
              </button>
            </div>
          ) : (
            <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
              {activeTab === 'relevant' ? 'Recipe Photo' : 'Original Scan'}
            </h3>
          )}
          
          {activeTab === 'relevant' && recipe.image_drive_id && (
            <div style={{ 
              borderRadius: '16px', 
              overflow: 'hidden', 
              boxShadow: '0 12px 40px rgba(0,0,0,0.6)', 
              border: '1px solid var(--glass-border)',
              background: 'rgba(0,0,0,0.3)',
              position: 'sticky',
              top: '2rem'
            }}>
              <img 
                src={`/api/files/${recipe.image_drive_id}`} 
                alt="Recipe Photo" 
                style={{ width: '100%', height: 'auto', display: 'block', maxHeight: '75vh', objectFit: 'contain' }} 
              />
            </div>
          )}

          {activeTab === 'original' && recipe.original_drive_ids && recipe.original_drive_ids.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'sticky', top: '2rem', maxHeight: '100vh', overflowY: 'auto', paddingRight: '0.5rem' }}>
              {recipe.original_drive_ids.map((drive_id, idx) => (
                <div key={idx} style={{ 
                  borderRadius: '16px', 
                  overflow: 'hidden', 
                  boxShadow: '0 12px 40px rgba(0,0,0,0.6)', 
                  border: '1px solid var(--glass-border)',
                  background: 'rgba(0,0,0,0.3)',
                  flexShrink: 0
                }}>
                  <img 
                    src={`/api/files/${drive_id}`} 
                    alt={`Original Scan ${idx + 1}`} 
                    style={{ width: '100%', height: 'auto', display: 'block', objectFit: 'contain' }} 
                  />
                </div>
              ))}
            </div>
          )}

          {!recipe.image_drive_id && (!recipe.original_drive_ids || recipe.original_drive_ids.length === 0) && (
            <div style={{ 
              aspectRatio: '3/4', 
              background: 'rgba(0,0,0,0.2)', 
              borderRadius: '16px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              color: 'var(--text-muted)',
              border: '1px dashed var(--glass-border)'
            }}>
              No scanned image available
            </div>
          )}
        </div>

        {/* Right Side: Structured Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Title and Metadata */}
          <div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: '800', margin: '0 0 1rem 0', color: '#fff', lineHeight: '1.2' }}>
              {recipe.title}
            </h1>
            
            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
              {recipe.servings && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                  <span>👥 {recipe.servings}</span>
                </div>
              )}
              {recipe.cooking_time && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                  <span>⏱️ {recipe.cooking_time}</span>
                </div>
              )}
            </div>

            {recipe.tags && recipe.tags.length > 0 && (
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '1.2rem' }}>
                {recipe.tags.map((tag, i) => (
                  <span 
                    key={i} 
                    style={{ 
                      background: 'rgba(255,255,255,0.08)', 
                      border: '1px solid rgba(255,255,255,0.1)', 
                      padding: '0.3rem 0.8rem', 
                      borderRadius: '2rem', 
                      fontSize: '0.8rem',
                      color: 'var(--primary-light)'
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Ingredients section with interactive check-off items */}
          <div className="glass-card" style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: 'var(--primary)', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>Ingredients</h3>
            <ul style={{ paddingLeft: '1.2rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              {recipe.ingredients?.map((ing, i) => (
                <li key={i} style={{ color: 'var(--text-main)', fontSize: '1.05rem', lineHeight: '1.5' }}>
                  {ing}
                </li>
              ))}
            </ul>
          </div>

          {/* Instructions Section */}
          <div>
            <h3 style={{ margin: '0 0 1.2rem 0', color: 'var(--primary)', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>Instructions</h3>
            <ol style={{ paddingLeft: '1.2rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
              {recipe.instructions?.map((step, i) => (
                <li key={i} style={{ color: 'var(--text-main)', fontSize: '1.05rem', lineHeight: '1.6', paddingLeft: '0.5rem' }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          {/* Notes Section */}
          {recipe.notes && (
            <div style={{ borderLeft: '4px solid var(--primary)', paddingLeft: '1.2rem', background: 'rgba(255,255,255,0.02)', padding: '1rem 1.2rem', borderRadius: '0 8px 8px 0' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--primary-light)', fontSize: '1rem' }}>Recipe Notes</h4>
              <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: '1.5', fontStyle: 'italic' }}>
                {recipe.notes}
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default RecipeDetail;
