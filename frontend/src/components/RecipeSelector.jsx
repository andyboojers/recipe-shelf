import React from 'react';

function RecipeSelector({ recipes, onSelect }) {
  return (
    <div className="recipe-selector" style={{ padding: '20px' }}>
      <h2>We found multiple recipes!</h2>
      <p>Which one would you like to save?</p>
      <div className="recipe-cards" style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
        {recipes.map((recipe, index) => (
          <div 
            key={index} 
            className="card" 
            onClick={() => onSelect(recipe)}
            style={{ 
              border: '1px solid #ccc', 
              padding: '15px', 
              borderRadius: '8px',
              cursor: 'pointer',
              width: '250px'
            }}
          >
            {recipe.extracted_image_base64 && (
              <img 
                src={recipe.extracted_image_base64} 
                alt={recipe.title} 
                style={{ width: '100%', height: '150px', objectFit: 'cover', borderRadius: '4px' }} 
              />
            )}
            <h3 style={{ marginTop: '10px' }}>{recipe.title || 'Untitled Recipe'}</h3>
            <p>{recipe.ingredients?.length || 0} ingredients</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RecipeSelector;
