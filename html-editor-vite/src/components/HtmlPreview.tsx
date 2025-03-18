import React from 'react';

interface HtmlPreviewProps {
  htmlContent: string;
  onSave: () => void;
}

const HtmlPreview: React.FC<HtmlPreviewProps> = ({ htmlContent, onSave }) => {
  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-2 bg-gray-100 border-b">
        <h2 className="text-lg font-medium">Preview</h2>
        <button 
          onClick={onSave}
          className="px-4 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Save HTML
        </button>
      </div>
      <div className="flex-grow p-4 overflow-auto bg-white">
        <iframe
          srcDoc={htmlContent}
          title="HTML Preview"
          className="w-full h-full border-0"
          sandbox="allow-scripts"
        />
      </div>
    </div>
  );
};

export default HtmlPreview;