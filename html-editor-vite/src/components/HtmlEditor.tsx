import React from 'react';

interface HtmlEditorProps {
  htmlContent: string;
  onChange: (content: string) => void;
}

const HtmlEditor: React.FC<HtmlEditorProps> = ({ htmlContent, onChange }) => {
  return (
    <div className="flex flex-col h-full">
      <div className="p-2 bg-gray-100 border-b">
        <h2 className="text-lg font-medium">HTML Editor</h2>
      </div>
      <textarea
        value={htmlContent}
        onChange={(e) => onChange(e.target.value)}
        className="flex-grow p-4 font-mono text-sm resize-none focus:outline-none"
        spellCheck="false"
      />
    </div>
  );
};

export default HtmlEditor;