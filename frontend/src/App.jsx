import React, { useState, useEffect } from 'react';
import ImageUploader from './components/ImageUploader';
import RecipeSelector from './components/RecipeSelector';
import ImageSelector from './components/ImageSelector';
import DraftEditor from './components/DraftEditor';
import RecipeDetail from './components/RecipeDetail';

function App() {
  // State machine: 'idle' | 'fetching_drafts' | 'selecting' | 'selecting_image' | 'editing' | 'viewing'
  const [viewState, setViewState] = useState('idle');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  
  // Workflow data
  const [draftIds, setDraftIds] = useState([]);
  const [candidateImages, setCandidateImages] = useState([]);
  const [loadedDrafts, setLoadedDrafts] = useState([]);
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  // Search recipes
  useEffect(() => {
    if (viewState === 'idle') {
      fetch(`/api/recipes?q=${searchQuery}`)
        .then(res => res.json())
        .then(data => setSearchResults(data.results || []))
        .catch(err => console.error("Search failed", err));
    }
  }, [searchQuery, viewState]);

  // Handle successful upload
  const handleUploadComplete = async (data) => {
    const ids = data.draft_ids || [];
    setDraftIds(ids);
    setCandidateImages(data.candidate_images || []);
    setViewState('fetching_drafts');
    
    try {
      const draftPromises = ids.map(id => 
        fetch(`/api/drafts/${id}`).then(res => {
          if (!res.ok) throw new Error('Failed to fetch draft');
          return res.json();
        })
      );
      const drafts = await Promise.all(draftPromises);
      setLoadedDrafts(drafts);
      
      if (drafts.length === 1) {
        setSelectedDraft(drafts[0]);
        if (data.candidate_images && data.candidate_images.length > 0) {
          setViewState('selecting_image');
        } else {
          setViewState('editing');
        }
      } else if (drafts.length > 1) {
        setViewState('selecting');
      } else {
        alert("Gemini could not find any recipes in this image.");
        setViewState('idle');
      }
    } catch (err) {
      alert("Error loading drafts: " + err.message);
      setViewState('idle');
    }
  };

  const resetFlow = () => {
    setDraftIds([]);
    setCandidateImages([]);
    setLoadedDrafts([]);
    setSelectedDraft(null);
    setViewState('idle');
  };

  const handleRecipeSelect = (draft) => {
    setSelectedDraft(draft);
    if (candidateImages.length > 0) {
      setViewState('selecting_image');
    } else {
      setViewState('editing');
    }
  };

  const handleImageSelect = async (base64Image) => {
    try {
      const res = await fetch(`/api/drafts/${selectedDraft.id}/image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_data: base64Image })
      });
      if (!res.ok) throw new Error('Failed to attach image');
      const data = await res.json();
      setSelectedDraft(prev => ({ ...prev, image_path: data.image_path }));
    } catch (err) {
      alert("Error attaching image: " + err.message);
    }
    setViewState('editing');
  };

  const handleImageSkip = () => {
    setViewState('editing');
  };

  const handleRecipeClick = (recipe) => {
    setSelectedRecipe(recipe);
    setViewState('viewing');
  };

  return (
    <div>
      <header className="app-header">
        <h1 className="app-title">Recipe Shelf</h1>
        <p className="app-subtitle">Your AI-powered culinary archive</p>
      </header>

      {viewState === 'idle' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
          <ImageUploader onUploadComplete={handleUploadComplete} />
          
          <div className="glass-card">
            <h2 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>Library</h2>
            <input 
              type="text" 
              placeholder="Search recipes by title, ingredient, or tag..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ marginBottom: '2rem' }}
            />
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
              {searchResults.map(recipe => (
                <div 
                  key={recipe.id} 
                  className="glass-card hover-scale" 
                  onClick={() => handleRecipeClick(recipe)}
                  style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', cursor: 'pointer' }}
                >
                  <h3>{recipe.title || "Untitled"}</h3>
                  <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    <span>{recipe.ingredients?.length || 0} ingredients</span>
                    {recipe.cooking_time && <span>• {recipe.cooking_time}</span>}
                  </div>
                  {recipe.tags && recipe.tags.length > 0 && (
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                      {recipe.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} style={{ background: 'rgba(255,255,255,0.1)', padding: '0.2rem 0.6rem', borderRadius: '1rem', fontSize: '0.75rem' }}>
                          {tag}
                        </span>
                      ))}
                      {recipe.tags.length > 3 && <span style={{ fontSize: '0.75rem', alignSelf: 'center' }}>+{recipe.tags.length - 3}</span>}
                    </div>
                  )}
                </div>
              ))}
              {searchResults.length === 0 && (
                <p style={{ color: 'var(--text-muted)' }}>No recipes found.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {viewState === 'fetching_drafts' && (
        <div className="glass-card loader-pulse" style={{ textAlign: 'center', padding: '4rem' }}>
          <h2 style={{ color: 'var(--primary)' }}>Loading Drafts...</h2>
        </div>
      )}

      {viewState === 'selecting' && (
        <RecipeSelector 
          drafts={loadedDrafts} 
          onSelect={handleRecipeSelect}
          onCancel={resetFlow}
        />
      )}

      {viewState === 'selecting_image' && (
        <ImageSelector
          candidateImages={candidateImages}
          onSelect={handleImageSelect}
          onSkip={handleImageSkip}
        />
      )}

      {viewState === 'editing' && (
        <DraftEditor 
          draft={selectedDraft} 
          onSave={resetFlow}
          onCancel={resetFlow}
        />
      )}

      {viewState === 'viewing' && (
        <RecipeDetail 
          recipe={selectedRecipe}
          onBack={() => {
            setSelectedRecipe(null);
            setViewState('idle');
          }}
        />
      )}
    </div>
  );
}

export default App;
