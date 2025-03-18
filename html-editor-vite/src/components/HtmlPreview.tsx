import React, { useState } from 'react';

interface HtmlPreviewProps {
  htmlContent: string;
  onSave: () => void;
}

const HtmlPreview: React.FC<HtmlPreviewProps> = ({ htmlContent, onSave }) => {
  const [scale, setScale] = useState(1);

  // Функция для изменения масштаба
  const changeScale = (newScale: number) => {
    setScale(newScale);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-2 bg-gray-100 border-b">
        <div className="flex items-center">
          <h2 className="text-lg font-medium mr-4">Preview</h2>
          <div className="flex items-center space-x-2">
            <button onClick={() => changeScale(0.5)} className="px-2 py-1 bg-gray-200 rounded">50%</button>
            <button onClick={() => changeScale(0.75)} className="px-2 py-1 bg-gray-200 rounded">75%</button>
            <button onClick={() => changeScale(1)} className="px-2 py-1 bg-gray-300 rounded">100%</button>
            <button onClick={() => changeScale(1.25)} className="px-2 py-1 bg-gray-200 rounded">125%</button>
          </div>
        </div>
        <button 
          onClick={onSave}
          className="px-4 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Save HTML
        </button>
      </div>
      <div 
        className="flex-grow overflow-auto bg-gray-100 p-4"
        style={{ 
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start'
        }}
      >
        <div style={{ 
          transform: `scale(${scale})`, 
          transformOrigin: 'top center',
          transition: 'transform 0.3s ease'
        }}>
          <iframe
            srcDoc={htmlContent}
            title="HTML Preview"
            style={{ 
              width: '1024px',  // Такой же ширины, как и в вашем HTML
              height: '1280px', // Такой же высоты, как и в вашем HTML
              border: '1px solid #ddd',
              background: 'white',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
            }}
            sandbox="allow-scripts allow-same-origin"
          />
        </div>
      </div>
    </div>
  );
};

export default HtmlPreview;