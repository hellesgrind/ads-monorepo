import { useState } from 'react';
import HtmlPreview from './components/HtmlPreview';
import HtmlEditor from './components/HtmlEditor';
import ImageUpload from './components/ImageUpload';
import { generateHtmlFromImage, saveHtml } from './api/api';

function App() {
  const [htmlContent, setHtmlContent] = useState<string>('<div>Upload an image to generate HTML</div>');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleImageUpload = async (file: File) => {
    setIsLoading(true);
    try {
      const html = await generateHtmlFromImage(file);
      setHtmlContent(html);
    } catch (error) {
      console.error('Failed to generate HTML', error);
      alert('Failed to generate HTML from image');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveHtml = async () => {
    try {
      await saveHtml(htmlContent);
      alert('HTML saved successfully!');
    } catch (error) {
      console.error('Failed to save HTML', error);
      alert('Failed to save HTML');
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-gray-800 text-white p-4">
        <h1 className="text-xl font-bold">HTML Editor</h1>
      </header>
      
      <div className="p-4">
        <ImageUpload onImageUpload={handleImageUpload} isLoading={isLoading} />
      </div>
      
      <div className="flex flex-1 gap-4 p-4 overflow-hidden">
        <div className="w-1/2 bg-white rounded shadow-md overflow-hidden">
          <HtmlPreview htmlContent={htmlContent} onSave={handleSaveHtml} />
        </div>
        <div className="w-1/2 bg-white rounded shadow-md overflow-hidden">
          <HtmlEditor htmlContent={htmlContent} onChange={setHtmlContent} />
        </div>
      </div>
    </div>
  );
}

export default App;