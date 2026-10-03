# 🎨 ComicCraft – AI Comic Creator

ComicCraft is an AI-powered web application that creates personalized comics from a simple text prompt.

Users can provide a story idea, character name, setting, tone, and art style. The application automatically generates the comic story, creates AI-generated images, arranges them into panels, and exports the final comic as a PDF.

## ✨ Features

* 📝 AI-powered story generation
* 🎭 Custom character and story prompts
* 🖼️ AI-generated comic panel images
* 🎨 Multiple art styles
* 📚 Automatic 5-panel comic generation
* 📐 Automatic comic layout
* 📄 PDF export
* 🌐 FastAPI web application
* ☁️ Cloud deployment using Render

## 🛠️ Technologies Used

* **Python**
* **FastAPI**
* **Jinja2**
* **Gemini AI**
* **Cloudflare AI / FLUX**
* **Pillow**
* **FPDF / PDF generation**
* **HTML & CSS**
* **Render**

## 🔄 How It Works

```text
User Input
    ↓
AI Comic Outline
    ↓
Panel Story Generation
    ↓
AI Image Generation
    ↓
Comic Layout
    ↓
PDF Export
    ↓
Final Comic
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/anantheeshwaran01-bot/ComicCraft.git
cd ComicCraft
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows:**

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
```

### 6. Start the application

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## 🌐 Live Demo

**ComicCraft:**
https://comiccraft-l2ft.onrender.com/

## 📁 Project Structure

```text
ComicCraft/
│
├── app/
│   ├── main.py
│   ├── routes.py
│   ├── config.py
│   ├── schemas.py
│   ├── gemini_flash.py
│   ├── gemini_pro.py
│   ├── image_generator.py
│   ├── layout_builder.py
│   └── exporters.py
│
├── static/
│   └── css/
│
├── templates/
│   ├── index.html
│   ├── comic_preview.html
│   └── export_success.html
│
├── tests/
├── requirements.txt
├── render.yaml
├── .env.example
├── .gitignore
└── README.md
```

## 🎯 Project Goal

The main goal of ComicCraft is to demonstrate how AI can be used to automate the comic creation process by combining **AI text generation, image generation, web development, layout processing, and PDF export** into a single application.

## 👨‍💻 Authors

**Anantheeshwaran S
  Dharshath S
  Harish D
  Hemanathan M
  Ajay K**

B.Tech Artificial Intelligence and Data Science Students 
