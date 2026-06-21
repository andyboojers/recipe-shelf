import React, { useState, useRef, useEffect } from 'react';

function ImageUploader({ onUploadComplete }) {
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [queuedFiles, setQueuedFiles] = useState([]);
  const inputRef = useRef(null);
  const queuedFilesRef = useRef([]);

  useEffect(() => {
    queuedFilesRef.current = queuedFiles;
  }, [queuedFiles]);

  useEffect(() => {
    return () => {
      queuedFilesRef.current.forEach(item => {
        if (item.previewUrl) {
          URL.revokeObjectURL(item.previewUrl);
        }
      });
    };
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleFilesAdded = (filesList) => {
    const newQueued = [];
    for (let i = 0; i < filesList.length; i++) {
      const file = filesList[i];
      const isValid = file && (
        file.type.startsWith('image/') || 
        file.type === 'application/pdf' || 
        /\.(jpg|jpeg|png|webp|gif|heic|heif|pdf)$/i.test(file.name)
      );
      if (isValid) {
        newQueued.push({
          id: Math.random().toString(36).substring(2, 9),
          file,
          previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
        });
      }
    }
    
    if (newQueued.length === 0) {
      alert('Please select valid image or PDF files');
      return;
    }
    
    setQueuedFiles(prev => [...prev, ...newQueued]);
  };

  const handleRemoveFile = (id) => {
    setQueuedFiles(prev => {
      const itemToRemove = prev.find(item => item.id === id);
      if (itemToRemove && itemToRemove.previewUrl) {
        URL.revokeObjectURL(itemToRemove.previewUrl);
      }
      return prev.filter(item => item.id !== id);
    });
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      handleFilesAdded(e.target.files);
    }
  };

  const handleExtract = async () => {
    if (queuedFiles.length === 0) return;
    setLoading(true);
    
    try {
      const imageParts = await Promise.all(queuedFiles.map(item => {
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const base64Data = e.target.result.split(',')[1];
            let mimeType = item.file.type;
            if (!mimeType || mimeType === "application/octet-stream") {
              const ext = item.file.name.split('.').pop().toLowerCase();
              if (ext === 'heic') mimeType = 'image/heic';
              else if (ext === 'heif') mimeType = 'image/heif';
              else if (ext === 'png') mimeType = 'image/png';
              else if (ext === 'webp') mimeType = 'image/webp';
              else if (ext === 'pdf') mimeType = 'application/pdf';
              else mimeType = 'image/jpeg';
            }
            resolve({
              image_data: base64Data,
              mime_type: mimeType
            });
          };
          reader.onerror = reject;
          reader.readAsDataURL(item.file);
        });
      }));

      const response = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images: imageParts })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Extraction failed');
      }
      const data = await response.json();
      
      // Cleanup all object URLs
      queuedFiles.forEach(item => {
        if (item.previewUrl) {
          URL.revokeObjectURL(item.previewUrl);
        }
      });
      setQueuedFiles([]);
      
      onUploadComplete(data);
    } catch (err) {
      alert('Error extracting recipes: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="glass-card" 
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      style={{ 
        textAlign: 'center', 
        transition: 'all 0.3s',
        border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--glass-border)'}`,
        background: dragActive ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
      }}
    >
      <input 
        ref={inputRef}
        type="file" 
        accept="image/*,application/pdf" 
        multiple
        onChange={handleChange} 
        style={{ display: 'none' }} 
      />

      {loading ? (
        <div className="loader-pulse" style={{ padding: '3rem 0' }}>
          <h2 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Extracting Recipes...</h2>
          <p style={{ color: 'var(--text-muted)' }}>Gemini is scanning your images.</p>
        </div>
      ) : queuedFiles.length === 0 ? (
        <div 
          onClick={() => inputRef.current.click()}
          style={{
            padding: '4rem 2rem',
            cursor: 'pointer'
          }}
        >
          <h3 style={{ marginBottom: '1rem' }}>Upload Recipe Pages</h3>
          <p style={{ color: 'var(--text-muted)' }}>Drag and drop multiple pages or screenshots here, or click to browse.</p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.5rem' }}>Supports images and PDFs.</p>
        </div>
      ) : (
        <div style={{ padding: '2rem 1rem' }}>
          <h3 style={{ marginBottom: '0.5rem' }}>Selected Recipe Pages</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            You have {queuedFiles.length} page{queuedFiles.length > 1 ? 's' : ''} queued. Drag and drop more files here to add them.
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
            gap: '1rem',
            maxHeight: '300px',
            overflowY: 'auto',
            padding: '0.5rem',
            background: 'rgba(0,0,0,0.15)',
            borderRadius: '8px',
            marginBottom: '2rem'
          }}>
            {queuedFiles.map(item => (
              <div key={item.id} style={{
                position: 'relative',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--glass-border)',
                borderRadius: '8px',
                padding: '0.5rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                aspectRatio: '1',
                overflow: 'hidden'
              }}>
                {item.previewUrl ? (
                  <img 
                    src={item.previewUrl} 
                    alt={item.file.name} 
                    style={{ width: '100%', height: '80%', objectFit: 'cover', borderRadius: '4px' }} 
                  />
                ) : (
                  <div style={{ fontSize: '2rem', color: 'var(--primary)' }}>📄</div>
                )}
                <span style={{
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                  width: '100%',
                  textAlign: 'center',
                  marginTop: '0.25rem'
                }}>
                  {item.file.name}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveFile(item.id);
                  }}
                  style={{
                    position: 'absolute',
                    top: '4px',
                    right: '4px',
                    background: 'rgba(239, 68, 68, 0.9)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: '20px',
                    height: '20px',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    fontSize: '12px',
                    boxShadow: 'none',
                    transform: 'none',
                    lineHeight: '1'
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            <button 
              onClick={() => inputRef.current.click()}
              style={{
                background: 'transparent',
                border: '1px solid var(--glass-border)',
                color: 'var(--text-main)',
                boxShadow: 'none'
              }}
            >
              Add More Pages
            </button>
            <button 
              onClick={handleExtract}
              style={{
                background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%)',
              }}
            >
              Extract Recipe ({queuedFiles.length} page{queuedFiles.length > 1 ? 's' : ''})
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ImageUploader;
