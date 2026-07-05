import React, { useState } from 'react';

function DraftEditor({ draft, onSave, onCancel }) {
  const [saving, setSaving] = useState(false);

  if (!draft) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    const formData = new FormData(e.target);
    const updatedRecipe = {
      draft_id: draft.id,
      title: formData.get('title'),
      ingredients: formData.get('ingredients').split('\n').filter(i => i.trim()),
      instructions: formData.get('instructions').split('\n\n').filter(i => i.trim()),
      notes: formData.get('notes'),
      servings: formData.get('servings'),
      cooking_time: formData.get('cooking_time'),
      tags: formData.get('tags').split(',').map(t => t.trim()).filter(t => t),
    };
    
    try {
      const res = await fetch('/api/recipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedRecipe),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 409 && errorData.detail?.duplicate_detected) {
            const msg = errorData.detail.message || `This looks very similar to your existing recipe. Do you still want to save it as a new recipe?`;
            if (window.confirm(msg)) {
                // User chose to save anyway, set force_save and resubmit
                updatedRecipe.force_save = true;
                const forceRes = await fetch('/api/recipes', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(updatedRecipe),
                });
                if (!forceRes.ok) {
                   const forceErr = await forceRes.json().catch(() => ({}));
                   throw new Error(forceErr.detail || 'Save failed after overriding duplicate');
                }
                onSave();
                return;
            } else {
                // User cancelled the save
                return;
            }
        }
        throw new Error(errorData.detail || 'Save failed');
      }
      onSave();
    } catch (err) {
      alert("Error saving recipe: " + (err.message || err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="glass-card" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ color: 'var(--primary)' }}>Edit Recipe Draft</h2>
      </div>
      
      <div className="two-column-layout">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {draft.original_image_paths && draft.original_image_paths.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'sticky', top: '2rem' }}>
              {draft.original_image_paths.map((_, idx) => (
                <img 
                  key={idx}
                  src={`/api/drafts/${draft.id}/original-image?page=${idx}`} 
                  alt={`Original Scan ${idx + 1}`} 
                  style={{ width: '100%', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.5)' }} 
                />
              ))}
            </div>
          ) : draft.image_path ? (
            <div style={{ position: 'sticky', top: '2rem' }}>
              <img 
                src={`/api/drafts/${draft.id}/image`} 
                alt="Recipe" 
                style={{ width: '100%', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.5)' }} 
              />
            </div>
          ) : (
            <div style={{ aspectRatio: '3/4', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              No image available
            </div>
          )}
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <label>Title</label>
            <input type="text" name="title" defaultValue={draft.title} required />
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label>Servings</label>
              <input type="text" name="servings" defaultValue={draft.servings || ''} placeholder="e.g. 4 people" />
            </div>
            <div>
              <label>Cooking Time</label>
              <input type="text" name="cooking_time" defaultValue={draft.cooking_time || ''} placeholder="e.g. 45 mins" />
            </div>
          </div>
          
          <div>
            <label>Tags (comma separated)</label>
            <input type="text" name="tags" defaultValue={draft.tags?.join(', ') || ''} placeholder="e.g. dinner, vegetarian" />
          </div>
          
          <div>
            <label>Ingredients (one per line)</label>
            <textarea name="ingredients" defaultValue={draft.ingredients?.join('\n')} rows={6} required />
          </div>
          
          <div>
            <label>Instructions (separate steps with an empty line)</label>
            <textarea name="instructions" defaultValue={draft.instructions?.join('\n\n')} rows={8} required />
          </div>

          <div>
            <label>Notes (optional)</label>
            <textarea name="notes" defaultValue={draft.notes} rows={3} />
          </div>
        </div>
      </div>

      <div style={{ marginTop: '3rem', display: 'flex', gap: '1rem', justifyContent: 'flex-end', borderTop: '1px solid var(--glass-border)', paddingTop: '2rem' }}>
        <button 
          type="button"
          onClick={onCancel}
          style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: 'var(--text-main)', boxShadow: 'none' }}
        >
          Cancel
        </button>
        <button type="submit" disabled={saving}>
          {saving ? 'Saving to Drive...' : 'Save Recipe'}
        </button>
      </div>
    </form>
  );
}

export default DraftEditor;
