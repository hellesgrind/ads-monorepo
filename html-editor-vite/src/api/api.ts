import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const generateHtmlFromImage = async (imageFile: File): Promise<string> => {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  try {
    const response = await axios.post(`${API_URL}/generate-html`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data.html;
  } catch (error) {
    console.error('Error generating HTML:', error);
    throw error;
  }
};

export const saveHtml = async (html: string): Promise<void> => {
  try {
    await axios.post(`${API_URL}/save-html`, { html });
  } catch (error) {
    console.error('Error saving HTML:', error);
    throw error;
  }
};