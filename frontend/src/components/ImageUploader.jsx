import React, { useState, useRef } from 'react';

function ImageUploader({ onUploadComplete }) {
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processFile = (file) => {
    console.log("[DEBUG] processFile called with file:", file ? { name: file.name, type: file.type, size: file.size } : null);
    const isImageOrPdf = file && (file.type.startsWith('image/') || file.type === 'application/pdf' || /\.(jpg|jpeg|png|webp|gif|heic|heif|pdf)$/i.test(file.name));
    if (!isImageOrPdf) {
      alert('Please upload a valid image or PDF file');
      return;
    }

    setLoading(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Data = e.target.result.split(',')[1]; // Remove data:image/jpeg;base64,
      const mimeType = file.type || "application/octet-stream";
      
      try {
        const response = await fetch('/api/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image_data: base64Data, mime_type: mimeType })
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Extraction failed');
        }
        const data = await response.json();
        onUploadComplete(data);
      } catch (err) {
        alert('Error extracting recipes: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="glass-card" style={{ textAlign: 'center', transition: 'all 0.3s' }}>
      {loading ? (
        <div className="loader-pulse" style={{ padding: '3rem 0' }}>
          <h2 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Extracting Recipes...</h2>
          <p style={{ color: 'var(--text-muted)' }}>Gemini is scanning your image.</p>
        </div>
      ) : (
        <div 
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
          style={{
            border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--glass-border)'}`,
            borderRadius: 'var(--card-radius)',
            padding: '4rem 2rem',
            cursor: 'pointer',
            background: dragActive ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
            transition: 'var(--transition)'
          }}
        >
          <input 
            ref={inputRef}
            type="file" 
            accept="image/*" 
            onChange={handleChange} 
            style={{ display: 'none' }} 
          />
          <h3 style={{ marginBottom: '1rem' }}>Upload Recipe Image</h3>
          <p style={{ color: 'var(--text-muted)' }}>Drag and drop a scan or screenshot here, or click to browse.</p>
        </div>
      )}
    </div>
  );
}

export default ImageUploader;
