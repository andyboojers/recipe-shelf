import React, { useState } from 'react';

function DraftEditor({ recipe, onSave, onCancel }) {
  const [saving, setSaving] = useState(false);

  if (!recipe) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    const formData = new FormData(e.target);
    const updatedRecipe = {
      draft_id: recipe.draft_id,
      title: formData.get('title'),
      ingredients: formData.get('ingredients').split('\n').filter(i => i.trim()),
      instructions: formData.get('instructions').split('\n\n').filter(i => i.trim()),
      notes: formData.get('notes'),
    };
    
    try {
      const res = await fetch('/api/recipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedRecipe),
      });
      if (!res.ok) throw new Error('Save failed');
      onSave(); // call parent onSave on success
    } catch (err) {
      alert("Error saving recipe.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="draft-editor" style={{ padding: '20px', maxWidth: '900px', margin: '0 auto' }}>
      <h2>Edit Recipe Draft</h2>
      
      <div style={{ display: 'flex', gap: '30px', marginTop: '20px' }}>
        <div style={{ flex: 1 }}>
          {recipe.extracted_image_base64 ? (
            <img 
              src={recipe.extracted_image_base64} 
              alt="Extracted Recipe" 
              style={{ maxWidth: '100%', borderRadius: '8px', boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }} 
            />
          ) : (
            <div style={{ padding: '40px', backgroundColor: '#f0f0f0', textAlign: 'center', borderRadius: '8px' }}>
              No image extracted
            </div>
          )}
        </div>
        
        <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold' }}>Title:</label>
            <input 
              type="text" 
              name="title"
              defaultValue={recipe.title} 
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }} 
            />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold' }}>Ingredients:</label>
            <textarea 
              name="ingredients"
              defaultValue={recipe.ingredients?.join('\n')} 
              rows={6} 
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', fontFamily: 'inherit' }} 
            />
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold' }}>Instructions (separated by empty line):</label>
            <textarea 
              name="instructions"
              defaultValue={recipe.instructions?.join('\n\n')} 
              rows={8} 
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', fontFamily: 'inherit' }} 
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontWeight: 'bold' }}>Notes:</label>
            <textarea 
              name="notes"
              defaultValue={recipe.notes} 
              rows={3} 
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', fontFamily: 'inherit' }} 
            />
          </div>
        </div>
      </div>

      <div style={{ marginTop: '30px', display: 'flex', gap: '15px', justifyContent: 'flex-end' }}>
        <button 
          type="button"
          onClick={onCancel}
          style={{ padding: '10px 20px', borderRadius: '4px', border: '1px solid #ccc', cursor: 'pointer', background: 'white' }}
        >
          Cancel
        </button>
        <button 
          type="submit"
          disabled={saving}
          style={{ padding: '10px 20px', borderRadius: '4px', border: 'none', cursor: saving ? 'not-allowed' : 'pointer', background: saving ? '#ccc' : '#007bff', color: 'white', fontWeight: 'bold' }}
        >
          {saving ? 'Saving...' : 'Save Recipe'}
        </button>
      </div>
    </form>
  );
}

export default DraftEditor;
