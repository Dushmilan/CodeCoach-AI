# CodeCoach AI 🚀

**CodeCoach AI** is your intelligent, personal coding companion designed to elevate your problem-solving skills. Whether you're preparing for technical interviews or just sharpening your algorithmic thinking, CodeCoach AI provides a seamless, modern environment to practice, learn, and grow.

---

## ✨ Features

- 🧠 **NVIDIA NIM AI Coach**: Real-time coding guidance powered by `meta/llama-3.1-8b-instruct`.
- ⚡ **Inline Code Execution**: Run your JavaScript solutions directly in the browser with an integrated console.
- 📋 **AI Code Review**: Get instant, comprehensive feedback on logic, complexity, and best practices with one click.
- 💡 **Quick-Action Chips**: One-tap access to hints, complexity analysis, optimal approaches, and edge case discovery.
- 💬 **Rich Chat Interface**: A freeform coach chat with Markdown support, code block rendering, and session management.
- 🔐 **Secure Key Management**: Volatile, memory-only storage for your NVIDIA API key—never persisted to disk or local storage.
- 💻 **Pro Editor Experience**: A high-performance code editor powered by **Monaco** (the engine behind VS Code).
- 📚 **Curated Problem Library**: Hand-picked challenges covering Strings, Arrays, Stacks, Linked Lists, and Dynamic Programming.
- 🎨 **Modern Glassmorphic UI**: A visually stunning interface with animated backgrounds, typing indicators, and message fade-in effects.
- 🔄 **Smart Navigation**: Quickly jump between problems, filter by difficulty, or take a leap of faith with the "Random" challenge button.

---

## 🛠️ Tech Stack

- **Framework**: [React 19](https://react.dev/)
- **AI Model**: [NVIDIA NIM (Llama 3.1 8B Instruct)](https://build.nvidia.com/meta/llama-3.1-8b-instruct)
- **Code Editor**: [@monaco-editor/react](https://github.com/suren-atoyan/monaco-react)
- **Markdown**: [react-markdown](https://github.com/remarkjs/react-markdown) & [remark-gfm](https://github.com/remarkjs/remark-gfm)
- **Proxy**: [http-proxy-middleware](https://github.com/chimurai/http-proxy-middleware) (Bypasses CORS for local development)
- **Styling**: Vanilla CSS3 (Custom Animations, Glassmorphism)

---

## 🚀 Getting Started

Follow these steps to get your own instance of CodeCoach AI running locally:

### Prerequisites
- [Node.js](https://nodejs.org/) (v16.x or higher recommended)
- npm or yarn
- **NVIDIA API Key**: Get a free key at [NVIDIA Build](https://build.nvidia.com/meta/llama-3.1-8b-instruct).

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/CodeCoach-AI.git
   ```

2. **Navigate to the project directory**:
   ```bash
   cd CodeCoach-AI/codecoach-ai
   ```

3. **Install dependencies**:
   ```bash
   npm install
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

5. **Enter your API Key**: When the app loads, paste your NVIDIA API key into the secure modal to enable the AI features.

---

## 📂 Project Structure

```text
codecoach-ai/
├── public/             # Static assets
└── src/
    ├── components/     # UI Components (AiBar, CodeEditor, ApiKeyModal, QuestionBar)
    ├── data/           # Questions and problem sets (JSON)
    ├── setupProxy.js   # Local development CORS proxy
    ├── App.js          # Main application logic & state management
    └── index.js        # Entry point
```

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for new problems, AI features, or UI improvements, feel free to open an issue or submit a pull request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Happy Coding!* 🎈
